#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "SSStation.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSVisualStationTestWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FSSVisualStationTestWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FSSVisualStationTestWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSVisualStationClearance, "SpaceSurvival.Integration.StationVisualClearance",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSVisualStationClearance::RunTest(const FString &)
{
    if (!FPackageName::DoesPackageExist(TEXT("/Game/SciFiCorridor/Meshes/SM_Floor_01")))
    {
        AddInfo(TEXT("SKIPPED licensed station dressing: optional Corridor assets are not installed. "
                     "This run does not establish licensed visual clearance."));
        return true;
    }
    const TCHAR *CargoPath = TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/Cargo/SM_ServiceCargo");
    const bool HasCargo = FPackageName::DoesPackageExist(CargoPath);
    if (!HasCargo)
        AddInfo(TEXT("Private cargo derivative is absent; this run verifies the installed Corridor dressing only."));

    // SSStation::CanAssistDocking protects Y +/-700 and deck-to-beam Z -10..967.5.
    // Extend the test volume through the exterior entrance frame and the whole
    // bay, so newly decorative geometry cannot visually obstruct either the
    // inbound approach or central walk/ship lane despite having no collision.
    const FBox ProtectedLane(FVector(-1900, -700, -10), FVector(1715, 700, 967.5));
    for (bool Home : {false, true})
    {
        FSSVisualStationTestWorld Fixture;
        if (!TestNotNull(TEXT("Create isolated station visual world"), Fixture.World))
            return false;
        auto *Hub = Fixture.World->SpawnActor<ASSStation>(FVector(16000, -8000, 5000), FRotator(0, 75, 0));
        if (!TestNotNull(TEXT("Spawn actual station with a nonidentity world transform"), Hub))
            return false;
        Hub->SetActorScale3D(FVector(1.25f));
        Hub->bUseLicensedPresentation = true;
        Hub->BuildHub(Home);
        const FString Context = Home ? TEXT("Home hangar: ") : TEXT("Service station: ");
        TInlineComponentArray<UStaticMeshComponent *> Batches;
        Hub->GetComponents(Batches);
        TSet<FName> PresentedMeshes;
        bool HasDetails = false;
        for (auto *Batch : Batches)
        {
            if (!Batch->ComponentHasTag(TEXT("StationVisualDetail")))
                continue;
            HasDetails = true;
            const FString Label = Context + Batch->GetName();
            TestTrue(Label + TEXT(" is registered and retained by the actual hub"),
                     Batch->IsRegistered() && Batch->GetOwner() == Hub &&
                         Batch->GetAttachParent() == Hub->GetRootComponent());
            TestEqual(Label + TEXT(" has no collision"), Batch->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
            TestFalse(Label + TEXT(" generates no overlaps"), Batch->GetGenerateOverlapEvents());
            TestFalse(Label + TEXT(" does not affect navigation"), Batch->CanEverAffectNavigation());
            UStaticMesh *Mesh = Batch->GetStaticMesh();
            if (!TestNotNull(Label + TEXT(" resolves its actual imported mesh"), Mesh))
                return false;
            PresentedMeshes.Add(Mesh->GetFName());
            const auto &Slots = Mesh->GetStaticMaterials();
            TestTrue(Label + TEXT(" has authored material slots"), Slots.Num() > 0);
            for (int32 Slot = 0; Slot < Slots.Num(); ++Slot)
                TestNotNull(FString::Printf(TEXT("%s resolves material slot %d"), *Label, Slot),
                            Batch->GetMaterial(Slot));
            auto *Instanced = Cast<UInstancedStaticMeshComponent>(Batch);
            const int32 InstanceCount = Instanced ? Instanced->GetInstanceCount() : 1;
            TestTrue(Label + TEXT(" contains visible geometry"), InstanceCount > 0);
            for (int32 Index = 0; Index < InstanceCount; ++Index)
            {
                const FString InstanceLabel = FString::Printf(TEXT("%s instance %d"), *Label, Index);
                FTransform WorldTransform = Batch->GetComponentTransform();
                if (Instanced && !TestTrue(InstanceLabel + TEXT(" exposes its real world transform"),
                                           Instanced->GetInstanceTransform(Index, WorldTransform, true)))
                    return false;
                const FTransform LocalTransform = WorldTransform.GetRelativeTransform(Hub->GetActorTransform());
                const FBox Bounds = Mesh->GetBoundingBox().TransformBy(LocalTransform.ToMatrixWithScale());
                TestTrue(InstanceLabel + TEXT(" has finite nonempty mesh bounds"),
                         Bounds.IsValid && !Bounds.Min.ContainsNaN() && !Bounds.Max.ContainsNaN() &&
                             Bounds.GetSize().GetMin() > 0);
                TestFalse(InstanceLabel + TEXT(" leaves the full entrance and central lane clear"),
                          Bounds.Intersect(ProtectedLane));
            }
        }
        // These assertions prevent a silently skipped asset/material load from
        // producing a vacuous clearance pass; instance counts are deliberately
        // unconstrained so the presentation can be tuned without weakening safety.
        TestTrue(Context + TEXT("actually builds the licensed visual pass"), HasDetails);
        TestTrue(Context + TEXT("includes the overhead machinery whose underside must clear the ship"),
                 PresentedMeshes.Contains(TEXT("SM_ReatorCelling")));
        TestTrue(Context + TEXT("includes the entrance frame whose sides must clear the opening"),
                 PresentedMeshes.Contains(TEXT("SM_Groove01")));
        if (HasCargo)
            TestTrue(Context + TEXT("includes the installed paid cargo with valid materials and safe placement"),
                     PresentedMeshes.Contains(TEXT("SM_ServiceCargo")));

        if (FPackageName::DoesPackageExist(
                TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P161_ElectricMeter_01")))
            TestTrue(Context + TEXT("includes installed service instruments with safe material-resolved bounds"),
                     PresentedMeshes.Contains(TEXT("SM_P161_ElectricMeter_01")));

        TInlineComponentArray<USkeletalMeshComponent *> StaffComponents;
        Hub->GetComponents(StaffComponents);
        int32 StaffCount = 0;
        bool HasMica = false;
        for (auto *Staff : StaffComponents)
        {
            if (!Staff->ComponentHasTag(TEXT("StationRobotStaff")))
                continue;
            ++StaffCount;
            HasMica |= Staff->ComponentHasTag(TEXT("StationRobotMica"));
            const FString Label = Context + Staff->GetName();
            TestTrue(Label + TEXT(" remains owned and attached to the actual hub"),
                     Staff->GetOwner() == Hub && Staff->IsRegistered() &&
                         Staff->GetAttachParent() == Hub->GetRootComponent() &&
                         Hub->GetInstanceComponents().Contains(Staff));
            TestEqual(Label + TEXT(" cannot block services or walking"), Staff->GetCollisionEnabled(),
                      ECollisionEnabled::NoCollision);
            TestFalse(Label + TEXT(" generates no overlaps"), Staff->GetGenerateOverlapEvents());
            TestFalse(Label + TEXT(" does not affect navigation"), Staff->CanEverAffectNavigation());
            TestTrue(Label + TEXT(" only animates when rendered at a bounded update frequency"),
                     Staff->VisibilityBasedAnimTickOption == EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered &&
                         Staff->GetComponentTickInterval() >= 1.f / 30.f && Staff->bEnableUpdateRateOptimizations);
            auto *Mesh = Staff->GetSkeletalMeshAsset();
            if (!TestNotNull(Label + TEXT(" has the native robot mesh"), Mesh))
                return false;
            for (int32 Slot = 0; Slot < Mesh->GetMaterials().Num(); ++Slot)
                TestNotNull(FString::Printf(TEXT("%s resolves skeletal material slot %d"), *Label, Slot),
                            Staff->GetMaterial(Slot));
            auto *Idle = Staff->GetSingleNodeInstance();
            if (!TestNotNull(Label + TEXT(" uses a single idle clip without an NPC animation blueprint"), Idle))
                return false;
            auto *Animation = Idle->GetAnimationAsset();
            if (!TestNotNull(Label + TEXT(" resolves its idle animation"), Animation))
                return false;
            TestTrue(Label + TEXT(" loops the matching source idle"),
                     Idle->IsLooping() && Animation->GetSkeleton() == Mesh->GetSkeleton() &&
                         Animation->GetName() == TEXT("ThirdPersonIdle"));
            const FTransform LocalTransform =
                Staff->GetComponentTransform().GetRelativeTransform(Hub->GetActorTransform());
            const FBox Bounds = Mesh->GetBounds().GetBox().TransformBy(LocalTransform.ToMatrixWithScale());
            TestFalse(Label + TEXT(" leaves the full entrance and central lane clear"),
                      Bounds.Intersect(ProtectedLane));
            TestTrue(Label + TEXT(" rests on the deck at human scale"),
                     FMath::IsNearlyEqual(Bounds.Min.Z, -7., .1) && FMath::IsNearlyEqual(Bounds.GetSize().Z, 190., .1));
        }
        TestTrue(Context + TEXT("never adds more than two animated staff"), StaffCount <= 2);
        if (FPackageName::DoesPackageExist(TEXT("/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21")) &&
            FPackageName::DoesPackageExist(TEXT("/Game/Robot_scout_R_21/Demo/Animations/ThirdPersonIdle")))
        {
            TestEqual(Context + TEXT("presents the two installed idle staff"), StaffCount, 2);
            TestTrue(Context + TEXT("provides the precise Mica visual replacement tag"), HasMica);
        }
    }
    return true;
}
#endif
