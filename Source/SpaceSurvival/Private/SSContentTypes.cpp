#include "SSContentTypes.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Misc/PackageName.h"

bool FSSHeroDefinition::AssetInstalled(const FString &ObjectPath)
{
    return !ObjectPath.IsEmpty() && FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(ObjectPath));
}

bool FSSHeroDefinition::Installed(ESSHeroSlot Slot) const
{
    return AssetInstalled(MeshPath) && AssetInstalled(Slot == ESSHeroSlot::Pilot ? PilotClipPath : WalkClipPath);
}

FSSHeroDefinition FSSHeroDefinition::ResolvedPresentation() const
{
    FSSHeroDefinition Result = *this;
    if (Identity != ESSHeroIdentity::AlienFemale)
        return Result;
    const FSSHeroDefinition Legacy(ESSHeroIdentity::AlienFemale);
    if (MeshPath != Legacy.MeshPath || WalkClipPath != Legacy.WalkClipPath || IdleClipPath != Legacy.IdleClipPath ||
        RunClipPath != Legacy.RunClipPath)
        return Result;
    const FString Base = TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/");
    const FString Mesh = Base + TEXT("SK_AlienFemalePresentation.SK_AlienFemalePresentation");
    const FString Walk = Base + TEXT("A_AlienFemaleWalk.A_AlienFemaleWalk");
    const FString Idle = Base + TEXT("A_AlienFemaleIdle.A_AlienFemaleIdle");
    const FString Run = Base + TEXT("A_AlienFemaleRun.A_AlienFemaleRun");
    if (AssetInstalled(Mesh) && AssetInstalled(Walk) && AssetInstalled(Idle) && AssetInstalled(Run))
    {
        Result.MeshPath = Mesh;
        Result.WalkClipPath = Walk;
        Result.IdleClipPath = Idle;
        Result.RunClipPath = Run;
    }
    return Result;
}

float FSSHeroDefinition::RenderedScale(const USkeletalMesh *Mesh) const
{
    if (FitHeight <= 0.f || !Mesh)
        return MeshScale;
    const float Height = Mesh->GetBounds().BoxExtent.Z * 2.f;
    return Height > 1.f ? FitHeight / Height : 1.f;
}

double FSSHeroDefinition::ScaledSoleOffset(const USkeletalMesh *Mesh) const
{
    // A declared offset is a float product, as it always was; a fitted one is measured from bounds
    // that are doubles, and stays one. Both reach the caller at the width its arithmetic used.
    if (FitHeight <= 0.f || !Mesh)
        return SoleOffset * MeshScale;
    const FBoxSphereBounds Bounds = Mesh->GetBounds();
    return -(Bounds.Origin.Z - Bounds.BoxExtent.Z) * RenderedScale(Mesh);
}

bool FSSHeroDefinition::ResolveBone(const USkeletalMeshComponent *Mesh, FName Bone, FTransform &Out)
{
    Out = Mesh ? Mesh->GetComponentTransform() : FTransform::Identity;
    if (!Mesh || Bone.IsNone() || !Mesh->DoesSocketExist(Bone))
        return false;
    Out = Mesh->GetSocketTransform(Bone);
    return true;
}

bool FSSHullDefinition::Installed() const
{
    // Classic is always installed: ASSShip::HullAssetPath picks between three meshes the game has always
    // shipped, and which one it picks depends on a command-line flag, so there is no single path to test.
    // Anything else has to actually be present, and the Phoenix lives in a git-ignored licensed folder,
    // so a build without it is the ordinary state rather than a fault.
    return Identity == ESSHullIdentity::Classic || FSSHeroDefinition::AssetInstalled(MeshPath);
}
