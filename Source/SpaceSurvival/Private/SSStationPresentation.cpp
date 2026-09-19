#include "SSStationPresentation.h"
#include "Animation/AnimSequence.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
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

void BuildSupplementalStaff(AActor *Owner)
{
    if (!IsValid(Owner) || !Owner->GetRootComponent())
        return;
    struct FStaffSource
    {
        const TCHAR *Name;
        const TCHAR *Mesh;
        const TCHAR *Idle;
        FVector Center;
        float Height;
        float Yaw;
        float Rate;
    };
    const FStaffSource Sources[] = {
        {TEXT("StationHeavyTrooper"),
         TEXT("/Game/Heavy_space_trooper/character/mesh/Heavy_space_trooper_A_Pose.Heavy_space_trooper_A_Pose"),
         TEXT("/Game/Heavy_space_trooper/Demo/animations/ThirdPersonIdle.ThirdPersonIdle"),
         FVector(-1450.f, 1120.f, 88.f), 190.f, 90.f, .86f},
        {TEXT("StationCompanionDrone"),
         TEXT("/Game/SpaceSurvival/Licensed/StationAssets/Drone/SK_StationDrone.SK_StationDrone"),
         TEXT("/Game/SpaceSurvival/Licensed/StationAssets/Drone/A_DroneIdle.A_DroneIdle"),
         FVector(1390.f, -1080.f, 300.f), 95.f, -90.f, .72f},
    };
    for (const FStaffSource &Source : Sources)
    {
        if (!Owner->GetComponentsByTag(USkeletalMeshComponent::StaticClass(), FName(Source.Name)).IsEmpty())
            continue;
        bool Ready = true;
        for (const TCHAR *Path : {Source.Mesh, Source.Idle})
            if (!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(FString(Path))))
                Ready = false;
        if (!Ready)
            continue;
        if (auto *Mesh = LoadObject<USkeletalMesh>(nullptr, Source.Mesh))
            if (auto *Idle = LoadObject<UAnimSequence>(nullptr, Source.Idle))
                if (Mesh->GetSkeleton() == Idle->GetSkeleton() && !Mesh->GetMaterials().IsEmpty())
                {
                    const FBoxSphereBounds Bounds = Mesh->GetBounds();
                    const float NativeHeight = Bounds.BoxExtent.Z * 2.f;
                    if (FMath::IsFinite(NativeHeight) && NativeHeight > 1.f)
                    {
                        const float Scale = Source.Height / NativeHeight;
                        const FRotator Rotation(0.f, Source.Yaw, 0.f);
                        auto *Staff = NewObject<USkeletalMeshComponent>(Owner, FName(Source.Name));
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
                        Staff->ComponentTags.Add(FName(Source.Name));
                        const FVector Location = Source.Center - Rotation.RotateVector(Bounds.Origin * Scale);
                        Staff->SetRelativeTransform(FTransform(Rotation, Location, FVector(Scale)));
                        Owner->AddInstanceComponent(Staff);
                        Staff->RegisterComponent();
                        Staff->PlayAnimation(Idle, true);
                        Staff->SetPlayRate(Source.Rate);
                    }
                }
    }
}

// The alien clips are retargeted from the MoCap mannequin, and that mesh is authored facing +Y - the
// same convention BuildStaff relies on. A component turned straight at a heading therefore presents
// its shoulder, not its face, so every heading below gives up a quarter turn.
constexpr float AlienMeshFacesPlusY = 90.f;
constexpr int32 AlienGroupCount = 2;

// Who wanders, and how far. Deliberately only two of the seven: a group mid-conversation that drifts
// apart stops reading as a conversation.
struct FAlienPace
{
    const TCHAR *Name;
    FVector Center;
    float SpanX;
    float SpanY;
    float Speed;
    float Phase;
};
const FAlienPace AlienPacers[] = {
    {TEXT("StationAlienFidget"), FVector(1420.f, -820.f, 88.f), 96.f, 58.f, .42f, 0.f},
    {TEXT("StationAlienWatch"), FVector(-1420.f, 820.f, 88.f), 112.f, 64.f, .33f, 1.7f},
};

