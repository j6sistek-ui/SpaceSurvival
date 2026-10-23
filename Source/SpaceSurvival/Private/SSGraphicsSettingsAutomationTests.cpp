#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGraphicsSettings.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/ScopeExit.h"
#include "Scalability.h"
#include "Misc/App.h"
#include "RHI.h"
#if SS_WITH_NVIDIA
#include "DLSSLibrary.h"
#include "StreamlineLibraryDLSSG.h"
#include "StreamlineLibraryReflex.h"
#endif

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSNvidiaLiveSettingsTest, "SpaceSurvival.Settings.NvidiaLiveModes",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSNvidiaLiveSettingsTest::RunTest(const FString &)
{
    if (!FApp::CanEverRender() || GUsingNullRHI)
    {
        AddInfo(TEXT("Renderer checks require a separate real-RHI run; this NullRHI run is not graphics evidence."));
        return true;
    }
    const auto C = SSGraphics::Query();
    AddInfo(FString::Printf(TEXT("Capabilities DLSS=%d DLAA=%d FG=%d Reflex=%d RR=%d NIS=%d Vibrance=%d"), C.DLSS,
                            C.DLAA, C.FrameGeneration, C.Reflex, C.RayReconstruction, C.NIS, C.Vibrance));
    auto *Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    ON_SCOPE_EXIT
    {
        Instance->Session.settings = SS::Settings{};
        Instance->ApplySettings();
    };
    auto *Screen = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
    TestNotNull(TEXT("Renderer screen scale"), Screen);
    for (int32 Method : {0, 1, 2, 3})
    {
        if ((Method == 1 && !C.DLSS) || (Method == 2 && !C.DLAA) || (Method == 3 && !C.NIS))
            continue;
        Instance->Session.settings.reconstruction = Method;
        Instance->ApplySettings();
        const float Scale = Screen->GetFloat();
        AddInfo(FString::Printf(TEXT("%s screen percentage %.2f"), *SSGraphics::ReconstructionName(Method), Scale));
        TestTrue(TEXT("Native and DLAA use native resolution; upscalers reduce rendering resolution"),
                 Method == 0 || Method == 2 ? FMath::IsNearlyEqual(Scale, 100.f) : Scale > 0 && Scale < 100);
#if SS_WITH_NVIDIA
        if (C.DLSS)
            TestEqual(TEXT("DLSS enable state follows selected method"), UDLSSLibrary::IsDLSSEnabled(),
                      Method == 1 || Method == 2);
#endif
    }
#if SS_WITH_NVIDIA
    if (C.FrameGeneration)
    {
        Instance->Session.settings.reconstruction = 1;
        Instance->Session.settings.frameGeneration = true;
        Instance->Session.settings.reflex = 0;
        Instance->ApplySettings();
        TestTrue(TEXT("Frame generation mode enabled"),
                 UStreamlineLibraryDLSSG::GetDLSSGMode() != EStreamlineDLSSGMode::Off);
        TestTrue(TEXT("Frame generation requires Reflex"),
                 UStreamlineLibraryReflex::GetReflexMode() != EStreamlineReflexMode::Off);
        Instance->Session.settings.frameGeneration = false;
        Instance->ApplySettings();
        TestTrue(TEXT("Preferred Reflex Off restored"),
                 UStreamlineLibraryReflex::GetReflexMode() == EStreamlineReflexMode::Off);
        AddInfo(TEXT("Mode state is not proof of generated frames presenting on a physical display."));
    }
#endif
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSNvidiaFallbackTest, "SpaceSurvival.Settings.NvidiaFallbackAndDependencies",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSNvidiaFallbackTest::RunTest(const FString &)
{
    SS::Settings Wanted;
    Wanted.reconstruction = 2;
    Wanted.frameGeneration = true;
    Wanted.frameGenerationMode = 5;
    Wanted.reflex = 0;
    Wanted.rayReconstruction = true;
    Wanted.sharpening = true;
    Wanted.vibrance = true;
    Wanted.vsync = true;
    const auto Before = SS::EncodeSettings(Wanted);
    SSGraphics::FCapabilities C;
    auto Actual = SSGraphics::Resolve(Wanted, C);
    TestEqual(TEXT("Unsupported GPU falls back to native"), Actual.reconstruction, 0);
    TestFalse(TEXT("Unsupported FG stays off"), Actual.frameGeneration);
    TestFalse(TEXT("Unsupported RR stays off"), Actual.rayReconstruction);
    TestFalse(TEXT("Unsupported vibrance stays off"), Actual.vibrance);
    C.DLSS = C.DLAA = C.FrameGeneration = C.Reflex = C.RayReconstruction = C.NIS = C.Vibrance = true;
    C.QualityModes = {0, 1, 2};
    C.FrameModes = {0, 1, 2};
    Actual = SSGraphics::Resolve(Wanted, C);
    TestEqual(TEXT("DLAA retained when supported"), Actual.reconstruction, 2);
    TestEqual(TEXT("Unsupported 6x resolves to a queried mode"), Actual.frameGenerationMode, 0);
    TestEqual(TEXT("FG requires Reflex"), Actual.reflex, 1);
    TestFalse(TEXT("Incompatible FG VSync disabled"), Actual.vsync);
    TestTrue(TEXT("Compatible RR retained"), Actual.rayReconstruction);
    TestTrue(TEXT("Capability resolution preserves requested preferences"), Before == SS::EncodeSettings(Wanted));
    Wanted.frameGeneration = false;
    Wanted.reconstruction = 0;
    Actual = SSGraphics::Resolve(Wanted, C);
    TestEqual(TEXT("Disabling FG restores preferred Reflex Off"), Actual.reflex, 0);
    TestFalse(TEXT("Native mode disables RR"), Actual.rayReconstruction);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSNativeResolutionQualityTest,
                                 "SpaceSurvival.Settings.NativeResolutionAcrossQualityTiers",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSNativeResolutionQualityTest::RunTest(const FString &Parameters)
{
    UGameUserSettings *Settings = UGameUserSettings::GetGameUserSettings();
    IConsoleVariable *Screen = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
    IConsoleVariable *Blur = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MotionBlurQuality"));
    if (!TestNotNull(TEXT("Native user settings available"), Settings) ||
        !TestNotNull(TEXT("Native screen percentage available"), Screen) ||
        !TestNotNull(TEXT("Motion blur setting available"), Blur))
        return false;
    // A console-forced 100 would mask the production regression. Do not replace it.
    if (!TestTrue(TEXT("Resolution regression has no higher-priority console override"),
                  (Screen->GetFlags() & ECVF_SetByMask) <= ECVF_SetByScalability))
        return false;
    const auto PreviousSettings = Settings->ScalabilityQuality;
    const auto PreviousRuntime = Scalability::GetQualityLevels();
    const FIntPoint Resolution = Settings->GetScreenResolution();
    const EWindowMode::Type WindowMode = Settings->GetFullscreenMode();
    const float FrameLimit = Settings->GetFrameRateLimit();
    const int32 PreviousBlur = Blur->GetInt();
    const auto BlurPriority = EConsoleVariableFlags(Blur->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        // Production ApplySettings owns this level; release it before restoring prior scalability.
        Blur->Unset(ECVF_SetByGameSetting);
        Settings->ScalabilityQuality = PreviousSettings;
        Settings->SetFrameRateLimit(FrameLimit);
        Settings->ApplyNonResolutionSettings();
        Scalability::SetQualityLevels(PreviousRuntime);
        Blur->Set(PreviousBlur, BlurPriority);
    };
    // No Init/OnStart: do not load an owner account or invoke any save operation.
    USSGameInstance *Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    if (!TestNotNull(TEXT("Isolated settings instance"), Instance))
        return false;
    for (int32 Quality = 0; Quality <= 3; ++Quality)
    {
        Instance->Session.settings.quality = Quality;
        Instance->Session.settings.frameLimit = 144;
        Instance->Session.settings.motionBlur = Quality % 2 != 0;
        Instance->ApplySettings();
        float Normalized = 0, Scale = 0, Minimum = 0, Maximum = 0;
        Settings->GetResolutionScaleInformationEx(Normalized, Scale, Minimum, Maximum);
        const FString Prefix = FString::Printf(TEXT("Quality tier %d: "), Quality);
        TestEqual(Prefix + TEXT("native render scale"), Scale, 100.f);
        TestEqual(Prefix + TEXT("effective runtime screen percentage"), Screen->GetFloat(), 100.f);
        TestEqual(Prefix + TEXT("requested quality tier is retained"), Settings->GetTextureQuality(), Quality);
        TestTrue(Prefix + TEXT("viewport resolution is retained"), Settings->GetScreenResolution() == Resolution);
        TestEqual(Prefix + TEXT("window mode is retained"), int32(Settings->GetFullscreenMode()), int32(WindowMode));
        TestEqual(Prefix + TEXT("requested frame limit is retained"), Settings->GetFrameRateLimit(), 144.f);
        TestEqual(Prefix + TEXT("motion blur preference is retained"), Blur->GetInt(), Quality % 2 != 0 ? 3 : 0);
    }
    return !HasAnyErrors();
}
#endif
