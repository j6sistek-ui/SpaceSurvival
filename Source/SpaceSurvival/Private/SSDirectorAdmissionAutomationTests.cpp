#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSWreckageBudgetWorld
{
    UWorld *World = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    USSSurvivalDirectorComponent *Director = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated wreckage budget world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No GameInstance Init, BeginPlay, save API or production slots.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install the actual content/Director owner"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve actual GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        auto *Controller = World->SpawnActor<APlayerController>();
        auto *Ship = World->SpawnActor<ASSShip>();
        if (!Test.TestNotNull(TEXT("Create controlled flight pawn"), Ship) ||
            !Test.TestNotNull(TEXT("Create input-free local controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->Possess(Ship);
        if (!Test.TestTrue(TEXT("Start only an in-memory run"), Instance->Session.StartRun("wreckage-budget")))
            return false;
        Instance->Session.run.wave = 6;
        auto &Selection = Mode->Tuning->DirectorContent;
        Selection.EnemyChance = Selection.FieldChance = 0.f;
        Selection.WreckageSelectionStart = 0.f;
        Selection.SpawnIntervalMin = Selection.SpawnIntervalMax = .1f;
        for (auto &Hazard : Mode->Tuning->Hazards)
            if (Hazard.Kind == ESSWorldKind::Wreckage)
            {
                Hazard.SelectionWeight = 1.f;
                Hazard.PressureCost = .5f;
            }
        Director = Mode->Director;
        Director->BaseBudgetPerSecond = 0.f;
        Director->MaximumActiveThreats = 8;
        Director->Configure(6, false); // Existing one-unit initial pressure budget; never reset during a scenario.
        Director->SetActive(true);
        return true;
    }

    void Step(float Seconds = .2f)
    {
        Director->TickComponent(Seconds, LEVELTICK_All, nullptr);
    }

    int32 WreckageCount() const
    {
        int32 Count = 0;
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->GetKind() == ESSWorldKind::Wreckage)
                ++Count;
        return Count;
    }

    void RemoveWreckage()
    {
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (It->GetKind() == ESSWorldKind::Wreckage)
            {
                // Keep deferred destruction out of the next spatial-admission attempt.
                It->SetActorLocation(FVector(-1000000, 0, 0));
                It->Destroy();
            }
    }

    ~FSSWreckageBudgetWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorAsteroidReadability,
                                 "SpaceSurvival.Integration.DirectorAsteroidReadability",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorAsteroidReadability::RunTest(const FString &)
{
    FSSWreckageBudgetWorld F;
    if (!F.Initialize(*this))
        return false;
    ASSShip *Ship = F.Director->FindShip();
    if (!TestNotNull(TEXT("Resolve ship for faster approach admission"), Ship))
        return false;
    Ship->Velocity = FVector(6000.f, 0.f, 0.f);
    const IConsoleVariable *Trajectory = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HazardTrajectory"));
    const bool bAimed = Trajectory && Trajectory->GetInt() != 0;
    for (auto Kind : {ESSWorldKind::SmallAsteroid, ESSWorldKind::MediumAsteroid, ESSWorldKind::MassiveAsteroid})
    {
        auto *Body = F.Director->SpawnHazard(Kind, -1.f);
        if (!TestNotNull(TEXT("Admit actual enlarged Director asteroid"), Body))
            return false;
        const float Radius = F.Mode->Tuning->Hazard(Kind).Radius * 3.f;
        TestEqual(TEXT("Director body is three times the catalog radius"), Body->GetBodyRadius(), Radius);
        TestEqual(TEXT("Collision uses the enlarged radius"), Body->Collision->GetUnscaledSphereRadius(), Radius);
        const float VisualRadius =
            Body->Visual->GetStaticMesh()->GetBounds().BoxExtent.GetMax() * Body->Visual->GetRelativeScale3D().X;
        TestTrue(TEXT("Visible surface scales with collision"), FMath::IsNearlyEqual(VisualRadius, Radius, 1.f));
        const FVector Location = Body->GetActorLocation();
        if (bAimed)
        {
            // Owner decision, September 27: rocks are thrown at the pilot. Its path crosses the ship's predicted
            // path near enough to demand an answer, and not before the reaction floor.
            const FVector Relative = Location - Ship->GetActorLocation();
            const FVector Closing = Body->GetVelocity() - Ship->GetVelocity();
            const double Time = -FVector::DotProduct(Relative, Closing) / FMath::Max(1.0, Closing.SizeSquared());
            const double Pass = (Relative + Closing * Time).Size();
            TestTrue(TEXT("Aimed rock reaches the ship's path no sooner than the reaction floor"),
                     Time >= F.Director->MinimumReactionSeconds);
            TestTrue(TEXT("Aimed rock passes within a few hull widths of the ship's predicted path"),
                     Pass <= Radius + 3.5f * ASSShip::FlightCollisionRadius() + 1.f);
            const double Contact = Radius + Ship->Collision->GetScaledSphereRadius();
            if (Pass < Contact && Closing.SizeSquared() > UE_SMALL_NUMBER)
            {
                const double FirstContact =
                    Time - FMath::Sqrt((Contact * Contact - Pass * Pass) / Closing.SizeSquared());
                TestTrue(TEXT("Aimed rock's first surface contact respects the reaction floor"),
                         FirstContact + .001 >= F.Director->MinimumReactionSeconds);
            }
        }
        else
        {
            TestTrue(TEXT("Legacy approach retains the forward reaction-time corridor"),
                     Location.X - Radius - F.Director->PlayerClearanceRadius >=
                         6000.f * F.Director->MinimumReactionSeconds);
            TestTrue(TEXT("Enlarged body remains outside the protected lane"),
                     FVector2D::Distance(FVector2D(Location.Y, Location.Z), F.Director->SafeLane) >=
                         Radius + F.Director->PlayerClearanceRadius + 320.f);
        }
        for (int32 Slot = 0; Slot < Body->Visual->GetNumMaterials(); ++Slot)
        {
            auto *Material = Cast<UMaterialInstanceDynamic>(Body->Visual->GetMaterial(Slot));
            if (!TestNotNull(TEXT("Every Director rock material slot has its distinct surface"), Material))
                return false;
            const FLinearColor Tint = Material->K2_GetVectorParameterValue(TEXT("Tint"));
            TestTrue(TEXT("Director surface is orange rather than the world belt's authored rock"),
                     Tint.R > .9f && Tint.G < .3f && Tint.B < .03f);
        }
        Body->KeepAdmittedAt(Ship->GetActorLocation());
        TestTrue(TEXT("Fast approach spawn survives distance retirement"),
                 Body->RetireDistance > FVector::Dist(Body->GetActorLocation(), Ship->GetActorLocation()));
        Body->SetActorLocation(FVector(-1000000, 0, 0));
        Body->Destroy();
    }
    auto *WorldRock = F.World->SpawnActor<ASSWorldBody>();
    WorldRock->Configure(ESSWorldKind::SmallAsteroid, F.Mode->Tuning->Hazard(ESSWorldKind::SmallAsteroid).Radius, 0.f);
    TestFalse(TEXT("Non-Director rocks retain their own size/material contract"), WorldRock->bDirectorAsteroid);
    TestEqual(TEXT("Non-Director radius is not multiplied"), WorldRock->GetBodyRadius(),
              F.Mode->Tuning->Hazard(ESSWorldKind::SmallAsteroid).Radius);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorTrajectoryFairness, "SpaceSurvival.Integration.DirectorTrajectoryFairness",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorTrajectoryFairness::RunTest(const FString &)
{
    struct FScopedDial
    {
        IConsoleVariable *Variable;
        FString Saved;
        explicit FScopedDial(const TCHAR *Name)
            : Variable(IConsoleManager::Get().FindConsoleVariable(Name)),
              Saved(Variable ? Variable->GetString() : FString())
        {
        }
        ~FScopedDial()
        {
            if (Variable)
                Variable->SetWithCurrentPriority(*Saved);
        }
        void Set(float Value) const
        {
            Variable->SetWithCurrentPriority(Value);
        }
    };
    FScopedDial Trajectory(TEXT("ss.HazardTrajectory")), Speed(TEXT("ss.HazardSpeed")),
        DirectShare(TEXT("ss.HazardDirectShare")), Spacing(TEXT("ss.HazardArrivalSpacing"));
    if (!TestNotNull(TEXT("Resolve trajectory mode"), Trajectory.Variable) ||
        !TestNotNull(TEXT("Resolve hazard speed"), Speed.Variable) ||
        !TestNotNull(TEXT("Resolve direct share"), DirectShare.Variable) ||
        !TestNotNull(TEXT("Resolve arrival spacing"), Spacing.Variable))
        return false;
    Trajectory.Set(1.f);
    Speed.Set(3.f);
    Spacing.Set(2.f);

    struct FApproach
    {
        double ClosestTime = 0.;
        double ClosestDistance = 0.;
        double FirstContact = 0.;
        double LastContact = 0.;
        bool bHit = false;
    };
    // Independent sphere-surface intersection, not the placer's selected arrival time. This fixture has
    // no BeginPlay/physics hull; its actual contact geometry is the ship's classic collision sphere.
    auto Approach = [](const ASSWorldBody *Body, const ASSShip *Ship)
    {
        FApproach Result;
        const FVector Relative = Body->GetActorLocation() - Ship->GetActorLocation();
        const FVector Velocity = Body->GetVelocity() - Ship->GetVelocity();
        const double Contact = Body->GetBodyRadius() + Ship->Collision->GetScaledSphereRadius();
        const double A = Velocity.SizeSquared();
        const double B = 2. * FVector::DotProduct(Relative, Velocity);
        const double C = Relative.SizeSquared() - Contact * Contact;
        Result.ClosestTime = A > UE_SMALL_NUMBER ? FMath::Max(0., -B / (2. * A)) : 0.;
        Result.ClosestDistance = (Relative + Velocity * Result.ClosestTime).Size();
        if (C <= 0.)
            Result.bHit = true;
        else if (A > UE_SMALL_NUMBER)
        {
            const double Discriminant = B * B - 4. * A * C;
            if (Discriminant >= 0.)
            {
                const double First = (-B - FMath::Sqrt(Discriminant)) / (2. * A);
                Result.bHit = First >= 0.;
                Result.FirstContact = First;
                Result.LastContact = (-B + FMath::Sqrt(Discriminant)) / (2. * A);
            }
        }
        return Result;
    };
    auto SetDrift = [](FSSWreckageBudgetWorld &F, float WorldSpeed)
    {
        for (auto &Hazard : F.Mode->Tuning->Hazards)
            if (Hazard.Kind == ESSWorldKind::SmallAsteroid)
                Hazard.DriftSpeedMin = Hazard.DriftSpeedMax = WorldSpeed / 3.f;
    };

    for (bool bDirect : {true, false})
        for (int32 Scenario = 0; Scenario < 4; ++Scenario)
        {
            FSSWreckageBudgetWorld F;
            if (!F.Initialize(*this))
                return false;
            ASSShip *Ship = F.Director->FindShip();
            if (!TestNotNull(TEXT("Resolve trajectory fixture ship"), Ship))
                return false;
            const FVector Motion = Scenario == 0   ? FVector(-600.f, 0.f, 0.f)
                                   : Scenario == 1 ? FVector(0.f, 6000.f, 0.f)
                                                   : FVector(6000.f, 0.f, 0.f);
            const float HullRadius = Scenario == 3 ? 700.f : 105.f;
            Ship->Collision->SetSphereRadius(HullRadius);
            Ship->Velocity = Motion;
            DirectShare.Set(bDirect ? 1.f : 0.f);
            SetDrift(F, 600.f);
            int32 Admitted = 0;
            for (int32 Seed = 1; Seed <= 8; ++Seed)
            {
                F.Director->ResetEncounter();
                F.Director->Configure(1, false);
                F.Director->Random.Initialize(Seed);
                ASSWorldBody *Body = F.Director->SpawnHazard(ESSWorldKind::SmallAsteroid, -1.f);
                if (!Body)
                    continue; // Unsafe/too-slow relative trajectories may be rejected before admission.
                ++Admitted;
                const FApproach Pass = Approach(Body, Ship);
                const FString Label =
                    FString::Printf(TEXT("%s hull %.0f velocity %s seed %d"), bDirect ? TEXT("Direct") : TEXT("Miss"),
                                    HullRadius, *Motion.ToString(), Seed);
                if (bDirect)
                {
                    TestTrue(Label + TEXT(" hits an unanswered constant-velocity ship"), Pass.bHit);
                    if (Pass.bHit)
                        TestTrue(Label + TEXT(" first surface contact respects the reaction floor"),
                                 Pass.FirstContact + .001 >= F.Director->MinimumReactionSeconds);
                }
                else
                    TestFalse(Label + TEXT(" stays outside the collision surface"), Pass.bHit);
                TestTrue(Label + TEXT(" remains alive through closest approach"),
                         Body->LifetimeSeconds <= 0.f || Body->LifetimeSeconds + .001 >= Pass.ClosestTime);
            }
            if (Motion.X >= 0.f)
                TestTrue(TEXT("Normal forward/lateral motion still admits a viable trajectory"), Admitted > 0);
        }

    DirectShare.Set(1.f);
    for (int32 Removal = 0; Removal < 4; ++Removal)
    {
        FSSWreckageBudgetWorld F;
        if (!F.Initialize(*this))
            return false;
        ASSShip *Ship = F.Director->FindShip();
        if (!TestNotNull(TEXT("Resolve stopped fixture ship"), Ship))
            return false;
        Ship->Velocity = FVector::ZeroVector;
        F.Director->Configure(1, false);
        F.Director->Random.Initialize(17);
        // The 120 cm/s shot cannot reach a stopped ship during the authored 65-second lifetime. The
        // 200 cm/s shot can, and tests releasing its reservation on destruction and encounter reset.
        SetDrift(F, Removal == 0 ? 120.f : 200.f);
        ASSWorldBody *Slow = F.Director->SpawnHazard(ESSWorldKind::SmallAsteroid, -1.f);
        if (Slow)
        {
            const FApproach Pass = Approach(Slow, Ship);
            TestTrue(TEXT("An admitted slow direct shot reaches the unanswered ship"), Pass.bHit);
            TestTrue(TEXT("An admitted slow shot lives through closest approach"),
                     Slow->LifetimeSeconds <= 0.f || Slow->LifetimeSeconds + .001 >= Pass.ClosestTime);
        }
        else if (Removal != 0)
            AddError(TEXT("A viable stopped-ship shot is required to exercise reservation removal."));
        if (Removal == 1 && Slow)
        {
            Slow->SetActorLocation(FVector(-1000000, 0, 0));
            Slow->Destroy();
        }
        if (Removal == 2)
        {
            F.Director->ResetEncounter();
            F.Director->Configure(1, false);
        }
        SetDrift(F, 900.f);
        F.Director->Random.Initialize(29);
        ASSWorldBody *Fast = F.Director->SpawnHazard(ESSWorldKind::SmallAsteroid, -1.f);
        if (TestNotNull(TEXT("A later faster shot remains admissible"), Fast))
            TestTrue(Removal == 0   ? TEXT("A rejected or much later shot does not suppress an earlier direct shot")
                     : Removal == 1 ? TEXT("Destroyed shot releases its direct-arrival reservation")
                     : Removal == 2 ? TEXT("Encounter reset releases its direct-arrival reservation")
                                    : TEXT("A live later shot permits a safely separated earlier direct shot"),
                     Approach(Fast, Ship).bHit);
    }

    // Distinguish surface windows from centre timestamps: these centres pass more than ten seconds
    // apart, but the large body's leading surface follows the small body's trailing surface too closely.
    FSSWreckageBudgetWorld F, Control;
    if (!F.Initialize(*this) || !Control.Initialize(*this))
        return false;
    ASSShip *Ship = F.Director->FindShip();
    ASSShip *ControlShip = Control.Director->FindShip();
    if (!TestNotNull(TEXT("Resolve surface-window fixture ship"), Ship) ||
        !TestNotNull(TEXT("Resolve unreserved comparison ship"), ControlShip))
        return false;
    Ship->Velocity = ControlShip->Velocity = FVector::ZeroVector;
    F.Director->Configure(1, false);
    F.Director->Random.Initialize(23);
    SetDrift(F, 300.f);
    ASSWorldBody *Large = F.Director->SpawnHazard(ESSWorldKind::SmallAsteroid, 650.f);
    Control.Director->Configure(1, false);
    Control.Director->Random.Initialize(1);
    SetDrift(Control, 350.f);
    ASSWorldBody *Unreserved = Control.Director->SpawnHazard(ESSWorldKind::SmallAsteroid, -1.f);
    if (!TestNotNull(TEXT("Admit the large reserved shot"), Large) ||
        !TestNotNull(TEXT("Admit a direct comparison shot without a conflicting reservation"), Unreserved))
        return false;
    const FApproach LargePass = Approach(Large, Ship), SmallPass = Approach(Unreserved, ControlShip);
    TestTrue(TEXT("Both unopposed shots really intersect the ship"), LargePass.bHit && SmallPass.bHit);
    TestTrue(TEXT("Centre timestamps alone appear safely separated"),
             LargePass.ClosestTime - SmallPass.ClosestTime > 4.);
    TestTrue(TEXT("Actual surface-contact intervals violate the four-second spacing"),
             LargePass.FirstContact - SmallPass.LastContact < 4.);
    SetDrift(F, 350.f);
    int32 WindowCandidates = 0;
    for (int32 Seed = 1; Seed <= 8; ++Seed)
    {
        F.Director->Random.Initialize(Seed);
        ASSWorldBody *Candidate = F.Director->SpawnHazard(ESSWorldKind::SmallAsteroid, -1.f);
        if (!Candidate)
            continue;
        ++WindowCandidates;
        TestFalse(TEXT("A conflicting surface window is changed to a genuine miss"), Approach(Candidate, Ship).bHit);
        Candidate->SetActorLocation(FVector(-1000000, 0, 0));
        Candidate->Destroy();
    }
    TestTrue(TEXT("The surface-window case exercises an admitted alternative"), WindowCandidates > 0);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSWreckageBudgetAdmission, "SpaceSurvival.Integration.WreckageBudgetAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSWreckageBudgetAdmission::RunTest(const FString &)
{
    for (bool SpatialBlock : {false, true})
    {
        FSSWreckageBudgetWorld F;
        if (!F.Initialize(*this))
            return false;
        ASSWorldBody *Blocker = nullptr;
        const FString Label = SpatialBlock ? TEXT("Spatially blocked passage") : TEXT("Four-slot capacity rejection");
        if (SpatialBlock)
        {
            Blocker = F.World->SpawnActor<ASSWorldBody>(FVector(12000, 0, 0), FRotator::ZeroRotator);
            if (!TestNotNull(TEXT("Create actual hazard covering every candidate spawn"), Blocker))
                return false;
            Blocker->Configure(ESSWorldKind::MassiveAsteroid, 50000.f, 0.f, 6);
        }
        else
            F.Director->MaximumActiveThreats =
                3; // Outer cap permits an attempt; the four-piece reservation cannot fit.
        F.Step(1.f);
        F.Step();
        F.Step();
        TestEqual(Label + TEXT(" creates no wreckage"), F.WreckageCount(), 0);
        if (Blocker)
            Blocker->SetActorLocation(FVector(-1000000, 0, 0));
        F.Director->MaximumActiveThreats = 8;
        // No Configure, private budget access or budget accrual: successful retries
        // must spend the budget preserved through those failed production admissions.
        F.Step();
        TestEqual(Label + TEXT(" retains enough budget for all four pieces after removal"), F.WreckageCount(), 4);
        F.RemoveWreckage();
        F.Step();
        TestEqual(Label + TEXT(" charges the half-unit passage once, not once per chunk"), F.WreckageCount(), 4);
        F.RemoveWreckage();
        F.Step();
        TestEqual(Label + TEXT(" stops spending after the two successful passages exhaust the budget"),
                  F.WreckageCount(), 0);
    }

    FSSWreckageBudgetWorld Partial;
    if (!Partial.Initialize(*this))
        return false;
    for (auto &Hazard : Partial.Mode->Tuning->Hazards)
        if (Hazard.Kind == ESSWorldKind::Wreckage)
        {
            Hazard.PressureCost = 1.f;
            // The first chunk's radius blocks the other three existing candidates.
            // This exercises a real partial passage, rather than fabricating a success flag.
            Hazard.BreakableChunkRadius = 2000.f;
        }
    Partial.Step(1.f);
    TestEqual(TEXT("A partially admitted passage retains its one actual chunk"), Partial.WreckageCount(), 1);
    Partial.RemoveWreckage();
    Partial.Step();
    TestEqual(TEXT("A partial passage still spends its normal one-unit cost"), Partial.WreckageCount(), 0);
    return true;
}

// Every placer derives its lead from the ship's speed; retirement was one fixed radius. Tripling hazard speed
// moved the lead for a 4,300 climax gravity field to 17,775-23,275 at cruise, so the packaged Wave 10 fixture saw
// its required gravity well admitted, charged for and deleted on its first tick, and the compound front never
// formed. Boost did the same to asteroids, enemies, salvage caches and distress attackers. The pawn in this world
// has not begun play and cannot be given a velocity, so the dial and the authored lead stand in for ship speed.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAdmittedBodiesOutliveAdmission,
                                 "SpaceSurvival.Integration.AdmittedBodiesOutliveAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAdmittedBodiesOutliveAdmission::RunTest(const FString &)
{
    IConsoleVariable *Speed = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HazardSpeed"));
    if (!TestNotNull(TEXT("Resolve the Director's speed dial"), Speed))
        return false;
    const float DefaultRetire = GetDefault<ASSWorldBody>()->RetireDistance;
    const float SavedSpeed = Speed->GetFloat();
    // 450 is the floor FindSafeSpawn puts under the largest authored drift. One step past the quotient lands a
    // body of any radius beyond the default retirement radius while the ship is at rest.
    const float Dial = FMath::CeilToFloat(DefaultRetire / (450.f * 3.5f)) + 1.f;
    Speed->Set(Dial, ECVF_SetByCode);
    if (!FMath::IsNearlyEqual(Speed->GetFloat(), Dial))
    {
        AddError(TEXT("ss.HazardSpeed is pinned by the console or the command line; clear it before this test."));
        return false;
    }
    // Survives the tick after it was placed, and says why: the radius now covers where the body was put.
    auto Outlives = [&](ASSWorldBody *Body, const ASSShip *Ship, const FString &Label)
    {
        const double Distance = FVector::Dist(Body->GetActorLocation(), Ship->GetActorLocation());
        TestTrue(Label + TEXT(" was placed beyond the default retirement radius"), Distance > DefaultRetire);
        Body->Tick(0.f);
        Body->Tick(.1f);
        TestFalse(Label + TEXT(" survives the tick after it was placed"), Body->IsActorBeingDestroyed());
        TestTrue(Label + TEXT(" has a retirement radius that covers where it was placed"),
                 Body->RetireDistance > Distance);
    };
    auto Find = [](UWorld *World, ESSWorldKind Kind)
    {
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->GetKind() == Kind)
                return *It;
        return static_cast<ASSWorldBody *>(nullptr);
    };
    bool bResult = true;
    {
        FSSWreckageBudgetWorld F;
        bResult &= F.Initialize(*this);
        if (bResult)
        {
            const ASSShip *Ship = Cast<ASSShip>(F.World->GetFirstPlayerController()->GetPawn());
            F.Director->BaseBudgetPerSecond = 100.f;
            F.Director->Configure(10, true);
            // The compound block admits gravity, then an asteroid, then a pursuer, one per spawn tick.
            ASSWorldBody *Gravity = nullptr, *Asteroid = nullptr, *Pursuer = nullptr;
            for (int32 Attempt = 0; Attempt < 60 && !(Gravity && Asteroid && Pursuer); ++Attempt)
            {
                F.Step(1.f);
                Gravity = Find(F.World, ESSWorldKind::GravityAnomaly);
                Asteroid = Find(F.World, ESSWorldKind::MediumAsteroid);
                Pursuer = Find(F.World, ESSWorldKind::Pursuer);
            }
            bResult &= TestNotNull(TEXT("The Wave 10 climax admits its required gravity field"), Gravity) &&
                       TestNotNull(TEXT("The Wave 10 climax admits its required asteroid"), Asteroid) &&
                       TestNotNull(TEXT("The Wave 10 climax admits its required pursuer"), Pursuer);
            if (bResult)
            {
                Outlives(Gravity, Ship, TEXT("The required gravity field"));
                Outlives(Asteroid, Ship, TEXT("The required asteroid"));
                Outlives(Pursuer, Ship, TEXT("The required pursuer"));
                // Fields are not drawn during a climax. One that is lost has to be asked for again.
                Gravity->SetActorLocation(FVector(-1000000, 0, 0));
                Gravity->Destroy();
                ASSWorldBody *Replacement = nullptr;
                for (int32 Attempt = 0; Attempt < 60 && !Replacement; ++Attempt)
                {
                    F.Step(1.f);
                    Replacement = Find(F.World, ESSWorldKind::GravityAnomaly);
                }
                bResult &= TestNotNull(TEXT("A required gravity field that is lost is admitted again"), Replacement);
            }
        }
    }
    {
        FSSWreckageBudgetWorld F;
        if (F.Initialize(*this))
        {
            const ASSShip *Ship = Cast<ASSShip>(F.World->GetFirstPlayerController()->GetPawn());
            F.Step(1.f);
            int32 Chunks = 0;
            for (TActorIterator<ASSWorldBody> It(F.World); It; ++It)
                if (It->GetKind() == ESSWorldKind::Wreckage)
                    Outlives(*It, Ship, FString::Printf(TEXT("Passage chunk %d"), ++Chunks));
            bResult &= TestEqual(TEXT("The wreckage passage was admitted whole"), Chunks, 4);
        }
        else
            bResult = false;
    }
    for (ESSEncounterKind Kind : {ESSEncounterKind::SalvageCache, ESSEncounterKind::DistressCombat})
    {
        // Accepted during a boost, the course starts past the radius. The authored lead says so here.
        const TCHAR *Name = Kind == ESSEncounterKind::SalvageCache ? TEXT("Salvage") : TEXT("Distress");
        FSSWreckageBudgetWorld F;
        if (!F.Initialize(*this))
        {
            bResult = false;
            continue;
        }
        const ASSShip *Ship = Cast<ASSShip>(F.World->GetFirstPlayerController()->GetPawn());
        for (auto &Entry : F.Mode->Tuning->Encounters)
            Entry.ObjectiveLeadDistance = DefaultRetire + 1000.f;
        auto *Beacon = F.World->SpawnActor<ASSEncounterBeacon>(FVector(1500, 0, 0), FRotator::ZeroRotator);
        if (!TestNotNull(TEXT("Create the accepted signal"), Beacon))
        {
            bResult = false;
            continue;
        }
        Beacon->ConfigureEncounter(Kind, Kind == ESSEncounterKind::SalvageCache ? 2 : 7);
        Beacon->Tick(.1f);
        if (!TestTrue(FString::Printf(TEXT("%s signal is accepted"), Name), Beacon->TryAccept()))
        {
            bResult = false;
            continue;
        }
        int32 Objectives = 0;
        for (TActorIterator<ASSWorldBody> It(F.World); It; ++It)
            if (*It != Beacon)
                Outlives(*It, Ship, FString::Printf(TEXT("%s objective body %d"), Name, ++Objectives));
        bResult &= TestTrue(FString::Printf(TEXT("%s acceptance placed its objectives"), Name),
                            Objectives >= Beacon->GetObjectiveRemaining());
        // The signal the objectives report to must still exist when the ship is at the far end of the course.
        TestTrue(FString::Printf(TEXT("%s signal is kept for the length of its course"), Name),
                 Beacon->RetireDistance > DefaultRetire + DefaultRetire);
    }
    Speed->Set(SavedSpeed, ECVF_SetByCode);
    return bResult;
}
#endif
