#include "SSStationPresentation.h"
#include "Animation/AnimSequence.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"

namespace SSStationPresentation
{
namespace
{
void BuildStaff(AActor *Owner)
{
    const TCHAR *RobotPath = TEXT("/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21.SK_Robot_scout_R21");
    const TCHAR *IdlePath = TEXT("/Game/Robot_scout_R_21/Demo/Animations/ThirdPersonIdle.ThirdPersonIdle");
    for (const TCHAR *Path : {RobotPath, IdlePath})
        if (!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(FString(Path))))
            return;
    auto *Mesh = LoadObject<USkeletalMesh>(nullptr, RobotPath);
    auto *Idle = LoadObject<UAnimSequence>(nullptr, IdlePath);
    if (!Mesh || !Idle || Mesh->GetSkeleton() != Idle->GetSkeleton() || Mesh->GetMaterials().IsEmpty())
        return;
    for (const auto &Slot : Mesh->GetMaterials())
        if (!Slot.MaterialInterface)
            return;

    const auto Bounds = Mesh->GetBounds();
    const float Height = Bounds.BoxExtent.Z * 2.f;
    if (!FMath::IsFinite(Height) || Height < 1.f)
        return;
    const float Scale = 190.f / Height;
    for (int32 Index = 0; Index < 2; ++Index)
    {
        const FName Name(Index == 0 ? TEXT("StationRobotMica") : TEXT("StationRobotService"));
        auto *Staff = NewObject<USkeletalMeshComponent>(Owner, Name);
        Staff->SetupAttachment(Owner->GetRootComponent());
        Staff->SetSkeletalMeshAsset(Mesh);
        Staff->SetCollisionProfileName(TEXT("NoCollision"));
        Staff->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Staff->SetGenerateOverlapEvents(false);
        Staff->SetCanEverAffectNavigation(false);
        Staff->SetMobility(EComponentMobility::Movable);
        Staff->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
        Staff->bEnableUpdateRateOptimizations = true;
        Staff->bComponentUseFixedSkelBounds = true;
        Staff->SetComponentTickInterval(1.f / 30.f);
        Staff->ComponentTags.Add(TEXT("StationRobotStaff"));
        Staff->ComponentTags.Add(Name);
        // UE4 mannequin source faces +Y. Both staff face inward from their
        // service alcoves; normalized bounds rest on the existing deck surface.
        const FRotator Rotation(0, Index == 0 ? 180.f : 0.f, 0);
        const FVector Center = Index == 0 ? FVector(1110, 1130, 88) : FVector(-1050, -1250, 88);
        const FVector Location = Center - Rotation.RotateVector(Bounds.Origin * Scale);
        Staff->SetRelativeTransform(FTransform(Rotation, Location, FVector(Scale)));
        Owner->AddInstanceComponent(Staff);
        Staff->RegisterComponent();
        Staff->PlayAnimation(Idle, true);
        Staff->SetPlayRate(Index == 0 ? .85f : .95f);
        Staff->SetPosition(Index == 0 ? 0.f : Idle->GetPlayLength() * .47f, false);
    }
}
} // namespace

