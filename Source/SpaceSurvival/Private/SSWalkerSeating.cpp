#include "SSStation.h"
#include "SSStationSeat.h"
#include "SSStationPoseTransition.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Engine/World.h"

bool ASSWalker::SitAt(ASSStationSeat *Seat)
{
    FTransform Exit;
    if (bResting || Boarding || Disembarking || !GetCharacterMovement()->IsMovingOnGround() || !IsValid(Seat) ||
        !Seat->CanReach(this) || !Seat->IsAvailable(this) || !Seat->FindExit(this, Exit) ||
        !GetMesh()->DoesSocketExist(Hero.PelvisBone))
        return false;
    RestStart = GetActorTransform();
    RestCameraLocation = Boom->GetRelativeLocation();
    RestCollision = GetCapsuleComponent()->GetCollisionEnabled();
    FPoseSnapshot Outgoing;
    GetMesh()->SnapshotPose(Outgoing);
    // Measure the actual pose at the hero's actual scale before fitting its pelvis to the cushion.
    PlayClip(Seat->ClipFor(this), 0.f, true, 1.f, false);
    GetMesh()->TickAnimation(0.f, false);
    GetMesh()->RefreshBoneTransforms();
    const FVector PelvisLocal =
        GetActorTransform().InverseTransformPosition(GetMesh()->GetSocketLocation(Hero.PelvisBone));
    RestTarget = FTransform(Seat->GetActorRotation(), Seat->GetActorLocation(), GetActorScale3D());
    RestTarget.AddToTranslation(FVector(0, 0, Seat->PelvisHeight) - RestTarget.TransformVector(PelvisLocal));
    GetMesh()->SetAnimInstanceClass(USSStationPoseTransition::StaticClass());
    if (auto *Transition = Cast<USSStationPoseTransition>(GetMesh()->GetAnimInstance()))
    {
        Transition->SetAnimationAsset(Seat->ClipFor(this), true, 1.f);
        Transition->SetRootMotionMode(ERootMotionMode::NoRootMotionExtraction);
        Transition->SetSourcePose(Outgoing);
        Transition->SetTailFloor(NAME_None, {}, {});
    }
    RestSeat = Seat;
    Seat->Occupant = this;
    bResting = true;
    RestSeconds = 0.f;
    LandingTailSeconds = -1.f;
    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->DisableMovement();
    ConsumeMovementInputVector();
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    return true;
}

bool ASSWalker::StandFromSeat()
{
    if (!bResting)
        return false;
    FTransform Exit = RestStart;
    if (RestSeat.IsValid())
    {
        // Recheck now: a person or prop may have moved into the aisle while we were seated.
        if (!RestSeat->FindExit(this, Exit))
            return false;
        RestSeat->Occupant.Reset();
    }
    else
    {
        FCollisionQueryParams Query(SCENE_QUERY_STAT(SSRemovedSeatExit), false, this);
        if (GetWorld()->OverlapBlockingTestByChannel(Exit.GetLocation(), Exit.GetRotation(), ECC_Pawn,
                                                     GetCapsuleComponent()->GetCollisionShape(), Query))
            return false;
    }
    RestSeat.Reset();
    bResting = false;
    SetActorTransform(Exit, false, nullptr, ETeleportType::TeleportPhysics);
    Boom->SetRelativeLocation(RestCameraLocation);
    GetCapsuleComponent()->SetCollisionEnabled(RestCollision);
    GetCharacterMovement()->SetMovementMode(MOVE_Walking);
    GetCharacterMovement()->StopMovementImmediately();
    ConsumeMovementInputVector();
    LastSupportedLocation = Exit.GetLocation();
    UnsupportedSeconds = 0.f;
    StartStandingAnimation();
    return true;
}
