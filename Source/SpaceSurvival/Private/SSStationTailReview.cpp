#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSStation.h"
#include "SSStationPoseTransition.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/HUD.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "UnrealClient.h"
#if WITH_EDITOR
#include "Rendering/SkeletalMeshModel.h"
#endif

namespace
{
int32 CapturedTailPhases(const TArray<TSharedPtr<FJsonValue>> &Frames)
{
    int32 Phases = 0;
    for (const auto &Value : Frames)
    {
        const auto &Row = Value->AsObject();
        const int32 Stage = int32(Row->GetNumberField(TEXT("tailMotionStage")));
        if ((Stage == 3 || Stage == 5) && Row->GetBoolField(TEXT("falling")))
        {
            const int32 Shift = Stage == 3 ? 0 : 3;
            const double Speed = Row->GetNumberField(TEXT("verticalSpeed"));
            if (Speed > 20.)
                Phases |= 1 << Shift;
            if (Speed < -20.)
                Phases |= 2 << Shift;
        }
        if ((Stage == 3 || Stage == 5) && Row->GetBoolField(TEXT("tailFirstGroundedAfterJump")))
            Phases |= 4 << (Stage == 3 ? 0 : 3);
    }
    return Phases;
}

bool TailSurfaceClearance(const USkeletalMeshComponent *Component, const FPlane &Floor, double &Clearance)
{
#if WITH_EDITOR
    const USkeletalMesh *Mesh = Component->GetSkeletalMeshAsset();
    const auto *Imported = Mesh ? Mesh->GetImportedModel() : nullptr;
    if (!Imported || Imported->LODModels.IsEmpty())
        return false;
    const FReferenceSkeleton &Reference = Mesh->GetRefSkeleton();
    const auto &InverseReference = Mesh->GetRefBasesInvMatrix();
    const auto &Pose = Component->GetComponentSpaceTransforms();
    const int32 Root = Reference.FindBoneIndex(TEXT("tail_01"));
    if (Root <= 0 || Pose.Num() != Reference.GetNum())
        return false;
    Clearance = MAX_dbl;
    for (const auto &Section : Imported->LODModels[0].Sections)
        for (const FSoftSkinVertex &Vertex : Section.SoftVertices)
        {
            bool IsTail = false;
            FVector Point = FVector::ZeroVector;
            for (int32 Influence = 0; Influence < MAX_TOTAL_INFLUENCES; ++Influence)
                if (Vertex.InfluenceWeights[Influence])
                {
                    const int32 Bone = Section.BoneMap[Vertex.InfluenceBones[Influence]];
                    IsTail |= Bone == Root || Reference.BoneIsChildOf(Bone, Root);
                    const FVector Local(InverseReference[Bone].TransformPosition(Vertex.Position));
                    Point +=
                        Pose[Bone].TransformPosition(Local) * (double(Vertex.InfluenceWeights[Influence]) / 65535.);
                }
            if (IsTail)
                Clearance =
                    FMath::Min(Clearance, Floor.PlaneDot(Component->GetComponentTransform().TransformPosition(Point)));
        }
    return FMath::IsFinite(Clearance) && Clearance != MAX_dbl;
#else
    return false;
#endif
}
} // namespace

