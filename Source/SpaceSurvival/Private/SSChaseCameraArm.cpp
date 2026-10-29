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

FQuat USSChaseCameraArm::GetFlightFrame() const
{
    const USceneComponent *Parent = GetAttachParent();
    if (!Parent)
        return FQuat::Identity;
    if (!bBankIndependentFollow)
        return Parent->GetComponentQuat();
    const FVector Forward = Parent->GetForwardVector();
    if (!bHasFollowFrame)
        return Forward.Rotation().Quaternion();
    const FVector PreviousForward = FollowFrame.GetForwardVector();
    const FQuat Turn = FVector::DotProduct(PreviousForward, Forward) < -.9999f
                           ? FQuat(FollowFrame.GetUpVector(), PI)
                           : FQuat::FindBetweenNormals(PreviousForward, Forward);
    return (Turn * FollowFrame).GetNormalized();
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
        if (!bHasAnchorOffset)
        {
            AnchorOffset = GetRelativeLocation();
            bHasAnchorOffset = true;
        }
        // Steering and the post-physics view share this pole-safe frame. Reading it
        // before physics does not advance the camera or include deliberate free-look.
        FollowFrame = GetFlightFrame();
        bHasFollowFrame = true;
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
