#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/PoseSnapshot.h"
#include "SSStationPoseTransition.generated.h"

// Keeps the outgoing pilot pose while the actor-clock exit takes over. The proxy
// evaluates the existing sequence and stops blending before the authored rise.
UCLASS(Transient)
class SPACESURVIVAL_API USSStationPoseTransition : public UAnimSingleNodeInstance
{
    GENERATED_BODY()
public:
    static constexpr float BlendDuration = .18f;
    bool SetSourcePose(const FPoseSnapshot &Pose);
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
