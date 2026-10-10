#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SpringArmComponent.h"
#include "SSChaseCameraArm.generated.h"

/** Follows the flight direction without inheriting the hull's bank or Euler pole flips. */
UCLASS()
class SPACESURVIVAL_API USSChaseCameraArm : public USpringArmComponent
{
    GENERATED_BODY()

public:
    USSChaseCameraArm();
    /** Opt in only for the physics hull; classic flight retains the ordinary spring arm. */
    void EnableBankIndependentFollow();
    /** A completed dock starts a new chase shot without retaining the previous flight's bank. */
    void ResetFollowFrame();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;
    virtual FRotator GetDesiredRotation() const override;

private:
    FQuat FollowFrame = FQuat::Identity;
    FVector AnchorOffset = FVector::ZeroVector;
    bool bBankIndependentFollow = false;
    bool bHasFollowFrame = false;
    bool bHasAnchorOffset = false;
};
