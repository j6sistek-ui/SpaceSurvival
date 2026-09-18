#include "NiagaraComponent.h"
#include "SSContentTypes.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSShipPresentation.h"
#include "SSDistantAsteroids.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "HAL/IConsoleManager.h"
#include "Misc/ScopeExit.h"
#include "Misc/PackageName.h"
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
#include "GameFramework/SpringArmComponent.h"

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
    const bool HasPrivateStarter = FPackageName::DoesPackageExist(
        TEXT("/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/SM_PlayerHavolkStarter"));
    const TCHAR *ExpectedHullPaths[] = {
        HasPrivateStarter ? TEXT("/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/"
                                 "SM_PlayerHavolkStarter.SM_PlayerHavolkStarter")
                          : TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShipGripFit.SM_AcornShipGripFit"),
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
        TestEqual(Label + TEXT(" only the private closed starter hides its flight pilot"), Pilot->IsVisible(),
                  !(Index == 0 && HasPrivateStarter));
        // The mount is the seated hero's own measurement of this cushion, not a constant of the ship, and
        // the ship's whole job with it is to apply it unchanged. Each hero's is written out here rather
        // than read back off the definition the ship just used, which would only assert that the ship had
        // used something: the Acornaut's 72 cm includes 62.9 cm of its own sole, and the imported hero,
        // whose origin is its sole, sits at 27.933 - inheriting the first is what floated it 44 cm up.
        const FSSHeroDefinition &PilotHero = Fixture.Ship->GetPilotHero();
        FVector ExpectedMount = FVector::ZeroVector;
        if (PilotHero.Identity == ESSHeroIdentity::Acornaut)
            ExpectedMount = FVector(-15, 0, 72);
        else if (PilotHero.Identity == ESSHeroIdentity::Squirrel)
            ExpectedMount = FVector(-12.5, 0, 27.933);
        else if (!TestTrue(Label + TEXT(" is flown by a hero this test has a measured mount for"), false))
            return false;
        TestTrue(Label + TEXT(" retains the seated hero's measured pilot mount and constant scale"),
                 Pilot->GetAttachParent() == Hull && Pilot->GetRelativeLocation().Equals(ExpectedMount, .001) &&
                     PilotHero.PilotMountOffset.Equals(ExpectedMount, .001) &&
                     Pilot->GetRelativeRotation().Equals(FRotator(0, -90, 0), .001) &&
                     Pilot->GetRelativeScale3D().Equals(FVector(1.5), .001));
        // Whether this hull wears the fitted-module presentation at all. USSShipPresentation measures its
        // mounts off a static mesh's bounding box and gates on the literal name SM_PlayerHavolkStarter, so
        // it fits exactly one hull; a hull that hides that mesh hides the modules with it, and asserting
        // they are visible would be asserting that a ship is wearing another ship's nacelle casings.
        const FSSHullDefinition Wearing(ASSShip::SelectedHullIdentity());
        if (Index == 0 && HasPrivateStarter && Wearing.UsesModulePresentation)
        {
            auto *Presentation = Fixture.Ship->FindComponentByClass<USSShipPresentation>();
            if (!TestNotNull(TEXT("Private Starter has its real module presentation"), Presentation))
                return false;
            FVector CosmeticMount;
            TestTrue(TEXT("Base exhaust clears the imported left nacelle outlet"),
                     Presentation->TryGetExhaustLocalPosition(0, CosmeticMount) &&
                         CosmeticMount.Equals(FVector(-235.f, -102.f, 10.f), .01));
            auto &Run = Fixture.Instance->Session.run;
            Run.tiers = {{5, 5, 5, 5, 5}};
            Run.utility = SS::Utility::VectorThrusters;
            Presentation->TickComponent(0.f, LEVELTICK_All, nullptr);
            TestTrue(TEXT("Tier-V exhaust clears the larger right nacelle casing"),
                     Presentation->TryGetExhaustLocalPosition(1, CosmeticMount) &&
                         CosmeticMount.Equals(FVector(-240.5f, 102.f, 10.f), .01));
            TestTrue(TEXT("Tier-V muzzle flash follows the visible ventral barrel tip"),
                     Presentation->TryGetMuzzleWorldPosition(CosmeticMount) &&
                         Hull->GetComponentTransform()
                             .InverseTransformPosition(CosmeticMount)
                             .Equals(FVector(246.f, 0.f, -25.f), .01));
            int32 FittedModules = 0;
            for (USceneComponent *Child : Hull->GetAttachChildren())
                if (auto *Module = Cast<UStaticMeshComponent>(Child))
                    if (Module->GetStaticMesh())
                    {
                        ++FittedModules;
                        TestTrue(TEXT("Closed Starter loads its own fitted private modules"),
                                 Module->GetStaticMesh()->GetPathName().StartsWith(
                                     TEXT("/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/")));
                        TestTrue(TEXT("Each fitted module is visible and collisionless"),
                                 Module->IsVisible() &&
                                     Module->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
                    }
            TestEqual(TEXT("Five tier-V tracks and one utility are visible on the new hull"), FittedModules, 6);
            Run.tiers = {{1, 1, 1, 1, 1}};
            Run.utility = SS::Utility::None;
            Presentation->TickComponent(0.f, LEVELTICK_All, nullptr);
            TestFalse(TEXT("Tier-I retains the original shot-origin flash fallback"),
                      Presentation->TryGetMuzzleWorldPosition(CosmeticMount));
            for (USceneComponent *Child : Hull->GetAttachChildren())
                if (auto *Module = Cast<UStaticMeshComponent>(Child))
                    TestFalse(TEXT("Tier-I removes the optional upgrade presentation"), Module->IsVisible());
        }
        else if (Index == 0 && !Wearing.UsesModulePresentation)
        {
            // The other half of the same claim, for a hull that declines the fitted modules: it is not
            // simply bare. This one carries its own exhausts on its own nozzle bones, which is why it does
            // not want a presentation measured against a different mesh. Asserting that keeps the suite
            // proving something rather than quietly skipping, and it would catch a hull that switched the
            // modules off and then shipped with no engine effect at all - which is exactly how this hull
            // first flew, and exactly what the first capture of it showed.
            auto *Skeletal = Fixture.Ship->SkeletalHull.Get();
            if (!TestNotNull(TEXT("A hull that declines module presentation has a skeletal hull"), Skeletal))
                return false;
            TestTrue(TEXT("It is the hull actually being drawn"), Skeletal->IsVisible() && !Hull->IsVisible());
            // What can honestly be asserted here, and what cannot.
            //
            // The plumes are spawned with UNiagaraFunctionLibrary::SpawnSystemAttached onto this hull's own
            // Nozzle_Back_* bones. Counting them was the obvious check, and it reads 0 in this gate for a
            // reason that has nothing to do with the ship: automation runs under -NullRHI, where the FX
            // system creates no Niagara components at all. An assertion that cannot pass however correct
            // the ship is, is worse than no assertion, because the way it gets "fixed" is by loosening it.
            //
            // So assert what holds without a renderer: this hull declines the fitted modules DELIBERATELY
            // rather than by omission - it is declared and validated - the engine effect it relies on
            // instead is present, and it is wearing none of the static hull's modules. That still catches
            // the failure this hull actually had once, which was flying with no engine effect because the
            // module presentation was hidden and nothing had been declared to replace it.
            const bool HasOwnExhaust =
                FPackageName::DoesPackageExist(TEXT("/Game/Stellar_Phoenix/Spaceship/VFX/VFX_Exhaust"));
            AddInfo(FString::Printf(TEXT("%s declines fitted modules; its own exhaust asset is %s"), *Label,
                                    HasOwnExhaust ? TEXT("present") : TEXT("ABSENT")));
            TestTrue(TEXT("A hull that declines the fitted modules brings its own engine effect asset"), HasOwnExhaust);
            bool AnyModuleVisible = false;
            for (USceneComponent *Child : Hull->GetAttachChildren())
                if (auto *Module = Cast<UStaticMeshComponent>(Child))
                    AnyModuleVisible |= Module->IsVisible();
            TestFalse(TEXT("And wears none of the static hull's fitted modules"), AnyModuleVisible);
        }

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
    // Whose agreement figures apply is whoever is actually flying, asked of the one function that decides
    // it. The first version of this re-derived the choice from the command line and got it wrong the moment
    // the hull stopped being flag-selected: it reported Classic while a Phoenix was in the air, and held a
    // force-solver hull to a fixed-substep integrator's numbers.
    const FSSHullDefinition Tolerances(ASSShip::SelectedHullIdentity());
    FString Why;
    TestTrue(FString::Printf(TEXT("The flying hull declares its own agreement figures: %s"), *Why),
             Tolerances.Validate(Why));
    AddInfo(FString::Printf(TEXT("Hull under test: %s (position %.0f cm, velocity %.0f cm/s, heading %.2f deg)"),
                            *Tolerances.Id.ToString(), Tolerances.FrameRatePositionCm, Tolerances.FrameRateVelocityCmS,
                            Tolerances.FrameRateHeadingDeg));
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
            AddInfo(FString::Printf(TEXT("%s: position error %.3f cm; velocity error %.3f cm/s; heading error "
                                         "yaw %.4f pitch %.4f deg"),
                                    *Label, PositionError, VelocityError, RotationError.Yaw, RotationError.Pitch));
            // The tolerances are the hull's own. The classic hull's are unchanged - 25 cm was always
            // derived as "under one eighth of the collision diameter", so it was a per-hull number frozen
            // as a literal the moment a second hull existed. Asking the hull keeps the rule and lets each
            // ship answer for itself, which is the whole of "confirm values exist for that model".
            TestTrue(Label + FString::Printf(TEXT(" position agrees within %.0f cm"), Tolerances.FrameRatePositionCm),
                     PositionError <= Tolerances.FrameRatePositionCm);
            TestTrue(Label +
                         FString::Printf(TEXT(" velocity agrees within %.0f cm/s"), Tolerances.FrameRateVelocityCmS),
                     VelocityError <= Tolerances.FrameRateVelocityCmS);
            TestTrue(Label +
                         FString::Printf(TEXT(" heading agrees within %.2f degrees"), Tolerances.FrameRateHeadingDeg),
                     FMath::Abs(RotationError.Yaw) <= Tolerances.FrameRateHeadingDeg &&
                         FMath::Abs(RotationError.Pitch) <= Tolerances.FrameRateHeadingDeg);
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
    AddInfo(FString::Printf(TEXT("Brake floor %.1f cm/s; lowest forward speed reached %.1f (undershoot %.1f)"), Minimum,
                            LowestForwardSpeed, Minimum - LowestForwardSpeed));
    // The claim in the name, asserted as the name states it, with no slack for any hull: a held brake slows
    // the ship and never brings it to a stop or pushes it backwards. This is the WAVE-zone rule - per
    // GAME_SCOPE section 6b the station zone deliberately lifts it, where stopping and a slow reverse on a
    // held brake are the specification - so when zones exist this assertion belongs to the wave and its
    // opposite belongs to the station.
    TestTrue(TEXT("Braking never stops or reverses forward travel"), LowestForwardSpeed > 0.);
    // And separately, how closely this hull settles onto the floor it was told to hold. A kinematic hull
    // resolves speed by assignment and lands on 1000 exactly; a force drive decelerates onto it and dips
    // under before settling - 924.1 measured on the Phoenix, 7.6 percent low, nowhere near stopping. That
    // is what deceleration does, not a ship disobeying, so it is the hull's own figure.
    const FSSHullDefinition BrakeHull(ASSShip::SelectedHullIdentity());
    TestTrue(FString::Printf(TEXT("A held brake settles onto the floor within %.0f cm/s"),
                             BrakeHull.BrakeFloorUndershootCmS),
             LowestForwardSpeed >= Minimum - BrakeHull.BrakeFloorUndershootCmS);
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
    // Whose figures apply, asked of the one function that decides which hull flies.
    const FSSHullDefinition Tolerances(ASSShip::SelectedHullIdentity());
    FString Why;
    if (!TestTrue(FString::Printf(TEXT("The flying hull declares its own agreement figures: %s"), *Why),
                  Tolerances.Validate(Why)))
        return false;
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
        // What this asserts: the contact shoved the ship outward, hard, and nothing else moved it.
        //
        // It used to spell "nothing else" as |Impulse.X| < 1 cm/s and a total under 601. Both are facts
        // about a fixed-substep integrator sitting exactly on its own fixed point - the kinematic hull is
        // seeded at precisely cruise, so Desired - Velocity is zero and the substep loop adds no
        // longitudinal change at all. A force drive has no such fixed point: DriveShipCore feeds a trim
        // ERROR to the thrusters every frame, so there is always some legitimate thrust inside the measured
        // step, and at this game's 3200 cm/s^2 that is up to ~107 cm/s at 30 Hz. The old bound is not tight,
        // it is unreachable in principle.
        //
        // So the allowance is one frame of THIS ship's own acceleration - a quantity both drives have, and
        // which is ~0 for the kinematic hull because it is already at its target. The outward push and its
        // dominance are unchanged, because those are the actual claim.
        // The push is the right size, points outward, and is dominated by outward.
        //
        // It used to require |Impulse.X| < 1 cm/s, which is not a fact about impacts: it is a fact about a
        // fixed-substep integrator seeded exactly at cruise, whose relative motion against an asteroid
        // given that same velocity is nil, so the contact normal comes out exactly perpendicular. A force
        // drive accelerates during the frame, a little relative drift accumulates, and the normal tilts -
        // measured at .12 of the outward component at 144 Hz and .44 at 30 Hz, while the magnitude stayed
        // exactly 600 cm/s at every rate. The shove is correct; its direction breathes with the frame.
        //
        // An earlier attempt allowed one frame of thrust here. That was the wrong mechanism - the tilt is
        // geometric amplification of the drift, not the drift itself - and it failed by roughly 2.3x,
        // which is how it got caught.
        const double ThrustPerFrame = double(Fixture.Instance->Session.Stats().acceleration) / Hertz;
        TestTrue(Label + TEXT(" causes an immediate bounded outward deflection"),
                 Impulse.Y < -450.f && Impulse.Size() <= 601.f + ThrustPerFrame &&
                     FMath::Abs(Impulse.X) <= FMath::Max(1.f, FMath::Abs(Impulse.Y) * Tolerances.ContactOffAxisShare));
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
            // Frame-rate agreement again, at contact scale. 12 cm over a quarter second is the residue of
            // the kinematic hull clamping every frame into identical 1/120 substeps, so 30 Hz is literally
            // four of what 120 Hz does once. Chaos substeps on its own schedule and cannot reproduce that,
            // which is the same reason the whole-trajectory figures moved into the hull. This one scales
            // with the hull's declared position tolerance rather than carrying a second literal: a quarter
            // second of contact recovery is a small fraction of the four-second flight that figure was
            // measured over.
            const double TravelAgreement = FMath::Max(12.0, Tolerances.FrameRatePositionCm * .25);
            TestTrue(
                Label + FString::Printf(TEXT(" quarter-second recovery travel agrees within %.0f cm"), TravelAgreement),
                Travel.Equals(ReferenceTravel, TravelAgreement));
        }
        AddInfo(FString::Printf(TEXT("%s: impulse (%.2f, %.2f, %.2f) size %.3f, allowance %.2f, lateral travel "
                                     "%.3f cm, residual %.3f cm/s"),
                                *Label, Impulse.X, Impulse.Y, Impulse.Z, Impulse.Size(), ThrustPerFrame, Travel.Y,
                                Fixture.Ship->GetVelocity().Y));
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
    // Whose drive is flying, because the next two lines differ by it.
    const FSSHullDefinition Hull(ASSShip::SelectedHullIdentity());
    Fixture.Ship->AddActorWorldOffset(FVector(800, 0, 0));
    Body->Tick(.1f);
    // A force drive needs one step before the push exists. ASSWorldBody::Tick calls ReceiveImpact, which on
    // a kinematic hull writes the velocity member and is readable immediately - but on a simulating body it
    // adds an impulse, and an impulse does nothing until physics runs. Without this the Phoenix measured a
    // deflection of exactly (0, 0, 0) while still taking the damage: the shove had been issued and never
    // integrated.
    //
    // Conditional, because stepping is not free for the other drive: a kinematic hull's Tick integrates
    // velocity back toward its target, so the same step spends part of the deflection before it is read and
    // the classic hull fails its own assertion. The step is an artifact of how an impulse becomes velocity,
    // so it belongs only to the drive that needs it. Caught by the classic gate, which is what it is for.
    if (Hull.Drive == ESSHullDrive::ForceSolver)
        Fixture.Step(1.f / 240.f);
    const FVector Deflection = Fixture.Ship->GetVelocity() - Before;
    TestEqual(TEXT("Continuous crossing still applies exactly one kinetic hit"), Fixture.Instance->Session.run.shield,
              Shield - 30.0);
    // The claim is that a crossing through the body's centre pushes the ship BACK the way it came, rather
    // than flinging it out the far side - which is what the degenerate-normal fallback in ASSWorldBody
    // exists for. The .01 cm/s bounds on the other two axes were the kinematic hull's stillness, not part
    // of that claim; a force drive carries its own thrust through the 100 ms the body is ticked for. The
    // allowance is that thrust, so the assertion still says "the push is backwards along entry, and
    // nothing sideways happened", which is the thing worth protecting.
    // Same rule as the contact suite: the push is backwards along entry and dominated by that axis. The
    // .01 cm/s bounds on the other two were the kinematic hull's stillness rather than part of the claim.
    const double OffAxis = FMath::Max(.01, FMath::Abs(Deflection.X) * Hull.ContactOffAxisShare);
    AddInfo(FString::Printf(TEXT("Centre crossing deflection (%.2f, %.2f, %.2f), off-axis allowance %.2f"),
                            Deflection.X, Deflection.Y, Deflection.Z, OffAxis));
    TestTrue(TEXT("Center crossing deflects against entry rather than accelerating out the far side"),
             Deflection.X < -599.f && FMath::Abs(Deflection.Y) <= OffAxis && FMath::Abs(Deflection.Z) <= OffAxis);
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
        // Derive obstruction size from the actual camera/muzzle parallax. A fixed
        // 60cm blocker intersected both rays after the chase-camera framing repair.
        const float RaySeparation =
            FMath::PointDistToSegment(Blocker->GetActorLocation(), CameraOrigin, TargetPosition);
        if (!TestTrue(Label + TEXT(" actual chase camera and muzzle have usable parallax"), RaySeparation > 10.f))
            return false;
        Blocker->Configure(ESSWorldKind::SmallAsteroid, RaySeparation * .4f, 0.f);
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSProjectileRelativeMotion, "SpaceSurvival.Flight.ProjectileRelativeMotion",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSProjectileRelativeMotion::RunTest(const FString &)
{
    // The two synchronized trajectories cross at different times in case 0,
    // and at the same time in the others. Endpoint-only world sweeps confuse them.
    for (float Step : {1.f / 30.f, 1.f / 60.f, 1.f / 144.f, .1f})
        for (int32 Case = 0; Case < 9; ++Case)
        {
            FSSFlightWorld Fixture;
            if (!Fixture.Initialize(*this))
                return false;
            FVector Origin(0, 0, 7000);
            const FVector ShipStart(0, Case == 0 ? -800.f : -400.f, 0);
            const FVector ShipEnd(0, Case == 0 ? 0.f : 400.f, 0);
            Fixture.Ship->SetActorLocation(Origin + ShipStart);
            auto *Source = Fixture.World->SpawnActor<AActor>(Origin + FVector(-2000, 0, 0), FRotator::ZeroRotator);
            auto *Shot = Fixture.World->SpawnActor<ASSProjectile>(Origin + FVector(-365, 0, 0), FRotator::ZeroRotator);
            if (!TestNotNull(TEXT("Create real projectile"), Shot) ||
                !TestNotNull(TEXT("Create firing source"), Source))
                return false;
            const bool bPlayerShot = Case == 8;
            Shot->Launch(FVector::ForwardVector, 7300.f, 40.f, bPlayerShot, Source, Case == 6 ? 146.f : -1.f);
            if (Case == 4 || Case == 5)
                Shot->LifetimeSeconds = Case == 4 ? .02f : .08f;
            ASSWorldBody *Cover = nullptr;
            if (Case == 2 || Case == 3)
            {
                Cover = Fixture.World->SpawnActor<ASSWorldBody>(Origin + FVector(Case == 2 ? -230.f : 230.f, 0, 0),
                                                                FRotator::ZeroRotator);
                if (!TestNotNull(TEXT("Create real intervening cover"), Cover))
                    return false;
                Cover->Configure(ESSWorldKind::SmallAsteroid, 25.f, 0.f);
            }
            if (Case == 7)
            {
                const FVector Shift(700000, -100000, 80000);
                Fixture.Ship->ApplyWorldOffset(Shift, true);
                Shot->ApplyWorldOffset(Shift, true);
                Origin += Shift;
            }
            const double ShieldBefore = Fixture.Instance->Session.run.shield;
            float Elapsed = 0.f;
            while (Elapsed < .1f - UE_SMALL_NUMBER && !Shot->IsActorBeingDestroyed())
            {
                const float Delta = FMath::Min(Step, .1f - Elapsed);
                Elapsed += Delta;
                Fixture.Ship->SetActorLocation(Origin + FMath::Lerp(ShipStart, ShipEnd, Elapsed / .1f));
                Shot->Tick(Delta);
            }
            const bool bExpectedHit = Case == 1 || Case == 3 || Case == 5 || Case == 7;
            const FString Label = FString::Printf(TEXT("Relative shot dt=%.6f case=%d"), Step, Case);
            TestEqual(Label + TEXT(" applies damage only at synchronized contact"),
                      Fixture.Instance->Session.run.shield, ShieldBefore - (bExpectedHit ? 54.0 : 0.0));
            if (Cover)
                TestEqual(Label + TEXT(" respects cover contact order"), Cover->IsActorBeingDestroyed(), Case == 2);
            const bool bExpectedConsumed = Case != 0 && Case != 8;
            TestEqual(Label + TEXT(" consumes exactly a hit or expired shot"), Shot->IsActorBeingDestroyed(),
                      bExpectedConsumed);
            if (Shot->IsActorBeingDestroyed())
            {
                const double ShieldAfter = Fixture.Instance->Session.run.shield;
                Shot->Tick(.1f);
                TestEqual(Label + TEXT(" cannot pay a second damage hit"), Fixture.Instance->Session.run.shield,
                          ShieldAfter);
            }
            if (Case == 0 || Case == 8)
                TestTrue(Label + TEXT(" preserves the unobstructed shot path"),
                         Shot->GetActorLocation().Equals(Origin + FVector(365, 0, 0), .01f));
        }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSFlightChaseFraming, "SpaceSurvival.Flight.ChaseFraming",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSFlightChaseFraming::RunTest(const FString &)
{
    // A bound that aborts the run on its first breach censors the very number it is trying to bound: the
    // recorded maximum is then whatever the threshold allowed, not what the camera did. Measuring with
    // -SSCameraLagSurvey lifts the bound so the worst is the real worst, and the figure is reported either
    // way rather than only on failure.
    const double LagBoundSlack = FParse::Param(FCommandLine::Get(), TEXT("SSCameraLagSurvey")) ? 1000. : 1.;
    double WorstLag = 0, WorstLagShare = 0;
    for (int32 Hertz : {30, 60, 144})
    {
        FSSFlightWorld Fixture;
        if (!Fixture.Initialize(*this))
            return false;
        auto *Ship = Fixture.Ship;
        // Frame whichever hull is actually on screen. This used to read the static mesh unconditionally,
        // which is right until a build draws something else: under the Phoenix the static hull is still
        // loaded but hidden, so the test was projecting a 4.82 m box that nobody can see while a 24.84 m
        // ship filled the frame. It reported the camera clipping a hull it was not looking at.
        // Whose framing figures apply, asked of the one function that decides which hull flies.
        const FSSHullDefinition Tolerances(ASSShip::SelectedHullIdentity());
        FString Why;
        if (!TestTrue(FString::Printf(TEXT("The flying hull declares its own framing: %s"), *Why),
                      Tolerances.Validate(Why)))
            return false;
        const bool Skeletal = Ship->SkeletalHull && Ship->SkeletalHull->IsVisible();
        const USceneComponent *Drawn = Skeletal ? static_cast<USceneComponent *>(Ship->SkeletalHull)
                                                : static_cast<USceneComponent *>(Ship->HullMesh);
        FBox Bounds(ForceInit);
        if (Skeletal)
        {
            if (const USkeletalMesh *Mesh = Ship->SkeletalHull->GetSkeletalMeshAsset())
                Bounds = Mesh->GetBounds().GetBox();
        }
        else if (const UStaticMesh *Mesh = Ship->HullMesh->GetStaticMesh())
            Bounds = Mesh->GetBoundingBox();
        if (!TestTrue(TEXT("Use the hull actually being drawn for camera projection"), Bounds.IsValid != 0))
            return false;
        AddInfo(FString::Printf(TEXT("Framing the %s hull: %s"), Skeletal ? TEXT("skeletal") : TEXT("static"),
                                *Bounds.GetSize().ToCompactString()));
        // Exercise the real spring arm/component tick, including acceleration,
        // bank, boost transitions and heat-limited braking; never move the camera directly.
        for (int32 Scenario = 0; Scenario < 5; ++Scenario)
        {
            Ship->SetFlightInput(Scenario == 3   ? FVector2D(1, .35)
                                 : Scenario == 4 ? FVector2D(-1, -.35)
                                                 : FVector2D::ZeroVector,
                                 Scenario >= 3 ? FVector2D(.7, .4) : FVector2D::ZeroVector, Scenario == 2 ? -1.f : 0.f,
                                 Scenario == 1, Scenario == 2);
            for (int32 Frame = 0; Frame < Hertz * 2; ++Frame)
            {
                Fixture.Step(1.f / Hertz);
                const FTransform View = Ship->Camera->GetComponentTransform();
                const double TanHalfHorizontal = FMath::Tan(FMath::DegreesToRadians(Ship->Camera->FieldOfView * .5));
                const double TanHalfVertical = TanHalfHorizontal / (16.0 / 9.0);
                for (int32 Corner = 0; Corner < 8; ++Corner)
                {
                    const FVector Point(Corner & 1 ? Bounds.Max.X : Bounds.Min.X,
                                        Corner & 2 ? Bounds.Max.Y : Bounds.Min.Y,
                                        Corner & 4 ? Bounds.Max.Z : Bounds.Min.Z);
                    const FVector Local =
                        View.InverseTransformPosition(Drawn->GetComponentTransform().TransformPosition(Point));
                    const double X = .5 + Local.Y / (2.0 * Local.X * TanHalfHorizontal);
                    const double Y = .5 - Local.Z / (2.0 * Local.X * TanHalfVertical);
                    if (Local.X <= 0 || X < .02 || X > .98 || Y < .02 || Y > .98)
                    {
                        AddError(FString::Printf(
                            TEXT("Hull clipped: %dHz scenario%d frame%d corner%d projection %.3f,%.3f depth%.1f"),
                            Hertz, Scenario, Frame, Corner, X, Y, Local.X));
                        return false;
                    }
                }
                // What the spring arm owes us is that the camera hangs at the arm length it was asked
                // for. That is exact and measurable: distance from the boom origin to the camera, minus
                // the socket offset, against TargetArmLength.
                //
                // This used to reconstruct the un-lagged anchor instead - camera + forward * arm - socket -
                // and assert it landed within 35.1 cm of the boom. That works at the classic hull's 125 cm
                // socket offset and stops working at the Phoenix's 3000: the reconstruction rotates the
                // offset by the boom's rotation as read AFTER the tick, and any fraction of a degree
                // between that and the rotation the engine placed the camera with is multiplied by the
                // offset. It reported 1974 cm of "lag" on a spring arm whose own CameraLagMaxDistance
                // clamps lag at 35, which is the tell: the number was arithmetic, not camera behaviour.
                // Measured arm shortfall on both hulls is 0.0 cm.
                const FVector SocketOffset =
                    Ship->CameraBoom->GetComponentRotation().RotateVector(Ship->CameraBoom->SocketOffset);
                const double ArmHeld = FVector::Distance(Ship->Camera->GetComponentLocation() - SocketOffset,
                                                         Ship->CameraBoom->GetComponentLocation());
                const double Shortfall = FMath::Abs(double(Ship->CameraBoom->TargetArmLength) - ArmHeld);
                WorstLag = FMath::Max(WorstLag, Shortfall);
                WorstLagShare =
                    FMath::Max(WorstLagShare, Shortfall / FMath::Max(1.0, double(Ship->CameraBoom->TargetArmLength)));
                const double ArmBound = Ship->CameraBoom->TargetArmLength * Tolerances.CameraLagShareOfArm;
                if (!TestTrue(
                        FString::Printf(TEXT("The chase camera holds its %.0f cm arm within %.1f cm (off by %.1f)"),
                                        Ship->CameraBoom->TargetArmLength, ArmBound, Shortfall),
                        Shortfall <= ArmBound * LagBoundSlack))
                    return false;
                if (!TestTrue(TEXT("Manual weapon sight remains the rendered camera forward"),
                              Ship->AimDirection().Equals(Ship->Camera->GetForwardVector(), .00001)))
                    return false;
            }
        }
    }
    // Reported whether or not anything tripped, because a bound that aborts on its first breach
    // censors the number it is bounding - the recorded worst becomes whatever the threshold allowed.
    AddInfo(FString::Printf(TEXT("Worst arm shortfall over every scenario and rate: %.1f cm, %.4f of the arm"),
                            WorstLag, WorstLagShare));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDistantAsteroidIsolation, "SpaceSurvival.Flight.DistantAsteroidIsolation",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDistantAsteroidIsolation::RunTest(const FString &)
{
    FSSFlightWorld Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    IConsoleVariable *Count = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.DistantAsteroidCount"));
    if (!TestNotNull(TEXT("Distant asteroid scalability control exists"), Count))
        return false;
    const int32 PreviousCount = Count->GetInt();
    const EConsoleVariableFlags Priority = EConsoleVariableFlags(Count->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Count->Set(PreviousCount, Priority);
    };
    Count->Set(128, Priority);
    auto *Field = Fixture.World->SpawnActor<ASSDistantAsteroids>();
    if (!TestNotNull(TEXT("Spawn actual distant field"), Field))
        return false;
    Field->Follow(Fixture.Ship);
    Field->SetFlightVisible(true);
    TestFalse(TEXT("Dressing cannot be a weapon/damage world-body target"), Field->IsA(ASSWorldBody::StaticClass()));
    TestFalse(TEXT("Dressing actor collision disabled"), Field->GetActorEnableCollision());
    TArray<UInstancedStaticMeshComponent *> Batches;
    Field->GetComponents(Batches);
    if (!TestTrue(TEXT("Renderable mesh batches loaded"), Batches.Num() > 0))
        return false;
    int32 Instances = 0;
    for (const auto *Batch : Batches)
    {
        TestTrue(TEXT("Each available mesh family participates at normal density"), Batch->GetInstanceCount() > 0);
        TestTrue(TEXT("Every batch disables collision"),
                 Batch->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Every batch disables overlaps"), Batch->GetGenerateOverlapEvents());
        Instances += Batch->GetInstanceCount();
    }
    TestEqual(TEXT("Requested density creates bounded real instances"), Instances, 128);
    auto CheckDistance = [&]()
    {
        for (const auto *Batch : Batches)
        {
            const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
            for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
            {
                FTransform Instance;
                if (!Batch->GetInstanceTransform(Index, Instance, true))
                    return false;
                const FVector Center = Instance.TransformPosition(Bounds.Origin);
                const double SurfaceDistance = FVector::Distance(Center, Fixture.Ship->GetActorLocation()) -
                                               Bounds.SphereRadius * Instance.GetScale3D().GetAbsMax();
                if (SurfaceDistance < Field->GetMinimumSurfaceDistance() - .1 ||
                    SurfaceDistance <= Fixture.Ship->Tuning->WeaponRange)
                    return false;
            }
        }
        return true;
    };
    TestTrue(TEXT("Actual transformed mesh bounds stay outside the playable weapon range initially"), CheckDistance());
    TArray<TArray<FVector>> InitialCenters;
    InitialCenters.SetNum(Batches.Num());
    TSet<int32> AnchorMeshBatches;
    int32 FarRocks = 0;
    bool bClearEntryAim = true;
    for (int32 BatchIndex = 0; BatchIndex < Batches.Num(); ++BatchIndex)
    {
        const auto *Batch = Batches[BatchIndex];
        TestFalse(TEXT("Decoration does not affect navigation"), Batch->CanEverAffectNavigation());
        TestFalse(TEXT("Decoration does not introduce distant shadow work"), Batch->CastShadow);
        const FBoxSphereBounds Bounds = Batch->GetStaticMesh()->GetBounds();
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Instance;
            Batch->GetInstanceTransform(Index, Instance, true);
            const FVector Center = Instance.TransformPosition(Bounds.Origin) - Fixture.Ship->GetActorLocation();
            InitialCenters[BatchIndex].Add(Center);
            const double Radius = Bounds.SphereRadius * Instance.GetScale3D().GetAbsMax();
            if (Radius > 2200.0)
                AnchorMeshBatches.Add(BatchIndex);
            if (Center.Size() > 100000.0)
                ++FarRocks;
            if (Center.GetSafeNormal().X > .97 &&
                ((Center.Size() < 65000.0 && Radius > 220.1) || Radius / Center.Size() > .05))
                bClearEntryAim = false;
        }
    }
    TestTrue(TEXT("Large silhouettes use multiple barren/mineral meshes instead of one repeated anchor"),
             AnchorMeshBatches.Num() >= 4);
    TestTrue(TEXT("Distant fragments supply a separate depth layer"), FarRocks > 0);
    TestTrue(TEXT("Initial nearby aim corridor is clear; distant field silhouettes stay below three angular degrees"),
             bClearEntryAim);
    const FRotator InitialRotation = Fixture.Ship->GetActorRotation();
    Fixture.Ship->SetActorRotation(FRotator(20.f, 90.f, 0.f));
    Field->Tick(0.f);
    bool bStableDuringTurn = true;
    for (int32 BatchIndex = 0; BatchIndex < Batches.Num(); ++BatchIndex)
    {
        const auto *Batch = Batches[BatchIndex];
        const FVector Origin = Batch->GetStaticMesh()->GetBounds().Origin;
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Instance;
            Batch->GetInstanceTransform(Index, Instance, true);
            const FVector Center = Instance.TransformPosition(Origin) - Fixture.Ship->GetActorLocation();
            bStableDuringTurn &= Center.Equals(InitialCenters[BatchIndex][Index], .1);
        }
    }
    TestTrue(TEXT("Turning the viewer does not swivel or reseed the environment"), bStableDuringTurn);
    Fixture.Ship->SetActorRotation(InitialRotation);
    Fixture.Ship->AddActorWorldOffset(FVector(0, 1000, 0));
    Field->Tick(0.f);
    double MinimumShift = TNumericLimits<double>::Max();
    double MaximumShift = 0.0;
    for (int32 BatchIndex = 0; BatchIndex < Batches.Num(); ++BatchIndex)
    {
        const auto *Batch = Batches[BatchIndex];
        const FVector Origin = Batch->GetStaticMesh()->GetBounds().Origin;
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Instance;
            Batch->GetInstanceTransform(Index, Instance, true);
            const FVector Center = Instance.TransformPosition(Origin) - Fixture.Ship->GetActorLocation();
            const double Shift = (Center - InitialCenters[BatchIndex][Index]).Size();
            MinimumShift = FMath::Min(MinimumShift, Shift);
            MaximumShift = FMath::Max(MaximumShift, Shift);
        }
    }
    TestTrue(TEXT("Translation produces different motion in the near and distant layers"),
             MinimumShift > 0.0 && MaximumShift > 40.0 && MinimumShift < MaximumShift * .5);
    for (int32 Step = 0; Step < 160; ++Step)
    {
        Fixture.Ship->AddActorWorldOffset(FVector(5000, 1000, 500));
        Fixture.Step();
    }
    TestTrue(TEXT("Long cumulative travel cannot reach decorative mesh bounds"), CheckDistance());
    TArray<FVector> BeforeFurtherTravel;
    for (const auto *Batch : Batches)
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Instance;
            Batch->GetInstanceTransform(Index, Instance, true);
            BeforeFurtherTravel.Add(Instance.TransformPosition(Batch->GetStaticMesh()->GetBounds().Origin) -
                                    Fixture.Ship->GetActorLocation());
        }
    Fixture.Ship->AddActorWorldOffset(FVector(1000, 0, 0));
    Field->Tick(0.f);
    int32 FurtherIndex = 0;
    bool bStillMoving = false;
    for (const auto *Batch : Batches)
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Instance;
            Batch->GetInstanceTransform(Index, Instance, true);
            const FVector Center = Instance.TransformPosition(Batch->GetStaticMesh()->GetBounds().Origin) -
                                   Fixture.Ship->GetActorLocation();
            bStillMoving |= !Center.Equals(BeforeFurtherTravel[FurtherIndex++], 1.0);
        }
    TestTrue(TEXT("Parallax continues after prolonged flight instead of saturating a fixed offset"), bStillMoving);
    const double BeforeShift = Field->GetMinimumSurfaceDistance();
    const FVector Shift(-700000, -100000, -60000);
    Fixture.Ship->ApplyWorldOffset(Shift, true);
    Field->ApplyWorldOffset(Shift, true);
    Field->Tick(0.f);
    TestTrue(TEXT("World rebase does not create false parallax travel"),
             FMath::IsNearlyEqual(Field->GetMinimumSurfaceDistance(), BeforeShift, .01));
    TestTrue(TEXT("Rebased real instance bounds retain safety separation"), CheckDistance());
    Count->Set(4000, Priority);
    Field->Tick(1.f);
    TestEqual(TEXT("Density is capped at 3072 decorative instances"), Field->GetRockCount(), 3072);
    TestTrue(TEXT("Tumbling dense field keeps actual bounds outside weapon range"), CheckDistance());
    Count->Set(0, Priority);
    Field->Tick(0.f);
    TestEqual(TEXT("Density zero removes every instance"), Field->GetRockCount(), 0);
    for (const auto *Batch : Batches)
        TestEqual(TEXT("Disabled batch has no residual instances"), Batch->GetInstanceCount(), 0);
    Count->Set(384, Priority);
    Field->Tick(1.f);
    TestEqual(TEXT("Density can be restored without spawning gameplay actors"), Field->GetRockCount(), 384);
    TestTrue(TEXT("Restored field retains conservative bounds"), CheckDistance());
    Field->SetFlightVisible(false);
    Fixture.Step();
    TestTrue(TEXT("Explicit station-visibility setter hides the field"), Field->IsHidden());
    AddInfo(TEXT("Visibility setter exercised only; this test does not establish GameMode station routing."));
    return true;
}
#endif