UMaterialInterface *InstancedMaterial(UMaterialInterface *Source)
{
    if (!Source)
        return nullptr;
    for (const TCHAR *Name : {TEXT("MI_Grid_Teto01"), TEXT("MI_TileTube")})
        if (Source->GetPathName() == FString::Printf(TEXT("/Game/SciFiCorridor/Materials/%s.%s"), Name, Name))
        {
            const FString PrivatePath =
                FString::Printf(TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/Materials/%s"), Name);
            if (FPackageName::DoesPackageExist(PrivatePath))
                if (auto *Material = LoadObject<UMaterialInterface>(nullptr, *PrivatePath))
                    return Material;
        }
    return Source;
}

void BuildDetails(AActor *Owner, TArray<TObjectPtr<UStaticMeshComponent>> &Geometry)
{
    if (!IsValid(Owner) || !Owner->GetRootComponent())
        return;

    auto Batch = [Owner, &Geometry](const TCHAR *Name, const TCHAR *Path)
    {
        if (!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(FString(Path))))
            return static_cast<UInstancedStaticMeshComponent *>(nullptr);
        auto *Mesh = LoadObject<UStaticMesh>(nullptr, Path);
        if (!Mesh)
            return static_cast<UInstancedStaticMeshComponent *>(nullptr);
        // A missing material must not leave visible checkerboard dressing.
        for (const auto &Slot : Mesh->GetStaticMaterials())
            if (!Slot.MaterialInterface)
                return static_cast<UInstancedStaticMeshComponent *>(nullptr);
        auto *Result = NewObject<UInstancedStaticMeshComponent>(Owner, FName(Name));
        Result->SetupAttachment(Owner->GetRootComponent());
        Result->SetStaticMesh(Mesh);
        for (int32 Slot = 0; Slot < Mesh->GetStaticMaterials().Num(); ++Slot)
            Result->SetMaterial(Slot, InstancedMaterial(Mesh->GetMaterial(Slot)));
        Result->SetCollisionProfileName(TEXT("NoCollision"));
        Result->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Result->SetGenerateOverlapEvents(false);
        Result->SetCanEverAffectNavigation(false);
        Result->SetMobility(EComponentMobility::Movable);
        Result->ComponentTags.Add(TEXT("StationVisualDetail"));
        Result->RegisterComponent();
        Geometry.Add(Result);
        return Result;
    };
    // Use actual imported bounds rather than assumptions about vendor pivots.
    auto Place = [](UInstancedStaticMeshComponent *Target, FVector Center, FVector Scale,
                    FRotator Rotation = FRotator::ZeroRotator)
    {
        if (!Target)
            return;
        const FVector Origin = Target->GetStaticMesh()->GetBounds().Origin;
        const FVector Location = Center - Rotation.RotateVector(Origin * Scale);
        Target->AddInstance(FTransform(Rotation, Location, Scale));
    };

    auto *Reactors =
        Batch(TEXT("StationCeilingMachinery"), TEXT("/Game/SciFiCorridor/Meshes/SM_ReatorCelling.SM_ReatorCelling"));
    // Undersides stay above the exact 967.5cm flight clearance; side machinery
    // remains outside the protected central +/-700cm docking corridor.
    Place(Reactors, FVector(-650, 0, 989), FVector(.45f));
    Place(Reactors, FVector(650, 0, 989), FVector(.45f));
    Place(Reactors, FVector(200, -1080, 965), FVector(.52f));
    Place(Reactors, FVector(-600, 1080, 965), FVector(.52f));

    auto *Pipes = Batch(TEXT("StationServicePipes"), TEXT("/Game/SciFiCorridor/Meshes/SM_Tube.SM_Tube"));
    auto *Cables =
        Batch(TEXT("StationServiceCables"), TEXT("/Game/SciFiCorridor/Meshes/SM_CorridorCable02.SM_CorridorCable02"));
    for (float Side : {-1.f, 1.f})
    {
        for (float X : {-1320.f, -320.f, 720.f, 1510.f})
        {
            // Closed conduits rise along the wall behind terminals and labels.
            Place(Pipes, FVector(X, Side * 1305.f, 650), FVector(.72f, .72f, 2.8f));
            Place(Cables, FVector(X + 37, Side * 1305.f, 650), FVector(1.f, 1.f, 2.8f));
        }
        for (int32 Index = 0; Index < 7; ++Index)
        {
            // Ceiling-level utility runs have near-native thickness.
            const float X = -1350.f + Index * 440.f;
            Place(Pipes, FVector(X, Side * 1295.f, 875), FVector(.65f, .65f, 2.2f), FRotator(90, 0, 0));
            Place(Cables, FVector(X, Side * 1240.f, 875), FVector(.85f, .85f, 2.2f), FRotator(90, 0, 0));
        }
    }

    auto *Cargo = Batch(TEXT("StationServiceCargo"),
                        TEXT("/Game/SpaceSurvival/Licensed/StationVisualPass/Cargo/SM_ServiceCargo.SM_ServiceCargo"));
    Place(Cargo, FVector(1320, -1240, 40), FVector(.8f), FRotator(0, 12, 0));
    Place(Cargo, FVector(1320, -1240, 112), FVector(.64f), FRotator(0, -6, 0));
    Place(Cargo, FVector(1460, 1190, 50), FVector(1), FRotator(0, -18, 0));

    auto *Cases = Batch(TEXT("StationServiceCases"), TEXT("/Game/SciFiCorridor/Meshes/SM_ArmoryBox.SM_ArmoryBox"));
    Place(Cases, FVector(-1450, 1190, 24), FVector(1.2f), FRotator(0, 90, 0));
    Place(Cases, FVector(-1435, 1190, 61), FVector(.65f), FRotator(0, 85, 0));
    Place(Cases, FVector(1540, 750, 20), FVector(1), FRotator(0, 90, 0));

    // Equipment stays against the perimeter, away from the functional consoles.
    auto *Controls =
        Batch(TEXT("StationBenchControls"), TEXT("/Game/SciFiCorridor/Meshes/SM_RemoteControl.SM_RemoteControl"));
    Place(Controls, FVector(1040, 1120, 130), FVector(.8f), FRotator(0, 180, 0));
    Place(Controls, FVector(-1450, 1190, 81), FVector(.8f), FRotator(0, 100, 0));

    // A continuous ribbed frame makes the actual docking opening legible. Its
    // side faces remain beyond +/-700cm and the lintel stays above967.5cm.
    auto *DockFrame = Batch(TEXT("StationDockEntryFrame"), TEXT("/Game/SciFiCorridor/Meshes/SM_Groove01.SM_Groove01"));
    Place(DockFrame, FVector(-1710, -732, 480), FVector(1, 2.13f, 1.8f), FRotator(0, 0, 90));
    Place(DockFrame, FVector(-1710, 732, 480), FVector(1, 2.13f, 1.8f), FRotator(0, 0, 90));
    Place(DockFrame, FVector(-1710, 0, 984), FVector(1, 3.3f, 1.8f));

    // A few unique native props do not require instancing shader permutations
    // in the supplied materials. Vendor mesh/material packages stay unchanged.
    auto Prop = [Owner, &Geometry](const TCHAR *Name, const TCHAR *Path, FVector Center, FVector Scale,
                                   FRotator Rotation = FRotator::ZeroRotator)
    {
        if (!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(FString(Path))))
            return;
        auto *Mesh = LoadObject<UStaticMesh>(nullptr, Path);
        if (!Mesh || Mesh->GetStaticMaterials().IsEmpty())
            return;
        for (const auto &Slot : Mesh->GetStaticMaterials())
            if (!Slot.MaterialInterface)
                return;
        auto *Detail = NewObject<UStaticMeshComponent>(Owner, FName(Name));
        Detail->SetupAttachment(Owner->GetRootComponent());
        Detail->SetStaticMesh(Mesh);
        Detail->SetCollisionProfileName(TEXT("NoCollision"));
        Detail->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Detail->SetGenerateOverlapEvents(false);
        Detail->SetCanEverAffectNavigation(false);
        Detail->SetMobility(EComponentMobility::Movable);
        Detail->ComponentTags.Add(TEXT("StationVisualDetail"));
        const FVector Location = Center - Rotation.RotateVector(Mesh->GetBounds().Origin * Scale);
        Detail->SetRelativeTransform(FTransform(Rotation, Location, Scale));
        Detail->RegisterComponent();
        Geometry.Add(Detail);
    };
    // Native wall instruments are authored flat in XY; their +Z faces rotate
    // inward. All equipment stays behind services and outside the central lane.
    Prop(TEXT("StationRepairMeter"),
         TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P161_ElectricMeter_01.SM_P161_ElectricMeter_01"),
         FVector(-910, -1290, 265), FVector(3), FRotator(0, 0, -90));
    Prop(TEXT("StationModuleMeter"),
         TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P161_ElectricMeter_02.SM_P161_ElectricMeter_02"),
         FVector(1260, 1290, 265), FVector(3), FRotator(0, 0, 90));
    Prop(TEXT("StationRepairSwitch"),
         TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P160_switch.SM_P160_switch"),
         FVector(-825, -1290, 195), FVector(2.5f), FRotator(0, 0, -90));
    Prop(TEXT("StationModuleSwitch"),
         TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P160_switch.SM_P160_switch"), FVector(1345, 1290, 195),
         FVector(2.5f), FRotator(0, 0, 90));
    Prop(TEXT("StationRepairAnnunciator"),
         TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P158_annunciator_01.SM_P158_annunciator_01"),
         FVector(-910, -1290, 365), FVector(2.5f), FRotator(0, 0, -90));
    Prop(TEXT("StationModuleAnnunciator"),
         TEXT("/Game/Defect/StaticMeshes/Props/WallDecoration/SM_P158_annunciator_02.SM_P158_annunciator_02"),
         FVector(1260, 1290, 365), FVector(2.5f), FRotator(0, 0, 90));
    Prop(TEXT("StationServiceLamp"), TEXT("/Game/Defect/StaticMeshes/Props/Photo/SM_P163_lamp.SM_P163_lamp"),
         FVector(1180, 1290, 445), FVector(3.5f), FRotator(0, 0, 90));

    BuildStaff(Owner);
}
} // namespace SSStationPresentation
