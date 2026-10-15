#include "SSBarEyeAuthoring.h"
#include "Animation/Skeleton.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/Package.h"

USkeleton *USSBarEyeAuthoring::CreateAstraEyeSkeleton(USkeletalMesh *PrivateMesh)
{
#if WITH_EDITOR
    const FString Root = TEXT("/Game/SpaceSurvival/Licensed/StationAssets/Waitress_20261015/Eyes/");
    const TArray<FString> Names = {TEXT("SK_Eyes_WhitePurpleRings"), TEXT("SK_Eyes_BlueNebula"),
                                   TEXT("SK_Eyes_PearlFlower"), TEXT("SK_Eyes_DarkMagenta"),
                                   TEXT("SK_Eyes_PurpleMandala")};
    if (!PrivateMesh || !Names.Contains(PrivateMesh->GetName()) ||
        PrivateMesh->GetPathName() != Root + PrivateMesh->GetName() + TEXT(".") + PrivateMesh->GetName())
        return nullptr;
    const auto &Ref = PrivateMesh->GetRefSkeleton();
    if (Ref.GetNum() < 3 || Ref.GetNum() > 5 || Ref.FindBoneIndex(TEXT("Eye_L")) == INDEX_NONE ||
        Ref.FindBoneIndex(TEXT("Eye_R")) == INDEX_NONE)
        return nullptr;
    for (const auto &Bone : Ref.GetRefBonePose())
        if (Bone.ContainsNaN())
            return nullptr;
    const FString Package = Root + TEXT("S_AstraEyes");
    if (auto *Existing = LoadObject<USkeleton>(nullptr, *(Package + TEXT(".S_AstraEyes"))))
    {
        // Reuse only an identical reference rig. Never rewrite its bones or the mesh geometry.
        const auto &Bones = Existing->GetReferenceSkeleton();
        if (Bones.GetNum() != Ref.GetNum())
            return nullptr;
        for (int32 I = 0; I < Ref.GetNum(); ++I)
            if (Bones.GetBoneName(I) != Ref.GetBoneName(I) || Bones.GetParentIndex(I) != Ref.GetParentIndex(I) ||
                !Bones.GetRefBonePose()[I].Equals(Ref.GetRefBonePose()[I], .001f))
                return nullptr;
        PrivateMesh->SetSkeleton(Existing);
        PrivateMesh->MarkPackageDirty();
        return Existing;
    }
    if (PrivateMesh->GetName() != TEXT("SK_Eyes_WhitePurpleRings"))
        return nullptr;
    auto *Skeleton = NewObject<USkeleton>(CreatePackage(*Package), TEXT("S_AstraEyes"),
                                          RF_Public | RF_Standalone | RF_Transactional);
    if (!Skeleton->MergeAllBonesToBoneTree(PrivateMesh, false))
    {
        Skeleton->ClearFlags(RF_Public | RF_Standalone);
        return nullptr;
    }
    PrivateMesh->SetSkeleton(Skeleton);
    Skeleton->SetPreviewMesh(PrivateMesh);
    Skeleton->MarkPackageDirty();
    PrivateMesh->MarkPackageDirty();
    return Skeleton;
#else
    return nullptr;
#endif
}
