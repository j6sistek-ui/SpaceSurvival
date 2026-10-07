#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/ScopeExit.h"
#include "Scalability.h"

#if WITH_DEV_AUTOMATION_TESTS
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
