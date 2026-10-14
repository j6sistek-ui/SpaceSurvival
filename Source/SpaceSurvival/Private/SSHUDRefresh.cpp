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

void ASSHUD::BeginRefreshLayout(bool FullViewport)
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
    RefreshScale = FMath::Min(Canvas->SizeX / (FullViewport ? 1440.f : 1920.f), Canvas->SizeY / 1080.f);
    RefreshOrigin = FVector2D(FullViewport ? 0.f : (Canvas->SizeX - 1920.f * RefreshScale) * .5f,
                              (Canvas->SizeY - 1080.f * RefreshScale) * .5f);
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

float ASSHUD::RefreshText(const FString &Value, float X, float Y, float Pixels, FLinearColor Color, float Width,
                          bool Render)
{
    float TextScale = 1.f;
    if (const auto *GI = GetGameInstance<USSGameInstance>())
        TextScale = FMath::Clamp(float(GI->Session.settings.uiScale), .8f, 1.4f);
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
            if (Render)
            {
                FCanvasTextItem Item(RefreshOrigin + FVector2D(X, CursorY) * RefreshScale, FText::FromString(Pending),
                                     Font, Color);
                Item.EnableShadow(FLinearColor(0, 0, 0, .9f), FVector2D(1, 1));
                Canvas->DrawItem(Item);
            }
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
    BeginRefreshLayout(true);
    const auto &S = GI->Session;
    const bool Live = S.IsFlying() && (Mode.Panel == ESSPanel::Depot || Mode.Panel == ESSPanel::Reward);
    const bool Settings = IsSettingsPanel(Mode.Panel);
    const bool Wardrobe = Mode.Panel == ESSPanel::Wardrobe;
    const bool Pause = Mode.Panel == ESSPanel::Main;
    const bool FullScreen = Settings || Wardrobe;
    const bool SaveError =
        !GI->LastSaveError.IsEmpty() && Mode.Announcement == GI->LastSaveError && Mode.IsAnnouncementVisible();
    const float ViewWidth = Canvas->SizeX / RefreshScale;
    // The world remains the backdrop for every in-game panel. Only the separately owned,
    // locked title menu draws its static artwork. Full pages use the actual viewport width.
    if (!Live)
        DrawRect(FLinearColor(.001f, .004f, .01f, FullScreen ? .72f : .42f), 0, 0, Canvas->SizeX, Canvas->SizeY);
    MenuBounds.Init(FBox2D(EForceInit::ForceInit), Mode.Entries.Num());
    if (ScrollPanel != static_cast<int32>(Mode.Panel))
    {
        ScrollFirst = 0;
        bScrollDragging = false;
        ScrollPanel = static_cast<int32>(Mode.Panel);
    }
    ScrollCount = 0;
    ScrollEntries.Reset();
    const float PanelW = FullScreen ? ViewWidth - 96.f : FMath::Min(Live ? 650.f : 1280.f, ViewWidth - 96.f);
    const float PanelX = Live ? ViewWidth - PanelW - 32.f : (ViewWidth - PanelW) * .5f;
    float PauseRowStep = 72.f;
    int32 PauseRows = 0;
    if (Pause)
        for (const FSSMenuEntry &Entry : Mode.Entries)
            if (Entry.Action != 0)
            {
                ++PauseRows;
                PauseRowStep = FMath::Max(PauseRowStep,
                                          RefreshText(Entry.Label, 0, 0, 26.f, UIWhite, PanelW - 164.f, false) + 30.f);
            }
    // The pause frame's inner top rim extends below the old eyebrow position.
    const float PauseHeadingOffset =
        Pause ? 64.f + RefreshText(TEXT("JOURNEY / PAUSED"), 0, 0, 18.f, UICyan, PanelW - 128.f, false) + 10.f : 72.f;
    const float PauseHeight = Pause ? PauseHeadingOffset +
                                          RefreshText(Mode.PanelTitle, 0, 0, 42.f, UIWhite, PanelW - 128.f, false) +
                                          32.f + PauseRows * PauseRowStep + 140.f
                                    : 0.f;
    const float PanelH = FullScreen ? 772.f : Live ? 780.f : Pause ? FMath::Clamp(PauseHeight, 460.f, 930.f) : 930.f;
    const float PanelY = FullScreen ? 202.f : Live ? 180.f : Pause ? (1080.f - PanelH) * .5f : 74.f;
    // Nine-slice the approved frame: growing a page must not grow its ornamental border
    // until the usable content is squeezed into a small central box.
    if (auto *Frame = RefreshTexture(TEXT("Frame")))
    {
        const float SourceW = Frame->GetSizeX(), SourceH = Frame->GetSizeY();
        constexpr float Corner = 84.f, SourceCorner = 128.f;
        const float X[] = {PanelX, PanelX + Corner, PanelX + PanelW - Corner, PanelX + PanelW};
        const float Y[] = {PanelY, PanelY + Corner, PanelY + PanelH - Corner, PanelY + PanelH};
        const float U[] = {0, SourceCorner / SourceW, 1.f - SourceCorner / SourceW, 1};
        const float V[] = {0, SourceCorner / SourceH, 1.f - SourceCorner / SourceH, 1};
        for (int32 Row = 0; Row < 3; ++Row)
            for (int32 Col = 0; Col < 3; ++Col)
            {
                FCanvasTileItem Item(RefreshOrigin + FVector2D(X[Col], Y[Row]) * RefreshScale, Frame->GetResource(),
                                     FVector2D(X[Col + 1] - X[Col], Y[Row + 1] - Y[Row]) * RefreshScale,
                                     FVector2D(U[Col], V[Row]), FVector2D(U[Col + 1], V[Row + 1]), FLinearColor::White);
                Item.BlendMode = SE_BLEND_Translucent;
                Canvas->DrawItem(Item);
            }
    }
    const float InnerX = PanelX + 64.f, InnerW = PanelW - 128.f;
    const float HeadingY = FullScreen ? 73.f : PanelY + PauseHeadingOffset;
    RefreshText(Settings ? TEXT("PREFERENCES")
                : Pause  ? TEXT("JOURNEY / PAUSED")
                         : TEXT("SHIP / STATION"),
                InnerX, FullScreen ? 35.f : PanelY + (Pause ? 64.f : 43.f), 18, UICyan);
    const float HeadingH = RefreshText(Mode.PanelTitle, InnerX, HeadingY, Live ? 28.f : 42.f, UIWhite, InnerW);
    const float BodyY = FullScreen ? 310.f : HeadingY + HeadingH + 32.f;
    const float BackY = PanelY + PanelH - 112.f;
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
    auto Button = [&](int32 I, float X, float Y, float Width, float Height, float Pixels)
    {
        const auto &Entry = Mode.Entries[I];
        const FBox2D B = RefreshBounds(X, Y, Width, Height);
        DrawRect(FLinearColor(.07f, .12f, .17f, .65f), B.Min.X, B.Min.Y, B.GetSize().X, B.GetSize().Y);
        Focus(I, X, Y, Width, Height);
        Bound(I, X, Y, Width, Height);
        RefreshText(Entry.Label, X + 18.f, Y + 12.f, Pixels,
                    Entry.Enabled ? (Mode.SelectedEntry == I ? UICyan : UIWhite) : FLinearColor(.38f, .44f, .5f),
                    Width - 36.f);
    };
    const int32 Back = Mode.Entries.IndexOfByPredicate([](const FSSMenuEntry &Entry) { return Entry.Action == 0; });
    if (Back != INDEX_NONE)
        Button(Back, InnerX, BackY, FullScreen ? 260.f : InnerW, 58.f, 24.f);
    if (!SaveError)
        RefreshText(UsingGamepad() ? (Live       ? TEXT("D-PAD: CHOOSE | A: SELECT | B: CLOSE")
                                      : Settings ? TEXT("LEFT STICK / D-PAD: MOVE / ADJUST | A: SELECT | B: BACK")
                                                 : TEXT("LEFT STICK / D-PAD: MOVE | A: SELECT | B: BACK"))
                                   : TEXT("ARROWS: MOVE | ENTER / CLICK: SELECT | ESC: BACK"),
                    Live    ? PanelX
                    : Pause ? InnerX
                            : 64.f,
                    Live    ? 990.f
                    : Pause ? PanelY + PanelH + 28.f
                            : 1024.f,
                    Live ? 16.f : 19.f, UIWhite,
                    Live    ? PanelW
                    : Pause ? InnerW
                            : ViewWidth - 128.f);
    if (Settings)
    {
        const int Actions[] = {5, 10, 11, 12};
        const TCHAR *Names[] = {TEXT("GENERAL"), TEXT("GRAPHICS"), TEXT("AUDIO"), TEXT("CONTROLS")};
        const ESSPanel Panels[] = {ESSPanel::Settings, ESSPanel::Graphics, ESSPanel::Audio, ESSPanel::Controls};
        const auto &V = S.settings;
        const bool Controls = Mode.Panel == ESSPanel::Controls;
        const float TabW = InnerW / 4.f;
        const float TabTextScale = FMath::Clamp(float(V.uiScale), .8f, 1.4f);
        const FSlateFontInfo TabFont(RefreshFont,
                                     FMath::Max(8, FMath::RoundToInt(23.f * RefreshScale * .75f * TabTextScale)));
        const float RowW = Controls ? InnerW * .61f : InnerW;
        const float LabelW = Controls ? RowW * .45f : RowW * .4f;
        const float ValueW = Controls ? 145.f : 235.f;
        const float ValueX = InnerX + RowW - ValueW - 18.f;
        const float ControlX = InnerX + LabelW + 30.f;
        const float ControlW = FMath::Max(140.f, ValueX - ControlX - 18.f);
        const float RowPixels = Controls ? 24.f : 28.f;
        const float RowStep = Controls ? 90.f : 114.f;
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
                const float X = InnerX + Tab * TabW;
                RefreshImage(Mode.Panel == Panels[Tab] || Mode.SelectedEntry == I ? TEXT("TabActive") : TEXT("Tab"), X,
                             172.f, TabW - 12.f, 92.f);
                const FBox2D TabBounds = RefreshBounds(X + 18.f, 187.f, TabW - 48.f, 58.f);
                FCanvasTextItem TabLabel(TabBounds.GetCenter(), FText::FromString(Names[Tab]), TabFont, UIWhite);
                TabLabel.bCentreX = true;
                TabLabel.bCentreY = true;
                TabLabel.EnableShadow(FLinearColor(0, 0, 0, .9f), FVector2D(1, 1));
                Canvas->DrawItem(TabLabel);
                Bound(I, X + 18.f, 187.f, TabW - 48.f, 58.f);
                Focus(I, X + 18.f, 187.f, TabW - 48.f, 58.f);
                continue;
            }
            if (Entry.Action == 0)
            {
                continue;
            }
            const float Y = BodyY + Row++ * RowStep;
            Focus(I, InnerX, Y - 10.f, RowW, RowStep - 6.f);
            Bound(I, InnerX, Y - 10.f, RowW, RowStep - 6.f);
            FString Label, Value;
            if (!Entry.Label.Split(TEXT(":"), &Label, &Value))
            {
                Label = Entry.Action == 9 ? TEXT("Asset acknowledgements") : TEXT("Flight guidance");
                Value = Entry.Action == 9 ? TEXT("VIEW") : TEXT("REPLAY NEXT RUN");
            }
            Value.TrimStartAndEndInline();
            RefreshText(Label, InnerX + 18.f, Y, RowPixels, UIWhite, LabelW - 18.f);
            const bool Toggle = Entry.Action == 13 || Entry.Action == 15 || Entry.Action == 18;
            const bool Slider = (Entry.Action >= 19 && Entry.Action <= 23);
            if (Toggle)
            {
                const bool On = Entry.Action == 13 ? V.subtitles : Entry.Action == 15 ? V.cameraShake : V.motionBlur;
                RefreshImage(On ? TEXT("ToggleOn") : TEXT("ToggleOff"), ControlX, Y - 20, 162, 88);
            }
            else if (Slider)
            {
                const float Amount = Entry.Action == 19   ? V.masterVolume
                                     : Entry.Action == 20 ? V.musicVolume
                                     : Entry.Action == 21 ? V.effectsVolume
                                     : Entry.Action == 22 ? (V.mouseSensitivity - .3) / 2.6
                                                          : (V.controllerSensitivity - .3) / 2.6;
                const float Start = ControlX;
                // Exact export padding: track core x20..640/y20..34; fill x20..320.
                // Preserve one scale for all three assets so rail, fill and knob share a centreline.
                const float SliderWidth = FMath::Min(360.f, ControlW);
                const float SliderScale = SliderWidth / 660.f;
                const float Rail = 620.f * SliderScale;
                const float CentreY = Y + 20.f;
                const float RailX = Start + 20.f * SliderScale;
                RefreshImage(TEXT("Track"), Start, CentreY - 27.f * SliderScale, SliderWidth, 54.f * SliderScale);
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
            RefreshText(Value.ToUpper(), ValueX, Y, Controls ? 21.f : 28.f,
                        Slider || Entry.Action == 14 ? UIAmber : UICyan, ValueW);
        }
        if (Controls)
        {
            const float GuideX = InnerX + RowW + 44.f, GuideW = InnerW - RowW - 44.f;
            const float GuideH = RefreshText(TEXT("CURRENT FLIGHT PRESET"), GuideX, BodyY, 26, UICyan, GuideW);
            RefreshText(Mode.PanelDetail, GuideX, BodyY + GuideH + 22.f, 20, UIWhite, GuideW);
        }
        else if (!Mode.PanelDetail.IsEmpty())
            RefreshText(Mode.PanelDetail, InnerX + 18.f, BackY - 70.f, 21, UIWhite, InnerW);
    }
    else
    {
        const float TextPixels = Wardrobe ? 30.f : Live ? 21.f : 26.f;
        const float ListW = Wardrobe ? InnerW * .68f : Pause ? InnerW : InnerW - 50.f;
        float RowStart = BodyY;
        if (Wardrobe)
        {
            const float InfoX = InnerX + ListW + 64.f, InfoW = InnerW - ListW - 64.f;
            const float InfoH = RefreshText(TEXT("CHOOSE YOUR CHARACTER"), InfoX, BodyY, 26, UICyan, InfoW);
            RefreshText(Mode.PanelDetail, InfoX, BodyY + InfoH + 24.f, 23, UIWhite, InfoW);
        }
        else if (!Pause && !Mode.PanelDetail.IsEmpty())
            RowStart += RefreshText(Mode.PanelDetail, InnerX, BodyY, Live ? 19.f : 23.f, UIWhite, InnerW) + 26.f;
        float RowStep = Wardrobe ? 82.f : Pause ? PauseRowStep : 72.f;
        for (int32 I = 0; I < Mode.Entries.Num(); ++I)
        {
            if (I == Back)
                continue;
            ScrollEntries.Add(I);
            RowStep = FMath::Max(
                RowStep, RefreshText(Mode.Entries[I].Label, 0, 0, TextPixels, UIWhite, ListW - 36.f, false) + 30.f);
        }
        ScrollCount = ScrollEntries.Num();
        const float ListBottom = Back != INDEX_NONE ? BackY - 24.f : PanelY + PanelH - 72.f;
        ScrollVisible = FMath::Max(1, FMath::FloorToInt((ListBottom - RowStart) / RowStep));
        const int32 SelectedRow = ScrollEntries.IndexOfByKey(Mode.SelectedEntry);
        if (SelectedRow != INDEX_NONE)
        {
            if (SelectedRow < ScrollFirst)
                ScrollFirst = SelectedRow;
            else if (SelectedRow >= ScrollFirst + ScrollVisible)
                ScrollFirst = SelectedRow - ScrollVisible + 1;
        }
        ScrollFirst = FMath::Clamp(ScrollFirst, 0, FMath::Max(0, ScrollCount - ScrollVisible));
        for (int32 Row = 0; Row < ScrollVisible && ScrollFirst + Row < ScrollCount; ++Row)
            Button(ScrollEntries[ScrollFirst + Row], InnerX, RowStart + Row * RowStep, ListW, RowStep - 8.f,
                   TextPixels);
        if (ScrollCount > ScrollVisible)
        {
            const float TrackX = InnerX + ListW + 12.f, TrackY = RowStart + 34.f;
            const float TrackHeight = FMath::Max(80.f, ScrollVisible * RowStep - 76.f);
            const float ThumbHeight = FMath::Max(28.f, TrackHeight * float(ScrollVisible) / ScrollCount);
            const float Fraction = float(ScrollFirst) / FMath::Max(1, ScrollCount - ScrollVisible);
            const float ThumbY = TrackY + Fraction * (TrackHeight - ThumbHeight);
            ScrollTrackBounds = RefreshBounds(TrackX, TrackY, 34, TrackHeight);
            ScrollThumbBounds = RefreshBounds(TrackX + 7.f, ThumbY, 20, ThumbHeight);
            ScrollUpBounds = RefreshBounds(TrackX - 4.f, TrackY - 38.f, 42, 36);
            ScrollDownBounds = RefreshBounds(TrackX - 4.f, TrackY + TrackHeight + 4.f, 42, 36);
            RefreshImage(TEXT("ScrollTrack"), TrackX, TrackY, 34, TrackHeight);
            RefreshImage(TEXT("ScrollThumb"), TrackX - 5.f, ThumbY - 12.f, 44, ThumbHeight + 24.f);
            RefreshImage(TEXT("ScrollUp"), TrackX, TrackY - 34.f, 33, 28);
            RefreshImage(TEXT("ScrollDown"), TrackX, TrackY + TrackHeight + 8.f, 33, 28);
        }
    }
    if (SaveError)
        RefreshText(Mode.Announcement, InnerX, FMath::Min(1000.f, PanelY + PanelH + 28.f), 18, UIAmber, InnerW);
    else if (!Pause && !FullScreen && Mode.IsAnnouncementVisible())
        RefreshText(Mode.Announcement, InnerX, PanelY + PanelH - 43.f, 18, UIAmber, InnerW);
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

