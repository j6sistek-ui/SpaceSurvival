#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Materials/MaterialInstanceDynamic.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
/** Actual hazard/damage/material ticks; no disk-backed run or advancing Director. */
struct FSSHazardWorld
{
    UWorld *World = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    APlayerController *Controller = nullptr;
    ASSShip *Ship = nullptr;
    ASSWorldBody *Storm = nullptr;
    UMaterialInstanceDynamic *Material = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create transient hazard world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No Init, BeginPlay, settings initialization, save API or production slot access.
        Instance->AccountStorageBlocked = true;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install actual content lookup GameMode"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve hazard GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        Controller = World->SpawnActor<APlayerController>();
        Ship = World->SpawnActor<ASSShip>();
        if (!Test.TestNotNull(TEXT("Create isolated ship"), Ship) ||
            !Test.TestNotNull(TEXT("Create isolated controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->Possess(Ship);
        return true;
    }

    bool Reset(FAutomationTestBase &Test, float Interval, float Telegraph = 3.5f, float ReactionOverride = 0.f)
    {
        if (Storm)
            Storm->Destroy();
        Instance->Session = SS::Session{};
        Instance->Session.tuning.baseHull = Instance->Session.tuning.baseShield = 50000.0;
        Instance->Session.settings.masterVolume = 0.0;
        Instance->Session.account.tutorialFlags = 255;
        if (!Test.TestTrue(TEXT("Create only an in-memory damage fixture"),
                           Instance->Session.StartRun("electrical-clock")))
            return false;
        Ship->SetActorLocation(FVector::ZeroVector);
        if (Controller->GetPawn() != Ship)
            Controller->Possess(Ship);
        for (auto &Hazard : Mode->Tuning->Hazards)
            if (Hazard.Kind == ESSWorldKind::ElectricalStorm)
            {
                Hazard.PulseInterval = Interval;
                Hazard.TelegraphSeconds = Telegraph;
            }
        Storm = World->SpawnActor<ASSWorldBody>(FVector(100, 0, 0), FRotator::ZeroRotator);
        if (!Test.TestNotNull(TEXT("Spawn actual storm actor"), Storm))
            return false;
        Storm->Configure(ESSWorldKind::ElectricalStorm, 3400.f, 7.f, 4);
        // Match the Director's actual post-Configure minimum-reaction override.
        if (ReactionOverride > 0.f)
            Storm->TelegraphSeconds = FMath::Max(Storm->TelegraphSeconds, ReactionOverride);
        // Long cadence sampling must not expire the isolated actor.
        Storm->LifetimeSeconds = 0.f;
        Material = Cast<UMaterialInstanceDynamic>(Storm->Visual->GetMaterial(0));
        return Test.TestNotNull(TEXT("Resolve the actual storm warning material"), Material);
    }

    double Step(float Seconds)
    {
        const double Before = Instance->Session.run.shield;
        Storm->Tick(Seconds);
        return Before - Instance->Session.run.shield;
    }
    float Emission() const
    {
        return Material->K2_GetScalarParameterValue(TEXT("Emission"));
    }
    ~FSSHazardWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
        if (Instance)
            Instance->RemoveFromRoot();
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSElectricalCadence, "SpaceSurvival.Integration.ElectricalPulseCadence",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSElectricalCadence::RunTest(const FString &Parameters)
{
    FSSHazardWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    for (int32 FramesPerSecond : {30, 60, 144})
        for (float Interval : {.2f, .73f, 1.8f, 2.6f})
        {
            if (!Fixture.Reset(*this, Interval))
                return false;
            constexpr int32 ExpectedPulses = 40;
            constexpr double InitialDelay = 3.5;
            const float Step = 1.f / FramesPerSecond;
            const double End = InitialDelay + (ExpectedPulses - 1) * double(Interval) + double(Step) * .5;
            const double InitialShield = Fixture.Instance->Session.run.shield;
            const double InitialHull = Fixture.Instance->Session.run.hull;
            double Elapsed = 0.0, LastHit = -100.0;
            int32 Hits = 0, ChargingSamples = 0;
            float PreviousEmission = Fixture.Emission();
            while (Elapsed < End)
            {
                const double Damage = Fixture.Step(Step);
                Elapsed += double(Step);
                const float Emission = Fixture.Emission();
                if (!TestTrue(TEXT("Visible storm emission remains finite"), FMath::IsFinite(Emission)))
                    return false;
                if (Damage > 0.0)
                {
                    const double Scheduled = InitialDelay + Hits * double(Interval);
                    if (!TestTrue(TEXT("Actual damage follows authored absolute timing without cumulative drift"),
                                  Elapsed >= Scheduled - 1.e-6 && Elapsed <= Scheduled + double(Step) + 1.e-6) ||
                        !TestTrue(TEXT("A pulse applies exactly one configured electrical hit"),
                                  FMath::IsNearlyEqual(Damage, 7.0)) ||
                        !TestTrue(TEXT("Actual damage and actual material discharge flash share the same frame"),
                                  FMath::IsNearlyEqual(Emission, 2.8f, .001f)))
                        return false;
                    LastHit = Elapsed;
                    ++Hits;
                }
                else if (Hits == 0 || Elapsed - LastHit > .12 + double(Step) * 2.0)
                {
                    if (!TestTrue(TEXT("Visible charge rises toward the next actual discharge"),
                                  Emission + .001f >= PreviousEmission))
                        return false;
                    ++ChargingSamples;
                }
                PreviousEmission = Emission;
            }
            TestEqual(TEXT("All sampled pulse intervals have the expected pulse count"), Hits, ExpectedPulses);
            TestTrue(TEXT("Charge was checked across multiple pre-discharge frames"), ChargingSamples > 20);
            TestTrue(TEXT("Only electrical pulses changed shield; hull remains intact"),
                     FMath::IsNearlyEqual(Fixture.Instance->Session.run.shield, InitialShield - 7.0 * ExpectedPulses) &&
                         FMath::IsNearlyEqual(Fixture.Instance->Session.run.hull, InitialHull));
            TestTrue(TEXT("Real damage path retains electrical interference"),
                     FMath::IsNearlyEqual(Fixture.Instance->Session.run.interferenceSeconds, 2.5));
            AddInfo(FString::Printf(TEXT("ELECTRICAL_CADENCE fps=%d interval=%.9g pulses=%d sampledSeconds=%.9f"),
                                    FramesPerSecond, Interval, Hits, Elapsed));
        }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSElectricalBoundaries, "SpaceSurvival.Integration.ElectricalPulseBoundaries",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSElectricalBoundaries::RunTest(const FString &Parameters)
{
    FSSHazardWorld Fixture;
    if (!Fixture.Initialize(*this) || !Fixture.Reset(*this, .8f, 1.f, 2.3f))
        return false;
    TestEqual(TEXT("Director reaction override delays first discharge"), Fixture.Step(2.29f), 0.0);
    TestEqual(TEXT("First discharge follows overridden delay"), Fixture.Step(.02f), 7.0);
    Fixture.Storm->Configure(ESSWorldKind::ElectricalStorm, 3400.f, 7.f, 4);
    TestEqual(TEXT("Reconfiguration restores full initial warning"), Fixture.Step(.99f), 0.0);
    TestEqual(TEXT("Reconfigured field waits for its new initial warning"), Fixture.Step(.02f), 7.0);

    if (!Fixture.Reset(*this, .8f, 1.f))
        return false;
    Fixture.Ship->SetActorLocation(FVector(10000, 0, 0));
    TestEqual(TEXT("Out-of-range initial discharge cannot damage the ship"), Fixture.Step(1.f), 0.0);
    TestTrue(TEXT("Out-of-range discharge remains visible"), FMath::IsNearlyEqual(Fixture.Emission(), 2.8f, .001f));
    Fixture.Ship->SetActorLocation(FVector::ZeroVector);
    TestEqual(TEXT("Entering during charge causes no unscheduled damage"), Fixture.Step(.4f), 0.0);
    TestEqual(TEXT("Entering permits next scheduled discharge"), Fixture.Step(.4f), 7.0);
    Fixture.Ship->SetActorLocation(FVector(10000, 0, 0));
    TestEqual(TEXT("Leaving the volume prevents next hit"), Fixture.Step(.8f), 0.0);
    Fixture.Controller->UnPossess();
    TestEqual(TEXT("Unpossessed interval never damages an absent ship"), Fixture.Step(.8f), 0.0);
    Fixture.Controller->Possess(Fixture.Ship);
    Fixture.Ship->SetActorLocation(FVector::ZeroVector);
    TestEqual(TEXT("Clock advanced while no flight pawn existed"), Fixture.Step(.4f), 0.0);
    TestEqual(TEXT("Repossessed ship meets following scheduled pulse"), Fixture.Step(.4f), 7.0);

    if (!Fixture.Reset(*this, 1.8f))
        return false;
    TestEqual(TEXT("Full initial warning is damage-free"), Fixture.Step(3.49f), 0.0);
    TestEqual(TEXT("A long frame never applies a catch-up damage burst"), Fixture.Step(10.f), 7.0);
    TestTrue(TEXT("Long-frame damage has matching flash"), FMath::IsNearlyEqual(Fixture.Emission(), 2.8f, .001f));
    TestEqual(TEXT("Hitch overshoot cannot cause an immediate repeat"), Fixture.Step(.02f), 0.0);

    for (float Invalid : {std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity(), -1.f, 0.f})
    {
        if (!Fixture.Reset(*this, Invalid))
            return false;
        TestEqual(TEXT("Malformed interval preserves initial warning"), Fixture.Step(3.49f), 0.0);
        TestEqual(TEXT("Malformed interval has a finite first discharge"), Fixture.Step(.02f), 7.0);
        TestEqual(TEXT("Malformed interval cannot create per-frame damage"), Fixture.Step(.05f), 0.0);
        TestTrue(TEXT("Malformed interval cannot create nonfinite warning"), FMath::IsFinite(Fixture.Emission()));
        const float ExpectedInterval = FMath::IsFinite(Invalid) ? .2f : 1.8f;
        TestEqual(TEXT("Malformed value retains the bounded/default recurring delay"),
                  Fixture.Step(ExpectedInterval - .08f), 0.0);
        TestEqual(TEXT("Bounded/default recurring interval still discharges"), Fixture.Step(.04f), 7.0);
    }
    if (!Fixture.Reset(*this, 1.8f, std::numeric_limits<float>::quiet_NaN()))
        return false;
    TestEqual(TEXT("Nonfinite initial delay uses authored default"), Fixture.Step(3.49f), 0.0);
    TestEqual(TEXT("Finite fallback warning leads to discharge"), Fixture.Step(.02f), 7.0);
    return true;
}
#endif
