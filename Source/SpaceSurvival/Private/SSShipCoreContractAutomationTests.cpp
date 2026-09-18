#include "Misc/AutomationTest.h"

#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "GyroManagerComp.h"
#include "PhysicsEngine/BodyInstance.h"
#include "ThrusterManagerComp.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
/** The flight model is moving to the ShipCore plugin, which is force-based on a simulating rigid body.
 *  Nothing in this project has ever used rigid-body physics: a grep for SetSimulatePhysics, AddImpulse and
 *  OnComponentHit across Source/SpaceSurvival returns nothing, and ASSShip integrates its own velocity by
 *  hand against a QueryOnly sphere. So before any of that is torn out, this proves the plugin can drive a
 *  body AT ALL inside this project, on this engine, in an automation world.
 *
 *  It deliberately uses a BARE AActor rather than ASSShip. The point is to test the plugin's contract, not
 *  the game's ship, and to be able to say - if this fails - that the failure is the plugin or the physics
 *  setup rather than anything the game does.
 *
 *  What makes this worth a test rather than a one-off experiment: the plugin FAILS SILENTLY-ISH when its
 *  contract is unmet. UThrusterManagerComp::BeginPlay casts the owner's root to UPrimitiveComponent and
 *  requires IsSimulatingPhysics(); if that is false it nulls its pointer, deactivates itself, disables its
 *  own tick and never checks again. The ship would simply not move, and the only clue would be one
 *  LogTemp Error and a red on-screen banner. Asserting the component is still active after BeginPlay is
 *  what turns that into a test failure instead of a mystery. */
