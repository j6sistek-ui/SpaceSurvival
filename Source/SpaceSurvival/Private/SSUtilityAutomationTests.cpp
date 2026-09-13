#include "Misc/AutomationTest.h"
#include "SSPhase1Data.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSUtilityDataAssetBridge, "SpaceSurvival.Content.UtilityDataAssetBridge",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSUtilityDataAssetBridge::RunTest(const FString &Parameters)
{
    // Actual reflected data assets and deterministic session only; no GameInstance Init or save APIs.
    auto *Saved = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!TestNotNull(TEXT("Persisted Phase 1 data asset resolves"), Saved))
        return false;
    TestTrue(TEXT("Persisted utility roster and values are valid"), Saved->HasValidUtilityTuning());
    auto *Data = NewObject<USSPhase1Data>();
    if (!TestNotNull(TEXT("Create transient reflected utility content"), Data))
        return false;
    SS::Session Session;
    if (!TestTrue(TEXT("Start isolated domain run"), Session.StartRun("utility-data-asset")))
        return false;
    Session.run.phase = SS::Phase::Station;
    Session.run.wave = Session.run.wavesCompleted = 5;
    Session.AwardCredits(1000);
    const auto Baseline = Session.Stats();
    auto Near = [](double A, double B) { return FMath::Abs(A - B) < 1.e-8; };
    TestTrue(TEXT("New asset preserves valid defaults"), Data->ApplyUtilityTuning(Session.tuning));
    TestEqual(TEXT("Default Vector price unchanged"), Session.UtilityPrice(SS::Utility::VectorThrusters), 150);
    TestEqual(TEXT("Default Cooling price unchanged"), Session.UtilityPrice(SS::Utility::OverdriveCooling), 150);
    Session.EquipUtility(SS::Utility::VectorThrusters);
    TestTrue(TEXT("Default Vector multipliers unchanged"),
             Near(Session.Stats().maneuver, Baseline.maneuver * 1.30) &&
                 Near(Session.Stats().response, Baseline.response * 1.12));
    Session.EquipUtility(SS::Utility::OverdriveCooling);
    TestTrue(TEXT("Default Cooling multipliers unchanged"),
             Near(Session.Stats().boostEfficiency, 1.35) && Near(Session.Stats().coolingEfficiency, 1.45));

    Data->Utilities[0].Price = 217;
    Data->Utilities[0].ManeuverMultiplier = 1.65;
    Data->Utilities[0].ResponseMultiplier = 1.28;
    Data->Utilities[1].Price = 193;
    Data->Utilities[1].BoostEfficiency = 1.70;
    Data->Utilities[1].CoolingEfficiency = 1.90;
    Data->Utilities.Swap(0, 1);
    TestTrue(TEXT("Custom asset maps through the same adapter used by GameMode"),
             Data->ApplyUtilityTuning(Session.tuning));
    TestEqual(TEXT("Custom Vector price reaches session despite row order"),
              Session.UtilityPrice(SS::Utility::VectorThrusters), 217);
    TestEqual(TEXT("Custom Cooling price reaches session"), Session.UtilityPrice(SS::Utility::OverdriveCooling), 193);
    TestTrue(TEXT("Custom paid replacement succeeds"), Session.PurchaseUtility(SS::Utility::VectorThrusters));
    TestEqual(TEXT("Custom price charged once"), Session.run.credits, 783);
    TestTrue(TEXT("Custom Vector effects reach actual session stats"),
             Near(Session.Stats().maneuver, Baseline.maneuver * 1.65) &&
                 Near(Session.Stats().response, Baseline.response * 1.28));
    TestFalse(TEXT("Fitted custom utility cannot charge twice"), Session.PurchaseUtility(SS::Utility::VectorThrusters));
    TestEqual(TEXT("Rejected purchase leaves balance"), Session.run.credits, 783);
    TestTrue(TEXT("Replace with custom Cooling"), Session.PurchaseUtility(SS::Utility::OverdriveCooling));
    TestEqual(TEXT("Cooling charges its own price"), Session.run.credits, 590);
    TestTrue(TEXT("Custom Cooling effects reach actual session stats"),
             Near(Session.Stats().boostEfficiency, 1.70) && Near(Session.Stats().coolingEfficiency, 1.90) &&
                 Near(Session.Stats().maneuver, Baseline.maneuver));
    TestTrue(TEXT("Free event fitting still ignores shop price"), Session.EquipUtility(SS::Utility::VectorThrusters));
    TestEqual(TEXT("Reward fitting does not spend credits"), Session.run.credits, 590);
    SS::Run Resumed;
    std::string Error;
    TestTrue(TEXT("Existing run codec still accepts utility identity"),
             SS::DecodeRun(SS::EncodeRun(Session.run), Resumed, Error));
    TestTrue(TEXT("Serialized utility ID remains Vector"), Resumed.utility == SS::Utility::VectorThrusters);

    Data->Utilities.Add(FSSUtilityDefinition());
    TestFalse(TEXT("Extra utility row is invalid"), Data->ApplyUtilityTuning(Session.tuning));
    TestEqual(TEXT("Wrong roster falls back to paid default"), Session.UtilityPrice(SS::Utility::VectorThrusters), 150);
    Data->Utilities.Empty();
    TestFalse(TEXT("Empty utility roster is invalid"), Data->ApplyUtilityTuning(Session.tuning));
    TestEqual(TEXT("Missing roster retains paid default"), Session.UtilityPrice(SS::Utility::OverdriveCooling), 150);
    for (ESSUtilityKind Kind : {ESSUtilityKind::VectorThrusters, static_cast<ESSUtilityKind>(99)})
    {
        Data->Utilities = {FSSUtilityDefinition(ESSUtilityKind::VectorThrusters), FSSUtilityDefinition(Kind)};
        Data->Utilities[0].Price = 1;
        TestFalse(TEXT("Duplicate or unknown identity cannot enter content"), Data->ApplyUtilityTuning(Session.tuning));
        TestEqual(TEXT("Roster fallback prevents discounted malformed offer"),
                  Session.UtilityPrice(SS::Utility::VectorThrusters), 150);
    }
    Data->Utilities = {FSSUtilityDefinition(ESSUtilityKind::VectorThrusters),
                       FSSUtilityDefinition(ESSUtilityKind::OverdriveCooling)};
    Data->Utilities[0].Price = 0;
    Data->Utilities[1].BoostEfficiency = std::numeric_limits<double>::quiet_NaN();
    TestFalse(TEXT("Zero price and nonfinite effect are invalid"), Data->HasValidUtilityTuning());
    TestFalse(TEXT("Malformed numeric rows report fallback"), Data->ApplyUtilityTuning(Session.tuning));
    TestEqual(TEXT("Malformed price never becomes a free purchase"), Session.UtilityPrice(SS::Utility::VectorThrusters),
              150);
    Session.EquipUtility(SS::Utility::OverdriveCooling);
    TestTrue(TEXT("Nonfinite effect restored to finite default"), Near(Session.Stats().boostEfficiency, 1.35));
    Data->Utilities[0].Price = 150;
    Data->Utilities[1].BoostEfficiency = 50.;
    Data->Utilities[1].CoolingEfficiency = 50.;
    TestFalse(TEXT("Out-of-range finite values report clamps"), Data->ApplyUtilityTuning(Session.tuning));
    TestTrue(TEXT("Runtime effect clamps stay finite and bounded"),
             Near(Session.Stats().boostEfficiency, 3.) && Near(Session.Stats().coolingEfficiency, 3.));
    return true;
}
#endif
