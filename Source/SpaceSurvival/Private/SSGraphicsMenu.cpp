#include "SSGameMode.h"
#include "SSGameInstance.h"

namespace
{
int32 StepChoice(int32 Value, const TArray<int32> &Values, int32 Direction)
{
    if (Values.IsEmpty())
        return Value;
    const int32 Index = FMath::Max(0, Values.IndexOfByKey(Value));
    return Values[Direction == 0 ? (Index + 1) % Values.Num()
                                 : FMath::Clamp(Index + FMath::Sign(Direction), 0, Values.Num() - 1)];
}
void StepToggle(bool &Value, int32 Direction)
{
    Value = Direction == 0 ? !Value : Direction > 0;
}
FString OnOff(bool Value)
{
    return Value ? TEXT("On") : TEXT("Off");
}
} // namespace

void ASSGameMode::BuildGraphicsEntries()
{
    PanelTitle = TEXT("GRAPHICS");
    const auto &S = GraphicsDraft;
    const auto &C = GraphicsCapabilities;
    auto Row = [&](const TCHAR *Name, FString Value, int32 Action, FString Help, bool Enabled = true)
    {
        AddEntry(FString(Name) + TEXT(": ") + Value, Action, Enabled);
        Entries.Last().Help = MoveTemp(Help);
    };
    AddEntry(TEXT("IMAGE & PERFORMANCE"), 220);
    AddEntry(TEXT("ADVANCED"), 221);
    AddEntry(TEXT("DISPLAY"), 222);
    if (GraphicsSection == 0)
    {
        Row(TEXT("Image reconstruction"), SSGraphics::ReconstructionName(S.reconstruction), 200,
            C.DLSS ? TEXT("Choose one rendering method.") : C.DLSSReason);
        Row(TEXT("DLSS quality"),
            S.reconstruction == 2 ? TEXT("Native resolution") : SSGraphics::QualityName(S.dlssQuality), 201,
            S.reconstruction == 1 ? TEXT("Quality, Balanced, Performance or Ultra Performance.")
                                  : TEXT("Select DLSS to adjust upscaling quality."),
            C.DLSS && S.reconstruction == 1);
        Row(TEXT("DLSS Frame Generation"), C.FrameGeneration ? OnOff(S.frameGeneration) : TEXT("Unavailable"), 202,
            C.FrameGeneration ? TEXT("Adds generated frames for smoother presentation.") : C.FrameReason,
            C.FrameGeneration);
        Row(TEXT("Frame generation mode"),
            C.FrameGeneration ? SSGraphics::FrameModeName(S.frameGenerationMode) : TEXT("Unavailable"), 203,
            S.frameGeneration ? TEXT("Choose from supported Dynamic or fixed modes.")
                              : TEXT("Enable Frame Generation to select its mode."),
            C.FrameGeneration && S.frameGeneration);
        Row(TEXT("NVIDIA Reflex Low Latency"),
            !C.Reflex           ? TEXT("Unavailable")
            : S.frameGeneration ? TEXT("On (required)")
            : S.reflex == 2     ? TEXT("On + Boost")
                                : OnOff(S.reflex != 0),
            204,
            !C.Reflex           ? C.ReflexReason
            : S.frameGeneration ? TEXT("Stays on while Frame Generation is enabled.")
                                : TEXT("Reduces the render queue for faster response."),
            C.Reflex && !S.frameGeneration);
        Row(TEXT("Frame rate limit"), S.frameLimit ? FString::Printf(TEXT("%d FPS"), S.frameLimit) : TEXT("Unlimited"),
            17, TEXT("Limits rendered frames; generated presentation can be higher."));
        Row(TEXT("Performance statistics"), OnOff(S.diagnosticsOverlay), 96,
            TEXT("Show frame timing, VRAM and response metrics."));
    }
    else if (GraphicsSection == 1)
    {
        const bool RR = C.RayReconstruction && (S.reconstruction == 1 || S.reconstruction == 2);
        Row(TEXT("DLSS Ray Reconstruction"), RR ? OnOff(S.rayReconstruction) : TEXT("Unavailable"), 205,
            RR ? TEXT("AI denoising for the active hardware ray-tracing path.")
               : TEXT("Requires DLSS/DLAA and hardware ray-traced Lumen."),
            RR);
        Row(TEXT("NVIDIA image sharpening"), C.NIS ? OnOff(S.sharpening) : TEXT("Unavailable"), 206,
            C.NIS ? TEXT("Independent sharpness adjustment when supported.") : C.NISReason, C.NIS);
        Row(TEXT("Sharpening strength"), FString::Printf(TEXT("%.0f%%"), S.sharpness * 100), 207,
            S.sharpening ? TEXT("Adjust fine edge contrast.") : TEXT("Enable sharpening to adjust this value."),
            C.NIS && S.sharpening);
        Row(TEXT("RTX Dynamic Vibrance"), C.Vibrance ? OnOff(S.vibrance) : TEXT("Unavailable"), 208,
            C.Vibrance ? TEXT("Optional colour enhancement; off by default.") : C.VibranceReason, C.Vibrance);
        Row(TEXT("Vibrance intensity"), FString::Printf(TEXT("%.0f%%"), S.vibranceIntensity * 100), 209,
            S.vibrance ? TEXT("Choose the strength of colour enhancement.")
                       : TEXT("Enable RTX Dynamic Vibrance to adjust."),
            C.Vibrance && S.vibrance);
        Row(TEXT("Saturation boost"), FString::Printf(TEXT("%.0f%%"), S.saturationBoost * 100), 210,
            TEXT("Available with RTX Dynamic Vibrance."), C.Vibrance && S.vibrance);
        Row(TEXT("Reflex Boost"), C.Reflex ? OnOff(S.reflex == 2) : TEXT("Unavailable"), 211,
            C.Reflex ? TEXT("On + Boost may use more power to lower latency.") : C.ReflexReason, C.Reflex);
    }
    else
    {
        const TCHAR *Quality[] = {TEXT("Low"), TEXT("Medium"), TEXT("High"), TEXT("Epic"), TEXT("Cinematic")};
        Row(TEXT("Quality"), Quality[FMath::Clamp(S.quality, 0, 4)], 16,
            TEXT("Effects, lighting and texture scalability; render method stays separate."));
        Row(TEXT("Motion blur"), OnOff(S.motionBlur), 18, TEXT("Camera and object motion blur."));
        const bool CanSync = !S.frameGeneration || C.FrameGenerationVSync;
        Row(TEXT("VSync"), CanSync ? OnOff(S.vsync) : TEXT("Off (required)"), 212,
            CanSync ? TEXT("Synchronize presentation to the display refresh.")
                    : TEXT("This Frame Generation configuration requires VSync off."),
            CanSync);
    }
    AddEntry(TEXT("DEFAULTS"), 223);
    AddEntry(TEXT("APPLY"), 224);
}

