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
