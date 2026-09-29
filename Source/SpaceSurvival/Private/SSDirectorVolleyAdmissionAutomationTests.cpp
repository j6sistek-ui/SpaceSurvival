#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "Camera/CameraComponent.h"
#include "Components/SphereComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSVolleyAdmissionWorld
{
    UWorld *World = nullptr;
    USSGameInstance *Instance = nullptr;
    ASSGameMode *Mode = nullptr;
    ASSShip *Ship = nullptr;
    USSSurvivalDirectorComponent *Director = nullptr;

    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create isolated volley admission world"), World))
            return false;
        auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        // No GameInstance Init, world BeginPlay, save calls or licensed ship setup.
        Instance->AccountStorageBlocked = true;
        Instance->Session.settings.masterVolume = 0.;
        Context.OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
        if (!Test.TestTrue(TEXT("Install actual volley content owner"), World->SetGameMode(FURL())))
            return false;
        Mode = World->GetAuthGameMode<ASSGameMode>();
        if (!Test.TestNotNull(TEXT("Resolve volley GameMode"), Mode))
            return false;
        Mode->Tuning = NewObject<USSPhase1Data>(Mode);
        auto *Controller = World->SpawnActor<APlayerController>();
        Ship = World->SpawnActor<ASSShip>();
        if (!Test.TestNotNull(TEXT("Create stopped flight pawn"), Ship) ||
            !Test.TestNotNull(TEXT("Create local volley controller"), Controller))
            return false;
        Controller->SetAsLocalPlayerController();
        World->AddController(Controller);
        Controller->Possess(Ship);
        if (!Test.TestTrue(TEXT("Start only an in-memory volley run"), Instance->Session.StartRun("volley-admission")))
            return false;
        Director = Mode->Director;
        Director->MaximumActiveThreats = 24;
        Director->BaseBudgetPerSecond = 0.f;
        auto &Content = Mode->Tuning->DirectorContent;
        Content.EnemyChance = Content.FieldChance = 0.f;
        Content.WreckageSelectionStart = 1.f;
        Content.BudgetCapacity = 30.f;
        Content.SpawnIntervalMin = Content.SpawnIntervalMax = .1f;
        for (auto &Hazard : Mode->Tuning->Hazards)
        {
            Hazard.SelectionWeight = Hazard.Kind == ESSWorldKind::SmallAsteroid ? 1.f : 0.f;
            // A stopped ship still sees this formation before its authored lifetime ends.
            Hazard.DriftSpeedMin = Hazard.DriftSpeedMax = 200.f;
        }
        Reset();
        return true;
    }
    void Reset(int32 Wave = 10)
    {
        Director->ResetEncounter();
        Director->Configure(Wave, false);
        Director->SetActive(true);
    }
    void Tune(float SmallCost, float MediumCost, float MediumLifetime = 65.f)
    {
        for (auto &Hazard : Mode->Tuning->Hazards)
            if (Hazard.Kind == ESSWorldKind::SmallAsteroid)
                Hazard.PressureCost = SmallCost;
            else if (Hazard.Kind == ESSWorldKind::MediumAsteroid)
            {
                Hazard.PressureCost = MediumCost;
                Hazard.Lifetime = MediumLifetime;
            }
    }
    TArray<ASSWorldBody *> Rocks() const
    {
        TArray<ASSWorldBody *> Result;
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->bDirectorAsteroid && It->IsSolidHazard())
                Result.Add(*It);
        return Result;
    }
    float RockCost() const
    {
        float Result = 0.f;
        for (const ASSWorldBody *Body : Rocks())
            Result += FMath::Max(.1f, Mode->Tuning->Hazard(Body->GetKind()).PressureCost);
        return Result;
    }
    ~FSSVolleyAdmissionWorld()
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDirectorVolleyAdmission, "SpaceSurvival.Integration.DirectorVolleyAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDirectorVolleyAdmission::RunTest(const FString &)
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
    };
    FScopedDial Volley(TEXT("ss.HazardVolley")), Trajectory(TEXT("ss.HazardTrajectory")), Speed(TEXT("ss.HazardSpeed")),
        Count(TEXT("ss.HazardCount"));
    if (!TestNotNull(TEXT("Resolve volley chance"), Volley.Variable) ||
        !TestNotNull(TEXT("Resolve trajectory dial"), Trajectory.Variable) ||
        !TestNotNull(TEXT("Resolve speed dial"), Speed.Variable) ||
        !TestNotNull(TEXT("Resolve threat cap"), Count.Variable))
        return false;
    Volley.Variable->SetWithCurrentPriority(1.f);
    Trajectory.Variable->SetWithCurrentPriority(1);
    Speed.Variable->SetWithCurrentPriority(3.f);
    Count.Variable->SetWithCurrentPriority(40);
    FSSVolleyAdmissionWorld F;
    if (!F.Initialize(*this))
        return false;
    F.Tune(2.25f, 4.5f);
    F.Director->Random.Initialize(1);
    float Spent = -1.f;
    const int32 FullCount = F.Director->SpawnVolley(3, 30.f, &Spent);
    if (!TestEqual(TEXT("A clear three-slot formation is admitted whole"), FullCount, 3))
        return false;
    const float FullCost = F.RockCost();
    TestEqual(TEXT("Returned cost equals the authored cost of actual spawned kinds"), Spent, FullCost);
    TestTrue(TEXT("The regression uses costs that differ from one unit per rock"), FullCost > FullCount);
    ASSWorldBody *Ring = nullptr;
    for (ASSWorldBody *Body : F.Rocks())
        if (Body->GetKind() == ESSWorldKind::MediumAsteroid)
            Ring = Body;
    if (!TestNotNull(TEXT("This deterministic formation contains a medium ring member"), Ring))
        return false;
    const FVector BlockedPosition = Ring->GetActorLocation();
    const float BlockedCost = F.Mode->Tuning->Hazard(Ring->GetKind()).PressureCost;

    F.Reset();
    F.Director->Random.Initialize(1);
    TestEqual(TEXT("The exact aggregate budget buys the same complete formation"),
              F.Director->SpawnVolley(3, FullCost, &Spent), FullCount);
    TestEqual(TEXT("Exact-budget admission charges the exact authored cost"), Spent, FullCost);
    F.Reset();
    F.Director->Random.Initialize(1);
    TestEqual(TEXT("An unaffordable formation is refused before actors are created"),
              F.Director->SpawnVolley(3, FullCost - .25f, &Spent), 0);
    TestEqual(TEXT("Refusal reports no charge"), Spent, 0.f);
    TestEqual(TEXT("Refusal leaves no partial formation"), F.Rocks().Num(), 0);
    TestEqual(TEXT("Refusal reserves no future direct hit"), F.Director->DirectArrivals.Num(), 0);

    auto *Blocker = F.World->SpawnActor<ASSWorldBody>(BlockedPosition, FRotator::ZeroRotator);
    if (!TestNotNull(TEXT("Place real cover at one ring slot"), Blocker))
        return false;
    Blocker->Configure(ESSWorldKind::Wreckage, 10.f, 0.f);
    F.Director->Random.Initialize(1);
    TestEqual(TEXT("Clear members can use the exact remaining budget when one slot is blocked"),
              F.Director->SpawnVolley(3, FullCost - BlockedCost, &Spent), FullCount - 1);
    TestEqual(TEXT("The blocked slot is not charged"), Spent, FullCost - BlockedCost);
    TestEqual(TEXT("Partial admission reports actual spawned cost"), Spent, F.RockCost());
    Blocker->Destroy();

    F.Reset();
    F.Tune(2.25f, 4.5f, 1.f);
    F.Director->Random.Initialize(1);
    TestEqual(TEXT("A ring member expiring before the pass refuses the whole formation"),
              F.Director->SpawnVolley(3, 30.f, &Spent), 0);
    TestEqual(TEXT("Lifetime refusal costs nothing"), Spent, 0.f);
    TestEqual(TEXT("Lifetime refusal leaves no actors or partial target"), F.Rocks().Num(), 0);
    TestEqual(TEXT("Lifetime refusal creates no direct reservation"), F.Director->DirectArrivals.Num(), 0);
    TestEqual(TEXT("Admission does not extend authored ring lifetime"),
              F.Mode->Tuning->Hazard(ESSWorldKind::MediumAsteroid).Lifetime, 1.f);
    F.Tune(2.25f, 4.5f);

    for (bool Affordable : {true, false})
    {
        F.Reset(1);
        const float Budget = Affordable ? 20.f : 2.25f;
        F.Director->AvailableBudget = Budget;
        F.Director->Random.Initialize(1);
        F.Director->TickComponent(1.f, LEVELTICK_All, nullptr);
        TestEqual(TEXT("Production admission subtracts the actual spawned costs"), F.Director->AvailableBudget,
                  Budget - F.RockCost());
        if (Affordable)
            TestTrue(TEXT("Affordable production admission retains its volley"), F.Rocks().Num() > 1);
        else
        {
            TestEqual(TEXT("An unaffordable volley falls back to one affordable ordinary asteroid"), F.Rocks().Num(),
                      1);
            TestEqual(TEXT("Fallback spends its own authored cost exactly once"), F.Director->AvailableBudget, 0.f);
        }
    }

    // Exercise actual Fire plus the projectile sweep and damage path, not ReceiveWeaponHit directly. This is
    // a cannon-response fixture; physical trigger input and the player's ability to aim remain playtest work.
    F.Reset();
    F.Director->Random.Initialize(1);
    if (!TestEqual(TEXT("Admit the formation for its cannon response"), F.Director->SpawnVolley(3, 30.f, &Spent), 3))
        return false;
    auto ClosestDistance = [&](const ASSWorldBody *Body)
    {
        const FVector Relative = Body->GetActorLocation() - F.Ship->GetActorLocation();
        const FVector Velocity = Body->GetVelocity() - F.Ship->GetVelocity();
        const double Time = FMath::Max(0., -FVector::DotProduct(Relative, Velocity) / Velocity.SizeSquared());
        return (Relative + Velocity * Time).Size();
    };
    ASSWorldBody *Target = nullptr;
    for (ASSWorldBody *Body : F.Rocks())
        if (ClosestDistance(Body) < Body->GetBodyRadius() + F.Ship->Collision->GetScaledSphereRadius())
            Target = Body;
    if (!TestNotNull(TEXT("Find the live rock on the collision course"), Target))
        return false;
    F.Instance->Session.run.weapon = SS::Weapon::HeavyCannon;
    F.Ship->Tuning = F.Mode->Tuning;
    const FRotator Aim = (Target->GetActorLocation() - F.Ship->GetActorLocation()).Rotation();
    F.Ship->SetActorRotation(Aim);
    F.Ship->Camera->SetWorldLocationAndRotation(F.Ship->GetActorLocation(), Aim);
    F.Ship->Fire();
    ASSProjectile *Shot = nullptr;
    for (TActorIterator<ASSProjectile> It(F.World); It; ++It)
        if (!It->IsActorBeingDestroyed())
            Shot = *It;
    if (!TestNotNull(TEXT("Actual ship Fire launches the equipped cannon projectile"), Shot))
        return false;
    for (int32 Step = 0; Step < 50 && !Shot->IsActorBeingDestroyed(); ++Step)
    {
        for (ASSWorldBody *Body : F.Rocks())
            Body->Tick(.02f);
        Shot->Tick(.02f);
    }
    TestTrue(TEXT("A real cannon projectile destroys the approaching centre rock"), Target->IsActorBeingDestroyed());
    TestTrue(TEXT("The cannon projectile is consumed by the contact"), Shot->IsActorBeingDestroyed());
    TestEqual(TEXT("Shooting the centre preserves the two fencing rocks"), F.Rocks().Num(), 2);
    for (const ASSWorldBody *Body : F.Rocks())
        TestTrue(TEXT("Every surviving ring member still misses the unchanged coasting path"),
                 ClosestDistance(Body) > Body->GetBodyRadius() + F.Ship->Collision->GetScaledSphereRadius());
    // Verify the opening with the starter laser as well. Two separately permitted trigger calls exercise
    // actual muzzle traces and normal weapon damage; a zero fixture-only interval avoids testing cadence here.
    FSSVolleyAdmissionWorld Laser;
    if (!Laser.Initialize(*this))
        return false;
    Laser.Tune(1.f, 1.f);
    Laser.Director->Random.Initialize(1);
    if (!TestEqual(TEXT("Admit a volley for the starter laser response"), Laser.Director->SpawnVolley(3), 3))
        return false;
    ASSWorldBody *LaserTarget = Laser.Director->DirectArrivals[0].Body.Get();
    if (!TestNotNull(TEXT("Resolve the admitted laser target"), LaserTarget))
        return false;
    Laser.Instance->Session.run.weapon = SS::Weapon::RapidLaser;
    Laser.Ship->Tuning = Laser.Mode->Tuning;
    Laser.Ship->Tuning->LaserInterval = 0.f;
    const FRotator LaserAim = (LaserTarget->GetActorLocation() - Laser.Ship->GetActorLocation()).Rotation();
    Laser.Ship->SetActorRotation(LaserAim);
    Laser.Ship->Camera->SetWorldLocationAndRotation(Laser.Ship->GetActorLocation(), LaserAim);
    Laser.Ship->Fire();
    TestFalse(TEXT("The centre survives the first normal starter-laser hit"), LaserTarget->IsActorBeingDestroyed());
    Laser.Ship->Fire();
    TestTrue(TEXT("Two actual starter-laser traces destroy the centre"), LaserTarget->IsActorBeingDestroyed());
    TestEqual(TEXT("The laser clears the centre while preserving the ring"), Laser.Rocks().Num(), 2);
    return true;
}
#endif