struct FSSShipCoreRig
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    AActor *Body = nullptr;
    USphereComponent *Hull = nullptr;
    UThrusterManagerComp *Thrusters = nullptr;
    UGyroManagerComp *Gyros = nullptr;
    UGameInstance *Instance = nullptr;
    /** Whether the hull reported simulating at the moment the plugin's components were attached, and again
     *  once play had begun. The plugin checks exactly once, in BeginPlay, so these two answers being
     *  different is the whole difference between a ship that flies and one that silently does not. */
    bool SimulatingBeforeComponents = false;
    bool SimulatingAfterBeginPlay = false;

    /** Mass is not arbitrary. ShipCore turns thrust into acceleration by dividing by the body's mass, and
     *  the plugin's default forward thrust is 15,000,000. The game's own base acceleration is 3200 cm/s^2
     *  (SurvivalCore.h). 15,000,000 / 3200 = 4687.5 kg, so this mass makes the plugin's stock numbers
     *  reproduce today's acceleration exactly instead of needing the whole force set re-derived. */
    static constexpr float MassKg = 4687.5f;
    static constexpr float ExpectedAcceleration = 3200.f;

    bool Initialize(FAutomationTestBase &Test)
    {
        // Every existing fixture in this project calls CreateWorld with no InitializationValues, which is
        // why none of them has a physics scene and why none could have caught this. Ask for one explicitly.
        UWorld::InitializationValues Values;
        Values.ShouldSimulatePhysics(true)
            .CreatePhysicsScene(true)
            .AllowAudioPlayback(false)
            .RequiresHitProxies(false)
            .CreateNavigation(false)
            .CreateAISystem(false);
        World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None, nullptr, true, ERHIFeatureLevel::Num, &Values);
        if (!Test.TestNotNull(TEXT("Create isolated physics world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        // UWorld::SetGameMode resolves the mode through the world's GameInstance, so a world without one
        // does not fail politely - it dereferences null and takes the whole editor process down, which is
        // an automation crash rather than a test failure. A stock UGameInstance is enough here; this rig
        // deliberately avoids USSGameInstance because it touches production account and settings storage.
        Instance = NewObject<UGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        if (!Test.TestNotNull(TEXT("World has a physics scene"), World->GetPhysicsScene()))
            return false;
        // A space game with a rigid body needs this to be zero in three independent places: the project
        // config, the component's own custom gravity, and here. Two of them silently not applying is the
        // failure that would read as "the new flight model feels heavy".
        World->GetWorldSettings()->bGlobalGravitySet = true;
        World->GetWorldSettings()->GlobalGravityZ = 0.f;
        // A GameMode is not optional scenery here. UWorld::BeginPlay dispatches through the authority
        // GameMode's StartPlay, so with no GameMode installed BeginPlay reaches no actor and no component.
        // The plugin assigns its ShipMesh pointer in BeginPlay and its TickComponent returns immediately
        // while that pointer is null - so the symptom is a ship that is active, ticking, correctly
        // configured, and completely motionless.
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!Test.TestTrue(TEXT("Install stock fixture GameMode"), World->SetGameMode(FURL())))
            return false;
        World->InitializeActorsForPlay(FURL());

        Body = World->SpawnActor<AActor>(FVector::ZeroVector, FRotator::ZeroRotator);
        if (!Test.TestNotNull(TEXT("Spawn bare physics body"), Body))
            return false;
        Hull = NewObject<USphereComponent>(Body, TEXT("Hull"));
        // 105 cm matches ASSShip's real collision radius, so anything measured here transfers.
        Hull->InitSphereRadius(105.f);
        Hull->SetMobility(EComponentMobility::Movable);
        Hull->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Hull->SetCollisionProfileName(TEXT("PhysicsActor"));
        // Root FIRST, then register. Registering a component while the actor still has no root leaves it
        // parented to nothing, and its physics body is created in that state - which is how the first run
        // of this test ended up with a hull that reported simulating later but was not simulating yet when
        // the thruster's BeginPlay asked. The plugin only asks once.
        Body->SetRootComponent(Hull);
        Hull->RegisterComponent();
        Hull->SetSimulatePhysics(true);
        Hull->SetEnableGravity(false);
        Hull->SetMassOverrideInKg(NAME_None, MassKg, true);
        Hull->SetLinearDamping(0.f);
        Hull->SetAngularDamping(0.f);
        SimulatingBeforeComponents = Hull->IsSimulatingPhysics();

        // bAutoActivate BEFORE registering, on both. The plugin's constructors set bCanEverTick and a
        // TG_PostPhysics tick group but never set bAutoActivate, and neither TickComponent checks
        // IsActive() - so a component added from C++ sits there inactive while still looking correctly
        // configured. This is the difference between a ship that flies and one that just sits, and it is
        // invisible in the Blueprint workflow the plugin was built for, where the editor activates
        // components for you.
        Thrusters = NewObject<UThrusterManagerComp>(Body, TEXT("Thrusters"));
        Thrusters->bCustomGravity = true;
        Thrusters->CustomGravity = FVector::ZeroVector;
        Thrusters->bAutoActivate = true;
        Thrusters->RegisterComponent();
        Gyros = NewObject<UGyroManagerComp>(Body, TEXT("Gyros"));
        Gyros->bAutoActivate = true;
        Gyros->RegisterComponent();

        World->BeginPlay();
        SimulatingAfterBeginPlay = Hull->IsSimulatingPhysics();
        if (!Test.TestTrue(TEXT("Thruster component reached BeginPlay"), Thrusters->HasBegunPlay()))
            return false;
        return true;
    }

    void Step(float DeltaSeconds = 1.f / 120.f)
    {
        ++GFrameCounter;
        World->Tick(LEVELTICK_All, DeltaSeconds);
    }

    void Frames(int32 Count, float DeltaSeconds = 1.f / 120.f)
    {
        for (int32 Index = 0; Index < Count; ++Index)
            Step(DeltaSeconds);
    }

    FVector Velocity() const
    {
        return Hull->GetPhysicsLinearVelocity();
    }

    ~FSSShipCoreRig()
    {
        // Order matters, and it matters more here than in the other fixtures because this is the only
        // world in the project with a physics scene. EndPlay first, then destroy the world, then drop its
        // context: skipping EndPlay leaves the Chaos solver attached to a world that is being torn down,
        // and the process survives long enough to crash inside an unrelated test eighteen tests later,
        // which is a miserable thing to debug. This mirrors FSSFlightWorld's teardown exactly.
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSShipCoreBodyContractTest, "SpaceSurvival.Flight.ShipCoreBodyContract",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSShipCoreBodyContractTest::RunTest(const FString &)
{
    FSSShipCoreRig Rig;
    if (!Rig.Initialize(*this))
        return false;

    // 1. The plugin accepted the body. If the root had not been simulating, BeginPlay would have
    //    deactivated the component and disabled its tick, and nothing below would move.
    AddInfo(FString::Printf(TEXT("Hull simulating: %s when components attached, %s after BeginPlay"),
                            Rig.SimulatingBeforeComponents ? TEXT("yes") : TEXT("NO"),
                            Rig.SimulatingAfterBeginPlay ? TEXT("yes") : TEXT("NO")));
    AddInfo(FString::Printf(TEXT("Thruster: begunPlay=%s active=%s ticking=%s | Gyro: active=%s ticking=%s"),
                            Rig.Thrusters->HasBegunPlay() ? TEXT("yes") : TEXT("NO"),
                            Rig.Thrusters->IsActive() ? TEXT("yes") : TEXT("NO"),
                            Rig.Thrusters->IsComponentTickEnabled() ? TEXT("yes") : TEXT("NO"),
                            Rig.Gyros->IsActive() ? TEXT("yes") : TEXT("NO"),
                            Rig.Gyros->IsComponentTickEnabled() ? TEXT("yes") : TEXT("NO")));
    TestTrue(TEXT("Hull was already simulating when the plugin's components were attached"),
             Rig.SimulatingBeforeComponents);
    TestTrue(TEXT("Thruster component still active after BeginPlay"), Rig.Thrusters->IsActive());
    TestTrue(TEXT("Thruster component still ticking after BeginPlay"), Rig.Thrusters->IsComponentTickEnabled());
    TestTrue(TEXT("Body is simulating physics"), Rig.Hull->IsSimulatingPhysics());
    TestTrue(TEXT("Mass override took"), FMath::IsNearlyEqual(Rig.Hull->GetMass(), FSSShipCoreRig::MassKg, 1.f));

    // 2. Nothing falls. A space game whose ship sinks is the most likely quiet failure here, because the
    //    plugin re-applies world gravity by hand as a force after disabling it on the body.
    Rig.Frames(120);
    const FVector Drift = Rig.Body->GetActorLocation();
    AddInfo(FString::Printf(TEXT("Idle drift after 1 s: %s"), *Drift.ToCompactString()));
    TestTrue(TEXT("No gravity drift over one idle second"), FMath::Abs(Drift.Z) < 5.f);

    // 3. Forward thrust accelerates, and roughly by the amount the mass was chosen to produce. The band is
    //    deliberately wide: the inertial dampener is on by default and this is a feasibility gate, not a
    //    tuning gate. What would fail it is zero, backwards, or an order of magnitude out.
    const FVector Before = Rig.Velocity();
    Rig.Thrusters->SetThrustersInput(FVector(1, 0, 0));
    Rig.Frames(120);
    const FVector After = Rig.Velocity();
    const float Gained = (After - Before).X;
    AddInfo(FString::Printf(TEXT("Forward acceleration measured: %.1f cm/s^2 (expected near %.0f)"), Gained,
                            FSSShipCoreRig::ExpectedAcceleration));
    TestTrue(TEXT("Forward thrust accelerates forward"), Gained > 100.f);
    TestTrue(TEXT("Forward acceleration is the right order of magnitude"),
             Gained > FSSShipCoreRig::ExpectedAcceleration * .25f &&
                 Gained < FSSShipCoreRig::ExpectedAcceleration * 4.f);

    // 4. The gyro turns the body. Same standard: this proves the torque path works, not that it feels right.
    Rig.Thrusters->SetThrustersInput(FVector::ZeroVector);
    const float YawBefore = Rig.Body->GetActorRotation().Yaw;
    Rig.Gyros->SetGyrosInput(FVector(0, 1, 0));
    Rig.Frames(120);
    const float YawGained = FMath::Abs(FRotator::NormalizeAxis(Rig.Body->GetActorRotation().Yaw - YawBefore));
    AddInfo(FString::Printf(TEXT("Yaw change over 1 s of full input: %.2f degrees"), YawGained));
    TestTrue(TEXT("Gyro input rotates the body"), YawGained > 1.f);

    return true;
}
#endif
