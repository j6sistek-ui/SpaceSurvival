#include "SSHUD.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSShip.h"
#include "SSStation.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "EngineUtils.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "EngineFontServices.h"
#include "Fonts/FontMeasure.h"
#include "Misc/Paths.h"
#include "Kismet/GameplayStatics.h"

namespace
{
const FLinearColor UIWhite = FLinearColor::FromSRGBColor(FColor(172, 193, 216));
const FLinearColor UICyan = FLinearColor::FromSRGBColor(FColor(154, 227, 240));
const FLinearColor UIAmber = FLinearColor::FromSRGBColor(FColor(255, 217, 138));
bool IsSettingsPanel(ESSPanel Panel)
{
    return Panel == ESSPanel::Settings || Panel == ESSPanel::Graphics || Panel == ESSPanel::Audio ||
           Panel == ESSPanel::Controls;
}
} // namespace

void ASSHUD::BeginRefreshLayout()
{
    if (!RefreshFont)
    {
        // Canvas requires a UFont provider even when Slate can measure a file-backed font directly.
        const FSlateFontInfo Source(FPaths::ProjectContentDir() / TEXT("SpaceSurvival/UI/Fonts/KeaniaOne-Regular.ttf"),
                                    16);
        RefreshFont = NewObject<UFont>(this);
        RefreshFont->FontCacheType = EFontCacheType::Runtime;
        RefreshFont->GetMutableInternalCompositeFont() = *Source.GetCompositeFont();
    }
    RefreshScale = FMath::Min(Canvas->SizeX / 1920.f, Canvas->SizeY / 1080.f);
    RefreshOrigin =
        FVector2D((Canvas->SizeX - 1920.f * RefreshScale) * .5f, (Canvas->SizeY - 1080.f * RefreshScale) * .5f);
}

UTexture2D *ASSHUD::RefreshTexture(FName Name)
{
    if (const auto *Found = RefreshTextures.Find(Name))
        return Found->Get();
    const FString Path = TEXT("/Game/SpaceSurvival/UI/Refresh/T_") + Name.ToString();
    auto *Texture = LoadObject<UTexture2D>(nullptr, *Path);
    RefreshTextures.Add(Name, Texture);
    return Texture;
}

FBox2D ASSHUD::RefreshBounds(float X, float Y, float Width, float Height) const
{
    return FBox2D(RefreshOrigin + FVector2D(X, Y) * RefreshScale,
                  RefreshOrigin + FVector2D(X + Width, Y + Height) * RefreshScale);
}

void ASSHUD::RefreshImage(FName Name, float X, float Y, float Width, float Height, FLinearColor Tint)
{
    if (auto *Texture = RefreshTexture(Name))
    {
        FCanvasTileItem Item(RefreshOrigin + FVector2D(X, Y) * RefreshScale, Texture->GetResource(),
                             FVector2D(Width, Height) * RefreshScale, Tint);
        Item.BlendMode = SE_BLEND_Translucent;
        Canvas->DrawItem(Item);
    }
}

float ASSHUD::RefreshText(const FString &Value, float X, float Y, float Pixels, FLinearColor Color, float Width)
{
    float TextScale = 1.f;
    if (const auto *GI = GetGameInstance<USSGameInstance>())
        TextScale = FMath::Clamp(float(GI->Session.settings.uiScale), .85f, 1.25f);
    FSlateFontInfo Font(RefreshFont, FMath::Max(8, FMath::RoundToInt(Pixels * RefreshScale * .75f * TextScale)));
    const auto Measure = FEngineFontServices::Get().GetFontMeasure();
    const float Dpi = FMath::Max(.1f, Canvas->GetDPIScale());
    const float LineHeight = Pixels * TextScale * 1.3f;
    TArray<FString> Lines;
    Value.ParseIntoArrayLines(Lines, false);
    float CursorY = Y;
    for (const FString &Line : Lines)
    {
        TArray<FString> Words;
        Line.ParseIntoArray(Words, TEXT(" "), true);
        FString Pending;
        auto Emit = [&]()
        {
            FCanvasTextItem Item(RefreshOrigin + FVector2D(X, CursorY) * RefreshScale, FText::FromString(Pending), Font,
                                 Color);
            Item.EnableShadow(FLinearColor(0, 0, 0, .9f), FVector2D(1, 1));
            Canvas->DrawItem(Item);
            CursorY += LineHeight;
            Pending.Empty();
        };
        for (const FString &Word : Words)
        {
            const FString Candidate = Pending.IsEmpty() ? Word : Pending + TEXT(" ") + Word;
            if (Width > 0 && !Pending.IsEmpty() && Measure.IsValid() &&
                Measure->Measure(Candidate, Font, Dpi).X / Dpi > Width * RefreshScale)
                Emit();
            Pending = Pending.IsEmpty() ? Word : Pending + TEXT(" ") + Word;
        }
        Emit();
    }
    return CursorY - Y;
}

