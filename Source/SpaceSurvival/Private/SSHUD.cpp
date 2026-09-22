#include "SSHUD.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSAlienGallery.h"
#include "SSInputGlyphs.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "CanvasItem.h"
#include "EngineFontServices.h"
#include "Fonts/FontMeasure.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UnrealType.h"
#include "Misc/Paths.h"

namespace
{
// Measured rendered bounds from ContentSource/FigmaMainMenu/provenance.json, in its 3840x2160
// canvas. The button halo is deliberately larger than its logical pointer rectangle.
struct FSSTitleTextureSource
{
    const TCHAR *Name;
    float X, Y, Width, Height;
};
const FSSTitleTextureSource TitleSources[] = {
    {TEXT("T_MainBackground"), 0.f, 0.f, 3840.f, 2160.f},
    {TEXT("T_MainTitle"), 710.f, 93.5f, 2619.9585f, 230.4f},
    {TEXT("T_MainHeroLeft"), 273.f, 482.f, 583.f, 1374.f},
    {TEXT("T_MainHeroRight"), 2792.f, 383.f, 1048.f, 1572.f},
    {TEXT("T_ContinueNormal"), 1149.f, 525.f, 1586.f, 385.f},
    {TEXT("T_ContinueHover"), 1138.f, 514.f, 1608.f, 407.f},
    {TEXT("T_NewGameNormal"), 1149.f, 854.f, 1586.f, 385.f},
    {TEXT("T_NewGameHover"), 1138.f, 843.f, 1608.f, 407.f},
    {TEXT("T_SettingsNormal"), 1149.f, 1183.f, 1586.f, 385.f},
    {TEXT("T_SettingsHover"), 1138.f, 1172.f, 1608.f, 407.f},
    {TEXT("T_ExitNormal"), 1149.f, 1512.f, 1586.f, 385.f},
    {TEXT("T_ExitHover"), 1138.f, 1501.f, 1608.f, 407.f},
    {TEXT("T_FooterPanel"), 86.f, 1936.f, 516.f, 146.f},
    {TEXT("T_HintEnter"), 1462.9803f, 2021.4563f, 144.0181f, 33.2581f},
    {TEXT("T_HintSelect"), 1631.5144f, 2025.7943f, 115.6309f, 28.9200f},
    {TEXT("T_HintMoveKeys"), 1840.9343f, 2021.4563f, 114.6007f, 39.6980f},
    {TEXT("T_HintMove"), 1981.0343f, 2034.7144f, 96.6226f, 20.f},
    {TEXT("T_HintEscape"), 2172.9803f, 2021.4563f, 81.7457f, 33.2581f},
    {TEXT("T_HintQuit"), 2279.7544f, 2025.7943f, 71.7034f, 37.8401f},
};

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
    FSlateFontInfo Font(RefreshFont, 16);
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
    if (State == 2)
    {
        const FLinearColor HitColor(1.f, .95f, .45f);
        for (int32 XSign : {-1, 1})
            for (int32 YSign : {-1, 1})
            {
                const float X0 = CentreX + XSign * 10.f * Scale;
                const float Y0 = CentreY + YSign * 10.f * Scale;
                const float X1 = CentreX + XSign * 23.f * Scale;
                const float Y1 = CentreY + YSign * 23.f * Scale;
                DrawLine(X0, Y0, X1, Y1, FLinearColor::Black, 5.f * Scale);
                DrawLine(X0, Y0, X1, Y1, HitColor, 2.5f * Scale);
            }
        Text(TEXT("HIT"), CentreX - MeasureText(TEXT("HIT"), .7f).X * .5f, CentreY + 35.f * Scale, .7f, HitColor);
    }
    UTexture2D *Texture = State == 0                              ? RefreshTexture(TEXT("Crosshair"))
                          : CrosshairTextures.IsValidIndex(State) ? CrosshairTextures[State].Get()
                                                                  : nullptr;
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
    const FVector2D Size =
        State == 0 ? FVector2D(80.8f, 80.8f) * Scale : FVector2D(Texture->GetSizeX() * Fit, Texture->GetSizeY() * Fit);
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
float ASSHUD::DrawPrompt(FName ActionId, const FString &KeyboardLabel, const FString &GamepadLabel, float X, float Y,
                         float Size, FLinearColor Color)
{
    const auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    const auto *PC = Cast<ASSPlayerController>(GetOwningPlayerController());
    const bool Gamepad = PC && PC->bLastInputWasGamepad;
    const USSInputGlyphSet *Set = GM ? (Gamepad ? GM->GamepadGlyphs : GM->KeyboardGlyphs) : nullptr;
    UTexture2D *Icon = (Set && !ActionId.IsNone()) ? Set->Find(ActionId) : nullptr;
    if (!Icon)
    {
        const FString &Label = Gamepad ? GamepadLabel : KeyboardLabel;
        Text(Label, X, Y, Size, Color);
        return X + MeasureText(Label, Size).X;
    }
    const float IconSize = 24.f * Scale * Size;
    FCanvasTileItem TileItem(FVector2D(X, Y), Icon->GetResource(), FVector2D(IconSize, IconSize), Color);
    TileItem.BlendMode = SE_BLEND_Translucent;
    Canvas->DrawItem(TileItem);
    return X + IconSize + 6.f * Scale;
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
    BeginRefreshLayout();
    const FVector2D Radar = RefreshOrigin + FVector2D(1672.f, 266.f) * RefreshScale;
    const float RadarRadius = 142.f * RefreshScale, RadarRange = 10000.f;
    const FLinearColor Grid(.18f, .33f, .4f, .65f);
    const FRotator ViewRotation = PlayerOwner->PlayerCameraManager->GetCameraRotation();
    const FVector ViewRight = FRotationMatrix(ViewRotation).GetUnitAxis(EAxis::Y);
    if (ShowRadar)
    {
        for (const TCHAR *Layer : {TEXT("RadarBack"), TEXT("RadarRings"), TEXT("RadarTicks"), TEXT("RadarRim")})
            RefreshImage(Layer, 1510, 104, 324, 324);
        RefreshImage(TEXT("RadarBezel"), 1492, 86, 361, 361);
        RefreshImage(TEXT("You"), 1653, 247, 38, 38);
        RefreshText(TEXT("CONTACTS / 100 m"), 1585, 59, 20, FLinearColor(.65f, .83f, .9f));
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
            const FVector2D At = (Radar + Offset - RefreshOrigin) / RefreshScale;
            RefreshImage(TEXT("Enemy"), At.X - 15, At.Y - 15, 30, 30);
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
        if (MenuBounds[I].bIsValid && MenuBounds[I].IsInside(Point))
            return I;
    return INDEX_NONE;
}
bool ASSHUD::DrawFigmaMainMenu(const ASSGameMode &Mode)
{
    // A changed native menu or absent local artwork must remain usable through the standard panel.
    const int32 Actions[] = {2, 4, 5, 7};
    if (!Canvas || !Mode.IsTitleMenu() || Mode.Entries.Num() != UE_ARRAY_COUNT(Actions))
        return false;
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Actions); ++Index)
        if (Mode.Entries[Index].Action != Actions[Index])
            return false;
    if (!bTitleAssetsRequested)
    {
        bTitleAssetsRequested = true;
        for (const FSSTitleTextureSource &Source : TitleSources)
        {
            const FString Path =
                FString::Printf(TEXT("/Game/SpaceSurvival/UI/MainMenu/%s.%s"), Source.Name, Source.Name);
            TitleTextures.Add(LoadObject<UTexture2D>(nullptr, *Path, nullptr, LOAD_NoWarn | LOAD_Quiet));
        }
    }
    if (TitleTextures.Num() != UE_ARRAY_COUNT(TitleSources))
        return false;
    for (const auto &Texture : TitleTextures)
        if (!Texture || !Texture->GetResource())
            return false;

