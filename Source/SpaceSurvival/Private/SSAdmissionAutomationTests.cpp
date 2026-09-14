#include "Misc/AutomationTest.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "SSPhase1Data.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSAdmissionWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    APlayerController *Controller = nullptr;
    ASSShip *Ship = nullptr;
    FSSAdmissionWorld()
    {
        if (!World)
            return;
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        Controller = World->SpawnActor<APlayerController>();
        Ship = World->SpawnActor<ASSShip>();
        if (Controller && Ship)
        {
            World->AddController(Controller);
            Controller->Possess(Ship);
        }
    }
    ~FSSAdmissionWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
    int32 Count(ESSWorldKind Kind) const
    {
        int32 Result = 0;
        for (TActorIterator<ASSWorldBody> It(World); It; ++It)
            if (!It->IsActorBeingDestroyed() && It->GetKind() == Kind)
                ++Result;
        return Result;
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSClimaxAdmission, "SpaceSurvival.Integration.RequiredClimaxAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSClimaxAdmission::RunTest(const FString &Parameters)
{
    // No GameInstance, BeginPlay, settings initialization or production save access.
    FSSAdmissionWorld Fixture;
    if (!TestNotNull(TEXT("Create admission world"), Fixture.World) ||
        !TestNotNull(TEXT("Possessed flight ship"), Fixture.Ship))
        return false;
    auto *Owner = Fixture.World->SpawnActor<AActor>();
    auto *Director = NewObject<USSSurvivalDirectorComponent>(Owner);
    Director->RegisterComponent();
    Director->Configure(10, true);
    Director->SetActive(true);
    Director->BaseBudgetPerSecond = 0.f;
    for (int32 I = 0; I < 3; ++I)
        Director->TickComponent(1.3f, LEVELTICK_All, nullptr);
    TestEqual(TEXT("Required gravity cannot bypass its pressure cost"), Director->GetActiveThreatCount(), 0);

    Director->BaseBudgetPerSecond = 100.f;
    Director->TickComponent(1.3f, LEVELTICK_All, nullptr);
    TestEqual(TEXT("First paid component is gravity"), Fixture.Count(ESSWorldKind::GravityAnomaly), 1);
    TestEqual(TEXT("Admission uses one normal spawn opportunity"), Director->GetActiveThreatCount(), 1);
    Director->MaximumActiveThreats = 1;
    Director->TickComponent(1.3f, LEVELTICK_All, nullptr);
    TestEqual(TEXT("Required composition respects occupied threat capacity"), Director->GetActiveThreatCount(), 1);
    Director->MaximumActiveThreats = 24;
    Director->TickComponent(1.3f, LEVELTICK_All, nullptr);
    TestEqual(TEXT("Asteroid component retries after capacity is available"),
              Fixture.Count(ESSWorldKind::MediumAsteroid), 1);
    Director->TickComponent(1.3f, LEVELTICK_All, nullptr);
    TestEqual(TEXT("Enemy component follows without depending on the random mixture"),
              Fixture.Count(ESSWorldKind::Pursuer), 1);
    TestEqual(TEXT("All three required components coexist within the normal cap"), Director->GetActiveThreatCount(), 3);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSObjectiveAdmission, "SpaceSurvival.Integration.ObjectiveRouteAdmission",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSObjectiveAdmission::RunTest(const FString &Parameters)
{
    for (ESSEncounterKind Kind : {ESSEncounterKind::SalvageCache, ESSEncounterKind::DistressCombat})
    {
        FSSAdmissionWorld Fixture;
        if (!TestNotNull(TEXT("Create objective world"), Fixture.World) ||
            !TestNotNull(TEXT("Possessed objective ship"), Fixture.Ship))
            return false;
        auto *Beacon = Fixture.World->SpawnActor<ASSEncounterBeacon>();
        auto *Obstacle = Fixture.World->SpawnActor<ASSWorldBody>(FVector(8000, 650, 0), FRotator::ZeroRotator);
        if (!TestNotNull(TEXT("Create optional beacon"), Beacon) ||
            !TestNotNull(TEXT("Create route obstruction"), Obstacle))
            return false;
        Beacon->ConfigureEncounter(Kind, Kind == ESSEncounterKind::SalvageCache ? 2 : 7);
        Obstacle->Configure(ESSWorldKind::MassiveAsteroid, 20000.f, 0.f);
        TestFalse(TEXT("Completely obstructed formation is not accepted"), Beacon->TryAccept());
        TestFalse(TEXT("Rejected route leaves acceptance uncommitted"), Beacon->IsAccepted());
        TestEqual(TEXT("Rejected route creates no objectives"), Beacon->GetObjectiveRemaining(), 0);
        TestEqual(TEXT("Rejected route creates no caches"), Fixture.Count(ESSWorldKind::Pickup), 0);
        TestEqual(TEXT("Rejected route creates no enemies"),
                  Fixture.Count(ESSWorldKind::Pursuer) + Fixture.Count(ESSWorldKind::Flanker), 0);

        Obstacle->Configure(ESSWorldKind::MassiveAsteroid, 650.f, 0.f);
        if (!TestTrue(TEXT("A bounded alternate formation avoids an obstruction"), Beacon->TryAccept()))
            return false;
        TArray<FVector> Caches;
        for (TActorIterator<ASSWorldBody> It(Fixture.World); It; ++It)
        {
            if (*It == Obstacle || (!It->IsSolidHazard() && !It->IsEnemy() && It->GetKind() != ESSWorldKind::Pickup))
                continue;
            TestTrue(TEXT("Accepted objective actors do not overlap the existing obstacle"),
                     FVector::Dist(It->GetActorLocation(), Obstacle->GetActorLocation()) >=
                         It->GetBodyRadius() + Obstacle->GetBodyRadius() + 420.f);
            if (It->GetKind() == ESSWorldKind::Pickup)
                Caches.Add(It->GetActorLocation());
        }
        Caches.Sort([](const FVector &A, const FVector &B) { return A.X < B.X; });
        FVector Previous = Fixture.Ship->GetActorLocation();
        for (const FVector &Cache : Caches)
        {
            TestTrue(TEXT("The entire cache approach remains clear of existing solid geometry"),
                     FMath::PointDistToSegment(Obstacle->GetActorLocation(), Previous, Cache) >= 120.f + 650.f + 420.f);
            Previous = Cache;
        }
    }
    return true;
}
#endif
