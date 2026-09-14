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

bool USSStationPoseTransition::SetSourcePose(const FPoseSnapshot &Pose)
{
    // Index mapping is valid only for the exact same mesh and reference order.
    // Reject malformed/cross-mesh snapshots instead of blending unrelated bones.
    SourcePose.Reset();
    ExitBlend = 1.f;
    ++SourceRevision;
    const auto *Component = GetSkelMeshComponent();
    const auto *Mesh = Component ? Component->GetSkeletalMeshAsset() : nullptr;
    if (!Mesh || !Pose.bIsValid || Pose.SkeletalMeshName != Mesh->GetFName() ||
        Pose.LocalTransforms.Num() != Mesh->GetRefSkeleton().GetNum() ||
        Pose.BoneNames.Num() != Pose.LocalTransforms.Num())
        return false;
    for (int32 I = 0; I < Pose.BoneNames.Num(); ++I)
        if (Pose.BoneNames[I] != Mesh->GetRefSkeleton().GetBoneName(I) || Pose.LocalTransforms[I].ContainsNaN() ||
            !Pose.LocalTransforms[I].IsRotationNormalized())
            return false;
    SourcePose = Pose;
    ExitBlend = 0.f;
    return true;
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