bool ASSHUD::DrawRefreshMenu(const ASSGameMode &Mode)
{
    if (!Mode.IsMenuOpen())
        return false;
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return false;
    BeginRefreshLayout();
    const auto &S = GI->Session;
    const bool Live = S.IsFlying() && (Mode.Panel == ESSPanel::Depot || Mode.Panel == ESSPanel::Reward);
    if (!Live)
    {
        DrawRect(FLinearColor(.001f, .004f, .01f), 0, 0, Canvas->SizeX, Canvas->SizeY);
        RefreshImage(TEXT("Background"), 0, 0, 1920, 1080, FLinearColor(.6f, .6f, .6f, 1));
    }
    MenuBounds.Init(FBox2D(EForceInit::ForceInit), Mode.Entries.Num());
    if (Mode.Panel != ESSPanel::Wardrobe)
    {
        ScrollFirst = ScrollCount = 0;
        bScrollDragging = false;
    }
    const bool Settings = IsSettingsPanel(Mode.Panel);
    const bool Pause = Mode.Panel == ESSPanel::Main;
    const float HeadingX = Live ? 1280.f : 72.f;
    RefreshText(Mode.PanelTitle, HeadingX, Live ? 165.f : 86.f, Live ? 28.f : 54.f, UIWhite, Live ? 550.f : 1730.f);
    if (!Live)
        RefreshText(Settings ? TEXT("PREFERENCES")
                    : Pause  ? (Mode.IsTitleMenu() ? TEXT("SPACE SURVIVAL") : TEXT("JOURNEY / PAUSED"))
                             : TEXT("STATION / SHIP SERVICES"),
                    72, 52, 19, UICyan);
    RefreshText(UsingGamepad() ? TEXT("LEFT STICK / D-PAD  NAVIGATE       A  SELECT       B  BACK")
                               : TEXT("ARROWS  NAVIGATE       ENTER / CLICK  SELECT       ESC  BACK"),
                72, 1003, 20, UIWhite);

    auto Bound = [&](int32 Index, float X, float Y, float Width, float Height)
    { MenuBounds[Index] = RefreshBounds(X, Y, Width, Height); };
    auto Focus = [&](int32 Index, float X, float Y, float Width, float Height)
    {
        if (Mode.SelectedEntry == Index)
        {
            const FBox2D B = RefreshBounds(X, Y, Width, Height);
            DrawRect(FLinearColor(.05f, .25f, .34f, .35f), B.Min.X, B.Min.Y, B.GetSize().X, B.GetSize().Y);
            DrawRect(UICyan, B.Min.X, B.Min.Y, 3.f * RefreshScale, B.GetSize().Y);
        }
    };
    if (Settings)
    {
        RefreshImage(TEXT("Frame"), 54, 214, 1150, 740);
        const int Actions[] = {5, 10, 11, 12};
        const TCHAR *Names[] = {TEXT("GENERAL"), TEXT("GRAPHICS"), TEXT("AUDIO"), TEXT("CONTROLS")};
        const ESSPanel Panels[] = {ESSPanel::Settings, ESSPanel::Graphics, ESSPanel::Audio, ESSPanel::Controls};
        const auto &V = S.settings;
        int32 Row = 0;
        for (int32 I = 0; I < Mode.Entries.Num(); ++I)
        {
            const auto &Entry = Mode.Entries[I];
            int32 Tab = INDEX_NONE;
            for (int32 T = 0; T < 4; ++T)
                if (Entry.Action == Actions[T])
                    Tab = T;
            if (Tab != INDEX_NONE)
            {
                const float X = 72.f + Tab * 236.f;
                RefreshImage(Mode.Panel == Panels[Tab] || Mode.SelectedEntry == I ? TEXT("TabActive") : TEXT("Tab"), X,
                             189, 226, 92);
                RefreshText(Names[Tab], X + 44, 219, 21, UIWhite);
                Bound(I, X + 18, 207, 190, 56);
                continue;
            }
            if (Entry.Action == 0)
            {
                Bound(I, 60, 982, 270, 60);
                Focus(I, 60, 982, 270, 60);
                continue;
            }
            const float Y = 390.f + Row++ * (Mode.Panel == ESSPanel::Controls ? 62.f : 102.f);
            Focus(I, 194, Y - 10, 848, 54);
            Bound(I, 194, Y - 10, 848, 54);
            FString Label, Value;
            if (!Entry.Label.Split(TEXT(":"), &Label, &Value))
            {
                Label = Entry.Action == 9 ? TEXT("Asset acknowledgements") : TEXT("Flight guidance");
                Value = Entry.Action == 9 ? TEXT("VIEW") : TEXT("REPLAY NEXT RUN");
            }
            Value.TrimStartAndEndInline();
            RefreshText(Label, 210, Y, Mode.Panel == ESSPanel::Controls ? 25.f : 28.f, UIWhite, 430);
            const bool Toggle = Entry.Action == 13 || Entry.Action == 15 || Entry.Action == 18;
            const bool Slider = (Entry.Action >= 19 && Entry.Action <= 23);
            if (Toggle)
            {
                const bool On = Entry.Action == 13 ? V.subtitles : Entry.Action == 15 ? V.cameraShake : V.motionBlur;
                RefreshImage(On ? TEXT("ToggleOn") : TEXT("ToggleOff"), 650, Y - 20, 162, 88);
            }
            else if (Slider)
            {
                const float Amount = Entry.Action == 19   ? V.masterVolume
                                     : Entry.Action == 20 ? V.musicVolume
                                     : Entry.Action == 21 ? V.effectsVolume
                                     : Entry.Action == 22 ? (V.mouseSensitivity - .3) / 2.6
                                                          : (V.controllerSensitivity - .3) / 2.6;
                const float Start = Mode.Panel == ESSPanel::Controls ? 646.f : 540.f;
                // Exact export padding: track core x20..640/y20..34; fill x20..320.
                // Preserve one scale for all three assets so rail, fill and knob share a centreline.
                constexpr float SliderScale = 270.f / 660.f;
                constexpr float Rail = 620.f * SliderScale;
                const float CentreY = Y + 20.f;
                const float RailX = Start + 20.f * SliderScale;
                RefreshImage(TEXT("Track"), Start, CentreY - 27.f * SliderScale, 270, 54.f * SliderScale);
                const float Fill = FMath::Clamp(Amount, 0.f, 1.f);
                if (Fill > 0)
                {
                    const float FillWidth = (Rail * Fill) * 340.f / 300.f;
                    RefreshImage(TEXT("Fill"), RailX - FillWidth * 20.f / 340.f, CentreY - 27.f * SliderScale,
                                 FillWidth, 54.f * SliderScale);
                }
                const float KnobSize = 74.f * SliderScale;
                RefreshImage(TEXT("Knob"), RailX + Rail * Fill - KnobSize * .5f, CentreY - KnobSize * .5f, KnobSize,
                             KnobSize);
            }
            else if (Entry.Action == 16 || Entry.Action == 17)
                RefreshImage(TEXT("Dropdown"), 744, Y - 22, 300, 84);
            RefreshText(Value.ToUpper(), Mode.Panel == ESSPanel::Controls ? 945.f : 822.f, Y,
                        Mode.Panel == ESSPanel::Controls ? 22.f : 28.f, Slider || Entry.Action == 14 ? UIAmber : UICyan,
                        Mode.Panel == ESSPanel::Controls ? 145.f : 210.f);
        }
        if (Mode.Panel == ESSPanel::Controls)
        {
            RefreshText(TEXT("CURRENT FLIGHT PRESET"), 1250, 345, 30, UICyan, 590);
            RefreshText(Mode.PanelDetail, 1250, 415, 21, UIWhite, 565);
        }
    }
    else if (Pause)
    {
        int32 Row = 0;
        const float Step = FMath::Min(156.f, 700.f / FMath::Max(1, Mode.Entries.Num()));
        for (int32 I = 0; I < Mode.Entries.Num(); ++I)
        {
            const auto &Entry = Mode.Entries[I];
            const float Y = 208.f + Row++ * Step;
            RefreshImage(Mode.SelectedEntry == I ? TEXT("ButtonFocus") : TEXT("Button"), 610, Y - 25, 680,
                         FMath::Min(267.f, Step * 1.95f),
                         Entry.Enabled ? FLinearColor::White : FLinearColor(.35f, .35f, .35f, 1));
            Focus(I, 716, Y + 48, 480, 55);
            RefreshText(Entry.Label, 730, Y + 58, Entry.Label.Len() > 45 ? 20.f : 27.f,
                        Entry.Enabled ? UIWhite : FLinearColor(.3f, .3f, .3f), 465);
            Bound(I, 685, Y + 32, 530, FMath::Min(116.f, Step - 6));
        }
    }
    else if (Mode.Panel == ESSPanel::Wardrobe)
    {
        RefreshImage(TEXT("Frame"), 70, 200, 1250, 760);
        RefreshText(Mode.PanelDetail, 1400, 420, 23, UIWhite, 425);
        ScrollCount = Mode.Entries.Num() - 1; // Native Back remains pinned below the character list.
        ScrollVisible = 6;
        if (Mode.SelectedEntry < ScrollCount)
        {
            if (Mode.SelectedEntry < ScrollFirst)
                ScrollFirst = Mode.SelectedEntry;
            else if (Mode.SelectedEntry >= ScrollFirst + ScrollVisible)
                ScrollFirst = Mode.SelectedEntry - ScrollVisible + 1;
        }
        ScrollFirst = FMath::Clamp(ScrollFirst, 0, FMath::Max(0, ScrollCount - ScrollVisible));
        for (int32 Row = 0; Row < ScrollVisible && ScrollFirst + Row < ScrollCount; ++Row)
        {
            const int32 I = ScrollFirst + Row;
            const float Y = 410.f + Row * 64.f;
            Focus(I, 226, Y, 866, 60);
            Bound(I, 226, Y, 866, 60);
            RefreshText(Mode.Entries[I].Label, 240, Y + 9, 32, UIWhite, 835);
        }
        const int32 Back = Mode.Entries.Num() - 1;
        Bound(Back, 226, 904, 866, 58);
        Focus(Back, 226, 904, 866, 58);
        RefreshText(TEXT("Back"), 240, 912, 30, UIWhite);
        RefreshText(TEXT("CHOOSE YOUR CHARACTER"), 1400, 300, 29, UICyan, 425);
        RefreshText(FString::Printf(TEXT("%d - %d / %d"), ScrollFirst + 1,
                                    FMath::Min(ScrollCount, ScrollFirst + ScrollVisible), ScrollCount),
                    1400, 355, 32, UIWhite);
        RefreshText(TEXT("Mouse wheel or D-pad / arrows to scroll.\nSelect to wear."), 1400, 660, 24, UIWhite, 420);
        const float TrackY = 410.f, TrackHeight = 384.f;
        const float ThumbHeight = TrackHeight * FMath::Min(1.f, float(ScrollVisible) / FMath::Max(1, ScrollCount));
        const float Fraction = float(ScrollFirst) / FMath::Max(1, ScrollCount - ScrollVisible);
        const float ThumbY = TrackY + Fraction * (TrackHeight - ThumbHeight);
        ScrollTrackBounds = RefreshBounds(1138, TrackY, 34, TrackHeight);
        ScrollThumbBounds = RefreshBounds(1145, ThumbY, 20, ThumbHeight);
        ScrollUpBounds = RefreshBounds(1134, 372, 42, 36);
        ScrollDownBounds = RefreshBounds(1134, 798, 42, 36);
        RefreshImage(TEXT("ScrollTrack"), 1138, TrackY, 34, TrackHeight);
        RefreshImage(TEXT("ScrollThumb"), 1133, ThumbY - 12, 44, ThumbHeight + 24);
        RefreshImage(TEXT("ScrollUp"), 1138, 376, 33, 28);
        RefreshImage(TEXT("ScrollDown"), 1138, 802, 33, 28);
    }
    else
    {
        // Current service actions retain their native transactions and availability. The approved
        // kit supplies the common frame; dynamic content replaces illustrative Figma sample values.
        const float X = Live ? 1250.f : 70.f, Y = Live ? 220.f : 200.f;
        const float Width = Live ? 600.f : 1250.f, Height = Live ? 710.f : 760.f;
        RefreshImage(TEXT("Frame"), X, Y, Width, Height);
        const float InnerX = X + Width * .135f, InnerWidth = Width * .73f;
        const float DetailY = Y + Height * .17f;
        const float DetailHeight =
            RefreshText(Mode.PanelDetail, InnerX, DetailY, Live ? 18.f : 23.f, UIWhite, InnerWidth);
        const float RowStart = DetailY + DetailHeight + 30.f;
        const float RowStep = FMath::Min(78.f, (Y + Height * .84f - RowStart) / FMath::Max(1, Mode.Entries.Num()));
        for (int32 I = 0; I < Mode.Entries.Num(); ++I)
        {
            const auto &Entry = Mode.Entries[I];
            const float RowY = RowStart + I * RowStep;
            Focus(I, InnerX - 12, RowY - 7, InnerWidth + 24, RowStep - 3);
            RefreshText(Entry.Label, InnerX, RowY, Live ? 18.f : FMath::Min(25.f, RowStep * .47f),
                        Entry.Enabled ? (Mode.SelectedEntry == I ? UICyan : UIWhite) : FLinearColor(.25f, .3f, .35f),
                        InnerWidth);
            Bound(I, InnerX - 12, RowY - 7, InnerWidth + 24, RowStep - 3);
        }
        if (!Live)
        {
            RefreshText(S.run.active ? TEXT("RUN CREDITS") : TEXT("ACCOUNT"), 1420, 280, 25, UICyan);
            RefreshText(S.run.active ? FString::Printf(TEXT("%d CR"), S.run.credits)
                                     : FString::Printf(TEXT("LEVEL %d"), S.account.level),
                        1420, 325, 46, UIAmber, 420);
        }
    }
    if (Mode.IsAnnouncementVisible())
        RefreshText(Mode.Announcement, Live ? 1250.f : 72.f, 945, 22, UIAmber, Live ? 590.f : 1750.f);
    return true;
}