bool ASSHUD::NavigateMenu(int32 Horizontal, int32 Vertical)
{
    auto *GM = GetWorld() ? GetWorld()->GetAuthGameMode<ASSGameMode>() : nullptr;
    if (!GM || !GM->IsMenuOpen() || GM->Entries.IsEmpty())
        return false;
    const auto Enabled = [&](int32 Index) { return GM->Entries.IsValidIndex(Index) && GM->Entries[Index].Enabled; };
    const int32 Current = FMath::Clamp(GM->SelectedEntry, 0, GM->Entries.Num() - 1);
    const bool Settings = IsSettingsPanel(GM->Panel) && GM->Entries.Num() > 4;
    if (Settings && Current < 4)
    {
        if (Horizontal != 0)
            GM->SelectedEntry = FMath::Clamp(Current + FMath::Sign(Horizontal), 0, 3);
        else if (Vertical > 0)
            GM->SelectedEntry = 4;
        return true;
    }
    if (Settings && Current == 4 && Vertical < 0)
    {
        GM->SelectedEntry = GM->Panel == ESSPanel::Settings   ? 0
                            : GM->Panel == ESSPanel::Graphics ? 1
                            : GM->Panel == ESSPanel::Audio    ? 2
                                                              : 3;
        return true;
    }
    if (Vertical == 0)
        return true;
    const int32 Step = FMath::Sign(Vertical);
    for (int32 Next = Current + Step; GM->Entries.IsValidIndex(Next); Next += Step)
        if (Enabled(Next))
        {
            GM->SelectedEntry = Next;
            break;
        }
    return true;
}

// Scrolling changes UI focus only; transactions remain in ActivateEntry.
bool ASSHUD::ScrollMenu(int32 Rows)
{
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!GM || static_cast<int32>(GM->Panel) != ScrollPanel || ScrollCount <= 0 || ScrollEntries.IsEmpty())
        return false;
    ScrollFirst = FMath::Clamp(ScrollFirst + Rows, 0, FMath::Max(0, ScrollCount - ScrollVisible));
    const int32 SelectedRow = ScrollEntries.IndexOfByKey(GM->SelectedEntry);
    if (SelectedRow != INDEX_NONE)
        GM->SelectedEntry = ScrollEntries[FMath::Clamp(SelectedRow, ScrollFirst,
                                                       FMath::Min(ScrollCount - 1, ScrollFirst + ScrollVisible - 1))];
    return true;
}

bool ASSHUD::HandleMenuScrollPointer(FVector2D Point, bool Pressed, bool Held)
{
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (!GM || static_cast<int32>(GM->Panel) != ScrollPanel || ScrollCount <= ScrollVisible)
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