void ASSWave10Soak::TickTailReview(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    auto *Walker = GM ? GM->Walker.Get() : nullptr;
    auto *Movement = Walker ? Walker->GetCharacterMovement() : nullptr;
    FlightSeconds += Dt;
    TailStageSeconds += Dt;
    ++CapturedFrames;
    AllFramesForeground &= FApp::HasFocus();
    if (!GI || !PC || !CaptureVisuals || !GM->Hub || !GM->Hub->IsUsingOutpost() || !Walker || !Movement ||
        PC->GetPawn() != Walker || FlightSeconds > 60.)
    {
        Stop(TEXT("Tail review lost the actual possessed outpost walker, renderer or bounded capture window."));
        return;
    }
    if (!Started)
    {
        GM->bAtTitleScreen = false;
        GM->ClosePanel();
        Walker->ApplyHero(TEXT("Squirrel"));
        if (Walker->GetHero().Id != TEXT("Squirrel") || Walker->GetHero().TailFloorEnvelopes.Num() != 7 ||
            !Walker->GetHero().MeshPath.Contains(TEXT("/HeroReplacement/Final/")))
        {
            Stop(TEXT("Tail review requires the exact installed replacement squirrel and seven measured envelopes."));
            return;
        }
        if (auto *HUD = PC->GetHUD())
            HUD->bShowHUD = false;
        // Physical input polling otherwise calls StopJumping before the scripted request reaches CharacterMovement.
        // The fixture owns input only; world camera updates, possession and ordinary pawn movement remain active.
        PC->SetActorTickEnabled(false);
        TailReviewRunBefore = UTF8_TO_TCHAR(SS::EncodeRun(GI->Session.run).c_str());
        TailReviewAccountBefore = UTF8_TO_TCHAR(SS::EncodeAccount(GI->Session.account).c_str());
        Started = true;
        TailStageSeconds = 0;
        ReviewCameraReadyAt = FPlatformTime::Seconds() + 8.;
        return;
    }
    if (TailReviewRunBefore != UTF8_TO_TCHAR(SS::EncodeRun(GI->Session.run).c_str()) ||
        TailReviewAccountBefore != UTF8_TO_TCHAR(SS::EncodeAccount(GI->Session.account).c_str()) ||
        Walker->OffDeckRecoveries() != 0)
    {
        Stop(TEXT("Tail review changed account/run state or triggered an off-deck rescue."));
        return;
    }
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSTailRenderedFloor), false, Walker);
    FHitResult Floor;
    const FVector Position = Walker->GetActorLocation();
    const bool HasFloor = GetWorld()->LineTraceSingleByChannel(Floor, Position + FVector(0, 0, 20),
                                                               Position - FVector(0, 0, 1400), ECC_Pawn, Query) &&
                          Floor.ImpactNormal.Z > .65f;
    const bool Grounded = Movement->IsMovingOnGround() && Movement->CurrentFloor.IsWalkableFloor();
    if (TailReviewStage == 0)
    {
        // Warm the actual mesh, materials and streamed home before motion; never write an asset or move the pawn.
        if (FPlatformTime::Seconds() < ReviewCameraReadyAt || !Grounded || !HasFloor)
            return;
        TailReviewStart = Position;
        const auto *Capsule = Walker->GetCapsuleComponent();
        const FCollisionShape Shape = Capsule->GetCollisionShape();
        FVector CameraPosition;
        for (int32 Index = 0; Index < 8 && TailReviewDirection.IsNearlyZero(); ++Index)
        {
            const FVector Direction = FRotator(0, GM->Hub->GetActorRotation().Yaw + Index * 45.f, 0).Vector();
            FHitResult Hit;
            bool Clear = !GetWorld()->SweepSingleByChannel(Hit, Position, Position + Direction * 400.f, FQuat::Identity,
                                                           ECC_Pawn, Shape, Query);
            for (float Along = 0; Clear && Along <= 400; Along += 40)
            {
                const FVector Point = Position + Direction * Along;
                Clear = GetWorld()->LineTraceSingleByChannel(Hit, Point + FVector(0, 0, 20), Point - FVector(0, 0, 200),
                                                             ECC_Pawn, Query) &&
                        Hit.ImpactNormal.Z > .65f && FMath::Abs(Hit.ImpactPoint.Z - Floor.ImpactPoint.Z) < 10.f;
            }
            for (float Side : {1.f, -1.f})
            {
                const FVector Camera = Position - Direction * 100.f +
                                       FVector::CrossProduct(FVector::UpVector, Direction) * (Side * 550.f) +
                                       FVector(0, 0, 160);
                if (Clear && !GetWorld()->LineTraceSingleByChannel(Hit, Camera, Position + FVector(0, 0, 30),
                                                                   ECC_Visibility, Query))
                {
                    TailReviewDirection = Direction;
                    CameraPosition = Camera;
                    break;
                }
            }
        }
        if (TailReviewDirection.IsNearlyZero())
        {
            Stop(
                TEXT("Tail review could not find a real supported 4m movement corridor and unobstructed side camera."));
            return;
        }
        StationReviewCamera = GetWorld()->SpawnActor<ACameraActor>();
        if (!StationReviewCamera)
        {
            Stop(TEXT("Tail review could not create its transient side camera."));
            return;
        }
        StationReviewCamera->SetActorEnableCollision(false);
        StationReviewCamera->GetCameraComponent()->SetFieldOfView(55.f);
        const FVector Target = Position + TailReviewDirection * 100.f + FVector(0, 0, 30);
        StationReviewCamera->SetActorLocationAndRotation(CameraPosition, (Target - CameraPosition).Rotation());
        PC->SetViewTarget(StationReviewCamera);
        PC->SetControlRotation(TailReviewDirection.Rotation());
        Walker->SetActorRotation(TailReviewDirection.Rotation());
        TailReviewStage = 1;
        TailStageSeconds = 0;
        ReviewCameraReadyAt = FPlatformTime::Seconds() + 2.;
        return;
    }
    if (!HasFloor || !StationReviewCamera || PC->GetViewTarget() != StationReviewCamera)
    {
        Stop(TEXT("Tail review lost the physical floor or its fixed side camera."));
        return;
    }
    if (TailReviewStage == 1)
    {
        if (FPlatformTime::Seconds() < ReviewCameraReadyAt)
            return;
        TailReviewStage = 2;
        TailStageSeconds = 0;
        // The isolated runner enables the declared 60Hz simulation step before engine startup.
        // Warmup uses wall time; recorded motion uses actual fixed-step CharacterMovement and animation.
    }
    if (TailReviewSamples.Num() >= 480)
    {
        Stop(TEXT("Tail review exceeded its bounded 480 motion ticks."));
        return;
    }
    const bool FirstGroundedAfterJump =
        (TailReviewStage == 3 || TailReviewStage == 5) && TailReviewSawAir && Grounded && TailStageSeconds > .3;
    double Clearance = 0;
    if (!TailSurfaceClearance(Walker->GetMesh(), FPlane(Floor.ImpactPoint, Floor.ImpactNormal), Clearance))
    {
        Stop(TEXT("Tail review cannot measure the actual deformed private mesh surface in this Editor process."));
        return;
    }
    TailMinimumSurfaceCm = FMath::Min(TailMinimumSurfaceCm, Clearance);
    auto Sample = MakeShared<FJsonObject>();
    Sample->SetNumberField(TEXT("seconds"), FlightSeconds);
    Sample->SetNumberField(TEXT("deltaSeconds"), Dt);
    Sample->SetNumberField(TEXT("frame"), double(GFrameCounter));
    Sample->SetNumberField(TEXT("stage"), TailReviewStage);
    Sample->SetBoolField(TEXT("falling"), Movement->IsFalling());
    Sample->SetNumberField(TEXT("verticalSpeed"), Walker->GetVelocity().Z);
    Sample->SetStringField(TEXT("position"), Position.ToString());
    Sample->SetNumberField(TEXT("floorZ"), Floor.ImpactPoint.Z);
    Sample->SetNumberField(TEXT("tailSurfaceClearanceCm"), Clearance);
    Sample->SetNumberField(TEXT("tailTipZ"), Walker->GetMesh()->GetSocketLocation(TEXT("tail_07")).Z);
    TailReviewSamples.Add(MakeShared<FJsonValueObject>(Sample));
    TailMaximumTravelCm = FMath::Max(TailMaximumTravelCm, FVector::Dist2D(Position, TailReviewStart));
    if ((FlightSeconds >= TailNextFrameAt || FirstGroundedAfterJump || Clearance < -.75) &&
        !FScreenshotRequest::IsScreenshotRequested())
    {
        const FString Name = FString::Printf(TEXT("Tail_%03d"), TailReviewFrames);
        CaptureVisual(*Name, float(FlightSeconds));
        if (VisualNames.Contains(Name))
        {
            auto Row = VisualRecords.Last()->AsObject();
            Row->SetNumberField(TEXT("tailSurfaceClearanceCm"), Clearance);
            Row->SetNumberField(TEXT("tailMotionStage"), TailReviewStage);
            Row->SetNumberField(TEXT("tailStageSeconds"), TailStageSeconds);
            Row->SetNumberField(TEXT("tailJumpCount"), TailReviewJumps);
            Row->SetBoolField(TEXT("falling"), Movement->IsFalling());
            Row->SetBoolField(TEXT("tailGrounded"), Grounded);
            Row->SetBoolField(TEXT("tailFirstGroundedAfterJump"), FirstGroundedAfterJump);
            Row->SetNumberField(TEXT("verticalSpeed"), Walker->GetVelocity().Z);
            Row->SetStringField(TEXT("walkerPosition"), Position.ToString());
            Row->SetStringField(TEXT("floorPoint"), Floor.ImpactPoint.ToString());
            Row->SetStringField(TEXT("mesh"), Walker->GetHero().MeshPath);
            Row->SetNumberField(TEXT("offDeckRescues"), Walker->OffDeckRecoveries());
            if (const auto *Animation = Cast<UAnimSingleNodeInstance>(Walker->GetMesh()->GetAnimInstance()))
                Row->SetStringField(TEXT("animation"), GetPathNameSafe(Animation->GetAnimationAsset()));
            ++TailReviewFrames;
        }
        TailNextFrameAt = FlightSeconds + 1. / 15.;
    }
    if (Clearance < -.75)
    {
        Stop(FString::Printf(TEXT("Actual rendered-pose tail surface crossed the floor by %.3fcm at stage%d."),
                             -Clearance, TailReviewStage));
        return;
    }
    if (TailReviewStage == 2 && TailStageSeconds >= .75)
    {
        Walker->Jump();
        TailReviewSawAir = false;
        TailReviewStage = 3;
        TailStageSeconds = 0;
    }
    else if (TailReviewStage == 3 || TailReviewStage == 5)
    {
        if (TailReviewStage == 5)
            Walker->Move(FVector2D(0, .65), FVector2D::ZeroVector, false, Dt);
        if (TailStageSeconds >= .15)
            Walker->StopJumping();
        TailReviewSawAir |= Movement->IsFalling();
        if (TailReviewSawAir && Grounded && TailStageSeconds > .3)
        {
            ++TailReviewJumps;
            ++TailReviewStage;
            TailStageSeconds = 0;
        }
        else if (TailStageSeconds > 3.)
            Stop(TEXT("The actual walker did not leave and return to the floor through ordinary Jump movement."));
    }
    else if (TailReviewStage == 4 && TailStageSeconds >= 1.15)
    {
        Walker->Jump();
        TailReviewSawAir = false;
        TailReviewStage = 5;
        TailStageSeconds = 0;
    }
    else if (TailReviewStage == 6)
    {
        Walker->Move(TailStageSeconds < .7 ? FVector2D(0, .65) : FVector2D::ZeroVector, FVector2D::ZeroVector, false,
                     Dt);
        if (TailStageSeconds >= 1.5 && TailReviewFrames >= 45)
        {
            const int32 Phases = CapturedTailPhases(VisualRecords);
            TailReviewComplete = Grounded && TailReviewJumps == 2 && TailMaximumTravelCm > 25. && Phases == 63;
            Stop(TailReviewComplete ? FString()
                                    : FString::Printf(TEXT("Tail review needs both completed jumps, movement and "
                                                           "captured ascent/descent/early-landing "
                                                           "for each; phase mask=%d/63 travel=%.2fcm."),
                                                      Phases, TailMaximumTravelCm));
        }
    }
