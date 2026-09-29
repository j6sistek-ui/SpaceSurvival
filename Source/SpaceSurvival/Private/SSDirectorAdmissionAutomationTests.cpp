#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "SSDirectorVillain.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Components/SphereComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
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
    // Only wreckage is on offer here. A refused passage now falls through to an asteroid, which is a separate
    // admission paid from the same budget; DirectorAdmissionFallThrough covers that. With no asteroid weight
    // the fall-through finds nothing, so this still measures what a refused passage itself costs.
    auto OfferOnlyWreckage = [](FSSWreckageBudgetWorld &F)
    {
        for (auto &Hazard : F.Mode->Tuning->Hazards)
            if (Hazard.Kind == ESSWorldKind::SmallAsteroid || Hazard.Kind == ESSWorldKind::MediumAsteroid ||
                Hazard.Kind == ESSWorldKind::MassiveAsteroid)
                Hazard.SelectionWeight = 0.f;
    };
    for (bool SpatialBlock : {false, true})
    {
        FSSWreckageBudgetWorld F;
        if (!F.Initialize(*this))
            return false;
        OfferOnlyWreckage(F);
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
    OfferOnlyWreckage(Partial);
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

// The Wave 5 climax asks for an enemy every interval. Once its five were alive every request was refused, each
// refusal ended its interval, and the rest of the climax admitted nothing: 0 asteroids in roughly 35 of its 40
// seconds. A refusal now passes its interval to an asteroid. Saving for an enemy it cannot yet afford still
// waits, so the climax keeps its hunters. The dial-off rows are the old chain, and prove the check can fail.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorAdmissionFallThrough,
                                 "SpaceSurvival.Integration.DirectorAdmissionFallThrough",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorAdmissionFallThrough::RunTest(const FString &)
{
    IConsoleVariable *FallThrough = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.AdmissionFallThrough"));
    IConsoleVariable *Trajectory = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HazardTrajectory"));
    if (!TestNotNull(TEXT("Resolve the fall-through dial"), FallThrough) ||
        !TestNotNull(TEXT("Resolve trajectory mode"), Trajectory))
        return false;
    const FString SavedFallThrough = FallThrough->GetString(), SavedTrajectory = Trajectory->GetString();
    Trajectory->SetWithCurrentPriority(1.f);
    auto Count = [](UWorld *World, std::initializer_list<ESSWorldKind> Kinds)
    {
        int32 Result = 0;
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            for (ESSWorldKind Kind : Kinds)
                if (!It->IsActorBeingDestroyed() && It->GetKind() == Kind)
                    ++Result;
        return Result;
    };
    const std::initializer_list<ESSWorldKind> Rocks = {ESSWorldKind::SmallAsteroid, ESSWorldKind::MediumAsteroid,
                                                       ESSWorldKind::MassiveAsteroid};
    const std::initializer_list<ESSWorldKind> Hunters = {ESSWorldKind::Pursuer, ESSWorldKind::Flanker};
    // A cruising pilot, so an aimed rock can reach the flight path inside its lifetime; five live hunters far
    // off the path fill the climax cap without standing in the way of anything admitted.
    auto Prepare = [&](FSSWreckageBudgetWorld &F, int32 Wave, int32 Hunting)
    {
        F.Director->FindShip()->Velocity = FVector(6000.f, 0.f, 0.f);
        F.Director->Configure(Wave, true);
        F.Director->MaximumActiveThreats = 24;
        for (int32 Index = 0; Index < Hunting; ++Index)
            F.World->SpawnActor<ASSEnemy>(FVector(-400000.f, Index * 6000.f, 0.f), FRotator::ZeroRotator);
    };
    bool bResult = true;
    for (int32 Dial : {1, 0})
    {
        FallThrough->SetWithCurrentPriority(float(Dial));
        const FString Label = Dial ? TEXT("With the fall-through") : TEXT("Old chain");
        {
            FSSWreckageBudgetWorld F;
            if (!F.Initialize(*this))
            {
                bResult = false;
                break;
            }
            Prepare(F, 5, 5);
            F.Director->BaseBudgetPerSecond = 100.f;
            TestFalse(Label + TEXT(": five live hunters fill the Wave 5 climax cap"), F.Director->HasEnemyRoom());
            int32 Admitted = 0;
            for (int32 Interval = 0; Interval < 4; ++Interval)
            {
                F.Step(1.f);
                Admitted += Count(F.World, Rocks);
                // Nothing ticks in this world, so admitted rocks would stay on the path and crowd out the next
                // one. Clearing them keeps each interval about the refusal, not about the room left.
                for (TActorIterator<ASSWorldBody> It(F.World); It; ++It)
                    if (It->GetKind() == ESSWorldKind::SmallAsteroid || It->GetKind() == ESSWorldKind::MediumAsteroid ||
                        It->GetKind() == ESSWorldKind::MassiveAsteroid)
                    {
                        It->SetActorLocation(FVector(-1000000, 0, 0));
                        It->Destroy();
                    }
            }
            if (Dial)
                TestEqual(Label + TEXT(": every refused climax enemy admits an asteroid in its own interval"), Admitted,
                          4);
            else
                TestEqual(Label + TEXT(": a full climax cap silences the interval (the September 28 stall)"), Admitted,
                          0);
            TestEqual(Label + TEXT(": no hunter is admitted past the climax cap"), Count(F.World, Hunters), 5);
        }
        {
            // The Wave 10 front asks for its required pursuer first, and returned on refusal as well.
            FSSWreckageBudgetWorld F;
            if (!F.Initialize(*this))
            {
                bResult = false;
                break;
            }
            Prepare(F, 10, 5);
            F.Director->BaseBudgetPerSecond = 100.f;
            auto *Field = F.World->SpawnActor<ASSWorldBody>(FVector(-400000.f, 0.f, 60000.f), FRotator::ZeroRotator);
            if (!TestNotNull(TEXT("Create the front's live gravity field"), Field))
            {
                bResult = false;
                break;
            }
            Field->Configure(ESSWorldKind::GravityAnomaly, 4300.f, 0.f, 10);
            F.Director->bCompoundGravitySpawned = F.Director->bCompoundAsteroidSpawned = true;
            F.Director->CompoundGravity = Field;
            const int32 Before = Count(F.World, Rocks) + Count(F.World, {ESSWorldKind::Wreckage});
            F.Step(1.f);
            const int32 Admitted = Count(F.World, Rocks) + Count(F.World, {ESSWorldKind::Wreckage}) - Before;
            if (Dial)
                TestTrue(Label + TEXT(": a required pursuer the cap refuses passes its interval on"), Admitted > 0);
            else
                TestEqual(Label + TEXT(": a refused required pursuer silenced the Wave 10 interval"), Admitted, 0);
            TestFalse(Label + TEXT(": the refused pursuer is still owed to the front"),
                      F.Director->bCompoundEnemySpawned);
        }
    }
    if (bResult)
    {
        // Saving is not a refusal: a free slot the budget cannot yet buy keeps the interval for the hunter.
        FallThrough->SetWithCurrentPriority(1.f);
        FSSWreckageBudgetWorld F;
        bResult = F.Initialize(*this);
        if (bResult)
        {
            Prepare(F, 5, 0);
            F.Director->BaseBudgetPerSecond = 0.f;
            F.Step(1.f);
            TestEqual(TEXT("Saving for a hunter admits no asteroid in its place"), Count(F.World, Rocks), 0);
            TestEqual(TEXT("Saving for a hunter keeps the whole budget"), F.Director->AvailableBudget, 1.f);
            F.Director->AvailableBudget = 3.f;
            F.Step(1.f);
            TestEqual(TEXT("The saved budget buys the hunter"), Count(F.World, Hunters), 1);
            TestEqual(TEXT("The hunter is bought instead of a rock, not beside one"), Count(F.World, Rocks), 0);
        }
    }
    FallThrough->SetWithCurrentPriority(*SavedFallThrough);
    Trajectory->SetWithCurrentPriority(*SavedTrajectory);
    return bResult;
}

// Owner decision, September 29: the villain launches the enemies, and an existing character rides his craft
// until the knight's files are named. A launch keeps every placement rule: a hidden or unplaced villain launches
// nothing, one inside the reaction lead hands the enemy to the ordinary placer, nothing starts inside a rock,
// and a hunter launched from his distance survives its first tick there. The rider is fitted in the world and
// stands on the craft, so the craft's scale never resizes him.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorVillainLaunch, "SpaceSurvival.Integration.DirectorVillainLaunch",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorVillainLaunch::RunTest(const FString &)
{
    IConsoleVariable *Launch = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.VillainLaunch"));
    if (!TestNotNull(TEXT("Resolve the villain launch dial"), Launch))
        return false;
    const FString SavedLaunch = Launch->GetString();
    Launch->SetWithCurrentPriority(1.f);
    // A villain on station ahead of the fixture ship, placed by his own first tick.
    auto Stage = [this](FSSWreckageBudgetWorld &F, ASSShip *&Ship, ASSDirectorVillain *&Villain)
    {
        Ship = F.Director->FindShip();
        Villain = F.World->SpawnActor<ASSDirectorVillain>();
        if (!TestNotNull(TEXT("Resolve the fixture ship"), Ship) || !TestNotNull(TEXT("Spawn the villain"), Villain))
            return false;
        Villain->SetPresent(true);
        Villain->Tick(.05f);
        return true;
    };
    bool bResult = true;
    {
        FSSWreckageBudgetWorld F;
        ASSShip *Ship = nullptr;
        ASSDirectorVillain *Villain = nullptr;
        bResult = F.Initialize(*this) && Stage(F, Ship, Villain);
        FVector Point;
        if (bResult)
        {
            Villain->SetPresent(false);
            TestFalse(TEXT("A hidden villain launches nothing"), ASSDirectorVillain::FindLaunchPoint(F.World, Point));
            Villain->SetPresent(true);
            TestFalse(TEXT("A villain not yet in his place launches nothing"),
                      ASSDirectorVillain::FindLaunchPoint(F.World, Point));
            Villain->Tick(.05f);
            bResult = TestTrue(TEXT("A placed villain offers his craft as the launch point"),
                               ASSDirectorVillain::FindLaunchPoint(F.World, Point));
        }
        if (bResult)
        {
            TestTrue(TEXT("The launch point is his craft"), Point.Equals(Villain->GetActorLocation(), 1.));
            ASSEnemy *Enemy = F.Director->SpawnEnemy(ESSWorldKind::Pursuer);
            bResult = TestNotNull(TEXT("Admit a launched hunter"), Enemy);
            if (bResult)
            {
                TestTrue(TEXT("The hunter leaves from his craft"), Enemy->GetActorLocation().Equals(Point, 1.));
                const double Distance = FVector::Dist(Enemy->GetActorLocation(), Ship->GetActorLocation());
                TestTrue(TEXT("His craft is beyond the default retirement radius"),
                         Distance > GetDefault<ASSWorldBody>()->RetireDistance);
                Enemy->Tick(0.f);
                Enemy->Tick(.1f);
                TestFalse(TEXT("A hunter launched from his distance survives its first ticks"),
                          Enemy->IsActorBeingDestroyed());
                TestTrue(TEXT("Its retirement radius covers where it was launched"), Enemy->RetireDistance > Distance);
                // A rock parked on his craft: the next hunter leaves beside it or is placed as before, never
                // inside it.
                auto *Rock = F.World->SpawnActor<ASSWorldBody>(Point, FRotator::ZeroRotator);
                if (TestNotNull(TEXT("Park a rock on the launch point"), Rock))
                {
                    Rock->Configure(ESSWorldKind::MassiveAsteroid, 650.f, 0.f, 6);
                    ASSEnemy *Beside = F.Director->SpawnEnemy(ESSWorldKind::Pursuer);
                    if (TestNotNull(TEXT("A crowded craft still admits the hunter"), Beside))
                        TestTrue(TEXT("A hunter never starts inside a rock"),
                                 FVector::Dist(Beside->GetActorLocation(), Rock->GetActorLocation()) >=
                                     Beside->GetBodyRadius() + Rock->GetBodyRadius() + 420.f - 1.f);
                }
            }
        }
    }
    for (int32 Case = 0; Case < 2 && bResult; ++Case)
    {
        // 0: a tuning that brings him inside the reaction lead. 1: the dial off. Both place as before.
        FSSWreckageBudgetWorld F;
        ASSShip *Ship = nullptr;
        ASSDirectorVillain *Villain = nullptr;
        bResult = F.Initialize(*this);
        if (!bResult)
            break;
        if (Case == 0)
        {
            F.Mode->Tuning->Villain.LeadDistance = 3000.f;
            F.Mode->Tuning->Villain.HeightOffset = F.Mode->Tuning->Villain.SwayAmplitude = 0.f;
        }
        else
            Launch->SetWithCurrentPriority(0.f);
        bResult = Stage(F, Ship, Villain);
        FVector Point;
        if (bResult && TestTrue(TEXT("The villain is on station"), ASSDirectorVillain::FindLaunchPoint(F.World, Point)))
        {
            ASSEnemy *Enemy = F.Director->SpawnEnemy(ESSWorldKind::Pursuer);
            const TCHAR *Why = Case == 0 ? TEXT("inside the reaction lead") : TEXT("with the launch dial off");
            if (TestNotNull(FString::Printf(TEXT("A hunter is still admitted %s"), Why), Enemy))
            {
                TestFalse(FString::Printf(TEXT("No hunter leaves his craft %s"), Why),
                          Enemy->GetActorLocation().Equals(Point, 1.));
                TestTrue(FString::Printf(TEXT("The ordinary placer keeps its reaction lead %s"), Why),
                         FVector::Dist(Enemy->GetActorLocation(), Ship->GetActorLocation()) >= 9000.f - 1.f);
            }
        }
        Launch->SetWithCurrentPriority(1.f);
    }
    if (bResult)
    {
        FSSWreckageBudgetWorld F;
        bResult = F.Initialize(*this);
        auto *Villain = bResult ? F.World->SpawnActor<ASSDirectorVillain>() : nullptr;
        bResult = bResult && TestNotNull(TEXT("Spawn the villain for his rider"), Villain);
        if (bResult)
        {
            // A tracked body stands in for the stand-in, so this holds on a clone without the licensed packs.
            auto &Data = F.Mode->Tuning->Villain;
            Data.RiderMeshPath = TEXT("/Game/SpaceSurvival/Character/SK_AcornautTailV2.SK_AcornautTailV2");
            Data.RiderClipPath.Empty();
            for (float CraftScale : {12.f, 3.f})
            {
                Data.FallbackCraftScale = CraftScale;
                Villain->ApplyDefinition();
                const USkeletalMesh *Body = Villain->Rider->GetSkeletalMeshAsset();
                if (!TestNotNull(TEXT("The named rider is worn"), Body))
                    break;
                TestTrue(TEXT("The rider is shown"), Villain->Rider->IsVisible());
                const FBoxSphereBounds Craft = Villain->Craft->Bounds;
                const FBoxSphereBounds Rider = Body->GetBounds().TransformBy(Villain->Rider->GetComponentTransform());
                const FString Scale = FString::Printf(TEXT(" (craft scale %.0f)"), CraftScale);
                TestTrue(TEXT("He stands his fitted height whatever the craft's scale") + Scale,
                         FMath::IsNearlyEqual(Rider.BoxExtent.Z * 2., double(Data.RiderHeight), 1.));
                TestTrue(
                    TEXT("His soles are on the top of the craft") + Scale,
                    FMath::IsNearlyEqual(Rider.Origin.Z - Rider.BoxExtent.Z, Craft.Origin.Z + Craft.BoxExtent.Z, 1.));
                TestTrue(TEXT("He stands over the craft's centre") + Scale,
                         FMath::Abs(Rider.Origin.X - Craft.Origin.X) <= 1. &&
                             FMath::Abs(Rider.Origin.Y - Craft.Origin.Y) <= 1.);
            }
            // Neither the knight nor a stand-in installed: the craft flies alone, with no empty or broken body.
            Data.RiderMeshPath.Empty();
            Data.StandInRiderMeshPath.Empty();
            Villain->ApplyDefinition();
            TestNull(TEXT("With no rider installed nobody is worn"), Villain->Rider->GetSkeletalMeshAsset());
            TestFalse(TEXT("With no rider installed nothing is shown"), Villain->Rider->IsVisible());
        }
    }
    Launch->SetWithCurrentPriority(*SavedLaunch);
    return bResult;
}

// Owner decision, September 29: the villain talks. Story beats always speak; chatter waits out his cooldown and
// chance; his caption never displaces an announcement or the pilot; the dial silences him; and the results
// panel carries his last word above the run's numbers.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorVillainVoice, "SpaceSurvival.Integration.DirectorVillainVoice",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorVillainVoice::RunTest(const FString &)
{
    // Selection, on lines written here so editing the authored script cannot break it.
    FSSVillainDefinition Voice;
    Voice.Lines = {FSSVillainLine(ESSVillainCue::WaveStart, 0, TEXT("any wave")),
                   FSSVillainLine(ESSVillainCue::WaveStart, 3, TEXT("wave three")),
                   FSSVillainLine(ESSVillainCue::Kill, 0, TEXT("first")),
                   FSSVillainLine(ESSVillainCue::Kill, 0, TEXT("second"))};
    FRandomStream Random(7);
    TestEqual(TEXT("A wave's own line replaces the any-wave line"),
              Voice.LineFor(ESSVillainCue::WaveStart, 3, Random, FString()), FString(TEXT("wave three")));
    TestEqual(TEXT("Other waves fall back to the any-wave line"),
              Voice.LineFor(ESSVillainCue::WaveStart, 4, Random, FString()), FString(TEXT("any wave")));
    TestTrue(TEXT("A cue with nothing written stays silent"),
             Voice.LineFor(ESSVillainCue::Retreat, 5, Random, FString()).IsEmpty());
    for (int32 Draw = 0; Draw < 8; ++Draw)
        TestEqual(TEXT("He never repeats the line he just said"),
                  Voice.LineFor(ESSVillainCue::Kill, 1, Random, TEXT("first")), FString(TEXT("second")));
    TestEqual(TEXT("Unless it is all he has for the moment"),
              Voice.LineFor(ESSVillainCue::WaveStart, 3, Random, TEXT("wave three")), FString(TEXT("wave three")));
    // The authored script: something for every cue, and every line short enough for one caption line.
    const FSSVillainDefinition Script;
    for (ESSVillainCue Cue :
         {ESSVillainCue::RunStart, ESSVillainCue::WaveStart, ESSVillainCue::Wormhole, ESSVillainCue::Climax,
          ESSVillainCue::Compound, ESSVillainCue::Retreat, ESSVillainCue::Finale, ESSVillainCue::LowHull,
          ESSVillainCue::Death, ESSVillainCue::Launch, ESSVillainCue::Hit, ESSVillainCue::Kill})
        TestFalse(FString::Printf(TEXT("Cue %d has an authored line"), int32(Cue)),
                  Script.LineFor(Cue, 1, Random, FString()).IsEmpty());
    for (int32 Wave = 2; Wave <= 9; ++Wave)
        TestFalse(FString::Printf(TEXT("Wave %d opens with a line"), Wave),
                  Script.LineFor(ESSVillainCue::WaveStart, Wave, Random, FString()).IsEmpty());
    for (const FSSVillainLine &Line : Script.Lines)
        TestTrue(FString::Printf(TEXT("\"%s\" fits one caption line"), *Line.Text), Line.Text.Len() <= 64);

    IConsoleVariable *Dial = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.VillainVoice"));
    FSSWreckageBudgetWorld F;
    if (!TestNotNull(TEXT("Resolve the villain voice dial"), Dial) || !F.Initialize(*this))
        return false;
    const FString SavedDial = Dial->GetString();
    Dial->SetWithCurrentPriority(1.f);
    auto &Villain = F.Mode->Tuning->Villain;
    Villain.ChatterChance = 1.f;
    F.Mode->Announce(TEXT("WAVE 3  |  Keep surviving"));
    F.Mode->React(TEXT("Steady."));
    const FString Announcement = F.Mode->Announcement, Reaction = F.Mode->PilotReaction;
    TestTrue(TEXT("A story cue speaks"), F.Mode->VillainSpeak(ESSVillainCue::Wormhole));
    TestTrue(TEXT("His caption is headed by his name"),
             F.Mode->VillainLine.StartsWith(Villain.DisplayName + TEXT(": ")));
    TestTrue(TEXT("His line stays up long enough to read"), F.Mode->VillainLineSeconds >= 3.5f);
    TestEqual(TEXT("He does not displace the announcement"), F.Mode->Announcement, Announcement);
    TestEqual(TEXT("He does not displace the pilot"), F.Mode->PilotReaction, Reaction);
    TestFalse(TEXT("Chatter waits out the cooldown after any line"), F.Mode->VillainSpeak(ESSVillainCue::Kill));
    TestTrue(TEXT("Story cues ignore the chatter cooldown"), F.Mode->VillainSpeak(ESSVillainCue::LowHull));
    const float Shown = F.Mode->VillainLineSeconds;
    F.Mode->UpdateThreatFeedback(1.f);
    TestEqual(TEXT("His caption counts down with the flight feedback"), F.Mode->VillainLineSeconds, Shown - 1.f, .001f);
    F.Mode->VillainChatterCooldown = 0.f;
    TestTrue(TEXT("Chatter speaks once the cooldown has run out"), F.Mode->VillainSpeak(ESSVillainCue::Kill));
    F.Mode->VillainChatterCooldown = 0.f;
    Villain.ChatterChance = 0.f;
    TestFalse(TEXT("A chatter chance of zero never speaks"), F.Mode->VillainSpeak(ESSVillainCue::Hit));
    Dial->SetWithCurrentPriority(0.f);
    TestFalse(TEXT("The voice dial silences even a story cue"), F.Mode->VillainSpeak(ESSVillainCue::Climax));
    Dial->SetWithCurrentPriority(*SavedDial);
    F.Mode->VillainEpitaph = TEXT("Sable: As promised.");
    F.Mode->OpenPanel(ESSPanel::Results);
    TestTrue(TEXT("The results panel carries his last word above the run's numbers"),
             F.Mode->PanelDetail.StartsWith(F.Mode->VillainEpitaph) && F.Mode->PanelDetail.Contains(TEXT("Score")));
    F.Mode->ClosePanel();
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