    const float Fit = FMath::Min(Canvas->SizeX / 3840.f, Canvas->SizeY / 2160.f);
    const FVector2D Origin((Canvas->SizeX - 3840.f * Fit) * .5f, (Canvas->SizeY - 2160.f * Fit) * .5f);
    // Gameplay UI scaling must not move the locked composition or separate its art from its hit boxes.
    TGuardValue<float> TitleScale(Scale, Fit * 2.f);
    DrawRect(FLinearColor::Black, 0.f, 0.f, Canvas->SizeX, Canvas->SizeY);
    auto DrawSource = [&](int32 Index, FLinearColor Tint = FLinearColor::White)
    {
        const FSSTitleTextureSource &Source = TitleSources[Index];
        FCanvasTileItem Item(Origin + FVector2D(Source.X, Source.Y) * Fit, TitleTextures[Index]->GetResource(),
                             FVector2D(Source.Width, Source.Height) * Fit, Tint);
        Item.BlendMode = SE_BLEND_Translucent;
        Canvas->DrawItem(Item);
    };
    DrawSource(0);
    DrawSource(2);
    DrawSource(3);
    DrawSource(1);
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Actions); ++Index)
    {
        const FVector2D Min = Origin + FVector2D(1207.f, 583.f + Index * 329.f) * Fit;
        MenuBounds.Add(FBox2D(Min, Min + FVector2D(1470.f, 269.f) * Fit));
    }

    float PointerX = 0.f, PointerY = 0.f;
    const bool HasPointer = PlayerOwner && PlayerOwner->GetMousePosition(PointerX, PointerY);
    const FVector2D Pointer(PointerX, PointerY);
    if (!bTitleWasOpen)
    {
        LastTitlePointer = Pointer;
        LastTitleSelection = Mode.SelectedEntry;
        bTitleNavigationFocus = UsingGamepad();
    }
    else
    {
        if (HasPointer && FVector2D::DistSquared(Pointer, LastTitlePointer) > 1.f)
            bTitleNavigationFocus = false;
        if (LastTitleSelection != Mode.SelectedEntry)
            bTitleNavigationFocus = true;
    }
    LastTitlePointer = Pointer;
    LastTitleSelection = Mode.SelectedEntry;
    bTitleWasOpen = true;
    const int32 Highlight =
        UsingGamepad() || bTitleNavigationFocus ? Mode.SelectedEntry : (HasPointer ? MenuIndexAt(Pointer) : INDEX_NONE);
    RenderedTitleFocus =
        Mode.Entries.IsValidIndex(Highlight) && Mode.Entries[Highlight].Enabled ? Highlight : INDEX_NONE;
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Actions); ++Index)
    {
        const bool Enabled = Mode.Entries[Index].Enabled;
        DrawSource(4 + Index * 2 + (Enabled && Highlight == Index ? 1 : 0),
                   Enabled ? FLinearColor::White : FLinearColor(.45f, .45f, .45f, 1.f));
    }
    DrawSource(12);
    const FString BuildLabel(TEXT("DEVELOPMENT REVIEW"));
    const FVector2D LabelSize = MeasureText(BuildLabel, .64f);
    Text(BuildLabel, Origin.X + 344.f * Fit - LabelSize.X * .5f, Origin.Y + 2009.f * Fit - LabelSize.Y * .5f, .64f,
         FLinearColor(.93f, .9f, .9f));
    for (int32 Index = 13; Index < UE_ARRAY_COUNT(TitleSources); ++Index)
        DrawSource(Index);

    const auto *GI = GetGameInstance<USSGameInstance>();
    if (GI && !GI->LastSaveError.IsEmpty() && Mode.Announcement == GI->LastSaveError && Mode.IsAnnouncementVisible())
    {
        const float X = Origin.X + 1207.f * Fit, Y = Origin.Y + 390.f * Fit, Width = 1470.f * Fit;
        const float Height =
            Paragraph(Mode.Announcement, 0.f, 0.f, Width - 24.f * Scale, .7f, FLinearColor::White, false);
        DrawRect(FLinearColor(.015f, .025f, .04f, .96f), X, Y, Width, Height + 16.f * Scale);
        Paragraph(Mode.Announcement, X + 12.f * Scale, Y + 8.f * Scale, Width - 24.f * Scale, .7f,
                  FLinearColor(1.f, .8f, .65f));
    }
    return true;
}
void ASSHUD::DrawHUD()
{
    Super::DrawHUD();
    MenuBounds.Empty();
    if (!Canvas)
    {
        bTitleWasOpen = false;
        return;
    }
    auto *GI = GetGameInstance<USSGameInstance>();
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!GI || !GM)
    {
        bTitleWasOpen = false;
        return;
    }
    BeginRefreshLayout();
    const auto &S = GI->Session;
    Scale = FMath::Clamp(float(Canvas->SizeY) / 1080.f * float(S.settings.uiScale), .65f, 1.6f);
    const float W = Canvas->SizeX, H = Canvas->SizeY, Margin = 30 * Scale;
    if (GM->AlienGallery && GM->AlienGallery->IsActive())
    {
        bTitleWasOpen = false;
        DrawRect(FLinearColor(.01f, .015f, .025f, .9f), Margin - 10, Margin - 8, W - 2 * Margin + 20, 120 * Scale);
        Text(GM->AlienGallery->Status(), Margin, Margin, .8f, FLinearColor(.55f, .95f, 1));
        Paragraph(TEXT("WASD / left stick: fly | mouse / right stick: look | E Q / bumpers: rise & fall | Shift / RT: "
                       "fast | Ctrl / LT: slow"),
                  Margin, Margin + 35 * Scale, W - 2 * Margin, .55f, FLinearColor::White);
        Text(TEXT("Tab / Y: switch showcase & all assets | Home / Start: reset view | Esc / B: return to station"),
             Margin, Margin + 78 * Scale, .55f);
        return;
    }
    if (bReviewFlightHUD)
    {
        DrawRefreshVitals(*GM, false);
        if (auto *ReviewShip = GM->GetPlayerShip())
        {
            DrawCrosshair(ReviewShip, Canvas->SizeX * .5f, Canvas->SizeY * .5f);
            DrawCombatCues(ReviewShip, true);
        }
        return;
    }
    const bool MenuOpen = GM->IsMenuOpen();
    if (MenuOpen && DrawFigmaMainMenu(*GM))
        return;
    bTitleWasOpen = false;
    const bool LiveMenu = S.IsFlying() && (GM->Panel == ESSPanel::Depot || GM->Panel == ESSPanel::Reward);
    if (MenuOpen && !LiveMenu && DrawRefreshMenu(*GM))
        return;
    const auto *Walker = Cast<ASSWalker>(UGameplayStatics::GetPlayerPawn(this, 0));
    if (S.run.active || Walker)
    {
        DrawRefreshVitals(*GM, Walker != nullptr);
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
        // Drawn where the ship is actually aiming, not at the middle of the screen. Those are the same
        // place only while the hull is small enough to leave the centre empty.
        FVector2D Reticle(W * .5f, H * .5f);
        if (APlayerController *Viewer = GetOwningPlayerController())
        {
            FVector2D Projected;
            if (Viewer->ProjectWorldLocationToScreen(Ship->CrosshairWorldPoint(), Projected))
                Reticle = Projected;
        }
        DrawCrosshair(Ship, Reticle.X, Reticle.Y);
        DrawCombatCues(Ship, true);
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
                const float GlyphW = Glyph(EKeys::E, EKeys::Gamepad_FaceButton_Left, Screen.X + Padding,
                                           Screen.Y + Padding + LabelH, .7f);
                Paragraph(TEXT("INTERACT"), Screen.X + Padding + GlyphW + GlyphGap, Screen.Y + Padding + LabelH,
                          TextW - GlyphW - GlyphGap, .7f, FLinearColor::White);
            }
        }
        if (S.run.phase == SS::Phase::Approach)
        {
            const FVector LandingTarget = GM->GetLandingTarget();
            FVector2D Screen(W * .5f, 130 * Scale);
            if (!PlayerOwner->ProjectWorldLocationToScreen(LandingTarget, Screen))
            {
                const FVector Local = Ship->GetActorTransform().InverseTransformPosition(LandingTarget);
                Screen = FVector2D(Local.Y < 0 ? 100 * Scale : W - 300 * Scale, H * .5f);
            }
            Screen.X = FMath::Clamp(Screen.X, 60 * Scale, FMath::Max(60 * Scale, W - 520 * Scale));
            Screen.Y = FMath::Clamp(Screen.Y, 130 * Scale, H - 180 * Scale);
            FString Status;
            const bool Ready = GM->DockingStatus(Status);
            const float StatusHeight = Paragraph(Status, Screen.X, Screen.Y, 500 * Scale, .75f,
                                                 Ready ? FLinearColor(.4f, 1.f, .65f) : FLinearColor(.45f, .9f, 1));
            if (Ready)
            {
                const float KeyWidth = Glyph(EKeys::E, EKeys::Gamepad_FaceButton_Left, Screen.X,
                                             Screen.Y + StatusHeight + 8 * Scale, .75f);
                Text(TEXT("ENGAGE DOCKING"), Screen.X + KeyWidth + 8 * Scale, Screen.Y + StatusHeight + 8 * Scale, .75f,
                     FLinearColor::White);
            }
        }
    }
    if (GM->IsDepartingStation())
        Text(GM->GetPlayerShip() && GM->GetPlayerShip()->IsTakingOff()
                 ? TEXT("TAKEOFF  |  Gear stowing; controls return after lift-off")
                 : TEXT("STATION ZONE  |  Fly clear of the pad to begin the next wave"),
             W * .22f, 130 * Scale, .85f, FLinearColor(.45f, .9f, 1));
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
                InteractionHint = It->ServiceGuidance(Walker->GetActorLocation());
                HintColor = FLinearColor(.68f, .82f, .9f);
            }
            if (GM->IsWalkerInsideShip(Walker))
            {
                GlyphBeforeHint = true;
                InteractionHint = TEXT("FLIGHT OPTIONS");
            }
            if (!GlyphBeforeHint && S.run.pendingReward)
            {
                InteractionHint = TEXT("REWARD SECURED / visit the Beacon Log");
                HintColor = FLinearColor(1, .8f, .4f);
            }
            Text(TEXT("WASD / left stick: walk | mouse / right stick: camera | Shift / X: run | Space / A: jump | E / "
                      "Y: use"),
                 Margin, H - 35 * Scale, .6f);
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
            const float GlyphW =
                Glyph(EKeys::E, Walker ? EKeys::Gamepad_FaceButton_Top : EKeys::Gamepad_FaceButton_Left, HintX, HintY,
                      HintSize, HintColor);
            Text(InteractionHint, HintX + GlyphW + GlyphGap, HintY, HintSize, HintColor);
        }
        else if (GlyphInsideHint)
        {
            Text(HintPrefix, HintX, HintY, HintSize, HintColor);
            const float PrefixW = MeasureText(HintPrefix, HintSize).X;
            const float GlyphW =
                Glyph(EKeys::E, EKeys::Gamepad_FaceButton_Left, HintX + PrefixW, HintY, HintSize, HintColor);
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
        DrawRefreshMenu(*GM);
}
