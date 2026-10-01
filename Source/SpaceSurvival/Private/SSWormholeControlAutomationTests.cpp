#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSSpaceScenery.h"
#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/WorldSettings.h"
#include "Physics/Experimental/PhysScene_Chaos.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSWormholeControlWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSShip *Ship = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        UWorld::InitializationValues Values;
        Values.ShouldSimulatePhysics(true)
            .CreatePhysicsScene(true)
            .AllowAudioPlayback(false)
            .RequiresHitProxies(false)
            .CreateNavigation(false)
            .CreateAISystem(false);
        World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
        if (!Test.TestNotNull(TEXT("Create isolated transit physics world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0.;
        Instance->Session.settings.cameraShake = false;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->bGlobalGravitySet = true;
        World->GetWorldSettings()->GlobalGravityZ = 0.f;
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!Test.TestTrue(TEXT("Install stock mode without gameplay progression"), World->SetGameMode(FURL())))
            return false;
        auto *Content = NewObject<USSPhase1Data>(Instance);
        auto &Session = Instance->Session;
        Session.tuning.baseSpeed = Content->FlightCruiseSpeed();
        Session.tuning.baseManeuver = Content->LateralSpeed;
        Session.tuning.baseResponse = Content->Response;
        Session.tuning.baseAcceleration = Content->FlightAcceleration();
        if (!Test.TestTrue(TEXT("Start only an in-memory transit run"), Session.StartRun("wormhole-controls")))
            return false;
        World->InitializeActorsForPlay(FURL());
        World->SetBegunPlay(true);
        if (World->GetPhysicsScene())
            World->GetPhysicsScene()->OnWorldBeginPlay();
        const FTransform Transform(FRotator::ZeroRotator, FVector(0, 0, 7000));
        Ship = World->SpawnActorDeferred<ASSShip>(ASSShip::StaticClass(), Transform);
        if (!Test.TestNotNull(TEXT("Spawn actual flight pawn"), Ship))
            return false;
        Ship->Tuning = Content;
        Ship->FinishSpawning(Transform);
        return Test.TestTrue(TEXT("Flight pawn began play with ordinary movement"),
                             Ship->HasActorBegunPlay() && Ship->GetVelocity().Size() > 1000.f);
    }
    void Step(float Dt)
    {
        ++GFrameCounter;
        World->Tick(LEVELTICK_All, Dt);
    }
    void EnterPhase()
    {
        Instance->Session.run.wave = 5;
        Instance->Session.run.phase = SS::Phase::Wormhole;
    }
    ~FSSWormholeControlWorld()
    {
        if (World)
        {
            World->EndPlay(EEndPlayReason::Quit);
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
            GWorld = PreviousWorld;
        }
        if (Instance)
            Instance->RemoveFromRoot();
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWormholeControl, "SpaceSurvival.Flight.WormholeTransitControl",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWormholeControl::RunTest(const FString &)
{
    for (const float Dt : {1.f / 30.f, 1.f / 120.f})
    {
        FSSWormholeControlWorld F;
        if (!F.Initialize(*this))
            return false;
        auto &Session = F.Instance->Session;
        const FVector Forward = FRotator(10, 35, 0).Vector();
        TestEqual(TEXT("The selected physics hull really uses its simulating body"),
                  F.Ship->Collision->IsSimulatingPhysics(),
                  ASSShip::SelectedHullIdentity() == ESSHullIdentity::StellarPhoenix);
        const FRotator NormalView = F.Ship->CameraBoom->GetRelativeRotation();
        F.Ship->SetFreeLookInput(FVector2D(1, 1));
        for (int32 Frame = 0; Frame < 5; ++Frame)
            F.Step(Dt);
        TestFalse(TEXT("Ordinary flight cannot accidentally enter transit"),
                  F.Ship->BeginWormholeTransit(Forward, 4.f));
        F.EnterPhase();
        TestFalse(TEXT("An invalid transit duration cannot capture controls"),
                  F.Ship->BeginWormholeTransit(Forward, 0.f));
        TestFalse(TEXT("A zero direction cannot capture controls"),
                  F.Ship->BeginWormholeTransit(FVector::ZeroVector, 4.f));
        const float EntrySpeed = float(F.Ship->GetVelocity().Size());
        const FVector Start = F.Ship->GetActorLocation();
        if (!TestTrue(TEXT("Wormhole takes flight control"), F.Ship->BeginWormholeTransit(Forward, 4.f)))
            return false;
        TestTrue(TEXT("Entering transit recentres an existing free look"),
                 F.Ship->CameraBoom->GetRelativeRotation().Equals(NormalView, .1f));
        TestFalse(TEXT("Repeated entry cannot overwrite the saved ordinary speed"),
                  F.Ship->BeginWormholeTransit(Forward, 40.f));
        if (F.Ship->Collision->IsSimulatingPhysics())
            TestTrue(TEXT("Transit changes the actual solver velocity immediately"),
                     FVector::DotProduct(F.Ship->Collision->GetPhysicsLinearVelocity(), Forward) > 22000.f);
        const double BoostBefore = Session.run.boost;
        float MaximumAcross = 0.f, MaximumAngle = 0.f, MinimumSpeed = MAX_flt;
        for (int32 Frame = 0; Frame < FMath::RoundToInt(3.f / Dt); ++Frame)
        {
            // All derailment inputs stay held, including repeated dodge. Observe actual motion rather
            // than private flags: reduced stick authority must remain bounded over the whole passage.
            F.Ship->SetFlightInput(FVector2D(1, 1), FVector2D(1, 1), 0.f, true, true, 1.f, true);
            F.Ship->SetFreeLookInput(FVector2D(1, 1));
            F.Ship->RequestDodge(1.f);
            F.Step(Dt);
            MaximumAcross = FMath::Max(
                MaximumAcross, float(FVector::VectorPlaneProject(F.Ship->GetActorLocation() - Start, Forward).Size()));
            MaximumAngle = FMath::Max(MaximumAngle,
                                      float(FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(
                                          FVector::DotProduct(F.Ship->GetActorForwardVector(), Forward), -1., 1.)))));
            MinimumSpeed = FMath::Min(MinimumSpeed, float(FVector::DotProduct(F.Ship->GetVelocity(), Forward)));
        }
        TestTrue(TEXT("Transit travels rapidly despite held brake and zero throttle"),
                 FVector::DotProduct(F.Ship->GetActorLocation() - Start, Forward) > 65000.f && MinimumSpeed > 22000.f);
        TestTrue(TEXT("Steering and wobble stay inside a small lateral envelope"),
                 MaximumAcross > 10.f && MaximumAcross < 550.f);
        TestTrue(TEXT("Held steering and roll cannot turn the ship out of the passage"), MaximumAngle < 5.f);
        TestTrue(TEXT("Held free look cannot turn the view out of the passage"),
                 F.Ship->CameraBoom->GetRelativeRotation().Equals(NormalView, .1f));
        TestEqual(TEXT("Suppressed dodge does not consume its cooldown"), Session.run.dodgeCooldown, 0.);
        TestTrue(TEXT("Transit does not spend boost or heat the brake"),
                 Session.run.boost >= BoostBefore && Session.run.brakeHeat == 0. && !Session.run.boosting &&
                     !Session.run.braking);
        const double Health = Session.run.hull + Session.run.shield;
        F.Ship->ReceiveDamage(10.f);
        TestTrue(TEXT("Transit does not grant blanket damage immunity"),
                 Session.run.hull + Session.run.shield < Health);

        F.Ship->EndWormholeTransit();
        TestFalse(TEXT("Explicit exit restores ordinary control"), F.Ship->IsInWormholeTransit());
        TestTrue(TEXT("Exit restores an ordinary speed instead of leaving warp momentum"),
                 FMath::IsNearlyEqual(float(F.Ship->GetVelocity().Size()),
                                      FMath::Min(EntrySpeed, float(Session.Stats().speed)), 1.f));
        F.Ship->EndWormholeTransit();
        const FVector ExitForward = F.Ship->GetActorForwardVector();
        for (int32 Frame = 0; Frame < FMath::RoundToInt(.75f / Dt); ++Frame)
        {
            F.Ship->SetFlightInput(FVector2D(1, 0), FVector2D::ZeroVector, 1.f, false, false);
            F.Step(Dt);
        }
        TestTrue(TEXT("Normal steering authority returns after exit"),
                 FVector::DotProduct(F.Ship->GetActorForwardVector(), ExitForward) <
                     FMath::Cos(FMath::DegreesToRadians(8.f)));
        const double SpeedBeforeBrake = F.Ship->GetVelocity().Size();
        for (int32 Frame = 0; Frame < FMath::RoundToInt(.5f / Dt); ++Frame)
        {
            F.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, true);
            F.Step(Dt);
        }
        TestTrue(TEXT("Normal braking returns after exit"), F.Ship->GetVelocity().Size() < SpeedBeforeBrake * .6);
        F.Ship->RequestDodge(1.f);
        TestTrue(TEXT("Normal dodge returns after exit"), Session.run.dodgeCooldown > 0.);

        TestTrue(TEXT("Reentry after exit is supported"), F.Ship->BeginWormholeTransit(Forward, Dt * 2.f));
        F.Step(Dt);
        F.Step(Dt);
        F.Step(Dt);
        TestFalse(TEXT("Duration guards against a missing passage End callback"), F.Ship->IsInWormholeTransit());
        TestTrue(TEXT("Prepare phase-change cleanup"), F.Ship->BeginWormholeTransit(Forward, 4.f));
        Session.run.phase = SS::Phase::Station;
        F.Step(Dt);
        TestFalse(TEXT("Station phase cannot retain restricted flight controls"), F.Ship->IsInWormholeTransit());
        TestTrue(TEXT("Station phase discards warp velocity on the live body"),
                 F.Ship->GetVelocity().IsNearlyZero(1.f));

        F.EnterPhase();
        TestTrue(TEXT("Prepare restart cleanup"), F.Ship->BeginWormholeTransit(Forward, 4.f));
        Session.EndRun();
        TestTrue(TEXT("Start the replacement in-memory run"), Session.StartRun("after-transit"));
        F.Step(Dt);
        TestFalse(TEXT("A restarted run cannot inherit transit control"), F.Ship->IsInWormholeTransit());
        TestTrue(TEXT("A restarted run cannot inherit warp speed"),
                 F.Ship->GetVelocity().Size() <= Session.Stats().speed + 1.);
        F.EnterPhase();
        TestTrue(TEXT("Prepare explicit hold cleanup"), F.Ship->BeginWormholeTransit(Forward, 4.f));
        TestTrue(TEXT("Mooring can still take ownership of the ship"), F.Ship->BeginMooring());
        TestFalse(TEXT("Mooring ends transit before holding the body"), F.Ship->IsInWormholeTransit());
        TestFalse(TEXT("A held ship cannot reenter transit"), F.Ship->BeginWormholeTransit(Forward, 4.f));
        F.Ship->EndMooring();
        F.EnterPhase();
        TestTrue(TEXT("Prepare death cleanup"), F.Ship->BeginWormholeTransit(Forward, 4.f));
        F.Ship->ReceiveDamage(100000.f);
        TestFalse(TEXT("Lethal damage ends transit immediately"), F.Ship->IsInWormholeTransit());
        TestTrue(TEXT("Death stops warp momentum in the real body"), F.Ship->GetVelocity().IsNearlyZero(1.f));
        AddInfo(
            FString::Printf(TEXT("Transit %.0f Hz: max lateral %.1f cm, max angle %.2f deg, minimum forward %.1f cm/s"),
                            1.f / Dt, MaximumAcross, MaximumAngle, MinimumSpeed));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWormholePassageCleanup, "SpaceSurvival.Flight.WormholePassageCleanup",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWormholePassageCleanup::RunTest(const FString &)
{
    FSSWormholeControlWorld F;
    if (!F.Initialize(*this))
        return false;
    F.EnterPhase();
    auto *SolidScenery = F.World->SpawnActor<ASSSpaceScenery>(F.Ship->GetActorLocation(), FRotator::ZeroRotator);
    auto *DisabledScenery = F.World->SpawnActor<ASSSpaceScenery>();
    if (!TestNotNull(TEXT("Create collision-enabled scenery owner"), SolidScenery) ||
        !TestNotNull(TEXT("Create intentionally disabled scenery owner"), DisabledScenery))
        return false;
    // Keep this test about ownership and exit clearance, without populating a streamed licensed field.
    SolidScenery->ConfigureLook(nullptr);
    DisabledScenery->ConfigureLook(nullptr);
    SolidScenery->SetActorTickEnabled(false);
    DisabledScenery->SetActorTickEnabled(false);
    SolidScenery->SetActorEnableCollision(true);
    DisabledScenery->SetActorEnableCollision(false);
    const FVector Forward = F.Ship->GetActorForwardVector();
    const FVector OriginalExit = F.Ship->GetActorLocation();
    auto *Rock = NewObject<USphereComponent>(SolidScenery, TEXT("ExitObstruction"));
    Rock->InitSphereRadius(60000.f);
    Rock->SetupAttachment(SolidScenery->GetRootComponent());
    Rock->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Rock->SetCollisionObjectType(ECC_WorldStatic);
    Rock->SetCollisionResponseToAllChannels(ECR_Block);
    SolidScenery->AddInstanceComponent(Rock);
    Rock->RegisterComponent();
    // Scenery BeginPlay can move its root to the world-region origin. Place the obstruction in
    // world space after registration so the fixture truly encloses this ship's exit at Z=7000.
    Rock->SetWorldLocation(OriginalExit + Forward * 5000.f);
    FHitResult BeforeHit;
    FCollisionQueryParams BeforeQuery(SCENE_QUERY_STAT(WormholeBlockedExitTest), false, F.Ship);
    if (!TestTrue(TEXT("A giant restored landmark really blocks the original hull and exit lead"),
                  F.Ship->SweepFlightHull(BeforeHit, OriginalExit, OriginalExit + Forward * 12000.f,
                                          F.Ship->GetActorQuat(), BeforeQuery)))
        return false;
    const ECollisionEnabled::Type HullCollision = F.Ship->Collision->GetCollisionEnabled();
    auto *Passage = F.World->SpawnActor<ASSWormholePassage>();
    if (!TestNotNull(TEXT("Create the actual passage actor"), Passage))
        return false;
    Passage->BeginPassage(F.Ship, 8.f);
    TestTrue(TEXT("The actual passage engages ship transit"), F.Ship->IsInWormholeTransit());
    TestFalse(TEXT("Normal-space scenery is suspended while enclosed"), SolidScenery->GetActorEnableCollision());
    TestFalse(TEXT("Previously disabled scenery stays disabled"), DisabledScenery->GetActorEnableCollision());
    TestEqual(TEXT("Passage does not disable the ship collision body"), F.Ship->Collision->GetCollisionEnabled(),
              HullCollision);
    Passage->Destroy();
    TestFalse(TEXT("Destroying a passage early releases its ship immediately"), F.Ship->IsInWormholeTransit());
    TestTrue(TEXT("Early exit restores previously enabled scenery"), SolidScenery->GetActorEnableCollision());
    TestFalse(TEXT("Early exit preserves previously disabled scenery"), DisabledScenery->GetActorEnableCollision());
    TestTrue(TEXT("The obstructed exit relocates before returning control"),
             FVector::DistSquared(F.Ship->GetActorLocation(), OriginalExit) > FMath::Square(1000.f));
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(WormholeCleanupTest), false, F.Ship);
    TestFalse(TEXT("The restored hull has a clear forward reaction lead"),
              F.Ship->SweepFlightHull(Hit, F.Ship->GetActorLocation(), F.Ship->GetActorLocation() + Forward * 12000.f,
                                      F.Ship->GetActorQuat(), Query));
    return true;
}
#endif
