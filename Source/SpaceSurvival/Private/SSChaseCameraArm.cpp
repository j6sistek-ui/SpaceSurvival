#include "SSChaseCameraArm.h"
#include "SSShip.h"
#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"

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
    RouteCameraOffset = FVector2D::ZeroVector;
    RouteReleaseOffset = FVector::ZeroVector;
}

FQuat USSChaseCameraArm::GetFlightFrame() const
{
    if (bRouteFollow)
        return RouteFrame;
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

void USSChaseCameraArm::SetRouteFrame(bool bEnabled, const FQuat &Frame)
{
    if (bEnabled != bRouteFollow)
    {
        if (!bEnabled && bHasAnchorOffset)
            if (const USceneComponent *Parent = GetAttachParent())
                RouteReleaseOffset = GetComponentLocation() - Parent->GetComponentLocation() -
                                     FollowFrame.RotateVector(Parent->GetComponentScale() * AnchorOffset);
        RouteCameraOffset = FVector2D::ZeroVector;
        if (bEnabled)
            RouteReleaseOffset = FVector::ZeroVector;
    }
    bRouteFollow = bEnabled;
    RouteFrame = Frame.GetNormalized();
    bInheritRoll = bBankIndependentFollow || bRouteFollow;
}

FVector USSChaseCameraArm::WaveFollowLocation(const ASSShip *Ship, const USceneComponent *Parent, float DeltaTime)
{
    const FVector Anchor = FollowFrame.RotateVector(Parent->GetComponentScale() * AnchorOffset);
    const FVector Centre = Ship->GetFlightRouteCenter();
    const FVector ShipOffset = FollowFrame.UnrotateVector(Parent->GetComponentLocation() - Centre);
    const FVector2D Across(ShipOffset.Y, ShipOffset.Z);
    const FQuat ArmRotation = (FollowFrame * GetRelativeRotation().Quaternion()).GetNormalized();
    const FQuat ViewRotation = (ArmRotation * Ship->Camera->GetRelativeRotation().Quaternion()).GetNormalized();
    // The same unlagged socket construction as the spring arm. The authored height/pitch stay intact;
    // only the lateral anchor is allowed to lag behind the ship's movement across the screen.
    const FVector Eye = Parent->GetComponentLocation() + Anchor + TargetOffset -
                        ArmRotation.GetForwardVector() * TargetArmLength + ArmRotation.RotateVector(SocketOffset) +
                        ArmRotation.RotateVector(Ship->Camera->GetRelativeLocation());
    FBox HullBounds(ForceInit);
    FTransform MeshTransform;
    if (Ship->SkeletalHull && Ship->SkeletalHull->IsVisible() && Ship->SkeletalHull->GetSkeletalMeshAsset())
    {
        HullBounds = Ship->SkeletalHull->GetSkeletalMeshAsset()->GetBounds().GetBox();
        MeshTransform = Ship->SkeletalHull->GetComponentTransform();
    }
    else if (Ship->HullMesh && Ship->HullMesh->GetStaticMesh())
    {
        HullBounds = Ship->HullMesh->GetStaticMesh()->GetBounds().GetBox();
        MeshTransform = Ship->HullMesh->GetComponentTransform();
    }
    if (!HullBounds.IsValid)
        return Parent->GetComponentLocation() + Anchor;
    float Aspect = FMath::Max(.5f, Ship->Camera->AspectRatio);
    if (GetWorld() && GetWorld()->GetGameViewport())
    {
        FVector2D Size;
        GetWorld()->GetGameViewport()->GetViewportSize(Size);
        if (Size.X > 0. && Size.Y > 0.)
            Aspect = float(Size.X / Size.Y);
    }
    const double TanHorizontal = FMath::Tan(FMath::DegreesToRadians(Ship->Camera->FieldOfView * .5));
    const double TanVertical = TanHorizontal / Aspect;
    const FVector ViewRight = ViewRotation.UnrotateVector(FollowFrame.GetRightVector());
    const FVector ViewUp = ViewRotation.UnrotateVector(FollowFrame.GetUpVector());
    FVector Corners[8];
    for (int32 Index = 0; Index < 8; ++Index)
    {
        const FVector Local(Index & 1 ? HullBounds.Max.X : HullBounds.Min.X,
                            Index & 2 ? HullBounds.Max.Y : HullBounds.Min.Y,
                            Index & 4 ? HullBounds.Max.Z : HullBounds.Min.Z);
        Corners[Index] = ViewRotation.UnrotateVector(MeshTransform.TransformPosition(Local) - Eye);
    }
    auto FitDisplacement = [&](FVector2D Displacement, double Margin)
    {
        // Each screen edge is a half-plane in lateral displacement. Projecting against all four
        // includes the camera's pitched view and the full rolling hull, rather than only its origin.
        const double Horizontal = TanHorizontal * (1. - 2. * Margin);
        const double Vertical = TanVertical * (1. - 2. * Margin);
        const FVector Planes[] = {FVector(-Horizontal, 1, 0), FVector(-Horizontal, -1, 0), FVector(-Vertical, 0, 1),
                                  FVector(-Vertical, 0, -1)};
        FVector2D Axes[4];
        double Limits[4];
        for (int32 Edge = 0; Edge < 4; ++Edge)
        {
            Axes[Edge] =
                FVector2D(FVector::DotProduct(Planes[Edge], ViewRight), FVector::DotProduct(Planes[Edge], ViewUp));
            Limits[Edge] = TNumericLimits<double>::Max();
            for (const FVector &Corner : Corners)
                Limits[Edge] = FMath::Min(Limits[Edge], -FVector::DotProduct(Planes[Edge], Corner));
        }
        for (int32 Pass = 0; Pass < 4; ++Pass)
            for (int32 Edge = 0; Edge < 4; ++Edge)
            {
                const double Excess = FVector2D::DotProduct(Axes[Edge], Displacement) - Limits[Edge];
                if (Excess > 0. && Axes[Edge].SizeSquared() > UE_SMALL_NUMBER)
                    Displacement -= Axes[Edge] * (Excess / Axes[Edge].SizeSquared());
            }
        return Displacement;
    };
    const double HullMargin = FSSHullDefinition(ASSShip::SelectedHullIdentity()).FrameMarginShare;
    const FVector2D Desired = Across - FitDisplacement(Across - RouteCameraOffset, HullMargin + .10);
    const float Follow = 1.f - FMath::Exp(-5.f * FMath::Max(0.f, DeltaTime));
    RouteCameraOffset = FMath::Lerp(RouteCameraOffset, Desired, Follow);
    // A fast edge dodge or changing bank can outrun the soft follow. Keep the whole hull inside the
    // outer border; its extra margin also covers the ordinary spring arm's bounded positional lag.
    RouteCameraOffset = Across - FitDisplacement(Across - RouteCameraOffset, HullMargin + .02);
    return Centre + Anchor + FollowFrame.RotateVector(FVector(0, RouteCameraOffset.X, RouteCameraOffset.Y));
}

void USSChaseCameraArm::TickComponent(float DeltaTime, ELevelTick TickType,
                                      FActorComponentTickFunction *ThisTickFunction)
{
    if (!bBankIndependentFollow && !bRouteFollow)
    {
        // A classic hull returns to its ordinary parent-relative spring arm after route travel.
        if (bHasAnchorOffset)
            if (const USceneComponent *Parent = GetAttachParent())
            {
                RouteReleaseOffset *= FMath::Exp(-5.f * FMath::Max(0.f, DeltaTime));
                SetWorldLocation(Parent->GetComponentTransform().TransformPosition(AnchorOffset) + RouteReleaseOffset);
            }
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
        if (const ASSShip *Ship = Cast<ASSShip>(GetOwner()); bRouteFollow && Ship && Ship->IsInWaveCorridor())
            SetWorldLocation(WaveFollowLocation(Ship, Parent, DeltaTime));
        else
        {
            RouteReleaseOffset *= FMath::Exp(-5.f * FMath::Max(0.f, DeltaTime));
            SetWorldLocation(Parent->GetComponentLocation() +
                             FollowFrame.RotateVector(Parent->GetComponentScale() * AnchorOffset) + RouteReleaseOffset);
        }
    }
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

FRotator USSChaseCameraArm::GetDesiredRotation() const
{
    const USceneComponent *Parent = GetAttachParent();
    if ((!bBankIndependentFollow && !bRouteFollow) || !Parent)
        return Super::GetDesiredRotation();
    const FQuat Frame = bHasFollowFrame ? FollowFrame : Parent->GetForwardVector().Rotation().Quaternion();
    // Authored pitch and deliberate free-look are applied AFTER removing hull spin.
    return (Frame * GetRelativeRotation().Quaternion()).Rotator();
}
