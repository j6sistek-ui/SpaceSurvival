#include "SSHUD.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSAlienGallery.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "CanvasItem.h"
#include "EngineFontServices.h"
#include "Fonts/FontMeasure.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"

namespace
{
// Ring radius measured on each source texture. The four states were authored at slightly different
// scales, so drawing them at one bitmap size makes the ring itself jump by up to 14% between
// states. Fitting each to a shared ring radius instead leaves the tick marks as the only thing
// that moves: they sit outside the ring at rest and pinch inward while firing.
struct FSSCrosshairSource
{
    const TCHAR *Path;
    float NativeRingRadius;
};
const FSSCrosshairSource CrosshairSources[] = {
    {TEXT("/Game/SpaceSurvival/Licensed/UI/Crosshairs/T_Crosshair_Default.T_Crosshair_Default"), 33.71f},
    {TEXT("/Game/SpaceSurvival/Licensed/UI/Crosshairs/T_Crosshair_Firing.T_Crosshair_Firing"), 37.47f},
    {TEXT("/Game/SpaceSurvival/Licensed/UI/Crosshairs/T_Crosshair_Hit.T_Crosshair_Hit"), 38.30f},
    {TEXT("/Game/SpaceSurvival/Licensed/UI/Crosshairs/T_Crosshair_Boost.T_Crosshair_Boost"), 38.09f},
};
TAutoConsoleVariable<float> CrosshairRingRadius(TEXT("ss.CrosshairSize"), 16.f,
                                                TEXT("Crosshair ring radius in pixels at 1080p."));

// The owned EasyInputPrompts pack (RPT-20260916-18) exposes each device family as an instance of
// its own Blueprint PrimaryDataAsset class, PDA_KeysIconsMapping, which has no native C++ header.
// Reading its single "KeysIcons" TMap<FKey, UTexture2D*> property through reflection avoids adding
// a duplicate native mirror of a Blueprint-owned schema.
UTexture2D *FindKeyIcon(const UObject *Mapping, const FKey &Key)
{
    if (!Mapping)
        return nullptr;
    const FMapProperty *MapProp = FindFProperty<FMapProperty>(Mapping->GetClass(), TEXT("KeysIcons"));
    const FStructProperty *KeyProp = MapProp ? CastField<FStructProperty>(MapProp->KeyProp) : nullptr;
    const FObjectProperty *ValueProp = MapProp ? CastField<FObjectProperty>(MapProp->ValueProp) : nullptr;
    if (!KeyProp || !ValueProp)
        return nullptr;
    FScriptMapHelper Helper(MapProp, MapProp->ContainerPtrToValuePtr<void>(Mapping));
    for (int32 Index = 0; Index < Helper.GetMaxIndex(); ++Index)
    {
        if (!Helper.IsValidIndex(Index))
            continue;
        const FKey *Candidate = reinterpret_cast<const FKey *>(Helper.GetKeyPtr(Index));
        if (Candidate && *Candidate == Key)
            return Cast<UTexture2D>(ValueProp->GetObjectPropertyValue(Helper.GetValuePtr(Index)));
    }
    return nullptr;
}
} // namespace

