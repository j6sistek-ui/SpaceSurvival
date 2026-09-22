#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "SSStation.h"
#include "SSStationVisualLayout.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FEditableStationWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FEditableStationWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FEditableStationWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};

TArray<UStaticMeshComponent *> CollisionComponents(ASSStation *Hub)
{
    TArray<UStaticMeshComponent *> Result;
    TInlineComponentArray<UStaticMeshComponent *> Components(Hub);
    for (auto *Component : Components)
        if (Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
            Result.Add(Component);
    return Result;
}

FString DescribeCollision(UStaticMeshComponent *Component)
{
    return FString::Printf(TEXT("%s mesh=%s relative=%s mode=%d object=%d pawn=%d"), *Component->GetName(),
                           *GetPathNameSafe(Component->GetStaticMesh()), *Component->GetRelativeTransform().ToString(),
                           int32(Component->GetCollisionEnabled()), int32(Component->GetCollisionObjectType()),
                           int32(Component->GetCollisionResponseToChannel(ECC_Pawn)));
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSStationEditableLayout, "SpaceSurvival.Integration.StationEditableLayout",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSStationEditableLayout::RunTest(const FString &)
{
    FEditableStationWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated editable station world"), Fixture.World))
        return false;
    auto *Missing = Fixture.World->SpawnActor<ASSStation>();
    Missing->VisualLayoutAsset =
        FSoftObjectPath(TEXT("/Game/SpaceSurvival/AbsentOptionalLayout.AbsentOptionalLayout_C"));
    Missing->BuildHub(false);
    TestNull(TEXT("Absent private Blueprint uses the real native fallback"), Missing->GetVisualLayout());
    TestTrue(TEXT("Absent optional Blueprint retains station collision"), !CollisionComponents(Missing).IsEmpty());
    Missing->Destroy();
    if (!FPackageName::DoesPackageExist(TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout")))
    {
        AddInfo(TEXT("Owner-editable layout is not authored locally; missing-asset fallback passed, authored-layout "
                     "coverage skipped."));
        return true;
    }
    auto *PreviewHub = Fixture.World->SpawnActor<ASSStation>();
    PreviewHub->VisualLayoutAsset = FSoftObjectPath(
        TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout.BP_StationVisualLayout_C"));
    PreviewHub->BuildHub(false);
    auto *PreviewLayout = PreviewHub->GetVisualLayout();
    TestNotNull(TEXT("Pre-play station has an authored layout to clean up"), PreviewLayout);
    TestFalse(TEXT("Pre-play cleanup exercises an uninitialized actor"), PreviewHub->IsActorInitialized());
    TestTrue(TEXT("Pre-play station destruction succeeds"), PreviewHub->Destroy());
    TestTrue(TEXT("Destroying before gameplay also removes the owned visual actor"),
             !IsValid(PreviewLayout) || PreviewLayout->IsActorBeingDestroyed());
    // DispatchBeginPlay alone does not initialize actors, so RouteEndPlay would be skipped.
    Fixture.World->InitializeActorsForPlay(FURL());
    for (bool Home : {false, true})
    {
        const FTransform Transform(FRotator(0, 75, 0), FVector(16000, -8000, 5000), FVector(1.25));
        auto *Hub = Fixture.World->SpawnActor<ASSStation>(ASSStation::StaticClass(), Transform);
        // This suite retains the original editable layout's regression coverage. StationResetRuntime
        // separately exercises the new default's deliberately different structure and service anchors.
        Hub->VisualLayoutAsset = FSoftObjectPath(
            TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout.BP_StationVisualLayout_C"));
        auto *Fallback = Fixture.World->SpawnActor<ASSStation>(FVector(-16000, 8000, 5000), FRotator(0, 75, 0));
        Fallback->bUseEditableLayout = false;
        Fallback->SetActorScale3D(FVector(1.25));
        Fallback->BuildHub(Home);
        Hub->BuildHub(Home);
        auto *Layout = Hub->GetVisualLayout();
        if (!TestNotNull(TEXT("Actual station loads the persisted editable Blueprint"), Layout))
            return false;
        TestTrue(TEXT("Layout belongs to and follows the transformed station"),
                 Layout->GetOwner() == Hub && Layout->GetAttachParentActor() == Hub &&
                     Layout->GetActorTransform().Equals(Hub->GetActorTransform(), .01));
        auto AuthoredCollision = CollisionComponents(Hub);
        auto UnmatchedCollision = CollisionComponents(Fallback);
        const bool ExpandedDeck = AuthoredCollision.ContainsByPredicate(
            [](const UStaticMeshComponent *Component)
            { return Component->ComponentHasTag(TEXT("StationAuthoredDeckCollision")); });
        if (ExpandedDeck)
        {
            for (const auto *Floor : AuthoredCollision)
                if (Floor->ComponentHasTag(TEXT("StationAuthoredDeckCollision")))
                {
                    const FVector Top = Floor->GetComponentTransform().TransformPosition(FVector(0, 0, 50));
                    TestTrue(TEXT("Every measured floor proxy belongs to the walker rescue envelope"),
                             Hub->Walkable(Top + FVector(0, 0, 100)));
                    FHitResult FloorHit;
                    TestTrue(TEXT("Every measured floor has actual support at its visible surface"),
                             Fixture.World->LineTraceSingleByObjectType(FloorHit, Top + FVector(0, 0, 25),
                                                                        Top - FVector(0, 0, 25),
                                                                        FCollisionObjectQueryParams(ECC_WorldStatic)) &&
                                 FloorHit.GetActor() == Hub && FMath::Abs(FloorHit.ImpactPoint.Z - Top.Z) < 1.f);
                }
            AuthoredCollision.RemoveAll([](const UStaticMeshComponent *Component)
                                        { return Component->ComponentHasTag(TEXT("StationAuthoredDeckCollision")); });
            UnmatchedCollision.RemoveAll([](const UStaticMeshComponent *Component)
                                         { return Component->ComponentHasTag(TEXT("StationLegacyRoomBoundary")); });
            TInlineComponentArray<UStaticMeshComponent *> NativeComponents(Hub);
            for (const auto *Component : NativeComponents)
                if (Component->ComponentHasTag(TEXT("StationLegacyRoomBoundary")))
                    TestTrue(TEXT("Old room walls do not invisibly cross the expanded authored deck"),
                             Component->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
        }
        TestEqual(TEXT("Layout preserves native collision apart from measured floor and obsolete room boundaries"),
                  AuthoredCollision.Num(), UnmatchedCollision.Num());
        for (auto *Component : AuthoredCollision)
        {
            const int32 Match = UnmatchedCollision.IndexOfByPredicate(
                [Component](const UStaticMeshComponent *Other)
                {
                    // Compare the actual values, not rounded text (which distinguishes 0 from -0).
                    return Component->GetStaticMesh() == Other->GetStaticMesh() &&
                           Component->GetRelativeTransform().Equals(Other->GetRelativeTransform(), 1.e-6) &&
                           Component->GetCollisionEnabled() == Other->GetCollisionEnabled() &&
                           Component->GetCollisionObjectType() == Other->GetCollisionObjectType() &&
                           Component->GetCollisionResponseToChannels() == Other->GetCollisionResponseToChannels();
                });
            if (TestTrue(TEXT("Blueprint replacement preserves every native collision shape and transform"),
                         Match != INDEX_NONE))
            {
                const auto *Other = UnmatchedCollision[Match];
                if (Component->GetRelativeTransform().ToString() != Other->GetRelativeTransform().ToString())
                    AddInfo(FString::Printf(TEXT("COLLISION_FORMAT_ONLY authored=%s fallback=%s"),
                                            *Component->GetRelativeTransform().ToString(),
                                            *Other->GetRelativeTransform().ToString()));
                UnmatchedCollision.RemoveAtSwap(Match);
            }
            else
                AddInfo(TEXT("UNMATCHED_AUTHORED_COLLISION ") + DescribeCollision(Component));
        }
        for (auto *Component : UnmatchedCollision)
            AddInfo(TEXT("UNMATCHED_FALLBACK_COLLISION ") + DescribeCollision(Component));
        TestTrue(TEXT("Every fallback collision shape has exactly one authored counterpart"),
                 UnmatchedCollision.IsEmpty());
        TestTrue(TEXT("Walk and dock anchors preserve exact station-local positions"),
                 Hub->WalkSpawn().Equals(Transform.TransformPosition(FVector(-300, 0, 180)), .01) &&
                     Hub->DockPosition().Equals(Transform.TransformPosition(FVector(850, 0, 220)), .01));
        const FVector ServicePoints[] = {FVector(200, -1000, 0), FVector(-800, -1000, 0), FVector(-1100, 850, 0),
                                         FVector(0, 1000, 0),    FVector(950, -450, 0),   FVector(1000, 1000, 0),
                                         FVector(-1400, 0, 0)};
        for (const FVector &Point : ServicePoints)
        {
            FString AuthoredLabel, FallbackLabel;
            const auto Panel = Hub->NearestService(Hub->GetActorTransform().TransformPosition(Point), AuthoredLabel);
            const auto Reference =
                Fallback->NearestService(Fallback->GetActorTransform().TransformPosition(Point), FallbackLabel);
            TestTrue(TEXT("Authored room keeps the same service panels and labels at all anchors"),
                     Panel == Reference && AuthoredLabel == FallbackLabel);
        }
        TInlineComponentArray<UInstancedStaticMeshComponent *> NativeBatches(Hub);
        for (auto *Batch : NativeBatches)
            TestTrue(TEXT("Native decorative room is not duplicated behind the Blueprint"),
                     !Batch->GetName().StartsWith(TEXT("LicensedStation_")) && Batch->GetInstanceCount() == 0);
        TestTrue(TEXT("Native bay lights are replaced by editable lighting"),
                 Hub->K2_GetComponentsByClass(UPointLightComponent::StaticClass()).IsEmpty());
        TInlineComponentArray<UPrimitiveComponent *> Primitives(Layout);
        int32 MeshCount = 0;
        for (auto *Component : Primitives)
        {
            TestTrue(TEXT("Authored and owner-added visual components cannot block gameplay/navigation"),
                     Component->GetCollisionEnabled() == ECollisionEnabled::NoCollision &&
                         !Component->GetGenerateOverlapEvents() && !Component->CanEverAffectNavigation());
            if (auto *Mesh = Cast<UStaticMeshComponent>(Component))
            {
                ++MeshCount;
                TestNotNull(TEXT("Editable static component resolves its real mesh"), Mesh->GetStaticMesh().Get());
                TestNull(TEXT("Editable components are individually selectable rather than ISM stamps"),
                         Cast<UInstancedStaticMeshComponent>(Mesh));
                for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
                    TestNotNull(TEXT("Editable component resolves every material slot"), Mesh->GetMaterial(Slot));
            }
        }
        TestTrue(TEXT("Persisted Blueprint has an actual populated visual room"), MeshCount > 0);
        auto *Added = NewObject<UStaticMeshComponent>(Layout);
        Added->SetupAttachment(Layout->GetRootComponent());
        Added->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        Added->SetGenerateOverlapEvents(true);
        Added->SetCanEverAffectNavigation(true);
        Layout->AddInstanceComponent(Added);
        Added->RegisterComponent();
        Layout->EnforcePresentationOnly();
        TestTrue(TEXT("Safety enforcement also covers a newly added component"),
                 Added->GetCollisionEnabled() == ECollisionEnabled::NoCollision && !Added->GetGenerateOverlapEvents() &&
                     !Added->CanEverAffectNavigation());
        const FVector Offset(350, -120, 30);
        Hub->AddActorWorldOffset(Offset);
        TestTrue(TEXT("Moving the owning station carries the authored layout once"),
                 Layout->GetActorLocation().Equals(Transform.GetLocation() + Offset, .01));
        Hub->DispatchBeginPlay();
        TestTrue(TEXT("Cleanup covers an initialized actor that began gameplay"),
                 Hub->IsActorInitialized() && Hub->HasActorBegunPlay());
        TestTrue(TEXT("Station destruction succeeds"), Hub->Destroy());
        TestTrue(TEXT("Station cleanup removes its authored visual actor"),
                 !IsValid(Layout) || Layout->IsActorBeingDestroyed());
        Fallback->Destroy();
    }
    return true;
}
#endif
