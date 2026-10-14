#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSDistantAsteroids.h"
#include "SSWorldActors.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "Physics/Experimental/PhysScene_Chaos.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHangarFieldRebase, "SpaceSurvival.Presentation.HangarFieldRebase",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSHangarFieldRebase::RunTest(const FString &)
{
    UWorld *PreviousWorld = GWorld;
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("Create isolated hangar rebase world"), World))
        return false;
    auto &Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    auto *Instance = NewObject<USSGameInstance>(GEngine, NAME_None, RF_Transient);
    Instance->AddToRoot();
    Instance->AccountStorageBlocked = true;
    Instance->Session.settings.masterVolume = 0;
    Instance->Session.account.tutorialFlags = 255;
    Context.OwningGameInstance = Instance;
    World->SetGameInstance(Instance);
    GWorld = World;
    ON_SCOPE_EXIT
    {
        World->EndPlay(EEndPlayReason::Quit);
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        GWorld = PreviousWorld;
        Instance->RemoveFromRoot();
    };
    World->GetWorldSettings()->DefaultGameMode = ASSGameMode::StaticClass();
    if (!TestTrue(TEXT("Install real hangar owner"), World->SetGameMode(FURL())))
        return false;
    auto *Mode = World->GetAuthGameMode<ASSGameMode>();
    auto *Content = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!TestNotNull(TEXT("Resolve production mode"), Mode) || !TestNotNull(TEXT("Load production content"), Content))
        return false;
    Mode->Tuning = DuplicateObject<USSPhase1Data>(Content, Mode);
    Mode->SetActorTickEnabled(false);
    Mode->Director->SetComponentTickEnabled(false);
    World->InitializeActorsForPlay(FURL());
    // Skip production startup/account initialization; ShowHangar itself is the path under test.
    World->SetBegunPlay(true);
    if (World->GetPhysicsScene())
        World->GetPhysicsScene()->OnWorldBeginPlay();
    auto *Controller = World->SpawnActor<APlayerController>();
    if (!TestNotNull(TEXT("Create isolated local controller"), Controller))
        return false;
    Controller->SetAsLocalPlayerController();
    Controller->SetActorTickEnabled(false);
    World->AddController(Controller);
    Mode->ShowHangar();
    Mode->Tick(0.f); // Ordinary mode activation creates the visible field's collision bodies.
    auto *Station = Mode->GetStation();
    auto *Ship = Mode->GetPlayerShip();
    if (!TestNotNull(TEXT("Home station exists"), Station) || !TestNotNull(TEXT("Actual parked hull exists"), Ship) ||
        !TestTrue(TEXT("Current authored Wayfarer is used"), Station->IsUsingOutpost()))
        return false;
    const FVector OriginalDock = Station->PadDockPosition();
    const FRotator OriginalFacing = Station->PadDockRotation();
    ASSDistantAsteroids *Field = nullptr;
    for (TActorIterator<ASSDistantAsteroids> It(World); It; ++It)
        if (!It->IsActorBeingDestroyed())
            Field = *It;
    if (!TestNotNull(TEXT("Actual persistent asteroid field exists"), Field))
        return false;
    const FVector OriginalAnchor = Field->GetActorLocation();
    const int32 OriginalCount = Field->GetRockCount();
    TMap<UInstancedStaticMeshComponent *, TArray<FTransform>> OriginalPoses;
    TArray<UInstancedStaticMeshComponent *> Batches;
    Field->GetComponents(Batches);
    for (auto *Batch : Batches)
    {
        auto &Poses = OriginalPoses.Add(Batch);
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Pose;
            Batch->GetInstanceTransform(Index, Pose, true);
            Poses.Add(Pose);
        }
    }
    if (!TestTrue(TEXT("Fixture contains actual asteroid geometry"), OriginalCount > 0))
        return false;
    const FIntVector Shift(1200000, -400000, 230000);
    if (!TestTrue(TEXT("Real world-origin rebase succeeds"), World->SetNewWorldOrigin(Shift)))
        return false;
    Mode->ShowHangar(); // Same production return used after death or ending free flight.
    Mode->Tick(0.f);
    Station = Mode->GetStation();
    Ship = Mode->GetPlayerShip();
    if (!TestNotNull(TEXT("Rebased return creates home"), Station) ||
        !TestNotNull(TEXT("Rebased return creates actual parked hull"), Ship))
        return false;
    const FVector Origin(World->OriginLocation);
    TestTrue(TEXT("Home returns to original absolute origin"), (Station->GetActorLocation() + Origin).IsNearlyZero(.1));
    TestTrue(TEXT("Pad retains its absolute location"), (Station->PadDockPosition() + Origin).Equals(OriginalDock, .1));
    TestTrue(TEXT("Parked hull retains the original field-relative clearance"),
             (Ship->GetActorLocation() - Field->GetActorLocation()).Equals(OriginalDock - OriginalAnchor, .1));
    TestTrue(TEXT("Departure heading is unchanged"), Station->PadDockRotation().Equals(OriginalFacing, .001));
    TestTrue(TEXT("Persistent field anchor is not moved to repair the station"),
             (Field->GetActorLocation() + Origin).Equals(OriginalAnchor, .1));
    TestEqual(TEXT("Returning does not rebuild the field population"), Field->GetRockCount(), OriginalCount);
    bool AllPosesRetained = true;
    for (const auto &Pair : OriginalPoses)
    {
        auto *Batch = Pair.Key;
        AllPosesRetained &= IsValid(Batch) && Batch->GetInstanceCount() == Pair.Value.Num();
        if (!IsValid(Batch) || Batch->GetInstanceCount() != Pair.Value.Num())
            continue;
        for (int32 Index = 0; Index < Pair.Value.Num(); ++Index)
        {
            FTransform Pose;
            AllPosesRetained &= Batch->GetInstanceTransform(Index, Pose, true);
            Pose.AddToTranslation(Origin);
            AllPosesRetained &= Pose.Equals(Pair.Value[Index], .1);
        }
    }
    TestTrue(TEXT("Every real field instance retains its component, ordinal and absolute pose"), AllPosesRetained);
    // Complete the ordinary takeoff handoff before querying: a moored ship has no active
    // compound physics body. Do not invoke disk-backed StartNewRun for this spatial invariant.
    const FVector Hover = Station->PadDockPosition() + Station->GetActorUpVector() * 700.f;
    Ship->BeginTakeoff(Hover, OriginalFacing, .1f);
    Ship->Tick(.1f);
    auto *HullRoot = Cast<UPrimitiveComponent>(Ship->GetRootComponent());
    if (!TestTrue(TEXT("Real takeoff restores the compound hull before the clearance probe"),
                  !Ship->IsTakingOff() && Ship->HasFlightHull() && HullRoot && HullRoot->IsCollisionEnabled() &&
                      HullRoot->IsPhysicsStateCreated()))
        return false;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSRebasedDepartureClearance), false, Ship);
    TestFalse(TEXT("Rebased outward departure retains real hull clearance for the first 180m"),
              Ship->SweepFlightHull(Hit, Hover, Hover + OriginalFacing.Vector() * 18000.f, OriginalFacing.Quaternion(),
                                    Query));
    return true;
}
#endif