void ASSHUD::DrawRefreshVitals(const ASSGameMode &Mode, bool Walking)
{
    BeginRefreshLayout();
    auto *GI = GetGameInstance<USSGameInstance>();
    const auto &S = GI->Session;
    const auto Stats = S.Stats();
    const FString Location =
        GI->IsFreeFlight() ? TEXT("FREE FLIGHT")
        : Walking          ? (Mode.InHangar() ? TEXT("HOME HANGAR")
                                              : FString::Printf(TEXT("STATION %02d"), FMath::Max(1, S.run.wave / 5)))
                           : FString::Printf(TEXT("WAVE %02d / 10"), bReviewFlightHUD ? 6 : S.run.wave);
    RefreshText(Location, 64, 52, Walking ? 48.f : 29.f, UIWhite);
    RefreshText(Walking              ? TEXT("PREPARE / SERVICES / DEPARTURE")
                : GI->IsFreeFlight() ? TEXT("EXPLORE THE SECTOR")
                                     : TEXT("SURVIVE THE SECTOR"),
                64, Walking ? 115.f : 96.f, 18, UICyan);
    if (Walking)
    {
        RefreshText(FString::Printf(TEXT("%d CR"), S.run.credits), 64, 160, 30, UIAmber);
        DrawStationRadar();
        return;
    }
    // Owner amendment: floating labels and bars only. No blue chassis or numeric percentages.
    const double Values[] = {bReviewFlightHUD ? .48 : S.run.hull / FMath::Max(1., Stats.maxHull),
                             bReviewFlightHUD ? .72 : S.run.shield / FMath::Max(1., Stats.maxShield),
                             bReviewFlightHUD ? .22 : S.run.brakeHeat / 100.};
    const TCHAR *Names[] = {TEXT("HULL"), TEXT("SHIELDS"),
                            S.run.brakeOverheated ? TEXT("BRAKE OVERHEAT") : TEXT("BRAKE HEAT")};
    const TCHAR *Pips[] = {TEXT("PipRed"), TEXT("PipBlue"), TEXT("PipAmber")};
    for (int32 Row = 0; Row < 3; ++Row)
    {
        const float Y = 762.f + Row * 77.f;
        RefreshText(Names[Row], 87, Y, 20, Row == 2 ? UIAmber : UIWhite);
        for (int32 Pip = 0; Pip < 13; ++Pip)
            RefreshImage(Pip < FMath::CeilToInt(FMath::Clamp(Values[Row], 0., 1.) * 13.) ? Pips[Row] : TEXT("PipOff"),
                         87.f + Pip * 31.f, Y + 29, 53, 39);
    }
    RefreshImage(TEXT("WideFrame"), 668, 880, 620, 180);
    RefreshText(S.run.weapon == SS::Weapon::RapidLaser ? TEXT("RAPID LASER") : TEXT("HEAVY CANNON"), 745, 932, 27,
                UIWhite);
    RefreshText(UsingGamepad() ? TEXT("A / FIRE") : TEXT("LEFT CLICK / FIRE"), 745, 971, 19, UICyan);
    if (auto *Ship = Mode.GetPlayerShip())
    {
        RefreshText(FString::Printf(TEXT("%.0f m/s"), Ship->GetVelocity().Size() / 100.f), 1460, 894, 34, UIAmber);
        RefreshText(Ship->GetThrottle() > .01f ? FString::Printf(TEXT("THROTTLE %.0f"), Ship->GetThrottle() * 100)
                                               : TEXT("ENGINE OFF / COAST"),
                    1460, 939, 20, UICyan);
        RefreshText(S.run.boosting ? TEXT("BOOST ACTIVE") : TEXT("BOOST"), 1460, 974, 19, UICyan);
        for (int32 Pip = 0; Pip < 10; ++Pip)
            RefreshImage(Pip < FMath::CeilToInt(S.run.boost / 10.) ? TEXT("PipBlue") : TEXT("PipOff"),
                         1450.f + Pip * 29.f, 1000, 47, 32);
    }
}

