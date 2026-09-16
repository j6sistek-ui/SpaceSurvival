#include "Misc/AutomationTest.h"
#include "SSAlienGallery.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSStation.h"
#include "SSPhase1Data.h"
#include "SSWorldActors.h"
#include "Components/PointLightComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/PackageName.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSAlienGalleryLifecycle, "SpaceSurvival.Integration.AlienGalleryLifecycle",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSAlienGalleryLifecycle::RunTest(const FString &Parameters)
{
    UWorld *Previous = GWorld;
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Create isolated gallery fixture"), World))
        return false;
    auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    auto *GI = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    GI->AddToRoot();
    GI->AccountStorageBlocked = true; // Never initialize disk-backed save/settings state.
    Context.OwningGameInstance = GI;
    World->SetGameInstance(GI);
    GWorld = World;
    World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
    World->SetGameMode(FURL());
    auto *GM = World->GetAuthGameMode<ASSGameMode>();
    GM->Tuning = NewObject<USSPhase1Data>(GM);
    World->InitializeActorsForPlay(FURL());
    auto *PC = World->SpawnActor<APlayerController>();
    PC->SetAsLocalPlayerController();
    World->AddController(PC);
    auto *Walker = World->SpawnActor<ASSWalker>(FVector(300, 200, 180), FRotator(0, 30, 0));
    PC->Possess(Walker);
    const FTransform Original = Walker->GetActorTransform();
    PC->SetControlRotation(FRotator(-15, 20, 0));
    const FRotator OriginalView = PC->GetControlRotation();
    auto *LightOwner = World->SpawnActor<AActor>();
    auto *Light = NewObject<UPointLightComponent>(LightOwner);
    LightOwner->SetRootComponent(Light);
    Light->RegisterComponent();
    Light->SetVisibility(true);
    LightOwner->SetActorEnableCollision(false);
    GI->Session.run.credits = 345;
    const std::string Run = SS::EncodeRun(GI->Session.run), Account = SS::EncodeAccount(GI->Session.account);
    auto *Gallery = GM->AlienGallery.Get();
    TestFalse(TEXT("Reject absent controller without entering evaluation"), Gallery->Enter(nullptr));
    GI->Session.run.phase = SS::Phase::Flight;
    TestFalse(TEXT("Cannot enter from an active flight phase"), Gallery->Enter(PC));
    GI->Session.run.phase = SS::Phase::Hangar;
    if (FPackageName::DoesPackageExist(USSAlienGallery::MapPath(false)))
    {
        TestTrue(TEXT("Request actual installed vendor showcase"), Gallery->Enter(PC));
        TestTrue(TEXT("Loading freezes run immediately"), Gallery->IsActive());
        TestFalse(TEXT("Station light is suppressed during review"), Light->IsVisible());
        TestFalse(TEXT("Reentrant portal entry is rejected"), Gallery->Enter(PC));
        GM->Tick(30.f);
        TestTrue(TEXT("Gallery time does not change run"), SS::EncodeRun(GI->Session.run) == Run);
        TestTrue(TEXT("Gallery time does not change account"), SS::EncodeAccount(GI->Session.account) == Account);
        // Cancel before completing load: this must release pending streaming and restore exact states.
        Gallery->Leave();
        World->FlushLevelStreaming();
        Gallery->Update(0);
        TestFalse(TEXT("Cancelled loading exits review"), Gallery->IsActive());
        TestTrue(TEXT("Original walker remains possessed"), PC->GetPawn() == Walker);
        TestTrue(TEXT("Return keeps walker transform"), Walker->GetActorTransform().Equals(Original));
        TestTrue(TEXT("Return keeps view orientation"), PC->GetControlRotation().Equals(OriginalView));
        TestTrue(TEXT("Station lighting restored"), Light->IsVisible());
        TestFalse(TEXT("Preexisting disabled collision stays disabled"), LightOwner->GetActorEnableCollision());
        TestTrue(TEXT("Re-enter actual showcase after cancellation"), Gallery->Enter(PC));
        auto CompleteStreaming = [&]()
        {
            // Fixture-only blocking; gameplay uses asynchronous loading and visible cancel/return controls.
            for (int32 Step = 0; Step < 4; ++Step)
            {
                World->FlushLevelStreaming();
                Gallery->Update(0);
            }
        };
        CompleteStreaming();
        TestTrue(TEXT("Full showcase becomes inspectable"), Gallery->IsReady());
        TestTrue(TEXT("Inspection uses isolated noclip camera"),
                 PC->GetPawn() && PC->GetPawn()->IsA<ASSGalleryCamera>());
        GM->Tick(60.f);
        TestTrue(TEXT("Viewing does not advance session"), SS::EncodeRun(GI->Session.run) == Run);
        if (FPackageName::DoesPackageExist(USSAlienGallery::MapPath(true)))
        {
            Gallery->SwitchScene();
            CompleteStreaming();
            TestTrue(TEXT("Can inspect full asset-layout map"), Gallery->IsReady());
            TestTrue(TEXT("Asset-map identity shown to owner"), Gallery->Status().Contains(TEXT("ASSET GALLERY")));
        }
        Gallery->Leave();
        CompleteStreaming();
        TestFalse(TEXT("Full traversal releases review mode"), Gallery->IsActive());
        TestTrue(TEXT("Full traversal restores walker"), PC->GetPawn() == Walker);
        TestTrue(TEXT("Full traversal restores position"), Walker->GetActorTransform().Equals(Original));
        TestTrue(TEXT("Full traversal restores station light"), Light->IsVisible());
        TestTrue(TEXT("Full traversal preserves exact run"), SS::EncodeRun(GI->Session.run) == Run);
    }
    else
    {
        TestFalse(TEXT("Source-only missing kit fails safely"), Gallery->Enter(PC));
        TestFalse(TEXT("Missing kit does not freeze station"), Gallery->IsActive());
        TestTrue(TEXT("Missing kit leaves lighting intact"), Light->IsVisible());
    }
    TestTrue(TEXT("Gallery never changes save/account payload"), SS::EncodeAccount(GI->Session.account) == Account);
    World->EndPlay(EEndPlayReason::Quit);
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    GWorld = Previous;
    GI->RemoveFromRoot();
    return true;
}
#endif