void BuildAlienCrew(AActor *Owner)
{
    if (!IsValid(Owner) || !Owner->GetRootComponent())
        return;

    // The pack ships a standard-proportion UE5 skeleton plus its own IK rig and retargeter, so these
    // clips are retarget results onto SKEL_Nyxar rather than anything hand-animated. They live under
    // /Game/SpaceSurvival, which always cooks; the mesh and its materials do not, which is why
    // Config/DefaultGame.ini names those three folders. Scripts/AuthorAlienCrew.py rebuilds both.
    const TCHAR *MeshPath = TEXT("/Game/Nyxar/Meshes/SKM_Nyxar.SKM_Nyxar");
    const FString AnimRoot = TEXT("/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/Anims/");
    const FString SkinRoot = TEXT("/Game/SpaceSurvival/Licensed/StationAssets/AlienCrew/");

    struct FAlien
    {
        const TCHAR *Name;
        const TCHAR *Clip;
        const TCHAR *Skin;
        FVector Center;
        int32 Group; // >=0 turns to face that group's centre; <0 faces Focus, or paces if listed below
        FVector Focus;
        float Height;
        float Rate;
        float Phase;
    };
    // Nobody is given a yaw. A conversation group faces the middle of its own circle, worked out below
    // from where its members actually stand, so moving one of them re-aims the others instead of
    // leaving a group talking past each other. The two solitary figures pace, and take their heading
    // from the direction they are travelling.
    const FVector ServiceCounter(700.f, -500.f, 88.f);
    const FVector DockMouth(-1710.f, 0.f, 88.f);
    const FAlien Crew[] = {
        {TEXT("StationAlienTalkerA"), TEXT("A_Alien_Convo_01_Low_Key_Loop"), TEXT("MI_NyxarCrew_Teal"),
         FVector(620.f, 900.f, 88.f), 0, FVector::ZeroVector, 196.f, .95f, 0.f},
        {TEXT("StationAlienListenerA"), TEXT("A_Alien_Convo_11_Listening_Loop"), TEXT("MI_NyxarCrew_Amber"),
         FVector(820.f, 1000.f, 88.f), 0, FVector::ZeroVector, 189.f, .90f, .31f},
        {TEXT("StationAlienListenerB"), TEXT("A_Alien_Convo_11_Listening_Loop"), TEXT("MI_NyxarCrew_Violet"),
         FVector(760.f, 760.f, 88.f), 0, FVector::ZeroVector, 193.f, 1.02f, .62f},
        {TEXT("StationAlienTalkerB"), TEXT("A_Alien_Convo_01_Low_Key_Loop"), TEXT("MI_NyxarCrew_Jade"),
         FVector(-640.f, -860.f, 88.f), 1, FVector::ZeroVector, 191.f, .88f, .45f},
        {TEXT("StationAlienListenerC"), TEXT("A_Alien_Convo_11_Listening_Loop"), TEXT("MI_NyxarCrew_Rose"),
         FVector(-840.f, -960.f, 88.f), 1, FVector::ZeroVector, 198.f, .97f, .18f},
        {TEXT("StationAlienFidget"), TEXT("A_Alien_MOB1_Walk_F_Loop_IPC"), TEXT("MI_NyxarCrew_Pale"),
         FVector(1420.f, -820.f, 88.f), -1, ServiceCounter, 187.f, .92f, .55f},
        {TEXT("StationAlienWatch"), TEXT("A_Alien_Walk_06_Look_Around_Loop_IP"), TEXT("MI_NyxarCrew_Teal"),
         FVector(-1420.f, 820.f, 88.f), -1, DockMouth, 194.f, .88f, .10f},
    };

    if (!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(FString(MeshPath))))
        return;
    auto *Mesh = LoadObject<USkeletalMesh>(nullptr, MeshPath);
    if (!Mesh || Mesh->GetMaterials().IsEmpty())
        return;
    for (const auto &Slot : Mesh->GetMaterials())
        if (!Slot.MaterialInterface)
            return;
    const FBoxSphereBounds Bounds = Mesh->GetBounds();
    const float NativeHeight = Bounds.BoxExtent.Z * 2.f;
    if (!FMath::IsFinite(NativeHeight) || NativeHeight < 1.f)
        return;

    // The body sits in the last slot; the first is the eye-occlusion shader, which stays as shipped.
    const int32 BodySlot = Mesh->GetMaterials().Num() - 1;

    // Where each conversation circle actually sits, rather than where it was assumed to sit.
    FVector Centre[AlienGroupCount];
    int32 Members[AlienGroupCount];
    for (int32 Index = 0; Index < AlienGroupCount; ++Index)
    {
        Centre[Index] = FVector::ZeroVector;
        Members[Index] = 0;
    }
    for (const FAlien &Member : Crew)
        if (Member.Group >= 0 && Member.Group < AlienGroupCount)
        {
            Centre[Member.Group] += Member.Center;
            ++Members[Member.Group];
        }
    for (int32 Index = 0; Index < AlienGroupCount; ++Index)
        if (Members[Index] > 0)
            Centre[Index] /= float(Members[Index]);

    for (const FAlien &Member : Crew)
    {
        if (!Owner->GetComponentsByTag(USkeletalMeshComponent::StaticClass(), FName(Member.Name)).IsEmpty())
            continue;
        const FString ClipPath = AnimRoot + Member.Clip + TEXT(".") + Member.Clip;
        if (!FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(ClipPath)))
            continue;
        auto *Clip = LoadObject<UAnimSequence>(nullptr, *ClipPath);
        if (!Clip || Clip->GetSkeleton() != Mesh->GetSkeleton())
            continue;

        // A two-member circle puts its centre exactly between the pair, so facing the centre and
        // facing the partner are the same aim; a trio gets the circle, which is what reads as one
        // conversation rather than two separate ones.
        const FVector Target = Member.Group >= 0 && Member.Group < AlienGroupCount && Members[Member.Group] > 0
                                   ? Centre[Member.Group]
                                   : Member.Focus;
        const FVector Toward = Target - Member.Center;
        const float Heading = Toward.IsNearlyZero() ? 0.f : FMath::RadiansToDegrees(FMath::Atan2(Toward.Y, Toward.X));

        const float Scale = Member.Height / NativeHeight;
        const FRotator Rotation(0.f, Heading - AlienMeshFacesPlusY, 0.f);
        auto *Crewman = NewObject<USkeletalMeshComponent>(Owner, FName(Member.Name));
        Crewman->SetupAttachment(Owner->GetRootComponent());
        Crewman->SetSkeletalMeshAsset(Mesh);
        Crewman->SetCollisionProfileName(TEXT("NoCollision"));
        Crewman->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Crewman->SetGenerateOverlapEvents(false);
        Crewman->SetCanEverAffectNavigation(false);
        Crewman->SetMobility(EComponentMobility::Movable);
        Crewman->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
        Crewman->bEnableUpdateRateOptimizations = true;
        Crewman->bComponentUseFixedSkelBounds = true;
        Crewman->SetComponentTickInterval(1.f / 30.f);
        Crewman->ComponentTags.Add(TEXT("StationAlienCrew"));
        Crewman->ComponentTags.Add(FName(Member.Name));

        const FString SkinPath = SkinRoot + Member.Skin + TEXT(".") + Member.Skin;
        if (FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(SkinPath)))
            if (auto *Skin = LoadObject<UMaterialInterface>(nullptr, *SkinPath))
                Crewman->SetMaterial(BodySlot, Skin);

        const FVector Location = Member.Center - Rotation.RotateVector(Bounds.Origin * Scale);
        Crewman->SetRelativeTransform(FTransform(Rotation, Location, FVector(Scale)));
        Owner->AddInstanceComponent(Crewman);
        Crewman->RegisterComponent();
        Crewman->PlayAnimation(Clip, true);
        Crewman->SetPlayRate(Member.Rate);
        Crewman->SetPosition(Clip->GetPlayLength() * Member.Phase, false);
    }
}