#endif
}

void ASSWave10Soak::AddTailReviewResult(const TSharedRef<FJsonObject> &Result) const
{
    const auto *GM = Mode.Get();
    const auto *Walker = GM ? GM->Walker.Get() : nullptr;
    Result->SetBoolField(TEXT("tailReviewComplete"), TailReviewComplete);
    Result->SetNumberField(TEXT("tailJumpCount"), TailReviewJumps);
    Result->SetNumberField(TEXT("tailOffDeckRescues"), Walker ? Walker->OffDeckRecoveries() : -1);
    Result->SetNumberField(TEXT("tailMinimumSurfaceCm"), TailMinimumSurfaceCm);
    Result->SetNumberField(TEXT("tailMaximumTravelCm"), TailMaximumTravelCm);
    Result->SetNumberField(TEXT("tailTargetFps"), 15);
    Result->SetNumberField(TEXT("tailCapturedPhaseMask"), CapturedTailPhases(VisualRecords));
    Result->SetBoolField(TEXT("tailSurfaceMeasuredEveryMotionTick"), true);
    Result->SetBoolField(TEXT("tailControllerInputTickDisabled"), true);
    Result->SetBoolField(TEXT("tailOfflineFixedStepReview"), true);
    Result->SetNumberField(TEXT("tailFixedSimulationStepSeconds"), 1. / 60.);
    Result->SetBoolField(TEXT("tailObservedFixedStepEnabled"), FApp::UseFixedTimeStep());
    Result->SetNumberField(TEXT("tailObservedDeclaredStepSeconds"), FApp::GetFixedDeltaTime());
    Result->SetNumberField(TEXT("tailObservedAppDeltaSeconds"), FApp::GetDeltaTime());
    Result->SetNumberField(TEXT("tailObservedWorldDeltaSeconds"), GetWorld()->GetDeltaSeconds());
    Result->SetStringField(TEXT("tailWarmupClock"), TEXT("Wall time: 8 seconds mesh, 2 seconds fixed camera"));
    Result->SetArrayField(TEXT("tailReviewSamples"), TailReviewSamples);
}
