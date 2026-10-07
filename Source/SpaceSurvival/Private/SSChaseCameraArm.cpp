#include "SSChaseCameraArm.h"

USSChaseCameraArm::USSChaseCameraArm()
{
    bInheritRoll = false;
}

void USSChaseCameraArm::EnableBankIndependentFollow()
{
    bBankIndependentFollow = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
    // GetDesiredRotation already excludes hull bank. Stripping its Euler roll afterward
    // would reintroduce a discontinuity when the nose passes through vertical flight.
    bInheritRoll = true;
}

void USSChaseCameraArm::ResetFollowFrame()
{
    // Keep the original authored anchor: its current relative position compensates
    // for the last hull bank and must not become the next flight's new offset.
    bHasFollowFrame = false;
}

void USSChaseCameraArm::TickComponent(float DeltaTime, ELevelTick TickType,
                                      FActorComponentTickFunction *ThisTickFunction)
{
    if (!bBankIndependentFollow)
    {
        Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
        return;
    }
    if (const USceneComponent *Parent = GetAttachParent())
    {
        const FVector Forward = Parent->GetForwardVector();
        if (!bHasAnchorOffset)
        {
            AnchorOffset = GetRelativeLocation();
            bHasAnchorOffset = true;
        }
        if (!bHasFollowFrame)
        {
            FollowFrame = Forward.Rotation().Quaternion();
            bHasFollowFrame = true;
        }
        else
        {
            // Transport the view by the change in nose direction, not the full body
            // rotation. A complete barrel roll therefore leaves the chase view alone.
            // This quaternion frame also remains continuous through pitch +/-90,
            // where rebuilding zero-roll Euler angles flips camera yaw by 180 degrees.
            const FVector PreviousForward = FollowFrame.GetForwardVector();
            const FQuat Turn = FVector::DotProduct(PreviousForward, Forward) < -.9999f
                                   ? FQuat(FollowFrame.GetUpVector(), PI)
                                   : FQuat::FindBetweenNormals(PreviousForward, Forward);
            FollowFrame = (Turn * FollowFrame).GetNormalized();
        }
        // The elevated Phoenix anchor must not circle the nose when the body rolls.
        // Preserve its authored local offset in the same continuous chase frame.
        SetWorldLocation(Parent->GetComponentLocation() +
                         FollowFrame.RotateVector(Parent->GetComponentScale() * AnchorOffset));
    }
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

FRotator USSChaseCameraArm::GetDesiredRotation() const
{
    const USceneComponent *Parent = GetAttachParent();
    if (!bBankIndependentFollow || !Parent)
        return Super::GetDesiredRotation();
    const FQuat Frame = bHasFollowFrame ? FollowFrame : Parent->GetForwardVector().Rotation().Quaternion();
    // Authored pitch and deliberate free-look are applied AFTER removing hull spin.
    return (Frame * GetRelativeRotation().Quaternion()).Rotator();
}
