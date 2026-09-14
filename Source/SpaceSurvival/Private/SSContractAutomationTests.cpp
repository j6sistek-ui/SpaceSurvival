#include "Misc/AutomationTest.h"
#include "SSPhase1Data.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSContractDataAssetBridge, "SpaceSurvival.Content.ContractDataAssetBridge",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSContractDataAssetBridge::RunTest(const FString &Parameters)
{
    auto *Saved = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!TestNotNull(TEXT("Persisted Phase 1 data resolves"), Saved))
        return false;
    TestTrue(TEXT("Persisted contract magnitudes are valid"), Saved->HasValidContractTuning());
    auto *Data = NewObject<USSPhase1Data>();
    SS::Session S;
    TestTrue(TEXT("Default contract bridge valid"), Data->ApplyContractTuning(S.tuning));
    TestEqual(TEXT("Default Hunter target unchanged"), S.tuning.objectiveTarget, 6);
    TestEqual(TEXT("Default rewards unchanged"), S.tuning.objectiveContractReward, 150);
    TestEqual(TEXT("Default Pressure reward unchanged"), S.tuning.pressureContractReward, 150);
    Data->Contracts.ShieldMultiplier = 0.4;
    Data->Contracts.PressureAddition = 0.32;
    Data->Contracts.PressureReward = 241;
    Data->Contracts.ObjectiveTarget = 4;
    Data->Contracts.ObjectiveReward = 197;
    TestTrue(TEXT("Custom content maps through actual GameMode adapter"), Data->ApplyContractTuning(S.tuning));
    TestTrue(TEXT("Start in-memory session, no disk access"), S.StartRun("contract-asset"));
    S.run.wave = S.run.wavesCompleted = 5;
    S.run.phase = SS::Phase::Station;
    const double OriginalPressure = S.PressureMultiplier();
    TestTrue(TEXT("Accept existing Pressure identity"), S.AcceptContract(SS::Contract::Pressure));
    TestTrue(TEXT("Custom shield handicap reaches effective stats"), FMath::IsNearlyEqual(S.Stats().maxShield, 24.));
    TestTrue(TEXT("Custom pressure reaches Director domain input"),
             FMath::IsNearlyEqual(S.PressureMultiplier() - OriginalPressure, .32));
    S.run.wave = S.run.wavesCompleted = 10;
    S.run.phase = SS::Phase::Docking;
    S.run.contractProgress = 5;
    TestTrue(TEXT("Resolve custom reward at next station"), S.CompleteDocking());
    TestEqual(TEXT("Actual paid Pressure reward"), S.run.credits, 241);
    TestTrue(TEXT("Shield handicap removed on resolution"), FMath::IsNearlyEqual(S.Stats().maxShield, 60.));
    TestEqual(TEXT("Hunter target also mapped"), S.tuning.objectiveTarget, 4);
    TestEqual(TEXT("Independent Hunter reward mapped"), S.tuning.objectiveContractReward, 197);
    Data->Contracts.ShieldMultiplier = std::numeric_limits<double>::quiet_NaN();
    Data->Contracts.ObjectiveReward = -1;
    Data->Contracts.ObjectiveTarget = 10000;
    TestFalse(TEXT("Malformed reflected contract values reported"), Data->HasValidContractTuning());
    TestFalse(TEXT("Malformed content corrected before runtime use"), Data->ApplyContractTuning(S.tuning));
    TestTrue(TEXT("Nonfinite handicap recovers default"), FMath::IsNearlyEqual(S.tuning.pressureShieldMultiplier, .65));
    TestEqual(TEXT("Reward bounded positive"), S.tuning.objectiveContractReward, 1);
    TestEqual(TEXT("Objective bounded to codec-compatible target"), S.tuning.objectiveTarget, 1000);
    return true;
}
#endif
