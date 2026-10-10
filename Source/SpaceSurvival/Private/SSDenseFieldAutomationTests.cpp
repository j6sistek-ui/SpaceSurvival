#include "SSDistantAsteroids.h"
#include "SSSpaceLookData.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FFieldFixture
{
    UWorld *World = nullptr;
    UWorld *PreviousWorld = GWorld;
    UGameInstance *Instance = nullptr;
    AActor *Viewer = nullptr;
    ASSDistantAsteroids *Field = nullptr;
    bool Initialize(FAutomationTestBase &Test)
    {
        World = UWorld::CreateWorld(EWorldType::Game, false);
        if (!Test.TestNotNull(TEXT("Create world"), World))
            return false;
        GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
        Instance = NewObject<UGameInstance>(GEngine, NAME_None, RF_Transient);
        Instance->AddToRoot();
        GEngine->GetWorldContextFromWorldChecked(World).OwningGameInstance = Instance;
        World->SetGameInstance(Instance);
        GWorld = World;
        World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
        if (!World->SetGameMode(FURL()))
            return false;
        World->InitializeActorsForPlay(FURL());
        Viewer = World->SpawnActor<AActor>();
        auto *Root = NewObject<USceneComponent>(Viewer);
        Viewer->SetRootComponent(Root);
        Root->RegisterComponent();
        Field = World->SpawnActor<ASSDistantAsteroids>();
        World->BeginPlay();
        Field->Follow(Viewer);
        Field->SetFlightVisible(true);
        return true;
    }
    ~FFieldFixture()
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
struct FMeasuredRock
{
    FVector Center;
    double Radius;
    bool bAsteroid;
};
TMap<FString, FMeasuredRock> Snapshot(ASSDistantAsteroids *Field)
{
    TMap<FString, FMeasuredRock> Result;
    TArray<UInstancedStaticMeshComponent *> Batches;
    Field->GetComponents(Batches);
    for (const auto *Batch : Batches)
        for (int32 Index = 0; Index < Batch->GetInstanceCount(); ++Index)
        {
            FTransform Pose;
            Batch->GetInstanceTransform(Index, Pose, true);
            const auto Bounds = Batch->GetStaticMesh()->GetBounds();
            Result.Add(Batch->GetStaticMesh()->GetPathName() + Pose.ToString(),
                       {Pose.TransformPosition(Bounds.Origin), Bounds.SphereRadius * Pose.GetScale3D().GetAbsMax(),
                        Batch->GetStaticMesh()->GetName().Contains(TEXT("Asteroid"))});
        }
    return Result;
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDenseFieldGeometry, "SpaceSurvival.Presentation.DenseFieldGeometry",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDenseFieldGeometry::RunTest(const FString &)
{
    auto *Count = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.DistantAsteroidCount"));
    const int32 Before = Count->GetInt();
    const auto Priority = EConsoleVariableFlags(Count->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Count->Set(Before, Priority);
    };
    Count->Set(6144, Priority);
    FFieldFixture Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    auto *Look =
        LoadObject<USSSpaceLookData>(nullptr, TEXT("/Game/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook"));
    if (!TestNotNull(TEXT("Owned field layout data loads"), Look))
        return false;
    TestTrue(TEXT("All three owned procedural formations contribute nontrivial layouts"),
             Look->AsteroidArchSamples.Num() >= 24 && Look->AsteroidGlobularSamples.Num() >= 24 &&
                 Look->AsteroidLinearSamples.Num() >= 24);
    TArray<UInstancedStaticMeshComponent *> MaterialBatches;
    Fixture.Field->GetComponents(MaterialBatches);
    for (const auto *Batch : MaterialBatches)
        for (int32 Slot = 0; Slot < Batch->GetNumMaterials(); ++Slot)
        {
            auto *Fade = Cast<UMaterialInstanceDynamic>(Batch->GetMaterial(Slot));
            if (!TestNotNull(TEXT("Every field material uses its private distance-fade derivative"), Fade))
                return false;
            float Start = 0.f, End = 0.f;
            TestTrue(TEXT("Fade starts at 700m"),
                     Fade->GetScalarParameterValue(FMaterialParameterInfo(TEXT("SSFadeStart")), Start) &&
                         FMath::IsNearlyEqual(Start, 70000.f));
            TestTrue(TEXT("Fade is complete before the nearest cell insertion surface"),
                     Fade->GetScalarParameterValue(FMaterialParameterInfo(TEXT("SSFadeEnd")), End) &&
                         FMath::IsNearlyEqual(End, 95000.f));
            TestEqual(TEXT("Distance fading is wired through a masked material"), Fade->GetBlendMode(), BLEND_Masked);
            TestTrue(TEXT("Distance fading uses native blue-noise masking"),
                     Fade->GetMaterial() && Fade->GetMaterial()->DitherOpacityMask);
            TestTrue(TEXT("Native fade encoding retains its calibrated clip threshold"),
                     FMath::IsNearlyEqual(Fade->GetOpacityMaskClipValue(), .333f));
        }
    const auto Initial = Snapshot(Fixture.Field);
    TestEqual(TEXT("Dense budget corresponds to actual transformed mesh instances"), Initial.Num(), 6144);
    TMap<FIntVector, TArray<FMeasuredRock>> CellRocks;
    int32 IntersectingPeers = 0;
    for (const auto &Pair : Initial)
    {
        const auto &Rock = Pair.Value;
        if (!Rock.bAsteroid)
            continue;
        const FIntVector Cell(FMath::FloorToInt(Rock.Center.X / 50000. + .5),
                              FMath::FloorToInt(Rock.Center.Y / 50000. + .5),
                              FMath::FloorToInt(Rock.Center.Z / 50000. + .5));
        auto &Peers = CellRocks.FindOrAdd(Cell);
        for (const auto &Peer : Peers)
            if (FMath::Min(Rock.Radius, Peer.Radius) >= FMath::Max(Rock.Radius, Peer.Radius) * .6 &&
                FVector::Distance(Rock.Center, Peer.Center) < (Rock.Radius + Peer.Radius) * .95 - 1.)
                ++IntersectingPeers;
        Peers.Add(Rock);
    }
    TestEqual(TEXT("Comparable boulders retain separate silhouettes instead of deeply intersecting chains"),
              IntersectingPeers, 0);
    int32 Directions[6] = {};
    int32 Near = 0;
    double MinimumSurface = TNumericLimits<double>::Max();
    for (const auto &Pair : Initial)
    {
        const auto &Rock = Pair.Value;
        const double Distance = Rock.Center.Size();
        MinimumSurface = FMath::Min(MinimumSurface, Distance - Rock.Radius);
        if (Distance - Rock.Radius < 35000.)
            ++Near;
        if (Distance > 90000.)
            continue;
        for (int32 Axis = 0; Axis < 3; ++Axis)
            if (FMath::Abs(Rock.Center[Axis]) > Distance * .8)
                ++Directions[Axis * 2 + (Rock.Center[Axis] > 0 ? 1 : 0)];
    }
    TestTrue(TEXT("Launch starts clear of every actual mesh sphere"), MinimumSurface >= 7999.);
    TestTrue(TEXT("Close depth comes from real geometry within 350m, not the resident box count"), Near >= 40);
    for (int32 Axis = 0; Axis < 6; ++Axis)
    {
        AddInfo(FString::Printf(TEXT("View cone %d contains %d actual meshes inside 900m"), Axis, Directions[Axis]));
        TestTrue(TEXT("All six free-flight view directions show a substantial field"), Directions[Axis] >= 30);
    }
    AddInfo(FString::Printf(TEXT("Close meshes=%d, closest surface=%.1fm"), Near, MinimumSurface / 100.));
    Fixture.Viewer->SetActorRotation(FRotator(35, 145, 60));
    Fixture.Field->Tick(.05f);
    const auto Turned = Snapshot(Fixture.Field);
    for (const auto &Pair : Initial)
        if (!TestTrue(TEXT("Turning does not move or replace a world rock"), Turned.Contains(Pair.Key)))
            return false;
    // Cross the streaming seam in a 25m travel step, also covering a delayed flight frame.
    Fixture.Viewer->SetActorLocation(FVector(24000, 0, 0));
    Fixture.Field->Tick(.05f);
    const auto BeforeSeam = Snapshot(Fixture.Field);
    const FVector AfterPosition(26500, 0, 0);
    Fixture.Viewer->SetActorLocation(AfterPosition);
    Fixture.Field->Tick(.05f);
    const auto AfterSeam = Snapshot(Fixture.Field);
    double NearestChange = TNumericLimits<double>::Max();
    for (const auto &Pair : BeforeSeam)
        if (!AfterSeam.Contains(Pair.Key))
            NearestChange =
                FMath::Min(NearestChange, FVector::Distance(Pair.Value.Center, AfterPosition) - Pair.Value.Radius);
    for (const auto &Pair : AfterSeam)
        if (!BeforeSeam.Contains(Pair.Key))
            NearestChange =
                FMath::Min(NearestChange, FVector::Distance(Pair.Value.Center, AfterPosition) - Pair.Value.Radius);
    AddInfo(FString::Printf(TEXT("Nearest streaming change at 500m/s=%.1fm"), NearestChange / 100.));
    TestTrue(TEXT("No visible nearby surface is inserted or evicted during fast approach"), NearestChange > 95000.);
    Fixture.Field->SetFlightVisible(false);
    TestFalse(TEXT("Hidden station/title field cannot cause invisible collisions"),
              Fixture.Field->GetActorEnableCollision());
    Fixture.Field->SetFlightVisible(true);
    TestTrue(TEXT("Returning to visible flight restores solid geometry"), Fixture.Field->GetActorEnableCollision());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDenseFieldIncrementalStreaming,
                                 "SpaceSurvival.Presentation.DenseFieldIncrementalStreaming",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDenseFieldIncrementalStreaming::RunTest(const FString &)
{
    auto *Count = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.DistantAsteroidCount"));
    const int32 Before = Count->GetInt();
    const auto Priority = EConsoleVariableFlags(Count->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Count->Set(Before, Priority);
    };
    Count->Set(6144, Priority);
    FFieldFixture Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    // Obtain the complete deterministic destination using the supported teleport path.
    Fixture.Viewer->SetActorLocation(FVector(900000, 0, 0));
    Fixture.Field->Tick(.016f);
    Fixture.Viewer->SetActorLocation(FVector(30000, 0, 0));
    Fixture.Field->Tick(.016f);
    const auto Destination = Snapshot(Fixture.Field);
    TestEqual(TEXT("Teleport completes all destination cells immediately"), Fixture.Field->GetPendingCellCount(), 0);
    Fixture.Viewer->SetActorLocation(FVector(900000, 0, 0));
    Fixture.Field->Tick(.016f);
    Fixture.Viewer->SetActorLocation(FVector::ZeroVector);
    Fixture.Field->Tick(.016f);
    auto Previous = Snapshot(Fixture.Field);
    for (int32 Step = 0; Step <= 40; ++Step)
    {
        const FVector Eye(24000. + Step * 500., 0, 0);
        Fixture.Viewer->SetActorLocation(Eye);
        Fixture.Field->Tick(.016f);
        const auto Current = Snapshot(Fixture.Field);
        TestEqual(TEXT("Incremental turnover keeps exactly125 resident cells"), Fixture.Field->GetResidentCellCount(),
                  125);
        TestTrue(TEXT("Incremental turnover never exceeds the real6144instance budget"), Current.Num() <= 6144);
        for (const auto &Rock : Destination)
            if (FVector::Distance(Rock.Value.Center, Eye) - Rock.Value.Radius <= 95000.)
                if (!TestTrue(TEXT("Every destination surface inside the fade horizon is already resident"),
                              Current.Contains(Rock.Key)))
                    return false;
        for (const auto &Rock : Previous)
            if (!Current.Contains(Rock.Key))
                if (!TestTrue(TEXT("Removed surfaces are completely beyond the fade"),
                              FVector::Distance(Rock.Value.Center, Eye) - Rock.Value.Radius > 95000.))
                    return false;
        for (const auto &Rock : Current)
            if (!Previous.Contains(Rock.Key))
                if (!TestTrue(TEXT("New surfaces enter residency before becoming visible"),
                              FVector::Distance(Rock.Value.Center, Eye) - Rock.Value.Radius > 95000.))
                    return false;
        Previous = Current;
    }
    // No work is forced by timing in the test; continued idle ticks must drain the queue.
    for (int32 Step = 0; Step < 125 && Fixture.Field->GetPendingCellCount(); ++Step)
        Fixture.Field->Tick(.016f);
    TestEqual(TEXT("Bounded pending turnover finishes"), Fixture.Field->GetPendingCellCount(), 0);
    const auto Settled = Snapshot(Fixture.Field);
    TestEqual(TEXT("Incremental and synchronous destinations contain the same actual population"), Settled.Num(),
              Destination.Num());
    for (const auto &Rock : Destination)
        if (!TestTrue(TEXT("Incremental turnover preserves every deterministic world pose"),
                      Settled.Contains(Rock.Key)))
            return false;
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSDenseFieldDamage, "SpaceSurvival.Presentation.DenseFieldDamage",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSDenseFieldDamage::RunTest(const FString &)
{
    auto *Count = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.DistantAsteroidCount"));
    const int32 Before = Count->GetInt();
    const auto Priority = EConsoleVariableFlags(Count->GetFlags() & ECVF_SetByMask);
    ON_SCOPE_EXIT
    {
        Count->Set(Before, Priority);
    };
    Count->Set(512, Priority);
    FFieldFixture Fixture;
    if (!Fixture.Initialize(*this))
        return false;
    const auto Initial = Snapshot(Fixture.Field);
    TArray<UInstancedStaticMeshComponent *> Batches;
    Fixture.Field->GetComponents(Batches);
    FHitResult Hit;
    bool Found = false;
    for (const auto *Batch : Batches)
    {
        if (!Batch->GetStaticMesh()->GetName().Contains(TEXT("Asteroid")))
            continue;
        for (int32 Index = 0; Index < Batch->GetInstanceCount() && !Found; ++Index)
        {
            FTransform Pose;
            Batch->GetInstanceTransform(Index, Pose, true);
            const FVector Center = Pose.TransformPosition(Batch->GetStaticMesh()->GetBounds().Origin);
            const double Radius = Batch->GetStaticMesh()->GetBounds().SphereRadius * Pose.GetScale3D().GetAbsMax();
            FCollisionQueryParams Query(SCENE_QUERY_STAT(DenseFieldDamage), false);
            Found =
                Fixture.World->LineTraceSingleByChannel(Hit, Center - FVector(Radius * 2, 0, 0),
                                                        Center + FVector(Radius * 2, 0, 0), ECC_Visibility, Query) &&
                Hit.GetActor() == Fixture.Field &&
                Cast<UStaticMeshComponent>(Hit.GetComponent())->GetStaticMesh()->GetName().Contains(TEXT("Asteroid"));
        }
        if (Found)
            break;
    }
    if (!TestTrue(TEXT("Actual collision trace identifies a world asteroid instance"), Found))
        return false;
    auto *HitBatch = CastChecked<UInstancedStaticMeshComponent>(Hit.GetComponent());
    FTransform HitPose;
    HitBatch->GetInstanceTransform(Hit.Item, HitPose, true);
    const float Radius = HitBatch->GetStaticMesh()->GetBounds().SphereRadius * HitPose.GetScale3D().GetAbsMax();
    const float InitialHealth = FMath::Clamp(12.f + Radius * .02f, 24.f, 600.f);
    const FVector TraceStart = Hit.TraceStart, TraceEnd = Hit.TraceEnd;
    bool Destroyed = false;
    TestTrue(TEXT("World asteroid accepts a nonfatal laser-sized hit"),
             Fixture.Field->ApplyWeaponHit(Hit, 12.f, Destroyed));
    TestFalse(TEXT("Small damage does not remove the wrong instance"), Destroyed);
    Fixture.Viewer->SetActorLocation(FVector(900000, 0, 0));
    Fixture.Field->Tick(.05f);
    Fixture.Viewer->SetActorLocation(FVector::ZeroVector);
    Fixture.Field->Tick(.05f);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(DenseFieldRevisit), false);
    if (!TestTrue(TEXT("Returning trace reacquires the same damaged rock"),
                  Fixture.World->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Query)))
        return false;
    TestTrue(TEXT("Previously applied damage survives eviction"),
             Fixture.Field->ApplyWeaponHit(Hit, InitialHealth - 12.f + .1f, Destroyed));
    TestTrue(TEXT("Break removes the actual hit instance"), Destroyed);
    const auto Broken = Snapshot(Fixture.Field);
    TestEqual(TEXT("Only one mesh was removed"), Broken.Num(), Initial.Num() - 1);
    for (const auto &Pair : Broken)
        if (!TestTrue(TEXT("Removing an instance preserves every neighbour's world pose"), Initial.Contains(Pair.Key)))
            return false;
    Fixture.Viewer->SetActorLocation(FVector(900000, 0, 0));
    Fixture.Field->Tick(.05f);
    Fixture.Viewer->SetActorLocation(FVector::ZeroVector);
    Fixture.Field->Tick(.05f);
    const auto Returned = Snapshot(Fixture.Field);
    TestEqual(TEXT("Destroyed identity stays absent after eviction and revisit"), Returned.Num(), Broken.Num());
    for (const auto &Pair : Broken)
        if (!TestTrue(TEXT("Revisit restores each surviving pose exactly"), Returned.Contains(Pair.Key)))
            return false;
    Fixture.Field->SetRunSeed(723);
    TestEqual(TEXT("A new run resets field damage and population"), Fixture.Field->GetRockCount(), 512);
    return true;
}
#endif
