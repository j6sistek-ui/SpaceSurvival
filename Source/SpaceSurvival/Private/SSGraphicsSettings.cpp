#include "SSGraphicsSettings.h"
#include "DynamicRHI.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/App.h"
#include "Modules/ModuleManager.h"
#include "RHI.h"
#if SS_WITH_NVIDIA
#include "DLSSLibrary.h"
#include "NISLibrary.h"
#include "StreamlineLibraryDLSSG.h"
#include "StreamlineLibraryDeepDVC.h"
#include "StreamlineLibraryReflex.h"
#endif

namespace SSGraphics
{
namespace
{
bool RendererReady()
{
    if (!FApp::CanEverRender() || !GEngine || !GEngine->IsInitialized() || !GDynamicRHI || GUsingNullRHI)
        return false;
#if SS_WITH_NVIDIA
    // Blueprint libraries load before their renderer modules. Calling them from
    // GameInstance::Init can permanently cache missing NIS console variables.
    return FModuleManager::Get().IsModuleLoaded(TEXT("DLSS")) &&
           IConsoleManager::Get().FindConsoleVariable(TEXT("r.NIS.Upscaling")) != nullptr;
#else
    return true;
#endif
}
int32 CVarInt(const TCHAR *Name)
{
    const auto *Variable = IConsoleManager::Get().FindConsoleVariable(Name);
    return Variable ? Variable->GetInt() : 0;
}
void SetCurrent(const TCHAR *Name, float Value)
{
    if (auto *Variable = IConsoleManager::Get().FindConsoleVariable(Name))
        Variable->Set(Value, EConsoleVariableFlags(Variable->GetFlags() & ECVF_SetByMask));
}
#if SS_WITH_NVIDIA
const UDLSSMode QualityModes[] = {UDLSSMode::Quality, UDLSSMode::Balanced, UDLSSMode::Performance,
                                  UDLSSMode::UltraPerformance};
EStreamlineDLSSGMode FrameMode(int32 Mode)
{
    if (Mode == 0)
        return UStreamlineLibraryDLSSG::IsDLSSGModeSupported(EStreamlineDLSSGMode::OnDynamic)
                   ? EStreamlineDLSSGMode::OnDynamic
                   : EStreamlineDLSSGMode::Auto;
    const EStreamlineDLSSGMode Modes[] = {EStreamlineDLSSGMode::On2X, EStreamlineDLSSGMode::On3X,
                                          EStreamlineDLSSGMode::On4X, EStreamlineDLSSGMode::On5X,
                                          EStreamlineDLSSGMode::On6X};
    return Modes[FMath::Clamp(Mode - 1, 0, 4)];
}
FString StreamlineReason(EStreamlineFeatureSupport Support)
{
    switch (Support)
    {
    case EStreamlineFeatureSupport::Supported:
        return TEXT("");
    case EStreamlineFeatureSupport::NotSupportedIncompatibleHardware:
        return TEXT("Requires compatible NVIDIA RTX hardware.");
    case EStreamlineFeatureSupport::NotSupportedDriverOutOfDate:
        return TEXT("Update the NVIDIA graphics driver.");
    case EStreamlineFeatureSupport::NotSupportedOperatingSystemOutOfDate:
        return TEXT("Requires a newer Windows version.");
    case EStreamlineFeatureSupport::NotSupportedHardewareSchedulingDisabled:
        return TEXT("Enable Windows hardware GPU scheduling, then restart.");
    case EStreamlineFeatureSupport::NotSupportedByRHI:
        return TEXT("Unavailable with this rendering API or offscreen viewport.");
    case EStreamlineFeatureSupport::NotSupportedIncompatibleAPICaptureToolActive:
        return TEXT("Close the incompatible graphics capture tool.");
    case EStreamlineFeatureSupport::NotSupportedByPlatformAtBuildTime:
        return TEXT("Unavailable in this platform build.");
    default:
        return TEXT("Unavailable in this rendering session.");
    }
}
FString DLSSReason(UDLSSSupport Support)
{
    switch (Support)
    {
    case UDLSSSupport::Supported:
        return TEXT("");
    case UDLSSSupport::NotSupportedIncompatibleHardware:
        return TEXT("Requires an NVIDIA RTX GPU.");
    case UDLSSSupport::NotSupportedDriverOutOfDate:
        return TEXT("Update the NVIDIA graphics driver.");
    case UDLSSSupport::NotSupportedOperatingSystemOutOfDate:
        return TEXT("Requires a newer Windows version.");
    case UDLSSSupport::NotSupportedIncompatibleAPICaptureToolActive:
        return TEXT("Close the incompatible graphics capture tool.");
    default:
        return TEXT("DLSS is unavailable in this rendering session.");
    }
}
#endif
} // namespace

FCapabilities Query()
{
    FCapabilities C;
    C.DLSSReason = C.FrameReason = C.ReflexReason = C.RayReason = C.NISReason = C.VibranceReason =
        TEXT("NVIDIA rendering features are unavailable in this build/session.");
#if SS_WITH_NVIDIA
    if (!RendererReady() || !FModuleManager::Get().IsModuleLoaded(TEXT("DLSSBlueprint")))
        return C;
    C.DLSS = UDLSSLibrary::IsDLSSSupported();
    C.DLAA = C.DLSS && UDLSSLibrary::IsDLSSModeSupported(UDLSSMode::DLAA);
    C.DLSSReason = DLSSReason(UDLSSLibrary::QueryDLSSSupport());
    for (int32 I = 0; I < UE_ARRAY_COUNT(QualityModes); ++I)
        if (C.DLSS && UDLSSLibrary::IsDLSSModeSupported(QualityModes[I]))
            C.QualityModes.Add(I);
    C.Reflex = UStreamlineLibraryReflex::IsReflexSupported();
    C.ReflexReason = StreamlineReason(UStreamlineLibraryReflex::QueryReflexSupport());
    C.FrameGeneration = UStreamlineLibraryDLSSG::IsDLSSGSupported() && C.Reflex;
    C.FrameReason = StreamlineReason(UStreamlineLibraryDLSSG::QueryDLSSGSupport());
    if (!C.Reflex && C.FrameReason.IsEmpty())
        C.FrameReason = TEXT("Frame Generation requires NVIDIA Reflex.");
    for (int32 I = 0; I <= 5; ++I)
        if (C.FrameGeneration && UStreamlineLibraryDLSSG::IsDLSSGModeSupported(FrameMode(I)))
            C.FrameModes.Add(I);
    C.FrameGeneration = C.FrameGeneration && !C.FrameModes.IsEmpty();
    C.FrameGenerationVSync = C.FrameGeneration && UStreamlineLibraryDLSSG::GetDLSSGIsVsyncSupportAvailable();
    C.RayReconstruction = CVarInt(TEXT("r.RayTracing")) && CVarInt(TEXT("r.Lumen.HardwareRayTracing")) &&
                          UDLSSLibrary::IsRayTracingAvailable() && UDLSSLibrary::IsDLSSRRSupported();
    C.RayReason = C.RayReconstruction ? TEXT("") : TEXT("Requires DLSS/DLAA and compatible hardware ray-traced Lumen.");
    C.NIS = UNISLibrary::IsNISSupported();
    C.NISReason = C.NIS ? TEXT("") : TEXT("NVIDIA Image Scaling is unavailable with this rendering API.");
    C.Vibrance = UStreamlineLibraryDeepDVC::IsDeepDVCSupported();
    C.VibranceReason = StreamlineReason(UStreamlineLibraryDeepDVC::QueryDeepDVCSupport());
#endif
    return C;
}

SS::Settings Resolve(const SS::Settings &Requested, const FCapabilities &C)
{
    SS::Settings S = Requested;
    if ((S.reconstruction == 1 && (!C.DLSS || C.QualityModes.IsEmpty())) || (S.reconstruction == 2 && !C.DLAA) ||
        (S.reconstruction == 3 && !C.NIS) || S.reconstruction < 0 || S.reconstruction > 3)
        S.reconstruction = 0;
    if (!C.QualityModes.IsEmpty() && !C.QualityModes.Contains(S.dlssQuality))
        S.dlssQuality = C.QualityModes[0];
    S.frameGeneration = S.frameGeneration && C.FrameGeneration && C.Reflex && !C.FrameModes.IsEmpty();
    if (!C.FrameModes.IsEmpty() && !C.FrameModes.Contains(S.frameGenerationMode))
        S.frameGenerationMode = C.FrameModes[0];
    S.reflex = C.Reflex ? FMath::Clamp(S.reflex, S.frameGeneration ? 1 : 0, 2) : 0;
    S.rayReconstruction =
        S.rayReconstruction && C.RayReconstruction && (S.reconstruction == 1 || S.reconstruction == 2);
    S.sharpening = S.sharpening && C.NIS;
    S.vibrance = S.vibrance && C.Vibrance;
    S.vsync = S.vsync && (!S.frameGeneration || C.FrameGenerationVSync);
    S.sharpness = FMath::Clamp(S.sharpness, 0., 1.);
    S.vibranceIntensity = FMath::Clamp(S.vibranceIntensity, 0., 1.);
    S.saturationBoost = FMath::Clamp(S.saturationBoost, 0., 1.);
    return S;
}

void Apply(const SS::Settings &Requested)
{
    // Display controls remain functional on builds without NVIDIA plugins.
    if (auto *Settings = UGameUserSettings::GetGameUserSettings())
    {
        Settings->SetVSyncEnabled(Requested.vsync);
        Settings->ApplyNonResolutionSettings();
    }
#if SS_WITH_NVIDIA
    if (!RendererReady() || !FModuleManager::Get().IsModuleLoaded(TEXT("DLSSBlueprint")))
        return;
    const auto C = Query();
    const auto S = Resolve(Requested, C);
    // Disable RR first: this restores its saved denoiser state before changing the upscaler.
    if (C.DLSS && UDLSSLibrary::IsDLSSRREnabled())
        UDLSSLibrary::EnableDLSSRR(false);
    if (C.DLSS)
        UDLSSLibrary::EnableDLSS(S.reconstruction == 1 || S.reconstruction == 2);
    float Scale = 100.f;
    if (S.reconstruction == 1)
    {
        bool Supported = false, Fixed = false;
        float Minimum = 100, Maximum = 100, Sharpness = 0;
        const auto *Settings = UGameUserSettings::GetGameUserSettings();
        UDLSSLibrary::GetDLSSModeInformation(
            QualityModes[S.dlssQuality], Settings ? FVector2D(Settings->GetScreenResolution()) : FVector2D(1920, 1080),
            Supported, Scale, Fixed, Minimum, Maximum, Sharpness);
        if (!Supported)
            Scale = 100.f;
    }
    // NIS changes temporal upsampling and mip bias; restore both when returning to a temporal method.
    static TOptional<float> BeforeNISMipBias;
    if (C.NIS)
    {
        if (S.reconstruction == 3 && !BeforeNISMipBias.IsSet())
            if (const auto *Bias = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MipMapLODBias")))
                BeforeNISMipBias = Bias->GetFloat();
        UNISLibrary::SetNISMode(S.reconstruction == 3 ? UNISMode::Quality : UNISMode::Off);
        UNISLibrary::SetNISSharpness(S.sharpening ? S.sharpness : 0.f);
        if (S.reconstruction == 3)
            Scale = UNISLibrary::GetNISRecommendedScreenPercentage(UNISMode::Quality);
        else if (BeforeNISMipBias.IsSet())
        {
            SetCurrent(TEXT("r.MipMapLODBias"), BeforeNISMipBias.GetValue());
            BeforeNISMipBias.Reset();
        }
    }
    SetCurrent(TEXT("r.TemporalAA.Upscaler"), S.reconstruction == 3 ? 0 : 1);
    SetCurrent(TEXT("r.TemporalAA.Upsampling"), S.reconstruction == 3 ? 0 : 1);
    SetCurrent(TEXT("r.AntiAliasingMethod"), S.reconstruction == 3 ? 2 : 4);
    if (auto *Settings = UGameUserSettings::GetGameUserSettings())
    {
        Settings->SetResolutionScaleValueEx(Scale);
        Settings->SetVSyncEnabled(S.vsync);
        Settings->ApplyNonResolutionSettings();
    }
    SetCurrent(TEXT("r.ScreenPercentage"), Scale);
    if (C.Reflex)
        UStreamlineLibraryReflex::SetReflexMode(S.reflex == 2   ? EStreamlineReflexMode::Boost
                                                : S.reflex == 1 ? EStreamlineReflexMode::Enabled
                                                                : EStreamlineReflexMode::Off);
    if (C.FrameGeneration)
        UStreamlineLibraryDLSSG::SetDLSSGMode(S.frameGeneration ? FrameMode(S.frameGenerationMode)
                                                                : EStreamlineDLSSGMode::Off);
    if (C.RayReconstruction)
        UDLSSLibrary::EnableDLSSRR(S.rayReconstruction);
    if (C.Vibrance)
    {
        UStreamlineLibraryDeepDVC::SetDeepDVCIntensity(S.vibranceIntensity);
        UStreamlineLibraryDeepDVC::SetDeepDVCSaturationBoost(S.saturationBoost);
        UStreamlineLibraryDeepDVC::SetDeepDVCMode(S.vibrance ? EStreamlineDeepDVCMode::On
                                                             : EStreamlineDeepDVCMode::Off);
    }
#endif
}

FTelemetry Telemetry()
{
    FTelemetry T;
#if SS_WITH_NVIDIA
    if (!RendererReady())
        return T;
    if (UStreamlineLibraryDLSSG::IsDLSSGSupported())
    {
        UStreamlineLibraryDLSSG::GetDLSSGFrameTiming(T.DisplayedFPS, T.PresentedFrames);
        T.FrameGenerationActive =
            UStreamlineLibraryDLSSG::GetDLSSGMode() != EStreamlineDLSSGMode::Off && T.PresentedFrames > 1;
    }
    if (UStreamlineLibraryReflex::IsReflexSupported())
        T.LatencyMs = UStreamlineLibraryReflex::GetGameToRenderLatencyInMs();
#endif
    return T;
}
FString ReconstructionName(int32 Mode)
{
    const TCHAR *Names[] = {TEXT("Native / TSR"), TEXT("DLSS"), TEXT("DLAA"), TEXT("NVIDIA Image Scaling")};
    return Names[FMath::Clamp(Mode, 0, 3)];
}
FString QualityName(int32 Mode)
{
    const TCHAR *Names[] = {TEXT("Quality"), TEXT("Balanced"), TEXT("Performance"), TEXT("Ultra Performance")};
    return Names[FMath::Clamp(Mode, 0, 3)];
}
FString FrameModeName(int32 Mode)
{
    if (Mode > 0)
        return FString::Printf(TEXT("%dx"), Mode + 1);
#if SS_WITH_NVIDIA
    if (RendererReady() && UStreamlineLibraryDLSSG::IsDLSSGModeSupported(EStreamlineDLSSGMode::OnDynamic))
        return TEXT("Dynamic");
#endif
    return TEXT("Auto");
}
void CopyPreferences(const SS::Settings &F, SS::Settings &T)
{
    T.quality = F.quality;
    T.frameLimit = F.frameLimit;
    T.motionBlur = F.motionBlur;
    T.diagnosticsOverlay = F.diagnosticsOverlay;
    T.reconstruction = F.reconstruction;
    T.dlssQuality = F.dlssQuality;
    T.frameGeneration = F.frameGeneration;
    T.frameGenerationMode = F.frameGenerationMode;
    T.reflex = F.reflex;
    T.rayReconstruction = F.rayReconstruction;
    T.sharpening = F.sharpening;
    T.sharpness = F.sharpness;
    T.vibrance = F.vibrance;
    T.vibranceIntensity = F.vibranceIntensity;
    T.saturationBoost = F.saturationBoost;
    T.vsync = F.vsync;
}
} // namespace SSGraphics