void PaceAlienCrew(AActor *Owner)
{
    if (!IsValid(Owner) || !Owner->GetWorld())
        return;
    const float Time = Owner->GetWorld()->GetTimeSeconds();
    for (const FAlienPace &Route : AlienPacers)
    {
        const TArray<UActorComponent *> Found =
            Owner->GetComponentsByTag(USkeletalMeshComponent::StaticClass(), FName(Route.Name));
        if (Found.IsEmpty())
            continue;
        auto *Crewman = Cast<USkeletalMeshComponent>(Found[0]);
        if (!Crewman || !Crewman->GetSkeletalMeshAsset())
            continue;

        // A figure of eight, not a line: the heading comes from the derivative, so it is continuous
        // and nobody snaps round at the end of a leg. Amplitudes are under a metre - a few steps of
        // shifting weight near their post, not a patrol route.
        const float U = Time * Route.Speed + Route.Phase;
        const FVector Offset(Route.SpanX * FMath::Sin(U), Route.SpanY * FMath::Sin(2.f * U), 0.f);
        const FVector Velocity(Route.SpanX * FMath::Cos(U), 2.f * Route.SpanY * FMath::Cos(2.f * U), 0.f);
        const float Heading =
            Velocity.IsNearlyZero() ? 0.f : FMath::RadiansToDegrees(FMath::Atan2(Velocity.Y, Velocity.X));

        const FRotator Rotation(0.f, Heading - AlienMeshFacesPlusY, 0.f);
        const float Scale = Crewman->GetRelativeScale3D().X;
        const FBoxSphereBounds Bounds = Crewman->GetSkeletalMeshAsset()->GetBounds();
        const FVector Location = Route.Center + Offset - Rotation.RotateVector(Bounds.Origin * Scale);
        Crewman->SetRelativeLocationAndRotation(Location, Rotation);
    }
}

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
