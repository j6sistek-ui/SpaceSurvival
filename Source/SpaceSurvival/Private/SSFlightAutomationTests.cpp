#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
/** Real pawn/component ticks, without the Director, user input, or disk-backed GameInstance Init. */
struct FSSFlightWorld
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    USSGameInstance *Instance = nullptr;
    ASSShip *Ship = nullptr;
    APlayerController *Controller = nullptr;

    bool Initialize(FAutomationTestBase &Test, SS::Weapon Weapon = SS::Weapon::RapidLaser)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated flight world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // Do not call Init or InitializeStandalone: both touch production account/settings.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Instance->Session.settings.cameraShake = false;
        Instance->Session.account.level = 2; // In-memory eligibility for the cannon fixture.
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        // A stock GameMode starts actors without spawning the game's hangar or save orchestration.
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!Test.TestTrue(TEXT("Install stock fixture GameMode"), World->SetGameMode(FURL())))
            return false;
        World->InitializeActorsForPlay(FURL());
        Controller = World->SpawnActor<APlayerController>();
        Ship = World->SpawnActor<ASSShip>(FVector(0, 0, 7000), FRotator::ZeroRotator);
        auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
        if (!Test.TestNotNull(TEXT("Spawn actual ship"), Ship) ||
            !Test.TestNotNull(TEXT("Spawn input-free controller"), Controller) ||
            !Test.TestNotNull(TEXT("Load flight tuning"), Content))
            return false;
        Ship->Tuning = DuplicateObject<USSPhase1Data>(Content, Ship);
        auto &Tuning = Instance->Session.tuning;
        // Match the production GameMode's content-to-domain setup, without running that GameMode.
        Tuning.baseHull = Content->BaseHull;
        Tuning.baseShield = Content->BaseShield;
        Tuning.baseSpeed = Content->CruiseSpeed;
        Tuning.baseManeuver = Content->LateralSpeed;
        Tuning.baseResponse = Content->Response;
        Tuning.baseAcceleration = Content->Acceleration;
        Tuning.baseWeaponDamage = Content->BaseWeaponDamage;
        if (!Test.TestTrue(TEXT("Start fresh in-memory flight"),
                           Instance->Session.StartRun("flight-adapter-fixture", SS::Ship::Starter, Weapon)))
            return false;
        World->AddController(Controller);
        Controller->Possess(Ship);
        Controller->SetActorTickEnabled(false);
        World->BeginPlay();
        Controller->SetActorTickEnabled(false);
        return Test.TestTrue(TEXT("Actual pawn BeginPlay initialized forward velocity"),
                             Ship->HasActorBegunPlay() && Ship->GetVelocity().X > 1000.f);
    }

    void Step(float DeltaSeconds = 1.f / 60.f)
    {
        // TickTaskManager deduplicates by engine frame counter; every synthetic frame is new.
        ++GFrameCounter;
        World->Tick(LEVELTICK_All, DeltaSeconds);
    }

    void Frames(int32 Count, float DeltaSeconds = 1.f / 60.f)
    {
        for (int32 Index = 0; Index < Count; ++Index)
            Step(DeltaSeconds);
    }

    ASSWorldBody *Target(FVector Offset)
    {
        auto *Body = World->SpawnActor<ASSWorldBody>(Ship->GetActorLocation() + Offset, FRotator::ZeroRotator);
        if (Body)
        {
            Body->Configure(ESSWorldKind::SmallAsteroid, 120.f, 0.f);
            Body->SetLinearVelocity(FVector::ZeroVector);
        }
        return Body;
    }

    int32 Projectiles() const
    {
        int32 Count = 0;
        for (TActorIterator<ASSProjectile> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed())
                ++Count;
        return Count;
    }

    ~FSSFlightWorld()
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

struct FSSFlightSample
{
    FVector Position;
    FVector Velocity;
    FRotator Rotation;
};

