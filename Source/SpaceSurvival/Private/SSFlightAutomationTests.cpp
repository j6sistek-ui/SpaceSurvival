#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Components/SphereComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
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

    bool Initialize(FAutomationTestBase &Test, SS::Weapon Weapon = SS::Weapon::RapidLaser,
                    SS::Ship ShipKind = SS::Ship::Starter)
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
        Instance->Session.account.level = 3; // In-memory eligibility for both weapons and ships.
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
                           Instance->Session.StartRun("flight-adapter-fixture", ShipKind, Weapon)))
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSShipPresentationSelection, "SpaceSurvival.Integration.ShipPresentationSelection",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSShipPresentationSelection::RunTest(const FString &)
{
    // Independent expected assets: do not obtain these values from the production selection helper.
    const TCHAR *ExpectedHullPaths[] = {TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShipGripFit.SM_AcornShipGripFit"),
                                        TEXT("/Game/SpaceSurvival/Meshes/SM_SwiftCandidateV1.SM_SwiftCandidateV1")};
    const SS::Ship Kinds[] = {SS::Ship::Starter, SS::Ship::Agile};
    for (int32 Index = 0; Index < 2; ++Index)
    {
        FSSFlightWorld Fixture;
        if (!Fixture.Initialize(*this, SS::Weapon::RapidLaser, Kinds[Index]))
            return false;
        const FString Label = Index == 0 ? TEXT("Starter") : TEXT("Swift");
        TestTrue(Label + TEXT(" fixture uses its actual in-memory run selection"),
                 Fixture.Instance->Session.run.ship == Kinds[Index]);
        auto *Hull = Fixture.Ship->HullMesh.Get();
        auto *Pilot = Fixture.Ship->Pilot.Get();
        if (!TestNotNull(Label + TEXT(" has a real hull component"), Hull) ||
            !TestNotNull(Label + TEXT(" has a real pilot component"), Pilot) ||
            !TestNotNull(Label + TEXT(" BeginPlay loaded its authored hull"), Hull->GetStaticMesh().Get()))
            return false;
        TestEqual(Label + TEXT(" BeginPlay selects the exact candidate hull"), Hull->GetStaticMesh()->GetPathName(),
                  FString(ExpectedHullPaths[Index]));
        TestTrue(Label + TEXT(" display hull and pilot cannot add blocking collision"),
                 Hull->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                     Pilot->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        TestTrue(Label + TEXT(" retains the authored pilot mount and constant scale"),
                 Pilot->GetAttachParent() == Hull && Pilot->GetRelativeLocation().Equals(FVector(-15, 0, 72), .001) &&
                     Pilot->GetRelativeRotation().Equals(FRotator(0, -90, 0), .001) &&
                     Pilot->GetRelativeScale3D().Equals(FVector(1.5), .001));

        auto *Station = Fixture.World->SpawnActor<ASSStation>();
        if (!TestNotNull(Label + TEXT(" creates an actual station actor"), Station))
            return false;
        // Exercise the home hangar and station construction paths once each.
        Station->BuildHub(Index == 0);
        TArray<UStaticMeshComponent *> Components;
        Station->GetComponents<UStaticMeshComponent>(Components);
        UStaticMeshComponent *Bay = nullptr;
        int32 BayCount = 0;
        for (auto *Component : Components)
        {
            if (Component->GetRelativeLocation().Equals(FVector(850, 0, 220), .001))
            {
                Bay = Component;
                ++BayCount;
            }
        }
        TestEqual(Label + TEXT(" construction creates exactly one ship at the authored bay mount"), BayCount, 1);
        if (!TestNotNull(Label + TEXT(" exposes the real bay display component"), Bay) ||
            !TestNotNull(Label + TEXT(" bay loads its initial hull"), Bay->GetStaticMesh().Get()))
            return false;
        TestEqual(Label + TEXT(" BuildHub starts with the fitted starter display"), Bay->GetStaticMesh()->GetPathName(),
                  FString(ExpectedHullPaths[0]));
        for (int32 BayKind : {1, 0})
        {
            Station->SetBayShip(BayKind);
            if (!TestNotNull(Label + TEXT(" bay switch keeps a loaded hull"), Bay->GetStaticMesh().Get()))
                return false;
            TestEqual(FString::Printf(TEXT("%s bay selection %d uses the exact candidate"), *Label, BayKind),
                      Bay->GetStaticMesh()->GetPathName(), FString(ExpectedHullPaths[BayKind]));
            TestTrue(Label + TEXT(" bay switching preserves display collision and transform"),
                     Bay->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                         Bay->GetRelativeLocation().Equals(FVector(850, 0, 220), .001) &&
                         Bay->GetRelativeScale3D().Equals(FVector(1), .001));
        }
    }
    return true;
}

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSImpactFrameRates, "SpaceSurvival.Flight.ContactImpactResponse",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSImpactFrameRates::RunTest(const FString &)
{
    FVector ReferenceVelocity = FVector::ZeroVector;
    FVector ReferenceTravel = FVector::ZeroVector;
    for (int32 Hertz : {120, 30, 60, 144})
    {
        FSSFlightWorld Fixture;
        if (!Fixture.Initialize(*this))
            return false;
        auto *Body = Fixture.Target(FVector(0, 180, 0));
        if (!TestNotNull(TEXT("Create a real grazing asteroid contact"), Body))
            return false;
        Body->Configure(ESSWorldKind::SmallAsteroid, 120.f, 30.f);
        Body->SetLinearVelocity(Fixture.Ship->GetVelocity());
        const double Shield = Fixture.Instance->Session.run.shield;
        const FVector Before = Fixture.Ship->GetVelocity();
        Fixture.Step(1.f / Hertz);
        const FString Label = FString::Printf(TEXT("%d Hz contact"), Hertz);
        TestEqual(Label + TEXT(" routes a single 30-point impact through shield"), Fixture.Instance->Session.run.shield,
                  Shield - 30.0);
        const FVector Impulse = Fixture.Ship->GetVelocity() - Before;
        TestTrue(Label + TEXT(" causes an immediate bounded outward deflection"),
                 Impulse.Y < -450.f && Impulse.Size() <= 601.f && FMath::Abs(Impulse.X) < 1.f);
        const FVector Origin = Fixture.Ship->GetActorLocation();
        Fixture.Frames(Hertz / 4, 1.f / Hertz);
        const float Remainder = .25f - float(Hertz / 4) / Hertz;
        if (Remainder > .00001f)
            Fixture.Step(Remainder);
        const FVector Travel = Fixture.Ship->GetActorLocation() - Origin;
        TestEqual(Label + TEXT(" contact cooldown prevents repeat damage during recovery"),
                  Fixture.Instance->Session.run.shield, Shield - 30.0);
        TestTrue(Label + TEXT(" preserves forward flight while controls recover"),
                 Fixture.Ship->GetVelocity().X > 2000.f && Fixture.Ship->GetVelocity().Y > Impulse.Y &&
                     Travel.Y < -40.f && Travel.Y > -150.f);
        if (Hertz == 120)
        {
            ReferenceVelocity = Fixture.Ship->GetVelocity();
            ReferenceTravel = Travel;
        }
        else
        {
            TestTrue(Label + TEXT(" recovery velocity agrees with 120 Hz within 25 cm/s"),
                     Fixture.Ship->GetVelocity().Equals(ReferenceVelocity, 25.f));
            TestTrue(Label + TEXT(" quarter-second recovery travel agrees within 12 cm"),
                     Travel.Equals(ReferenceTravel, 12.f));
        }
        AddInfo(FString::Printf(TEXT("%s: impulse %.3f cm/s, lateral travel %.3f cm, residual %.3f cm/s"), *Label,
                                Impulse.Size(), Travel.Y, Fixture.Ship->GetVelocity().Y));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSImpactCrossing, "SpaceSurvival.Flight.SweptImpactDirection",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSImpactCrossing::RunTest(const FString &)
{
    FSSFlightWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto *Body = Fixture.Target(FVector(400, 0, 0));
    if (!TestNotNull(TEXT("Create a real asteroid across the high-speed path"), Body))
        return false;
    Body->Configure(ESSWorldKind::SmallAsteroid, 120.f, 30.f);
    Body->Tick(0.f);
    const FVector Before = Fixture.Ship->GetVelocity();
    const double Shield = Fixture.Instance->Session.run.shield;
    // A 100 ms crossing at 8000 cm/s ends beyond the obstacle, outside its radius.
    Fixture.Ship->AddActorWorldOffset(FVector(800, 0, 0));
    Body->Tick(.1f);
    const FVector Deflection = Fixture.Ship->GetVelocity() - Before;
    TestEqual(TEXT("Continuous crossing still applies exactly one kinetic hit"), Fixture.Instance->Session.run.shield,
              Shield - 30.0);
    TestTrue(TEXT("Center crossing deflects against entry rather than accelerating out the far side"),
             Deflection.X < -599.f && FMath::Abs(Deflection.Y) < .01f && FMath::Abs(Deflection.Z) < .01f);
    TestTrue(TEXT("Impact preserves forward momentum"), Fixture.Ship->GetVelocity().X > 1000.f);
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
        Fixture.Ship->Tuning->SoftAimDegrees = 0.f;
        // Settle the actual default chase view; do not flatten its pitch or use the aiming helper.
        Fixture.Frames(30);
        const FVector CameraRay = Fixture.Ship->Camera->GetForwardVector();
        const FVector TargetPosition = Fixture.Ship->Camera->GetComponentLocation() + CameraRay * 5000.f;
        auto *Target = Fixture.Target(TargetPosition - Fixture.Ship->GetActorLocation());
        auto *Miss = Fixture.Target(TargetPosition - Fixture.Ship->GetActorLocation() +
                                    Fixture.Ship->Camera->GetRightVector() * 1200.f);
        if (!TestNotNull(TEXT("Spawn target on the actual default camera ray"), Target) ||
            !TestNotNull(TEXT("Spawn off-axis control target"), Miss))
            return false;
        TestNull(TEXT("Manual camera-ray case has no soft-assist target"), Fixture.Ship->SoftTarget);
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
            TestTrue(TEXT("Third manual laser hitscan defeats the camera-ray target"), Target->IsActorBeingDestroyed());
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWeaponRange, "SpaceSurvival.Flight.CannonRangeAndHitch",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWeaponRange::RunTest(const FString &)
{
    for (float Step : {1.f / 30.f, 1.f / 144.f, .35f})
        for (bool BeyondRange : {false, true})
        {
            FSSFlightWorld Fixture;
            if (!Fixture.Initialize(*this, SS::Weapon::HeavyCannon))
                return false;
            Fixture.Ship->Tuning->SoftAimDegrees = 0.f;
            Fixture.Ship->Tuning->WeaponRange = 4000.f;
            Fixture.Frames(30);
            const FVector Muzzle = Fixture.Ship->GetActorLocation() + Fixture.Ship->GetActorForwardVector() * 240.f;
            const FVector AimPoint =
                Fixture.Ship->Camera->GetComponentLocation() + Fixture.Ship->Camera->GetForwardVector() * 4000.f;
            const FVector Direction = (AimPoint - Muzzle).GetSafeNormal();
            auto *Target =
                Fixture.Target(Muzzle + Direction * (BeyondRange ? 4500.f : 3500.f) - Fixture.Ship->GetActorLocation());
            if (!TestNotNull(TEXT("Create isolated range target"), Target))
                return false;
            Fixture.Ship->Fire();
            ASSProjectile *Round = nullptr;
            for (TActorIterator<ASSProjectile> It(Fixture.World); It; ++It)
                Round = *It;
            if (!TestNotNull(TEXT("Actual Heavy Cannon creates a round"), Round))
                return false;
            for (int32 Frame = 0; Frame < 150 && !Round->IsActorBeingDestroyed(); ++Frame)
                Fixture.Step(Step);
            const FString Label = FString::Printf(TEXT("Cannon dt=%.6f target=%s"), Step,
                                                  BeyondRange ? TEXT("beyond range") : TEXT("inside range"));
            TestTrue(Label + TEXT(" consumes or expires the round"), Round->IsActorBeingDestroyed());
            TestEqual(Label + TEXT(" damages only an in-range target"), Target->IsActorBeingDestroyed(), !BeyondRange);
            if (BeyondRange)
                TestTrue(Label + TEXT(" final sweep ends at the configured 4000 cm muzzle range"),
                         FMath::IsNearlyEqual(FVector::Distance(Muzzle, Round->GetActorLocation()), 4000.0, .1));
        }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFlightMuzzleObstruction, "SpaceSurvival.Flight.CameraAimMuzzleObstruction",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFlightMuzzleObstruction::RunTest(const FString &)
{
    for (SS::Weapon Weapon : {SS::Weapon::RapidLaser, SS::Weapon::HeavyCannon})
    {
        FSSFlightWorld Fixture;
        if (!Fixture.Initialize(*this, Weapon))
            return false;
        const FString Label = Weapon == SS::Weapon::RapidLaser ? TEXT("Laser") : TEXT("Cannon");
        Fixture.Instance->Session.tuning.baseWeaponDamage = 30;
        Fixture.Ship->Tuning->SoftAimDegrees = 0.f;
        Fixture.Frames(30);
        const FVector CameraOrigin = Fixture.Ship->Camera->GetComponentLocation();
        const FVector CameraForward = Fixture.Ship->Camera->GetForwardVector();
        const FVector TargetPosition = CameraOrigin + CameraForward * 5000.f;
        const FVector Muzzle = Fixture.Ship->GetActorLocation() + Fixture.Ship->GetActorForwardVector() * 240.f;
        auto *Target = Fixture.Target(TargetPosition - Fixture.Ship->GetActorLocation());
        auto *Blocker = Fixture.Target(FMath::Lerp(Muzzle, TargetPosition, .2f) - Fixture.Ship->GetActorLocation());
        if (!TestNotNull(Label + TEXT(" creates a camera-visible target"), Target) ||
            !TestNotNull(Label + TEXT(" creates a real damageable muzzle obstruction"), Blocker))
            return false;
        Blocker->Configure(ESSWorldKind::SmallAsteroid, 60.f, 0.f);
        // Geometry is independently checked before Fire: the elevated camera sees over the
        // blocker, while a shot converging from the unchanged muzzle must physically hit it.
        FCollisionQueryParams Query;
        Query.AddIgnoredActor(Fixture.Ship);
        FHitResult CameraHit, MuzzleHit;
        const bool bCameraHit =
            Fixture.World->LineTraceSingleByChannel(CameraHit, CameraOrigin, TargetPosition, ECC_Visibility, Query);
        const bool bMuzzleHit =
            Fixture.World->LineTraceSingleByChannel(MuzzleHit, Muzzle, TargetPosition, ECC_Visibility, Query);
        if (!TestTrue(Label + TEXT(" camera ray reaches the target without hitting the blocker"),
                      bCameraHit && CameraHit.GetActor() == Target) ||
            !TestTrue(Label + TEXT(" actual muzzle path is obstructed before the target"),
                      bMuzzleHit && MuzzleHit.GetActor() == Blocker))
            return false;
        TestNull(Label + TEXT(" obstruction case has no soft-assist target"), Fixture.Ship->SoftTarget);
        Fixture.Ship->Fire();
        Fixture.Frames(12);
        TestTrue(Label + TEXT(" hits and destroys the real muzzle blocker"), Blocker->IsActorBeingDestroyed());
        TestFalse(Label + TEXT(" cannot damage the camera-visible target through the blocker"),
                  Target->IsActorBeingDestroyed());
        TestEqual(Label + TEXT(" leaves its source pawn undamaged"), Fixture.Instance->Session.run.shield,
                  Fixture.Instance->Session.Stats().maxShield);
    }
    return true;
}
#endif
