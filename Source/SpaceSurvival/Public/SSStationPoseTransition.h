#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/PoseSnapshot.h"
#include "SSStationPoseTransition.generated.h"

/** Why a seated pose could not be reused. The index mapping is only valid for the exact same mesh in
 *  the exact same reference order, so every value but Accepted names a real rig mismatch that the
 *  caller has to be able to say out loud rather than discard.
 *
 *  The last three are the caller's own reasons: SetSourcePose never returns them, because in those
 *  cases it is never reached. They live here so the walker has one vocabulary for the single question
 *  a reader actually asks, which is why the hero snapped into the exit clip instead of rising out of
 *  the seat. The common answer today is NotSharedRig, and it was the one that used to go unsaid. */
enum class ESSPoseRefusal : uint8
{
    Accepted,
    NoMesh,
    InvalidSnapshot,
    DifferentMesh,
    BoneCountMismatch,
    BoneNameMismatch,
    MalformedTransform,
    NotSharedRig,
    NoSnapshot,
    NoTransitionInstance
};

// Keeps the outgoing pilot pose while the actor-clock exit takes over. The proxy
// evaluates the existing sequence and stops blending before the authored rise.
UCLASS(Transient)
class SPACESURVIVAL_API USSStationPoseTransition : public UAnimSingleNodeInstance
{
    GENERATED_BODY()
public:
    static constexpr float BlendDuration = .18f;
    bool SetSourcePose(const FPoseSnapshot &Pose, ESSPoseRefusal *OutRefusal = nullptr);
    static const TCHAR *RefusalReason(ESSPoseRefusal Refusal);
    void SetExitTime(float Seconds);
    const FPoseSnapshot &GetSourcePose() const
    {
        return SourcePose;
    }
    float GetExitBlend() const
    {
        return ExitBlend;
    }
    uint32 GetSourceRevision() const
    {
        return SourceRevision;
    }

protected:
    virtual FAnimInstanceProxy *CreateAnimInstanceProxy() override;

private:
    UPROPERTY(Transient)
    FPoseSnapshot SourcePose;
    float ExitBlend = 1.f;
    uint32 SourceRevision = 0;
};
