#include "Misc/AutomationTest.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSWorldActors.h"
#include "SSPhase1Data.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSIsolatedTestWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FSSIsolatedTestWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FSSIsolatedTestWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationWalkerRecovery, "SpaceSurvival.Integration.StationWalkerRecovery",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationWalkerRecovery::RunTest(const FString &Parameters)
{
    // No game instance, BeginPlay, account initialization or platform saves.
    FSSIsolatedTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated world"), Fixture.World))
        return false;
    auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Create rotated hub"), Hub) || !TestNotNull(TEXT("Create walker"), Walker))
        return false;
    const FTransform HubTransform = Hub->GetActorTransform();
    const FVector DeckPosition = HubTransform.TransformPosition(FVector(-1200, 0, 180));
    Walker->SetActorLocation(DeckPosition);
    Walker->Tick(1.f / 60.f);
    TestTrue(TEXT("Ordinary deck position is unchanged"), Walker->GetActorLocation().Equals(DeckPosition, .01));

    const FVector Escapes[] = {FVector(-1800, 0, 180), FVector(1800, 0, 180), FVector(0, 1500, 180),
                               FVector(0, -1500, 180), FVector(0, 0, -300)};
    for (const FVector &Local : Escapes)
    {
        Walker->SetActorLocation(HubTransform.TransformPosition(Local));
        Walker->GetCharacterMovement()->Velocity = FVector(500, 0, -900);
        Walker->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
        Walker->Tick(1.f / 60.f);
        TestTrue(TEXT("Escaped walker returns to the rotated hub spawn"),
                 Walker->GetActorLocation().Equals(Hub->WalkSpawn(), .01));
        TestTrue(TEXT("Recovery clears falling momentum"), Walker->GetVelocity().IsNearlyZero());
        TestTrue(TEXT("Recovery restores walking"), Walker->GetCharacterMovement()->MovementMode == MOVE_Walking);
    }
    const FVector Exit = HubTransform.TransformPosition(FVector(650, -350, 100));
    Walker->BeginDisembark(HubTransform.TransformPosition(FVector(850, 0, 320)), Exit, Hub->GetActorRotation());
    Walker->Tick(1.4f);
    TestTrue(TEXT("Normal disembark still reaches its authored exit"), Walker->GetActorLocation().Equals(Exit, .01));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSLateEventAcceptance, "SpaceSurvival.Integration.LateEventAcceptance",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSLateEventAcceptance::RunTest(const FString &Parameters)
{
    for (ESSEncounterKind Kind : {ESSEncounterKind::SalvageCache, ESSEncounterKind::DistressCombat})
    {
        // Exercise real objective actors and weak-owner completion callbacks in a
        // transient world; no production save or account adapter is instantiated.
        FSSIsolatedTestWorld Fixture;
        if (!TestNotNull(TEXT("Create isolated event world"), Fixture.World))
            return false;
        auto *Controller = Fixture.World->SpawnActor<APlayerController>();
        auto *Ship = Fixture.World->SpawnActor<ASSShip>();
        auto *Beacon = Fixture.World->SpawnActor<ASSEncounterBeacon>();
        if (!TestNotNull(TEXT("Create event controller"), Controller) ||
            !TestNotNull(TEXT("Create event ship"), Ship) || !TestNotNull(TEXT("Create event beacon"), Beacon))
            return false;
        Fixture.World->AddController(Controller);
        Controller->Possess(Ship);
        if (!TestTrue(TEXT("Event resolves the possessed player ship"),
                      UGameplayStatics::GetPlayerPawn(Beacon, 0) == Ship))
            return false;
        Beacon->ConfigureEncounter(Kind, Kind == ESSEncounterKind::SalvageCache ? 2 : 7);
        Beacon->LifetimeSeconds = 1.f;
        Beacon->Tick(.9f);
        if (!TestTrue(TEXT("Accept just before the offer expires"), Beacon->TryAccept()))
            return false;
        const float ObjectiveDuration = GetDefault<USSPhase1Data>()->Encounter(Kind).ObjectiveDuration;
        Beacon->Tick(ObjectiveDuration - 1.f);
        if (!TestFalse(TEXT("Accepted signal survives its original offer expiry"), Beacon->IsActorBeingDestroyed()))
            return false;
        TestFalse(TEXT("Objective remains live until its own deadline"), Beacon->IsResolved());
        if (Kind == ESSEncounterKind::SalvageCache)
        {
            TArray<ASSPickup *> Caches;
            for (TActorIterator<ASSPickup> It(Fixture.World); It; ++It)
                Caches.Add(*It);
            TestEqual(TEXT("Acceptance spawned every salvage objective"), Caches.Num(),
                      Beacon->GetObjectiveRemaining());
            for (ASSPickup *Cache : Caches)
            {
                Ship->SetActorLocation(Cache->GetActorLocation());
                Cache->Tick(0.f);
            }
        }
        else
        {
            TArray<ASSEnemy *> Attackers;
            for (TActorIterator<ASSEnemy> It(Fixture.World); It; ++It)
                Attackers.Add(*It);
            TestEqual(TEXT("Acceptance spawned every combat objective"), Attackers.Num(),
                      Beacon->GetObjectiveRemaining());
            for (ASSEnemy *Enemy : Attackers)
                Enemy->ReceiveWeaponHit(100000.f);
        }
        TestTrue(TEXT("Actual objective completion resolves a late-accepted event"), Beacon->IsResolved());
        TestEqual(TEXT("All objective callbacks reached their surviving owner"), Beacon->GetObjectiveRemaining(), 0);
    }
    return true;
}
#endif
