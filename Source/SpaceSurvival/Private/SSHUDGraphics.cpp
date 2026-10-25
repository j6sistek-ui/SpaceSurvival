#include "SSHUD.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSGraphicsSettings.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Fonts/FontMeasure.h"
#include "EngineFontServices.h"
#include "Misc/Paths.h"
#include "RHI.h"
#include "RenderTimer.h"

bool ASSHUD::DrawGraphicsMenu(const ASSGameMode &Mode)
{
    BeginRefreshLayout();
    auto Font = [&](TObjectPtr<UFont> &Target, const TCHAR *File)
    {
        if (Target)
            return;
        FSlateFontInfo Source(FPaths::ProjectContentDir() / TEXT("SpaceSurvival/UI/Fonts") / File, 16);
        Target = NewObject<UFont>(this);
        Target->FontCacheType = EFontCacheType::Runtime;
        Target->GetMutableInternalCompositeFont() = *Source.GetCompositeFont();
    };
    Font(GraphicsBodyFont, TEXT("Rajdhani-Medium.ttf"));
    Font(GraphicsMonoFont, TEXT("IBMPlexMono-Regular.ttf"));
    const FLinearColor Cyan = FLinearColor::FromSRGBColor(FColor(140, 215, 255));
    const FLinearColor Muted = FLinearColor::FromSRGBColor(FColor(172, 193, 216));
    const FLinearColor Deep = FLinearColor::FromSRGBColor(FColor(1, 10, 22));
    const FLinearColor Body = FLinearColor::FromSRGBColor(FColor(2, 36, 58));
    const float UIScale =
        GetGameInstance<USSGameInstance>()
            ? FMath::Clamp(float(GetGameInstance<USSGameInstance>()->Session.settings.uiScale), .8f, 1.4f)
            : 1.f;
    const auto Measure = FEngineFontServices::Get().GetFontMeasure();
    auto Rect = [&](float X, float Y, float W, float H, FLinearColor Color)
    {
        const auto B = RefreshBounds(X, Y, W, H);
        DrawRect(Color, B.Min.X, B.Min.Y, B.GetSize().X, B.GetSize().Y);
    };
    auto TextAt = [&](const FString &Text, float X, float Y, float Size, float W, UFont *Face, FLinearColor Color,
                      bool Centre = false)
    {
        FSlateFontInfo Info(Face, FMath::Max(8, FMath::RoundToInt(Size * RefreshScale * .75f * UIScale)));
        const float DPI = FMath::Max(.1f, Canvas->GetDPIScale());
        while (Info.Size > 8 && Measure.IsValid() && Measure->Measure(Text, Info, DPI).X / DPI > W * RefreshScale)
            --Info.Size;
        FCanvasTextItem Item(RefreshOrigin + FVector2D(X + (Centre ? W * .5f : 0), Y) * RefreshScale,
                             FText::FromString(Text), Info, Color);
        Item.bCentreX = Centre;
        Canvas->DrawItem(Item);
    };
    auto ParagraphAt = [&](const FString &Text, float Y, float Size = 23.f)
    {
        TArray<FString> Words;
        Text.ParseIntoArray(Words, TEXT(" "), true);
        FString Line;
        FSlateFontInfo Info(GraphicsBodyFont, FMath::Max(8, FMath::RoundToInt(Size * RefreshScale * .75f)));
        const float DPI = FMath::Max(.1f, Canvas->GetDPIScale());
        for (const FString &Word : Words)
        {
            FString Candidate = Line.IsEmpty() ? Word : Line + TEXT(" ") + Word;
            if (!Line.IsEmpty() && Measure.IsValid() &&
                Measure->Measure(Candidate, Info, DPI).X / DPI > 528.f * RefreshScale)
            {
                TextAt(Line, 1288, Y, Size, 528, GraphicsBodyFont, Muted);
                Y += 29;
                Line = Word;
            }
            else
                Line = Candidate;
        }
        if (!Line.IsEmpty())
        {
            TextAt(Line, 1288, Y, Size, 528, GraphicsBodyFont, Muted);
            Y += 29;
        }
        return Y;
    };
    DrawRect(Deep, 0, 0, Canvas->SizeX, Canvas->SizeY);
    RefreshImage(TEXT("Background"), 0, 0, 1920, 1080, FLinearColor(1, 1, 1, .175f));
    MenuBounds.Init(FBox2D(EForceInit::ForceInit), Mode.Entries.Num());
    ScrollCount = 0;
    ScrollEntries.Reset();
    bScrollDragging = false;
    const auto IndexOf = [&](int32 Action)
    { return Mode.Entries.IndexOfByPredicate([&](const FSSMenuEntry &Entry) { return Entry.Action == Action; }); };
    auto Bound = [&](int32 I, float X, float Y, float W, float H)
    {
        if (I == INDEX_NONE)
            return;
        MenuBounds[I] = RefreshBounds(X, Y, W, H);
        if (Mode.SelectedEntry == I)
        {
            Rect(X, Y, W, H, FLinearColor(.1f, .35f, .5f, .18f));
            Rect(X, Y, 3, H, Cyan);
        }
    };
    auto Button = [&](int32 Action, float X, float Y, const TCHAR *Name, bool Active = false)
    {
        const int32 I = IndexOf(Action);
        RefreshImage(Active || Mode.SelectedEntry == I ? TEXT("TabActive") : TEXT("Tab"), X, Y, 250, 66);
        TextAt(Name, X + 10, Y + 15, 26, 230, RefreshFont, Cyan, true);
        Bound(I, X + 10, Y + 5, 230, 56);
    };
    TextAt(TEXT("PAUSE / SETTINGS"), 72, 52, 16, 1600, GraphicsMonoFont, Cyan);
    TextAt(TEXT("GRAPHICS"), 72, 82, 48, 1600, RefreshFont, Cyan);
    const int32 Tabs[] = {5, 10, 11, 12};
    const TCHAR *TabNames[] = {TEXT("GENERAL"), TEXT("GRAPHICS"), TEXT("AUDIO"), TEXT("CONTROLS")};
    for (int32 T = 0; T < 4; ++T)
        Button(Tabs[T], 72 + T * 266, 180, TabNames[T], T == 1);
    const float SectionX[] = {72, 526, 880};
    const float SectionW[] = {430, 330, 240};
    const TCHAR *Sections[] = {TEXT("IMAGE & PERFORMANCE"), TEXT("ADVANCED"), TEXT("DISPLAY")};
    for (int32 T = 0; T < 3; ++T)
    {
        TextAt(Sections[T], SectionX[T], 266, 26, SectionW[T], RefreshFont, Mode.GraphicsSection == T ? Cyan : Muted);
        Bound(IndexOf(220 + T), SectionX[T], 260, SectionW[T], 48);
    }
    int32 Row = 0;
    const auto &S = Mode.GraphicsDraft;
    for (int32 I = 0; I < Mode.Entries.Num(); ++I)
    {
        const auto &E = Mode.Entries[I];
        if (E.Help.IsEmpty())
            continue;
        const float Y = 326 + Row++ * 94;
        Rect(72, Y, 1120, 86, Body);
        FString Label, Value;
        E.Label.Split(TEXT(":"), &Label, &Value);
        Value.TrimStartAndEndInline();
        const FLinearColor C = E.Enabled ? Cyan : Muted.CopyWithNewOpacity(.55f);
        TextAt(Label, 92, Y + 9, 28, 690, GraphicsBodyFont, C);
        TextAt(E.Help, 92, Y + 47, 23, 690, GraphicsBodyFont, E.Enabled ? Muted : Muted.CopyWithNewOpacity(.6f));
        const bool Toggle = E.Action == 202 || E.Action == 205 || E.Action == 206 || E.Action == 208 ||
                            E.Action == 211 || E.Action == 212 || E.Action == 18 || E.Action == 96;
        const bool Range = E.Action == 207 || E.Action == 209 || E.Action == 210;
        if (Toggle)
        {
            TextAt(Value.ToUpper(), 868, Y + 33, 16, 164, GraphicsMonoFont, C);
            RefreshImage(!E.Enabled            ? TEXT("ToggleDisabled")
                         : Value == TEXT("On") ? TEXT("ToggleOn")
                                               : TEXT("ToggleOff"),
                         1066, Y + 13, 110, 59.75f);
        }
        else if (Range)
        {
            TextAt(Value, 868, Y + 33, 16, 56, GraphicsMonoFont, C);
            const float Amount = E.Action == 207   ? S.sharpness
                                 : E.Action == 209 ? S.vibranceIntensity
                                                   : S.saturationBoost;
            RefreshImage(TEXT("Track"), 940, Y + 38, 222, 18,
                         E.Enabled ? FLinearColor::White : FLinearColor(1, 1, 1, .45f));
            RefreshImage(TEXT("Knob"), 936 + Amount * 206, Y + 30, 24, 24,
                         E.Enabled ? FLinearColor::White : FLinearColor(1, 1, 1, .45f));
        }
        else
        {
            RefreshImage(TEXT("Dropdown"), 868, Y + 5, 302, 75.5f,
                         E.Enabled ? FLinearColor::White : FLinearColor(1, 1, 1, .4f));
            TextAt(Value, 890, Y + 30, 23, 250, GraphicsBodyFont, C, true);
        }
        Bound(I, 72, Y, 1120, 86);
    }
    Rect(1264, 326, 584, 638, Deep.CopyWithNewOpacity(.95f));
    Rect(1264, 326, 584, 1, Muted);
    Rect(1264, 963, 584, 1, Muted);
    Rect(1264, 326, 1, 638, Muted);
    Rect(1847, 326, 1, 638, Muted);
    TextAt(Mode.GraphicsSection == 1 ? TEXT("YOUR LOOK, YOUR CHOICE") : TEXT("IMAGE QUALITY & RESPONSE"), 1288, 350, 26,
           528, RefreshFont, Cyan);
    float Y =
        ParagraphAt(Mode.GraphicsSection == 1 ? TEXT("Keep colour enhancement and sharpening off for the original art "
                                                     "direction. Adjust them independently if you prefer.")
                                              : TEXT("DLSS renders at a lower resolution and reconstructs the final "
                                                     "image. DLAA prioritizes native-resolution anti-aliasing."),
                    400);
    Y += 20;
    const int32 Selected = Mode.SelectedEntry;
    if (Mode.Entries.IsValidIndex(Selected) && !Mode.Entries[Selected].Help.IsEmpty())
    {
        TextAt(TEXT("SELECTED OPTION"), 1288, Y, 26, 528, RefreshFont, Cyan);
        Y = ParagraphAt(Mode.Entries[Selected].Help, Y + 44) + 20;
    }
    TextAt(TEXT("LIVE MEASUREMENTS"), 1288, Y, 26, 528, RefreshFont, Cyan);
    Y += 46;
    const auto T = SSGraphics::Telemetry();
    const double Now = FPlatformTime::Seconds();
    if (!GraphicsMeasureAt || Now - GraphicsLastFrameAt > 2.)
    {
        GraphicsMeasureAt = Now;
        GraphicsFrames = 0;
        GraphicsFPS = 0;
    }
    GraphicsLastFrameAt = Now;
    ++GraphicsFrames;
    if (Now - GraphicsMeasureAt >= .75)
    {
        GraphicsFPS = GraphicsFrames / (Now - GraphicsMeasureAt);
        GraphicsMeasureAt = Now;
        GraphicsFrames = 0;
    }
    TextAt(GraphicsFPS > 0 ? FString::Printf(TEXT("Rendered FPS   %.0f"), GraphicsFPS)
                           : TEXT("Rendered FPS   unavailable"),
           1288, Y, 16, 528, GraphicsMonoFont, Muted);
    Y += 26;
    TextAt(T.DisplayedFPS > 0 ? FString::Printf(TEXT("Displayed FPS  %.0f"), T.DisplayedFPS)
                              : TEXT("Displayed FPS  unavailable"),
           1288, Y, 16, 528, GraphicsMonoFont, Muted);
    Y += 26;
    const uint32 GPUCycles = RHIGetGPUFrameCycles();
    TextAt(GPUCycles ? FString::Printf(TEXT("GPU time       %.1f ms"), FPlatformTime::ToMilliseconds(GPUCycles))
                     : TEXT("GPU time       unavailable"),
           1288, Y, 16, 528, GraphicsMonoFont, Muted);
    Y += 26;
    TextAt(T.LatencyMs > 0 ? FString::Printf(TEXT("Game to render %.1f ms"), T.LatencyMs)
                           : TEXT("Game to render unavailable"),
           1288, Y, 16, 528, GraphicsMonoFont, Muted);
    Y += 45;
    ParagraphAt(TEXT("Frame generation improves displayed smoothness. Rendered frame rate and latency still matter. "
                     "GPU memory appears in Performance statistics."),
                Y, 21);
    if (!Mode.GraphicsFeedback.IsEmpty())
        ParagraphAt(Mode.GraphicsFeedback, 868, 21);
    Button(0, 72, 992, TEXT("BACK"));
    Button(223, 346, 992, TEXT("DEFAULTS"));
    Button(224, 620, 992, TEXT("APPLY"), true);
    TextAt(UsingGamepad() ? TEXT("B Back   A Select   LB/RB Tabs") : TEXT("ESC Back   ENTER / CLICK Select"), 894, 998,
           16, 930, GraphicsMonoFont, Muted);
    TextAt(TEXT("D-pad / arrows Navigate   Left / right Change"), 894, 1025, 16, 930, GraphicsMonoFont, Muted);
    return true;
}
