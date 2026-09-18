#include "SSStationPoseTransition.h"
#include "Animation/AnimSingleNodeInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

namespace
{
struct FSSStationPoseProxy : FAnimSingleNodeInstanceProxy
{
    explicit FSSStationPoseProxy(UAnimInstance *Instance) : FAnimSingleNodeInstanceProxy(Instance) {}
    FPoseSnapshot Source;
    uint32 Revision = MAX_uint32;
    float Blend = 1.f;

    virtual void PreUpdate(UAnimInstance *Instance, float DeltaSeconds) override
    {
        FAnimSingleNodeInstanceProxy::PreUpdate(Instance, DeltaSeconds);
        const auto *Transition = CastChecked<USSStationPoseTransition>(Instance);
        Blend = Transition->GetExitBlend();
        if (Revision != Transition->GetSourceRevision())
        {
            Source = Transition->GetSourcePose();
            Revision = Transition->GetSourceRevision();
        }
    }
    virtual bool Evaluate(FPoseContext &Output) override
    {
        const bool Result = FAnimSingleNodeInstanceProxy::Evaluate(Output);
        if (!Result || Blend >= 1.f || !Source.bIsValid)
            return Result;
        const FBoneContainer &Bones = Output.Pose.GetBoneContainer();
        for (FCompactPoseBoneIndex Index : Output.Pose.ForEachBoneIndex())
        {
            const int32 MeshIndex = Bones.MakeMeshPoseIndex(Index).GetInt();
            if (Source.LocalTransforms.IsValidIndex(MeshIndex))
            {
                const FTransform Target = Output.Pose[Index];
                Output.Pose[Index].Blend(Source.LocalTransforms[MeshIndex], Target, Blend);
                Output.Pose[Index].NormalizeRotation();
            }
        }
        return Result;
    }
};
} // namespace

FAnimInstanceProxy *USSStationPoseTransition::CreateAnimInstanceProxy()
{
    return new FSSStationPoseProxy(this);
}

const TCHAR *USSStationPoseTransition::RefusalReason(ESSPoseRefusal Refusal)
{
    switch (Refusal)
    {
    case ESSPoseRefusal::Accepted:
        return TEXT("accepted");
    case ESSPoseRefusal::NoMesh:
        return TEXT("the walker has no skeletal mesh to map the pose onto");
    case ESSPoseRefusal::InvalidSnapshot:
        return TEXT("the snapshot itself is not valid");
    case ESSPoseRefusal::DifferentMesh:
        return TEXT("the snapshot was taken on a different mesh");
    case ESSPoseRefusal::BoneCountMismatch:
        return TEXT("the snapshot has a different number of bones than this reference skeleton");
    case ESSPoseRefusal::BoneNameMismatch:
        return TEXT("a bone name differs from this reference skeleton at the same index");
    case ESSPoseRefusal::MalformedTransform:
        return TEXT("a bone transform is not finite or its rotation is not normalized");
    case ESSPoseRefusal::NotSharedRig:
        return TEXT("the hero walking the deck is not the hero flying the ship, so there is no seated "
                    "pose of its own to carry");
    case ESSPoseRefusal::NoSnapshot:
        return TEXT("no seated pose was handed to the exit at all");
    case ESSPoseRefusal::NoTransitionInstance:
        return TEXT("the mesh would not take the pose transition instance");
    }
    return TEXT("unknown");
}

bool USSStationPoseTransition::SetSourcePose(const FPoseSnapshot &Pose, ESSPoseRefusal *OutRefusal)
{
    // Index mapping is valid only for the exact same mesh and reference order.
    // Reject malformed/cross-mesh snapshots instead of blending unrelated bones.
    SourcePose.Reset();
    ExitBlend = 1.f;
    ++SourceRevision;
    auto Refuse = [OutRefusal](ESSPoseRefusal Refusal)
    {
        if (OutRefusal)
            *OutRefusal = Refusal;
        return Refusal == ESSPoseRefusal::Accepted;
    };
    const auto *Component = GetSkelMeshComponent();
    const auto *Mesh = Component ? Component->GetSkeletalMeshAsset() : nullptr;
    if (!Mesh)
        return Refuse(ESSPoseRefusal::NoMesh);
    if (!Pose.bIsValid)
        return Refuse(ESSPoseRefusal::InvalidSnapshot);
    if (Pose.SkeletalMeshName != Mesh->GetFName())
        return Refuse(ESSPoseRefusal::DifferentMesh);
    if (Pose.LocalTransforms.Num() != Mesh->GetRefSkeleton().GetNum() ||
        Pose.BoneNames.Num() != Pose.LocalTransforms.Num())
        return Refuse(ESSPoseRefusal::BoneCountMismatch);
    for (int32 I = 0; I < Pose.BoneNames.Num(); ++I)
    {
        if (Pose.BoneNames[I] != Mesh->GetRefSkeleton().GetBoneName(I))
            return Refuse(ESSPoseRefusal::BoneNameMismatch);
        if (Pose.LocalTransforms[I].ContainsNaN() || !Pose.LocalTransforms[I].IsRotationNormalized())
            return Refuse(ESSPoseRefusal::MalformedTransform);
    }
    SourcePose = Pose;
    ExitBlend = 0.f;
    return Refuse(ESSPoseRefusal::Accepted);
}

void USSStationPoseTransition::SetExitTime(float Seconds)
{
    const float Time = FMath::IsFinite(Seconds) ? FMath::Max(0.f, Seconds) : BlendDuration;
    const float Alpha = FMath::Clamp(Time / BlendDuration, 0.f, 1.f);
    ExitBlend = Alpha * Alpha * (3.f - 2.f * Alpha);
    if (Alpha >= 1.f && SourcePose.bIsValid)
    {
        SourcePose.Reset();
        ++SourceRevision;
    }
}