FSlateFontInfo ASSHUD::HudFont(float Size) const
{
    FSlateFontInfo Font = GEngine->GetMediumFont()->GetLegacySlateFontInfo();
    // Request glyphs at their displayed size. Scaling a cached 10pt atlas quad
    // magnifies the bitmap and made the HUD/menu lettering visibly soft.
    Font.Size = FMath::Clamp(FMath::RoundToFloat(Font.Size * Size * Scale * 1.65f * 4.f) * .25f, 6.f, 64.f);
    return Font;
}
FVector2D ASSHUD::MeasureText(const FString &Value, float Size) const
{
    if (!FEngineFontServices::IsInitialized())
        return FVector2D::ZeroVector;
    const auto Measure = FEngineFontServices::Get().GetFontMeasure();
    const float Dpi = Canvas ? FMath::Max(.1f, Canvas->GetDPIScale()) : 1.f;
    return Measure.IsValid() ? FVector2D(Measure->Measure(Value, HudFont(Size), Dpi)) / Dpi : FVector2D::ZeroVector;
}
void ASSHUD::Text(const FString &Value, float X, float Y, float Size, FLinearColor Color)
{
    FCanvasTextItem Item(FVector2D(FMath::RoundToFloat(X), FMath::RoundToFloat(Y)), FText::FromString(Value),
                         HudFont(Size), Color);
    Canvas->DrawItem(Item);
}
bool ASSHUD::UsingGamepad() const
{
    const auto *PC = Cast<ASSPlayerController>(GetOwningPlayerController());
    return PC && PC->GetInputFamily() == ESSInputFamily::Gamepad;
}
UTexture2D *ASSHUD::GlyphTexture(const FKey &Key, bool Gamepad)
{
    // Lazily resolved rather than loaded in BeginPlay: this HUD class also runs for automation
    // fixtures that never touch a prompt, so a build without the licensed pack staged still runs.
    if (Gamepad)
    {
        if (!GamepadIcons)
            GamepadIcons = LoadObject<UObject>(nullptr,
                                               TEXT("/Game/EasyInputPrompts/Datas/IconsData/DA_InputsPrompt_XB_Gamepad."
                                                    "DA_InputsPrompt_XB_Gamepad"),
                                               nullptr, LOAD_NoWarn | LOAD_Quiet);
        return FindKeyIcon(GamepadIcons, Key);
    }
    if (!KeyboardMouseIcons)
        KeyboardMouseIcons = LoadObject<UObject>(
            nullptr,
            TEXT("/Game/EasyInputPrompts/Datas/IconsData/DA_InputsPrompt_KeyboardMouse.DA_InputsPrompt_KeyboardMouse"),
            nullptr, LOAD_NoWarn | LOAD_Quiet);
    return FindKeyIcon(KeyboardMouseIcons, Key);
}
float ASSHUD::Glyph(const FKey &KeyboardKey, const FKey &GamepadKey, float X, float Y, float Size, FLinearColor Color)
{
    const bool Gamepad = UsingGamepad();
    const FKey &Key = Gamepad ? GamepadKey : KeyboardKey;
    const float Extent = FMath::RoundToFloat(22.f * Size * Scale);
    if (UTexture2D *Texture = GlyphTexture(Key, Gamepad))
    {
        FCanvasTileItem Item(FVector2D(FMath::RoundToFloat(X), FMath::RoundToFloat(Y)), Texture->GetResource(),
                             FVector2D(Extent, Extent), Color);
        Item.BlendMode = SE_BLEND_Translucent;
        Canvas->DrawItem(Item);
        return Extent;
    }
    // The pack not being staged in this build, or a name it does not carry, must not blank the
    // prompt out; the key's own display name keeps it legible either way.
    Text(Key.GetDisplayName().ToString(), X, Y, Size, Color);
    return MeasureText(Key.GetDisplayName().ToString(), Size).X;
}
void ASSHUD::DrawCrosshair(ASSShip *Ship, float CentreX, float CentreY)
{
    if (CrosshairTextures.Num() != UE_ARRAY_COUNT(CrosshairSources))
    {
        CrosshairTextures.Reset();
        for (const FSSCrosshairSource &Source : CrosshairSources)
            CrosshairTextures.Add(LoadObject<UTexture2D>(nullptr, Source.Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
    }
    float Power = 0.f, Damage = 0.f;
    bool Boosting = false, Braking = false;
    Ship->GetDrivePresentation(Power, Boosting, Braking, Damage);
    const auto *GM = Cast<ASSGameMode>(UGameplayStatics::GetGameMode(this));
    // A connecting shot outranks the act of firing, which outranks boosting.
    int32 State = 0;
    if (GM && GM->PlayerHitFlashSeconds > 0.f)
        State = 2;
    else if (Ship->IsFiring())
        State = 1;
    else if (Boosting)
        State = 3;
    UTexture2D *Texture = CrosshairTextures.IsValidIndex(State) ? CrosshairTextures[State].Get() : nullptr;
    if (!Texture || !Texture->GetResource())
    {
        // The art is absent from this build; the original three ticks still mark the aim point.
        DrawLine(CentreX - 14 * Scale, CentreY, CentreX - 5 * Scale, CentreY, FLinearColor::White, 1.3f);
        DrawLine(CentreX + 5 * Scale, CentreY, CentreX + 14 * Scale, CentreY, FLinearColor::White, 1.3f);
        DrawLine(CentreX, CentreY - 14 * Scale, CentreX, CentreY - 5 * Scale, FLinearColor::White, 1.3f);
        return;
    }
    const float Ring = FMath::Max(4.f, CrosshairRingRadius.GetValueOnGameThread()) * Scale;
    const float Fit = Ring / CrosshairSources[State].NativeRingRadius;
    const FVector2D Size(Texture->GetSizeX() * Fit, Texture->GetSizeY() * Fit);
    FCanvasTileItem Item(FVector2D(CentreX - Size.X * .5f, CentreY - Size.Y * .5f), Texture->GetResource(), Size,
                         FLinearColor::White);
    // Straight-alpha over. The kit's glow keeps full-saturation colour as alpha falls off, so a
    // premultiplied mode blooms the faint halo into a solid cyan block.
    Item.BlendMode = SE_BLEND_Translucent;
    Canvas->DrawItem(Item);
}
float ASSHUD::Paragraph(const FString &Value, float X, float Y, float Width, float Size, FLinearColor Color,
                        bool Render)
{
    TArray<FString> Paragraphs;
    Value.ParseIntoArrayLines(Paragraphs, false);
    const float StartY = Y;
    float TextWidth = 0, LineHeight = 0;
    LineHeight = MeasureText(TEXT("Mg"), Size).Y;
    LineHeight = FMath::Max(LineHeight + 4 * Scale, 17 * Scale);
    for (const auto &Part : Paragraphs)
    {
        TArray<FString> Words;
        Part.ParseIntoArray(Words, TEXT(" "), true);
        FString Line;
        for (const auto &Word : Words)
        {
            const FString Candidate = Line.IsEmpty() ? Word : Line + TEXT(" ") + Word;
            TextWidth = MeasureText(Candidate, Size).X;
            if (!Line.IsEmpty() && TextWidth > Width)
            {
                if (Render)
                    Text(Line, X, Y, Size, Color);
                Y += LineHeight;
                Line = Word;
            }
            else
                Line = Candidate;
        }
        if (Render)
            Text(Line, X, Y, Size, Color);
        Y += LineHeight;
    }
    return Y - StartY;
}
void ASSHUD::Stroke(FVector2D A, FVector2D B, FLinearColor Color, float Width)
{
    // A dark under-stroke retains the symbol against stars, lamps and light rock.
    DrawLine(A.X, A.Y, B.X, B.Y, FLinearColor(0.f, .008f, .015f, .8f), (Width + 2.f) * Scale);
    DrawLine(A.X, A.Y, B.X, B.Y, Color, Width * Scale);
}
void ASSHUD::ThreatGlyph(FVector2D Centre, bool Flanker, bool Charging, float Size, FLinearColor Color)
{
    const float R = Size * Scale;
    if (Flanker)
    {
        // Split wings versus one pursuit arrow: identity does not rely on color.
        Stroke(Centre + FVector2D(-R, R * .4f), Centre + FVector2D(-R * .45f, -R * .45f), Color);
        Stroke(Centre + FVector2D(-R * .45f, -R * .45f), Centre + FVector2D(0.f, R * .15f), Color);
        Stroke(Centre + FVector2D(R, R * .4f), Centre + FVector2D(R * .45f, -R * .45f), Color);
        Stroke(Centre + FVector2D(R * .45f, -R * .45f), Centre + FVector2D(0.f, R * .15f), Color);
    }
    else
    {
        Stroke(Centre + FVector2D(-R * .65f, R * .45f), Centre + FVector2D(0.f, -R * .5f), Color);
        Stroke(Centre + FVector2D(0.f, -R * .5f), Centre + FVector2D(R * .65f, R * .45f), Color);
    }
    if (Charging)
        Stroke(Centre + FVector2D(-R, R * .9f), Centre + FVector2D(R, R * .9f), FLinearColor(1.f, .94f, .7f), 2.f);
}
void ASSHUD::DrawCombatCues(ASSShip *Ship, bool ShowRadar)
{
    if (!PlayerOwner || !PlayerOwner->PlayerCameraManager)
        return;
    const float W = Canvas->SizeX, H = Canvas->SizeY;
    const FVector2D Centre(W * .5f, H * .5f);
    const FVector2D Radar(W - 107.f * Scale, 210.f * Scale);
    const float RadarRadius = 63.f * Scale, RadarRange = 10000.f;
    const FLinearColor Grid(.18f, .33f, .4f, .65f);
    const FRotator ViewRotation = PlayerOwner->PlayerCameraManager->GetCameraRotation();
    const FVector ViewRight = FRotationMatrix(ViewRotation).GetUnitAxis(EAxis::Y);
    if (ShowRadar)
    {
        DrawRect(FLinearColor(.008f, .018f, .03f, .72f), Radar.X - 78.f * Scale, Radar.Y - 92.f * Scale, 156.f * Scale,
                 180.f * Scale);
        Text(TEXT("HOSTILES"), Radar.X - 44.f * Scale, Radar.Y - 85.f * Scale, .52f, FLinearColor(.65f, .83f, .9f));
        for (int32 Ring = 1; Ring <= 2; ++Ring)
            for (int32 Segment = 0; Segment < 32; ++Segment)
            {
                const float A = 2.f * PI * Segment / 32.f, B = 2.f * PI * (Segment + 1) / 32.f;
                const float R = RadarRadius * Ring * .5f;
                DrawLine(Radar.X + FMath::Cos(A) * R, Radar.Y + FMath::Sin(A) * R, Radar.X + FMath::Cos(B) * R,
                         Radar.Y + FMath::Sin(B) * R, Grid, Scale);
            }
        DrawLine(Radar.X - RadarRadius, Radar.Y, Radar.X + RadarRadius, Radar.Y, Grid, Scale);
        DrawLine(Radar.X, Radar.Y - RadarRadius, Radar.X, Radar.Y + RadarRadius, Grid, Scale);
        Stroke(Radar + FVector2D(-4.f, 5.f) * Scale, Radar + FVector2D(0.f, -5.f) * Scale, FLinearColor::White);
        Stroke(Radar + FVector2D(0.f, -5.f) * Scale, Radar + FVector2D(4.f, 5.f) * Scale, FLinearColor::White);
        Text(TEXT("100 m"), Radar.X - 23.f * Scale, Radar.Y + 70.f * Scale, .48f, FLinearColor(.65f, .75f, .8f));
    }
    for (TActorIterator<ASSEnemy> It(GetWorld()); It; ++It)
    {
        if (It->IsActorBeingDestroyed())
            continue;
        const bool Flanker = It->GetKind() == ESSWorldKind::Flanker, Charging = It->IsChargingShot();
        // Affiliation has one consistent color; glyph shape identifies the archetype.
        const FLinearColor Color(1.f, .32f, .25f);
        const FVector Position = It->GetActorLocation();
        const FVector Local = Ship->GetActorTransform().InverseTransformPosition(Position);
        if (ShowRadar)
        {
            // Radial clamp denotes a contact beyond range without warping its bearing.
            const FVector2D Offset =
                FVector2D(Local.Y, -Local.X).GetClampedToMaxSize(RadarRange) / RadarRange * RadarRadius;
            ThreatGlyph(Radar + Offset, Flanker, Charging, 4.f, Color);
        }
        FVector2D Screen;
        const bool InFront = PlayerOwner->ProjectWorldLocationToScreen(Position, Screen);
        const bool OnScreen = InFront && Screen.X > 25.f * Scale && Screen.X < W - 25.f * Scale &&
                              Screen.Y > 125.f * Scale && Screen.Y < H - 180.f * Scale;
        if (OnScreen)
        {
            FVector2D Edge;
            float Radius = 18.f * Scale;
            if (PlayerOwner->ProjectWorldLocationToScreen(Position + ViewRight * It->GetBodyRadius(), Edge))
                Radius = FMath::Clamp(float(FVector2D::Distance(Screen, Edge)), 18.f * Scale, 90.f * Scale);
            const float GlyphY = FMath::Max(float(Screen.Y) - Radius - 12.f * Scale, 125.f * Scale);
            ThreatGlyph(FVector2D(Screen.X, GlyphY), Flanker, Charging, 9.f, Color);
            Text(Charging ? TEXT("HOSTILE / FIRING") : TEXT("HOSTILE"), Screen.X + 14.f * Scale, GlyphY - 8.f * Scale,
                 .45f, Color);
        }
        else if (Charging)
        {
            // An off-screen committed shot keeps a directional cue in addition to audio.
            FVector2D Direction = InFront ? Screen - Centre : FVector2D(Local.Y, -Local.Z);
            if (Direction.IsNearlyZero())
                Direction = FVector2D(0.f, 1.f);
            Direction.Normalize();
            const FVector2D At = Centre + Direction * FMath::Min(W * .38f, H * .32f);
            ThreatGlyph(At, Flanker, true, 8.f, Color);
        }
    }
    if (IsValid(Ship->SoftTarget))
    {
        FVector2D Screen;
        if (PlayerOwner->ProjectWorldLocationToScreen(Ship->SoftTarget->GetActorLocation(), Screen) &&
            Screen.X > 70.f * Scale && Screen.X < W - 70.f * Scale && Screen.Y > 125.f * Scale &&
            Screen.Y < H - 180.f * Scale)
        {
            const FLinearColor Lock(.48f, 1.f, .85f);
            const float R = 22.f * Scale, Arm = 8.f * Scale;
            for (int32 XSign : {-1, 1})
                for (int32 YSign : {-1, 1})
                {
                    const FVector2D Corner = Screen + FVector2D(XSign * R, YSign * R);
                    Stroke(Corner, Corner - FVector2D(XSign * Arm, 0.f), Lock, 1.5f);
                    Stroke(Corner, Corner - FVector2D(0.f, YSign * Arm), Lock, 1.5f);
                }
            if (const auto *Target = Cast<ASSWorldBody>(Ship->SoftTarget))
            {
                const FString Label =
                    (Cast<ASSEnemy>(Target) ? TEXT("HOSTILE / ") : TEXT("HAZARD / ")) + Target->GetLabel();
                const float LabelWidth = MeasureText(Label, .5f).X;
                float LabelX = Screen.X + 29.f * Scale;
                if (LabelX + LabelWidth > W - 12.f * Scale)
                    LabelX = Screen.X - 29.f * Scale - LabelWidth;
                LabelX = FMath::Clamp(LabelX, 12.f * Scale, FMath::Max(12.f * Scale, W - LabelWidth - 12.f * Scale));
                Text(Label, LabelX, Screen.Y - 8.f * Scale, .5f, Lock);
            }
        }
    }
}
void ASSHUD::Meter(const FString &Name, double Value, double Maximum, float X, float Y, FLinearColor Color)
{
    DrawRect(FLinearColor(.015f, .025f, .045f, .9f), X, Y, 220 * Scale, 29 * Scale);
    DrawRect(Color, X, Y + 25 * Scale, 220 * Scale * FMath::Clamp(float(Value / FMath::Max(1.0, Maximum)), 0.f, 1.f),
             4 * Scale);
    Text(FString::Printf(TEXT("%s  %.0f / %.0f"), *Name, Value, Maximum), X + 8 * Scale, Y + 4 * Scale, .75f);
}
int32 ASSHUD::MenuIndexAt(FVector2D Point) const
{
    for (int I = 0; I < MenuBounds.Num(); ++I)
        if (MenuBounds[I].IsInside(Point))
            return I;
    return INDEX_NONE;
}
void ASSHUD::DrawHUD()
{
    Super::DrawHUD();
    MenuBounds.Empty();
    if (!Canvas)
        return;
    auto *GI = GetGameInstance<USSGameInstance>();
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!GI || !GM)
        return;
    const auto &S = GI->Session;
    const auto Stats = S.Stats();
    Scale = FMath::Clamp(float(Canvas->SizeY) / 1080.f * float(S.settings.uiScale), .65f, 1.6f);
    const float W = Canvas->SizeX, H = Canvas->SizeY, Margin = 30 * Scale;
    if (GM->AlienGallery && GM->AlienGallery->IsActive())
    {
        DrawRect(FLinearColor(.01f, .015f, .025f, .9f), Margin - 10, Margin - 8, W - 2 * Margin + 20, 120 * Scale);
        Text(GM->AlienGallery->Status(), Margin, Margin, .8f, FLinearColor(.55f, .95f, 1));
        Paragraph(TEXT("WASD / left stick: fly | mouse / right stick: look | E Q / bumpers: rise & fall | Shift / RT: "
                       "fast | Ctrl / LT: slow"),
                  Margin, Margin + 35 * Scale, W - 2 * Margin, .55f, FLinearColor::White);
        Text(TEXT("Tab / Y: switch showcase & all assets | Home / Start: reset view | Esc / B: return to station"),
             Margin, Margin + 78 * Scale, .55f);
        return;
    }
    const bool MenuOpen = GM->IsMenuOpen();
    const auto *Walker = Cast<ASSWalker>(UGameplayStatics::GetPlayerPawn(this, 0));
    if (S.run.active)
    {
        const FString Location =
            Walker ? (GM->InHangar() ? TEXT("HOME HANGAR")
                                     : FString::Printf(TEXT("STATION %02d"), FMath::Max(1, S.run.wave / 5)))
                   : FString::Printf(TEXT("WAVE %02d"), S.run.wave);
        Text(Location, Margin, Margin, 1.5f);
        Text(FString::Printf(TEXT("%d CREDITS"), S.run.credits), W - 250 * Scale, Margin, 1.f,
             FLinearColor(1, .78f, .35f));
        Meter(TEXT("HULL"), S.run.hull, Stats.maxHull, Margin, H - 150 * Scale, FLinearColor(.35f, .9f, .65f));
        Meter(TEXT("SHIELD"), S.run.shield, Stats.maxShield, Margin, H - 112 * Scale, FLinearColor(.25f, .7f, 1));
        if (!Walker)
        {
            Meter(TEXT("BOOST"), S.run.boost, 100, Margin, H - 74 * Scale, FLinearColor(.7f, .4f, 1));
            Meter(S.run.brakeOverheated ? TEXT("BRAKE OVERHEAT") : TEXT("BRAKE HEAT"), S.run.brakeHeat, 100,
                  W - 250 * Scale, H - 112 * Scale, FLinearColor(1, .6f, .25f));
            Text(S.run.weapon == SS::Weapon::RapidLaser ? TEXT("RAPID LASER") : TEXT("HEAVY CANNON"), W - 250 * Scale,
                 H - 68 * Scale, .9f);
        }
        if (S.run.criticalSeconds > 0)
            Text(TEXT("! SUBSYSTEM IMPAIRED / REPAIR AVAILABLE"), Margin, 100 * Scale, .9f, FLinearColor(1, .7f, .2f));
        if (S.run.contract != SS::Contract::None)
        {
            const bool Hunter = S.run.contract == SS::Contract::Objective;
            const FString Objective = FString::Printf(
                TEXT("%s: %d / %d"),
                Hunter ? TEXT("HUNTER CONTRACT / Destroy enemy ships") : TEXT("PRESSURE CONTRACT / Survive waves"),
                FMath::Min(S.run.contractProgress, S.run.contractTarget), S.run.contractTarget);
            const FString Terms = S.run.contractProgress >= S.run.contractTarget
                                      ? TEXT("Objective met / reach Station 2 to collect reward")
                                      : TEXT("Complete before Station 2 / reward paid on arrival");
            const float PanelW = FMath::Min(490.f * Scale, W - 2.f * Margin);
            const float ObjectiveH =
                Paragraph(Objective, 0, 0, PanelW - 20.f * Scale, .65f, FLinearColor::White, false);
            const float TermsH = Paragraph(Terms, 0, 0, PanelW - 20.f * Scale, .52f, FLinearColor::White, false);
            DrawRect(FLinearColor(.015f, .025f, .04f, .88f), Margin, 133.f * Scale, PanelW,
                     ObjectiveH + TermsH + 16.f * Scale);
            Paragraph(Objective, Margin + 10.f * Scale, 141.f * Scale, PanelW - 20.f * Scale, .65f,
                      FLinearColor(.8f, .94f, 1.f));
            Paragraph(Terms, Margin + 10.f * Scale, 141.f * Scale + ObjectiveH, PanelW - 20.f * Scale, .52f,
                      FLinearColor(.7f, .8f, .85f));
        }
    }
    // Observe credited kills, not disappearing actors: hazards/despawns are not player kills.
    // A new or resumed run establishes a baseline and never replays old confirmations.
    const FString CurrentRun = UTF8_TO_TCHAR(S.run.id.c_str());
    if (FeedbackRun != CurrentRun || S.run.kills < ObservedKills)
    {
        FeedbackRun = CurrentRun;
        ObservedKills = S.run.kills;
        KillNoticeUntil = 0.f;
        RecentKills = 0;
    }
    const float Now = GetWorld()->GetTimeSeconds();
    if (S.run.kills > ObservedKills)
    {
        RecentKills = (Now < KillNoticeUntil ? RecentKills : 0) + S.run.kills - ObservedKills;
        ObservedKills = S.run.kills;
        KillNoticeUntil = Now + 2.2f;
    }
    if (S.IsFlying() && Now < KillNoticeUntil && !MenuOpen)
    {
        const FString Notice =
            RecentKills > 1 ? FString::Printf(TEXT("%d HOSTILES DESTROYED"), RecentKills) : TEXT("HOSTILE DESTROYED");
        const float NoticeW = MeasureText(Notice, .7f).X;
        DrawRect(FLinearColor(.015f, .025f, .04f, .88f), (W - NoticeW) * .5f - 12.f * Scale, H * .5f + 44.f * Scale,
                 NoticeW + 24.f * Scale, 32.f * Scale);
        Text(Notice, (W - NoticeW) * .5f, H * .5f + 50.f * Scale, .7f, FLinearColor(.65f, 1.f, .8f));
    }
    if (auto *Ship = GM->GetPlayerShip(); Ship && S.IsFlying())
    {
        DrawCrosshair(Ship, W * .5f, H * .5f);
        DrawCombatCues(Ship, GM->Director && GM->Director->GetActiveThreatCount() > 3);
        if (Ship->IsMoored())
            Text(TEXT("MAGNETIC LOCK / Close services to release"), Margin, H - 195.f * Scale, .7f,
                 FLinearColor(.55f, .95f, 1.f));
        ASSEncounterBeacon *InteractBeacon = nullptr;
        float InteractDistance = MAX_flt;
        if (!MenuOpen && !Walker && !S.run.pendingReward)
            for (TActorIterator<ASSEncounterBeacon> It(GetWorld()); It; ++It)
                if (It->IsPlayerInRange() && !It->IsResolved())
                {
                    const float Distance = FVector::DistSquared(Ship->GetActorLocation(), It->GetActorLocation());
                    if (Distance < InteractDistance)
                    {
                        InteractDistance = Distance;
                        InteractBeacon = *It;
                    }
                }
        for (TActorIterator<ASSEncounterBeacon> It(GetWorld()); It; ++It)
        {
            if (It->IsResolved())
                continue;
            FVector2D Screen(W * .5f, 180 * Scale);
            if (!PlayerOwner->ProjectWorldLocationToScreen(It->GetActorLocation(), Screen))
            {
                const FVector Local = Ship->GetActorTransform().InverseTransformPosition(It->GetActorLocation());
                Screen = FVector2D(Local.Y < 0 ? 180 * Scale : W - 360 * Scale, H * .5f);
            }
            const float Meters = FVector::Dist(Ship->GetActorLocation(), It->GetActorLocation()) / 100.f;
            const FString Label = FString::Printf(TEXT("<> %s / %.0f m"), *It->GetEncounterLabel(), Meters);
            const bool ShowPrompt = *It == InteractBeacon && !It->IsAccepted();
            const FLinearColor LabelColor(1, .8f, .4f);
            const float Padding = 10.f * Scale, PanelW = FMath::Min(420.f * Scale, W - 2.f * Margin);
            const float TextW = PanelW - 2.f * Padding;
            const float LabelH = Paragraph(Label, 0, 0, TextW, .7f, LabelColor, false);
            const float GlyphGap = 6.f * Scale;
            const float PromptH =
                ShowPrompt ? Paragraph(TEXT("INTERACT"), 0, 0, TextW, .7f, FLinearColor::White, false) : 0.f;
            const float PanelH = LabelH + PromptH + 2.f * Padding;
            Screen.X = FMath::Clamp(float(Screen.X), Margin, W - Margin - PanelW);
            Screen.Y = FMath::Clamp(float(Screen.Y), Margin, H - Margin - PanelH);
            DrawRect(FLinearColor(.015f, .025f, .04f, .94f), Screen.X, Screen.Y, PanelW, PanelH);
            Paragraph(Label, Screen.X + Padding, Screen.Y + Padding, TextW, .7f, LabelColor);
            if (ShowPrompt)
            {
                const float GlyphW = Glyph(EKeys::E, EKeys::Gamepad_FaceButton_Bottom, Screen.X + Padding,
                                           Screen.Y + Padding + LabelH, .7f);
                Paragraph(TEXT("INTERACT"), Screen.X + Padding + GlyphW + GlyphGap, Screen.Y + Padding + LabelH,
                          TextW - GlyphW - GlyphGap, .7f, FLinearColor::White);
            }
        }
        if (S.run.phase == SS::Phase::Approach)
        {
            FVector2D Screen(W * .5f, 130 * Scale);
            if (!PlayerOwner->ProjectWorldLocationToScreen(GM->StationTarget, Screen))
            {
                const FVector Local = Ship->GetActorTransform().InverseTransformPosition(GM->StationTarget);
                Screen = FVector2D(Local.Y < 0 ? 100 * Scale : W - 300 * Scale, H * .5f);
            }
            Screen.X = FMath::Clamp(Screen.X, 100 * Scale, W - 300 * Scale);
            Screen.Y = FMath::Clamp(Screen.Y, 130 * Scale, H - 180 * Scale);
            Text(TEXT("[ STATION ]  APPROACH"), Screen.X, Screen.Y, .9f, FLinearColor(.45f, .9f, 1));
        }
    }
    if (auto *Ship = GM->GetPlayerShip(); Ship && S.IsFlying() && GM->ThreatWarningSeconds > 0.f)
    {
        const float AlertW = FMath::Min(620.f * Scale, W - 2.f * Margin);
        const float AlertX = (W - AlertW) * .5f, AlertY = H * .22f;
        DrawRect(FLinearColor(.04f, .025f, .02f, .94f), AlertX, AlertY, AlertW, 42.f * Scale);
        Text(TEXT("!  ") + GM->ThreatWarning, AlertX + 12.f * Scale, AlertY + 11.f * Scale, .8f,
             FLinearColor(1.f, .83f, .52f));
        if (FVector::DistSquared(GM->ThreatPosition, Ship->GetActorLocation()) > 1.f)
        {
            const FVector2D Centre(W * .5f, H * .5f);
            FVector2D Screen;
            const bool InFront = PlayerOwner->ProjectWorldLocationToScreen(GM->ThreatPosition, Screen);
            FVector2D Direction;
            if (InFront)
                Direction = Screen - Centre;
            else
            {
                const FVector Local = Ship->GetActorTransform().InverseTransformPosition(GM->ThreatPosition);
                Direction = FVector2D(Local.Y, -Local.Z);
            }
            if (Direction.IsNearlyZero())
                Direction = FVector2D(0.f, -1.f);
            Direction.Normalize();
            const FVector2D Tip = Centre + Direction * FMath::Min(W * .32f, H * .28f);
            const FVector2D Side(-Direction.Y, Direction.X);
            const FVector2D Base = Tip - Direction * 18.f * Scale;
            const FLinearColor CueColor(1.f, .83f, .52f);
            DrawLine(Tip.X, Tip.Y, Base.X + Side.X * 10.f * Scale, Base.Y + Side.Y * 10.f * Scale, CueColor, 3.f);
            DrawLine(Tip.X, Tip.Y, Base.X - Side.X * 10.f * Scale, Base.Y - Side.Y * 10.f * Scale, CueColor, 3.f);
            Text(InFront ? TEXT("!") : TEXT("! BEHIND"), Tip.X + 12.f * Scale, Tip.Y - 8.f * Scale, .7f, CueColor);
        }
    }
    if (S.settings.subtitles && GM->PilotReactionSeconds > 0.f)
    {
        const float CaptionW = FMath::Min(700.f * Scale, W - 2.f * Margin);
        const float CaptionX = (W - CaptionW) * .5f, CaptionY = H - 215.f * Scale;
        DrawRect(FLinearColor(.015f, .025f, .04f, .9f), CaptionX, CaptionY, CaptionW, 50.f * Scale);
        Paragraph(GM->PilotReaction, CaptionX + 12.f * Scale, CaptionY + 10.f * Scale, CaptionW - 24.f * Scale, .75f,
                  FLinearColor(.9f, .94f, 1.f));
    }
    if (!MenuOpen && (!Walker || !Walker->IsDisembarking()))
    {
        FString InteractionHint, HintPrefix, HintSuffix;
        FLinearColor HintColor = FLinearColor::White;
        bool GlyphBeforeHint = false, GlyphInsideHint = false;
        // Match Interact: walking always targets a service; pending rewards take priority only in the ship.
        if (Walker)
        {
            for (TActorIterator<ASSStation> It(GetWorld()); It; ++It)
            {
                FString Label;
                const auto Service = It->NearestService(Walker->GetActorLocation(), Label);
                if (Service != ESSPanel::None)
                {
                    GlyphBeforeHint = true;
                    InteractionHint =
                        Service == ESSPanel::Reward && S.run.pendingReward ? TEXT("CHOOSE SECURED REWARD") : Label;
                    break;
                }
            }
            if (InteractionHint.IsEmpty() && S.run.pendingReward)
            {
                InteractionHint = TEXT("REWARD SECURED / visit the Beacon Log");
                HintColor = FLinearColor(1, .8f, .4f);
            }
            Text(TEXT("WASD / left stick: walk | Mouse / right stick: turn | Shift / X: run | Esc / Menu: shell"),
                 Margin, H - 35 * Scale, .65f);
        }
        else if (GM->GetPlayerShip() && S.run.active && S.run.pendingReward)
        {
            GlyphInsideHint = true;
            HintPrefix = TEXT("REWARD SECURED / ");
            HintSuffix = TEXT(" to choose");
            HintColor = FLinearColor(1, .8f, .4f);
        }
        const float HintX = W * .5f - 200 * Scale, HintY = H - 80 * Scale, HintSize = .9f;
        const float GlyphGap = 6.f * Scale;
        if (GlyphBeforeHint)
        {
            const float GlyphW = Glyph(EKeys::E, EKeys::Gamepad_FaceButton_Bottom, HintX, HintY, HintSize, HintColor);
            Text(InteractionHint, HintX + GlyphW + GlyphGap, HintY, HintSize, HintColor);
        }
        else if (GlyphInsideHint)
        {
            Text(HintPrefix, HintX, HintY, HintSize, HintColor);
            const float PrefixW = MeasureText(HintPrefix, HintSize).X;
            const float GlyphW =
                Glyph(EKeys::E, EKeys::Gamepad_FaceButton_Bottom, HintX + PrefixW, HintY, HintSize, HintColor);
            Text(HintSuffix, HintX + PrefixW + GlyphW + GlyphGap, HintY, HintSize, HintColor);
        }
        else if (!InteractionHint.IsEmpty())
            Text(InteractionHint, HintX, HintY, HintSize, HintColor);
    }
    if (GM->IsAnnouncementVisible())
    {
        DrawRect(FLinearColor(.02f, .025f, .05f, .88f), Margin, 65 * Scale, W - 2 * Margin, 48 * Scale);
        Text(GM->Announcement, Margin + 12 * Scale, 77 * Scale, .75f);
    }
    if (GM->IsMenuOpen())
    {
        const bool Live = S.IsFlying() && (GM->Panel == ESSPanel::Depot || GM->Panel == ESSPanel::Reward);
        const float PW = Live ? FMath::Min(530.f * Scale, W * .43f) : FMath::Min(840.f * Scale, W - 80.f * Scale);
        const float X = Live ? W - PW - Margin : (W - PW) * .5f;
        const float DetailHeight = Paragraph(GM->PanelDetail, 0, 0, PW - 60.f * Scale, .7f, FLinearColor::White, false);
        const float MaxHeight = H - 100.f * Scale;
        const float RowH =
            FMath::Min(44.f * Scale, (MaxHeight - 136.f * Scale - DetailHeight) / FMath::Max(1, GM->Entries.Num()));
        const float PH = 136.f * Scale + DetailHeight + RowH * GM->Entries.Num();
        const float Y = (H - PH) * .5f;
        if (!Live)
            DrawRect(FLinearColor(0, 0, .015f, .32f), 0, 0, W, H);
        DrawRect(FLinearColor(.012f, .02f, .04f, .95f), X, Y, PW, PH);
        DrawRect(FLinearColor(.4f, .8f, .9f), X, Y, 4.f * Scale, PH);
        DrawRect(FLinearColor(.12f, .24f, .3f), X + 28.f * Scale, Y + 61.f * Scale, PW - 56.f * Scale, Scale);
        Text(GM->PanelTitle, X + 30.f * Scale, Y + 20.f * Scale, 1.25f, FLinearColor(.8f, .92f, 1));
        Paragraph(GM->PanelDetail, X + 30.f * Scale, Y + 78.f * Scale, PW - 60.f * Scale, .7f,
                  FLinearColor(.68f, .75f, .85f));
        float RowY = Y + 101.f * Scale + DetailHeight;
        for (int I = 0; I < GM->Entries.Num(); ++I)
        {
            const auto &Entry = GM->Entries[I];
            const bool Selected = I == GM->SelectedEntry;
            DrawRect(Selected ? FLinearColor(.075f, .18f, .25f) : FLinearColor(.025f, .045f, .07f), X + 25.f * Scale,
                     RowY, PW - 50.f * Scale, RowH - 4.f * Scale);
            if (Selected)
                DrawRect(FLinearColor(.4f, .8f, .9f), X + 25.f * Scale, RowY, 3.f * Scale, RowH - 4.f * Scale);
            Text((Selected ? TEXT(">  ") : TEXT("   ")) + Entry.Label, X + 34.f * Scale, RowY + 7.f * Scale, .76f,
                 Entry.Enabled ? FLinearColor(.92f, .95f, 1) : FLinearColor(.36f, .4f, .47f));
            MenuBounds.Add(
                FBox2D(FVector2D(X + 25.f * Scale, RowY), FVector2D(X + PW - 25.f * Scale, RowY + RowH - 4.f * Scale)));
            RowY += RowH;
        }
    }
}