bool RecordFlight(FAutomationTestBase &Test, int32 Hertz, TArray<FSSFlightSample> &Samples)
{
    FSSFlightWorld Fixture;
    if (!Fixture.Initialize(Test))
        return false;
    const FVector Origin = Fixture.Ship->GetActorLocation();
    for (int32 Second = 0; Second < 4; ++Second)
    {
        if (Second == 0)
            Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f, false, false);
        else if (Second < 3)
            Fixture.Ship->SetFlightInput(FVector2D(.65, .3), FVector2D(.25, .2), 1.f, false, false);
        else
            Fixture.Ship->SetFlightInput(FVector2D(-.3, -.15), FVector2D(-.2, .1), -.5f, false, false);
        Fixture.Frames(Hertz, 1.f / Hertz);
        Samples.Add(
            {Fixture.Ship->GetActorLocation() - Origin, Fixture.Ship->GetVelocity(), Fixture.Ship->GetActorRotation()});
    }
    return true;
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFlightFrameRates, "SpaceSurvival.Flight.FrameRateTrajectories",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFlightFrameRates::RunTest(const FString &)
{
    TArray<FSSFlightSample> Reference;
    if (!RecordFlight(*this, 120, Reference))
        return false;
    TestTrue(TEXT("Throttle accelerates the real pawn above cruise"), Reference[0].Velocity.X > 2800.f);
    TestTrue(TEXT("Steer and strafe produce substantial lateral and vertical travel"),
             Reference[2].Position.Y > 1000.f && Reference[2].Position.Z > 500.f);
    TestTrue(TEXT("Opposite steering reverses the change of heading"),
             Reference[3].Rotation.Yaw < Reference[2].Rotation.Yaw &&
                 Reference[3].Rotation.Pitch < Reference[2].Rotation.Pitch);
    TestTrue(TEXT("Reduced throttle decreases actual velocity"),
             Reference[3].Velocity.Size() < Reference[2].Velocity.Size() - 300.f);
    for (int32 Hertz : {30, 60, 144})
    {
        TArray<FSSFlightSample> Samples;
        if (!RecordFlight(*this, Hertz, Samples))
            return false;
        for (int32 Index = 0; Index < Reference.Num(); ++Index)
        {
            const FString Label = FString::Printf(TEXT("%d Hz at %d seconds"), Hertz, Index + 1);
            const double PositionError = FVector::Distance(Samples[Index].Position, Reference[Index].Position);
            const double VelocityError = FVector::Distance(Samples[Index].Velocity, Reference[Index].Velocity);
            const FRotator RotationError = (Samples[Index].Rotation - Reference[Index].Rotation).GetNormalized();
            AddInfo(FString::Printf(TEXT("%s: position error %.3f cm; velocity error %.3f cm/s"), *Label, PositionError,
                                    VelocityError));
            // 25 cm is under one eighth of the collision diameter after roughly 100 metres of travel.
            TestTrue(Label + TEXT(" position agrees within 25 cm"), PositionError <= 25.f);
            TestTrue(Label + TEXT(" velocity agrees within 15 cm/s"), VelocityError <= 15.f);
            TestTrue(Label + TEXT(" heading agrees within 0.05 degrees"),
                     FMath::Abs(RotationError.Yaw) <= .05f && FMath::Abs(RotationError.Pitch) <= .05f);
        }
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFlightBoostBrake, "SpaceSurvival.Flight.BoostBrakeMovement",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFlightBoostBrake::RunTest(const FString &)
{
    FSSFlightWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto &Run = Fixture.Instance->Session.run;
    const double Cruise = Fixture.Ship->GetVelocity().Size();
    const FVector Origin = Fixture.Ship->GetActorLocation();
    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, true, false);
    Fixture.Frames(60);
    const double BoostSpeed = Fixture.Ship->GetVelocity().Size();
    const double DrainedBoost = Run.boost;
    TestTrue(TEXT("Held boost drains resource while increasing actual speed"),
             Run.boosting && DrainedBoost < 90.0 && BoostSpeed > Cruise * 1.4);
    TestTrue(TEXT("Boost produces more distance than neutral cruise over the same second"),
             Fixture.Ship->GetActorLocation().X - Origin.X > Cruise * 1.2);
    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
    Fixture.Frames(60);
    TestTrue(TEXT("Release recharges boost while the pawn returns toward cruise"),
             !Run.boosting && Run.boost > DrainedBoost && Fixture.Ship->GetVelocity().Size() < BoostSpeed * .8);

    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, -1.f, false, true);
    const double Minimum = Fixture.Ship->Tuning->MinimumSpeed;
    double LowestForwardSpeed = Fixture.Ship->GetVelocity().X;
    for (int32 Index = 0; Index < 150; ++Index)
    {
        Fixture.Step();
        LowestForwardSpeed = FMath::Min(LowestForwardSpeed, Fixture.Ship->GetVelocity().X);
    }
    TestTrue(TEXT("Held brake builds heat and physically slows to the nonzero minimum"),
             Run.braking && Run.brakeHeat > 60.0 && Fixture.Ship->GetVelocity().X <= Minimum + 5.f);
    for (int32 Index = 0; Index < 120 && !Run.brakeOverheated; ++Index)
    {
        Fixture.Step();
        LowestForwardSpeed = FMath::Min(LowestForwardSpeed, Fixture.Ship->GetVelocity().X);
    }
    TestTrue(TEXT("Braking never stops or reverses forward travel"), LowestForwardSpeed >= Minimum - .5f);
    TestTrue(TEXT("Continued braking overheats and releases the brake"), Run.brakeOverheated && !Run.braking);
    Fixture.Frames(30);
    TestTrue(TEXT("Overheat physically restores speed despite the held brake"),
             !Run.braking && Fixture.Ship->GetVelocity().X > Minimum * 1.25);
    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, -1.f, false, false);
    Fixture.Frames(240);
    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, -1.f, false, true);
    Fixture.Step();
    TestTrue(TEXT("Cooling permits braking again"), !Run.brakeOverheated && Run.braking);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFlightDodgeCollision, "SpaceSurvival.Flight.DirectionalDodgeCollision",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFlightDodgeCollision::RunTest(const FString &)
{
    const FVector2D Steering[] = {FVector2D::ZeroVector, FVector2D(0, -1), FVector2D(-1, 0)};
    const FVector2D Strafe[] = {FVector2D(0, 1), FVector2D::ZeroVector, FVector2D(1, 1)};
    const FVector Expected[] = {FVector::UpVector, -FVector::UpVector, FVector(0, 1, 1).GetSafeNormal()};
    for (int32 Index = 0; Index < 3; ++Index)
    {
        FSSFlightWorld Fixture;
        if (!Fixture.Initialize(*this))
            return false;
        Fixture.Ship->SetFlightInput(Steering[Index], Strafe[Index], 0.f, false, false);
        const FVector Before = Fixture.Ship->GetVelocity();
        Fixture.Ship->RequestDodge();
        const FVector Impulse = Fixture.Ship->GetVelocity() - Before;
        TestTrue(FString::Printf(TEXT("Dodge case %d uses the requested lateral/vertical direction"), Index),
                 FVector::DotProduct(Impulse.GetSafeNormal(), Expected[Index]) > .999 && Impulse.Size() > 2000.f &&
                     FMath::Abs(Impulse.X) < .01f);
        const FVector After = Fixture.Ship->GetVelocity();
        Fixture.Ship->RequestDodge();
        TestTrue(TEXT("Immediate repeated dodge cannot stack another impulse"),
                 Fixture.Ship->GetVelocity().Equals(After, .01f));
    }

    FSSFlightWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto *Wall = Fixture.World->SpawnActor<AActor>();
    if (!TestNotNull(TEXT("Create transient collision fixture"), Wall))
        return false;
    auto *Box = NewObject<UBoxComponent>(Wall);
    Wall->SetRootComponent(Box);
    Wall->AddInstanceComponent(Box);
    Box->SetBoxExtent(FVector(10000, 10, 10000));
    Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Box->SetCollisionObjectType(ECC_WorldStatic);
    Box->SetCollisionResponseToAllChannels(ECR_Block);
    Box->RegisterComponent();
    Wall->SetActorLocation(Fixture.Ship->GetActorLocation() + FVector(0, 200, 0));
    const double ShieldBefore = Fixture.Instance->Session.run.shield;
    Fixture.Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D(1, 0), 0.f, false, false);
    Fixture.Ship->RequestDodge();
    Fixture.Frames(6);
    TestTrue(TEXT("Dodge is swept against a blocking wall rather than tunnelling through it"),
             Fixture.Ship->GetActorLocation().Y > 50.f && Fixture.Ship->GetActorLocation().Y <= 86.f);
    TestTrue(TEXT("The physical impact still damages shield during dodge cooldown"),
             Fixture.Instance->Session.run.dodgeCooldown > 0.0 &&
                 Fixture.Instance->Session.run.shield < ShieldBefore - 1.0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFlightManualWeapons, "SpaceSurvival.Flight.ManualWeaponImpacts",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFlightManualWeapons::RunTest(const FString &)
{
    for (SS::Weapon Weapon : {SS::Weapon::RapidLaser, SS::Weapon::HeavyCannon})
    {
        FSSFlightWorld Fixture;
        if (!Fixture.Initialize(*this, Weapon))
            return false;
        // Three 10-damage laser hits or one cannon round defeat the default 24-health target.
        // Deliberately nondefault damage also verifies Fire consumes the session's weapon stat.
        Fixture.Instance->Session.tuning.baseWeaponDamage = 10;
        Fixture.Ship->Camera->SetRelativeRotation(FRotator::ZeroRotator);
        auto *Target = Fixture.Target(FVector(5000, 0, 0));
        auto *Miss = Fixture.Target(FVector(5000, 1200, 0));
        if (!TestNotNull(TEXT("Spawn on-axis weapon target"), Target) ||
            !TestNotNull(TEXT("Spawn off-axis control target"), Miss))
            return false;
        Fixture.Frames(30);
        TestEqual(TEXT("Flight ticks alone do not fire a weapon"), Fixture.Projectiles(), 0);
        TestFalse(TEXT("Target survives without manual Fire"), Target->IsActorBeingDestroyed());
        Fixture.Ship->Fire();
        TestEqual(TEXT("Manual Fire spawns one projectile or laser tracer"), Fixture.Projectiles(), 1);
        Fixture.Ship->Fire();
        TestEqual(TEXT("Weapon cooldown rejects a second same-frame trigger"), Fixture.Projectiles(), 1);
        TestFalse(TEXT("First laser hit is nonfatal; cannon has not reached its target yet"),
                  Target->IsActorBeingDestroyed());
        if (Weapon == SS::Weapon::RapidLaser)
        {
            Fixture.Frames(15);
            TestFalse(TEXT("Laser tracer does not apply a second damage hit"), Target->IsActorBeingDestroyed());
            Fixture.Ship->Fire();
            TestFalse(TEXT("Two tuned laser hits leave the target alive"), Target->IsActorBeingDestroyed());
            Fixture.Frames(15);
            Fixture.Ship->Fire();
            TestTrue(TEXT("Third manual laser hitscan defeats the on-axis target"), Target->IsActorBeingDestroyed());
        }
        else
        {
            Fixture.Frames(24);
            TestTrue(TEXT("Cannon projectile sweep defeats the target after travel"), Target->IsActorBeingDestroyed());
            TestEqual(TEXT("Cannon projectile is consumed by impact"), Fixture.Projectiles(), 0);
        }
        TestFalse(TEXT("Off-axis control target survives the shot"), Miss->IsActorBeingDestroyed());
        TestEqual(TEXT("Player weapon does not damage its source pawn"), Fixture.Instance->Session.run.shield,
                  Fixture.Instance->Session.Stats().maxShield);
    }
    return true;
}
#endif