bool ASSGameMode::HandleGraphicsAction(int32 Action, int32 Direction)
{
    if (Action != 16 && Action != 17 && Action != 18 && Action != 96 && (Action < 200 || Action > 224))
        return false;
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !bGraphicsDraftActive)
        return false;
    auto &S = GraphicsDraft;
    const auto &C = GraphicsCapabilities;
    if (Action >= 220 && Action <= 222)
    {
        if (Direction != 0)
            return false;
        GraphicsSection = Action - 220;
    }
    else if (Action == 223)
    {
        if (Direction != 0)
            return false;
        SSGraphics::CopyPreferences(SS::Settings{}, S);
        GraphicsFeedback = TEXT("Defaults staged. Apply to save; Back cancels.");
    }
    else if (Action == 224)
    {
        if (Direction != 0)
            return false;
        GraphicsCapabilities = SSGraphics::Query();
        SS::Settings Applied = SSGraphics::Resolve(S, GraphicsCapabilities);
        if (GraphicsCapabilities.Reflex)
            Applied.reflex = S.reflex;
        const SS::Settings Previous = GI->Session.settings;
        SSGraphics::CopyPreferences(Applied, GI->Session.settings);
        if (GI->PersistSettings())
        {
            GraphicsDraft = GI->Session.settings;
            GraphicsFeedback = TEXT("Graphics settings applied and saved.");
        }
        else
        {
            GI->Session.settings = Previous;
            GI->ApplySettings();
            GraphicsFeedback = GI->LastSaveError;
        }
    }
    else
    {
        const int32 Step = Direction < 0 ? -1 : 1;
        switch (Action)
        {
        case 200:
        {
            TArray<int32> Methods{0};
            if (C.DLSS && !C.QualityModes.IsEmpty())
                Methods.Add(1);
            if (C.DLAA)
                Methods.Add(2);
            if (C.NIS)
                Methods.Add(3);
            S.reconstruction = StepChoice(S.reconstruction, Methods, Direction);
            break;
        }
        case 201:
            S.dlssQuality = StepChoice(S.dlssQuality, C.QualityModes, Direction);
            break;
        case 202:
            StepToggle(S.frameGeneration, Direction);
            break;
        case 203:
            S.frameGenerationMode = StepChoice(S.frameGenerationMode, C.FrameModes, Direction);
            break;
        case 204:
            S.reflex = StepChoice(S.reflex, {0, 1, 2}, Direction);
            break;
        case 205:
            StepToggle(S.rayReconstruction, Direction);
            break;
        case 206:
            StepToggle(S.sharpening, Direction);
            break;
        case 207:
            S.sharpness = FMath::Clamp(S.sharpness + Step * .05, 0., 1.);
            break;
        case 208:
            StepToggle(S.vibrance, Direction);
            break;
        case 209:
            S.vibranceIntensity = FMath::Clamp(S.vibranceIntensity + Step * .05, 0., 1.);
            break;
        case 210:
            S.saturationBoost = FMath::Clamp(S.saturationBoost + Step * .05, 0., 1.);
            break;
        case 211:
            S.reflex = Direction == 0 ? (S.reflex == 2 ? 1 : 2) : Direction > 0 ? 2 : 1;
            break;
        case 212:
            StepToggle(S.vsync, Direction);
            break;
        case 16:
            S.quality = StepChoice(S.quality, {0, 1, 2, 3, 4}, Direction);
            break;
        case 17:
            S.frameLimit = StepChoice(S.frameLimit, {30, 60, 90, 120, 144, 165, 240, 360, 0}, Direction);
            break;
        case 18:
            StepToggle(S.motionBlur, Direction);
            break;
        case 96:
            StepToggle(S.diagnosticsOverlay, Direction);
            break;
        default:
            return false;
        }
        GraphicsFeedback = TEXT("Changes staged. Apply to save; Back cancels.");
    }
    OpenPanel(ESSPanel::Graphics);
    return true;
}
