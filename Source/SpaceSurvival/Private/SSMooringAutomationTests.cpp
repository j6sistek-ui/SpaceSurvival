#include "Misc/AutomationTest.h"
#include "SSGameInstance.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSWorldActors.h"
#include "GameFramework/PlayerController.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SphereComponent.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSMooringFeedback, "SpaceSurvival.Flight.MagneticMooringAndAssist",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSMooringFeedback::RunTest(const FString &)
{
    TestEqual(TEXT("Disabled cone leaves manual aim unchanged"), ASSShip::SoftAssistWeight(1.f, 0.f, .2f), 0.f);
    const float Edge = FMath::Cos(FMath::DegreesToRadians(5.f));
    TestEqual(TEXT("Outside cone has no assistance"), ASSShip::SoftAssistWeight(Edge - .01f, 5.f, .2f), 0.f);
    TestEqual(TEXT("Cone edge has no abrupt pull"), ASSShip::SoftAssistWeight(Edge, 5.f, .2f), 0.f);
    TestTrue(TEXT("Centre assistance capped at twenty percent"),
             FMath::IsNearlyEqual(ASSShip::SoftAssistWeight(1.f, 5.f, .2f), .2f));
    TestTrue(TEXT("Assistance decreases toward cone edge"),
             FMath::IsNearlyEqual(ASSShip::SoftAssistWeight((1.f + Edge) * .5f, 5.f, .2f), .1f, .001f));
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Isolated mooring world"), World))
        return false;
    auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    auto *Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    Instance->AddToRoot();
    Instance->AccountStorageBlocked = true;
    Instance->Session.settings.masterVolume = 0;
    Context.OwningGameInstance = Instance;
    World->SetGameInstance(Instance);
    Instance->Session.StartRun("mooring-test");
    auto *Ship = World->SpawnActor<ASSShip>();
    auto *Controller = World->SpawnActor<APlayerController>();
    World->AddController(Controller);
    Controller->Possess(Ship);
    if (TestNotNull(TEXT("Actual ship actor"), Ship))
    {
        Ship->Tuning = NewObject<USSPhase1Data>(Ship);
        const FVector Before = Ship->GetActorLocation();
        const double Shield = Instance->Session.run.shield;
        TestTrue(TEXT("Flying ship accepts magnetic mooring"), Ship->BeginMooring());
        Ship->SetFlightInput(FVector2D(1, 1), FVector2D(1, 1), 1.f, true, true);
        Ship->AddExternalForce(FVector(1000, 2000, 1000));
        Ship->RequestDodge();
        Ship->Fire();
        int32 Shots = 0;
        for (TActorIterator<ASSProjectile> It(World); It; ++It)
            ++Shots;
        TestEqual(TEXT("Mooring prevents weapon fire"), Shots, 0);
        Ship->Tick(.1f);
        TestTrue(TEXT("Hold suppresses movement, input, force and dodge"),
                 Ship->GetActorLocation().Equals(Before) && Ship->GetVelocity().IsNearlyZero());
        Ship->ReceiveDamage(10.f);
        TestTrue(TEXT("Mooring provides no damage immunity"), Instance->Session.run.shield < Shield);
        Ship->EndMooring();
        TestFalse(TEXT("Release clears mooring"), Ship->IsMoored());
        TestTrue(TEXT("Release restores forward cruise"), Ship->GetVelocity().X > 1000.f);
        const FVector Released = Ship->GetVelocity();
        Ship->EndMooring();
        TestTrue(TEXT("Repeated release is harmless"), Ship->GetVelocity().Equals(Released));
        for (ESSEncounterKind Kind : {ESSEncounterKind::SalvageCache, ESSEncounterKind::MobileDepot})
        {
            auto *Beacon = World->SpawnActor<ASSEncounterBeacon>(FVector(500, 0, 0), FRotator::ZeroRotator);
            if (!TestNotNull(TEXT("Spawn optional beacon"), Beacon))
                continue;
            Beacon->ConfigureEncounter(Kind, 3);
            const FVector Anchor = Beacon->GetActorLocation();
            Ship->SetActorLocation(FVector(100, 0, 0));
            Beacon->Tick(.1f);
            TestTrue(TEXT("Proximity leaves signal anchored"), Beacon->GetActorLocation().Equals(Anchor));
            TestFalse(TEXT("Proximity alone never accepts an event or depot"), Beacon->IsAccepted());
            Ship->SetActorLocation(FVector(200, 0, 0));
            Beacon->Tick(.1f);
            TestTrue(TEXT("Moving player does not drag the beacon"), Beacon->GetActorLocation().Equals(Anchor));
            if (Kind == ESSEncounterKind::MobileDepot)
            {
                TestTrue(TEXT("Explicit safe depot acceptance succeeds"), Beacon->TryAccept());
                TestTrue(TEXT("Acceptance engages magnetic hold"), Ship->IsMoored());
                TestFalse(TEXT("Repeated acceptance cannot extend the hold"), Beacon->TryAccept());
                Beacon->Tick(19.9f);
                TestTrue(TEXT("Hold remains active before limit"), Ship->IsMoored());
                Beacon->Tick(.2f);
                TestTrue(TEXT("Service timeout releases and resolves encounter"),
                         !Ship->IsMoored() && Beacon->IsResolved());
                TestFalse(TEXT("Resolved depot cannot be reused"), Beacon->TryAccept());
            }
            Beacon->Destroy();
        }
    }
    auto *Rock = World->SpawnActor<ASSWorldBody>(FVector(0, 0, 20000), FRotator(17, 25, 8));
    if (TestNotNull(TEXT("Spawn asteroid pivot fixture"), Rock))
    {
        Rock->Configure(ESSWorldKind::MediumAsteroid, 300.f, 0.f);
        const UStaticMesh *RockMesh = Rock->Visual->GetStaticMesh();
        if (RockMesh && RockMesh->GetPathName().StartsWith(TEXT("/Game/Asteroid_Library/")))
        {
            const float CollisionRadius = Rock->Collision->GetUnscaledSphereRadius();
            Rock->SetLinearVelocity(FVector(30, 10, 20));
            for (float Step : {0.f, 8.f, 16.f})
            {
                Rock->Tick(Step);
                const FVector VisibleCentre =
                    Rock->Visual->GetComponentTransform().TransformPosition(RockMesh->GetBounds().Origin);
                TestTrue(TEXT("Vendor bounds centre stays aligned during nonzero rotation and translation"),
                         VisibleCentre.Equals(Rock->GetActorLocation(), .01));
                TestEqual(TEXT("Presentation pivot repair preserves gameplay collision radius"),
                          Rock->Collision->GetUnscaledSphereRadius(), CollisionRadius);
            }
        }
        else
            AddWarning(TEXT("Vendor asteroid unavailable: rotating vendor-pivot regression skipped explicitly."));
    }
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    Instance->RemoveFromRoot();
    return true;
}
#endif