void ASSHUD::DrawStationRadar()
{
    const auto *Walker = Cast<ASSWalker>(UGameplayStatics::GetPlayerPawn(this, 0));
    if (!Walker)
        return;
    const ASSStation *Station = nullptr;
    float Nearest = FMath::Square(20000.f);
    for (TActorIterator<ASSStation> It(GetWorld()); It; ++It)
    {
        const float Distance = FVector::DistSquared(It->GetActorLocation(), Walker->GetActorLocation());
        if (!It->IsHidden() && Distance < Nearest)
        {
            Nearest = Distance;
            Station = *It;
        }
    }
    if (!Station)
        return;
    for (const TCHAR *Layer : {TEXT("RadarBack"), TEXT("RadarRings"), TEXT("RadarTicks"), TEXT("RadarRim")})
        RefreshImage(Layer, 1510, 104, 324, 324);
    RefreshImage(TEXT("RadarBezel"), 1492, 86, 361, 361);
    RefreshText(TEXT("STATION / 60 m"), 1520, 54, 22, UICyan);
    const FRotator Heading(0, Walker->GetActorRotation().Yaw, 0);
    auto Marker = [&](FName Symbol, FVector World, float Size)
    {
        const FVector Local = Heading.UnrotateVector(World - Walker->GetActorLocation());
        FVector2D Offset(Local.Y, -Local.X);
        Offset *= 142.f / 6000.f;
        if (Offset.SizeSquared() > 142.f * 142.f)
            Offset = Offset.GetSafeNormal() * 142.f;
        RefreshImage(Symbol, 1672.f + Offset.X - Size * .5f, 266.f + Offset.Y - Size * .5f, Size, Size);
    };
    TArray<FVector> Services, Crew;
    Station->RadarContacts(Services, Crew);
    for (const FVector &Position : Services)
        Marker(TEXT("POI"), Position, 34);
    for (const FVector &Position : Crew)
        Marker(TEXT("Ally"), Position, 26);
    Marker(TEXT("Station"), Station->PadDockPosition(), 42);
    RefreshImage(TEXT("You"), 1653, 247, 38, 38);
    const TCHAR *Symbols[] = {TEXT("Ally"), TEXT("POI"), TEXT("Station")};
    const TCHAR *Labels[] = {TEXT("CREW"), TEXT("SERVICES"), TEXT("LANDING PAD")};
    for (int32 I = 0; I < 3; ++I)
    {
        RefreshImage(Symbols[I], 1520, 452.f + I * 32.f, 28, 28);
        RefreshText(Labels[I], 1560, 456.f + I * 32.f, 19, UIWhite);
    }
}

// Scrolling changes UI focus only; choosing a character still uses ActivateEntry.
bool ASSHUD::ScrollMenu(int32 Rows)
{
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!GM || GM->Panel != ESSPanel::Wardrobe || ScrollCount <= 0)
        return false;
    ScrollFirst = FMath::Clamp(ScrollFirst + Rows, 0, FMath::Max(0, ScrollCount - ScrollVisible));
    if (GM->SelectedEntry < ScrollCount)
        GM->SelectedEntry =
            FMath::Clamp(GM->SelectedEntry, ScrollFirst, FMath::Min(ScrollCount - 1, ScrollFirst + ScrollVisible - 1));
    return true;
}

bool ASSHUD::HandleMenuScrollPointer(FVector2D Point, bool Pressed, bool Held)
{
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!GM || GM->Panel != ESSPanel::Wardrobe || ScrollCount <= ScrollVisible)
    {
        bScrollDragging = false;
        return false;
    }
    if (bScrollDragging)
    {
        if (Held)
        {
            const float Travel = ScrollTrackBounds.GetSize().Y - ScrollThumbBounds.GetSize().Y;
            const float Fraction = FMath::Clamp(
                float(Point.Y - ScrollDragOffset - ScrollTrackBounds.Min.Y) / FMath::Max(1.f, Travel), 0.f, 1.f);
            ScrollMenu(FMath::RoundToInt(Fraction * (ScrollCount - ScrollVisible)) - ScrollFirst);
        }
        else
            bScrollDragging = false;
        return true;
    }
    if (!Pressed)
        return false;
    if (ScrollUpBounds.IsInside(Point))
        return ScrollMenu(-1);
    if (ScrollDownBounds.IsInside(Point))
        return ScrollMenu(1);
    if (ScrollThumbBounds.IsInside(Point))
    {
        bScrollDragging = true;
        ScrollDragOffset = Point.Y - ScrollThumbBounds.Min.Y;
        return true;
    }
    if (ScrollTrackBounds.IsInside(Point))
        return ScrollMenu(Point.Y < ScrollThumbBounds.Min.Y ? -ScrollVisible : ScrollVisible);
    return false;
}
