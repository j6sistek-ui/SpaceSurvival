#include "SSWave10Soak.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSShip.h"
#include "SSShipVisualRig.h"
#include "SSStation.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimationAsset.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraTypes.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"

void ASSWave10Soak::RestoreBoardingReviewGuards()
{
    if (!BoardingReviewStarted)
        return;
    if (auto *GI = BoardingReviewInstance.Get())
        GI->AccountStorageBlocked = BoardingReviewStorageBlocked;
    if (auto *GM = Mode.Get())
        GM->SetActorTickEnabled(BoardingReviewModeTick);
    if (auto *PC = BoardingReviewController.Get())
        PC->SetActorTickEnabled(BoardingReviewControllerTick);
    if (auto *Walker = BoardingReviewWalker.Get())
        Walker->SetActorTickEnabled(BoardingReviewWalkerTick);
    BoardingReviewGuardsRestored = true;
}

void ASSWave10Soak::WriteBoardingReviewResult(const FString &Error)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("evidenceType"), TEXT("RUNTIME_BOARDING_SCRIPTED_INPUT_WITH_CAPTURE_HOLDS"));
    Result->SetBoolField(TEXT("complete"), BoardingReviewComplete && Error.IsEmpty());
    Result->SetStringField(TEXT("error"), Error);
    Result->SetNumberField(TEXT("setupPlacements"), BoardingReviewStarted ? 1 : 0);
    Result->SetNumberField(TEXT("offDeckRescues"), BoardingReviewRescues);
    Result->SetNumberField(TEXT("travelCm"), BoardingReviewTravelCm);
    Result->SetNumberField(TEXT("maximumFrameStepCm"), BoardingReviewMaxStepCm);
    Result->SetNumberField(TEXT("seconds"), BoardingReviewSeconds);
    Result->SetNumberField(TEXT("handoffPoseErrorCm"), BoardingReviewPoseErrorCm);
    Result->SetBoolField(TEXT("toeContact"), BoardingReviewToe);
    Result->SetBoolField(TEXT("mainRampContact"), BoardingReviewRamp);
    Result->SetBoolField(TEXT("sameHeroNativeHandoff"), BoardingReviewHandoff);
    Result->SetBoolField(TEXT("guardsRestored"), BoardingReviewGuardsRestored);
    Result->SetStringField(TEXT("heroMesh"), BoardingReviewHeroMesh);
    Result->SetStringField(TEXT("pilotClip"), BoardingReviewPilotClip);
    Result->SetStringField(TEXT("selectedMode"), TEXT("FreeFlight"));
    Result->SetStringField(TEXT("modeSelectionLocation"), TEXT("SUPPORTED_COCKPIT_CHAIR"));
    Result->SetStringField(TEXT("cameraSource"), TEXT("POSSESSED_PAWN_NATIVE_CAMERA"));
    Result->SetStringField(TEXT("storageScope"), Root / TEXT("User/Saved"));
    Result->SetStringField(
        TEXT("limits"),
        TEXT("One disclosed placement at the rear ramp; ordinary Move/CharacterMovement thereafter. Waves and Free "
             "Flight cards are photographed at the supported chair around one scripted contextual mode-input edge. "
             "Physical "
             "controller polling is disabled only for scripted input. GameMode ticking is held during the real 1.4s "
             "sit so intermediate/seated poses can be photographed; walker ticking is briefly held at those "
             "photographed poses. Both resume before native chair commit/takeoff. AccountStorageBlocked is temporarily "
             "lifted only for that commit in the validated scratch UserDir, then restored. No natural-input, "
             "uninterrupted-transition timing, or performance claim. Every image uses the possessed pawn's native "
             "camera, including spring-arm collision. One stopped cabin view turns toward the existing right display, "
             "then restores forward view before walking resumes. Clearance/line-of-sight queries are diagnostic and do "
             "not "
             "replace visual review."));
    Result->SetArrayField(TEXT("frames"), BoardingReviewFrames);
    Result->SetArrayField(TEXT("samples"), BoardingReviewSamples);
    FString Json;
    FJsonSerializer::Serialize(Result, TJsonWriterFactory<>::Create(&Json));
    FFileHelper::SaveStringToFile(Json, *(Root / TEXT("boarding.json")),
                                  FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
#endif
}

void ASSWave10Soak::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (BoardingReviewStarted && !BoardingReviewComplete)
    {
        RestoreBoardingReviewGuards();
        WriteBoardingReviewResult(Failure.IsEmpty() ? TEXT("Boarding capture ended before completion.") : Failure);
    }
    Super::EndPlay(EndPlayReason);
}

bool ASSWave10Soak::TickBoardingReview(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    auto *Ship = GM ? GM->Ship.Get() : nullptr;
    auto *Walker = GM ? GM->Walker.Get() : nullptr;
    const auto Fail = [&](const FString &Reason)
    {
        RestoreBoardingReviewGuards();
        WriteBoardingReviewResult(Reason);
        Stop(Reason);
        return false;
    };
    if (!GM || !GI || !PC || !Ship || !GM->Hub || !GM->Hub->IsUsingOutpost() || !CaptureVisuals || !OutpostReview)
        return Fail(TEXT("Boarding review lost its actual outpost, game mode, ship or renderer."));
    BoardingReviewSeconds += Dt;
    if (BoardingReviewSeconds > 100. || BoardingReviewSamples.Num() > 6000)
        return Fail(TEXT("Boarding route exceeded its bounded duration; no movement or collision bypass."));
    if (!BoardingReviewStarted)
    {
        if (!Walker || PC->GetPawn() != Walker || GM->IsMenuOpen() || GI->IsFreeFlight() || GI->Session.run.active)
            return Fail(TEXT("Boarding review must begin with the actual possessed home walker."));
        // The surrounding soak already verifies marker/token/UserDir and production-save isolation.
        FString User = FPaths::ConvertRelativePathToFull(FPaths::ProjectUserDir());
        FPaths::NormalizeDirectoryName(User);
        if (!FPaths::ShouldSaveToUserDir() || !User.Equals(Root / TEXT("User"), ESearchCase::IgnoreCase))
            return Fail(TEXT("Boarding scratch storage scope differs from the verified fixture."));
        BoardingReviewStarted = true;
        BoardingReviewWalker = Walker;
        BoardingReviewController = PC;
        BoardingReviewInstance = GI;
        BoardingReviewStorageBlocked = GI->AccountStorageBlocked;
        BoardingReviewModeTick = GM->IsActorTickEnabled();
        BoardingReviewControllerTick = PC->IsActorTickEnabled();
        BoardingReviewWalkerTick = Walker->IsActorTickEnabled();
        BoardingReviewHeroMesh = GetPathNameSafe(Walker->GetMesh()->GetSkeletalMeshAsset());
        BoardingReviewPilotClip = Walker->GetHero().PilotClipPath;
        if (GM->GetSelectedDepartureMode() != ESSDepartureMode::Waves)
            return Fail(TEXT("Boarding review must begin with the default Waves preference."));
        PC->SetActorTickEnabled(false);
        PC->SetControlRotation(Ship->GetActorRotation());
        BoardingReviewDock = Ship->GetActorTransform();
        const float Half = Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        Walker->GetCharacterMovement()->StopMovementImmediately();
        Walker->SetActorLocation(BoardingReviewDock.TransformPosition(FVector(-1510, 0, Half + 1)), false, nullptr,
                                 ETeleportType::TeleportPhysics);
        Walker->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
        BoardingReviewLast = Walker->GetActorLocation();
        BoardingReviewStage = 1;
        return false;
    }
    const auto ExpectedMode = BoardingReviewRouteShot >= 5 ? ESSDepartureMode::FreeFlight : ESSDepartureMode::Waves;
    if (GM->IsMenuOpen() || GM->GetSelectedDepartureMode() != ExpectedMode)
        return Fail(TEXT("Walking/boarding opened a menu or changed the selected departure mode."));
    if (BoardingReviewStage < 5 && (!Walker || PC->GetPawn() != Walker || GI->IsFreeFlight() || GI->Session.run.active))
        return Fail(TEXT("Departure changed possession or run state before the completed sit."));
    auto *Mesh = Walker ? Walker->GetMesh() : Ship->Pilot.Get();
    if (!Mesh || !Mesh->IsVisible() || GetPathNameSafe(Mesh->GetSkeletalMeshAsset()) != BoardingReviewHeroMesh)
        return Fail(TEXT("The current hero disappeared or changed during the boarding route."));
    auto Sample = MakeShared<FJsonObject>();
    Sample->SetNumberField(TEXT("frame"), double(GFrameCounter));
    Sample->SetNumberField(TEXT("seconds"), BoardingReviewSeconds);
    Sample->SetNumberField(TEXT("stage"), BoardingReviewStage);
    Sample->SetNumberField(TEXT("deltaSeconds"), Dt);
    Sample->SetBoolField(TEXT("menuOpen"), GM->IsMenuOpen());
    Sample->SetBoolField(TEXT("freeFlight"), GI->IsFreeFlight());
    Sample->SetBoolField(TEXT("activeRun"), GI->Session.run.active);
    Sample->SetStringField(TEXT("selectedDepartureMode"), GM->GetSelectedDepartureMode() == ESSDepartureMode::FreeFlight
                                                              ? TEXT("FreeFlight")
                                                              : TEXT("Waves"));
    Sample->SetBoolField(TEXT("cockpitModeContext"), GM->IsWalkerAtPilotSeat(Walker));
    Sample->SetNumberField(TEXT("wave"), GI->Session.run.wave);
    Sample->SetNumberField(TEXT("phase"), int32(GI->Session.run.phase));
    Sample->SetBoolField(TEXT("takingOff"), Ship->IsTakingOff());
    Sample->SetStringField(TEXT("possessedPawn"), GetNameSafe(PC->GetPawn()));
    Sample->SetStringField(TEXT("heroMesh"), GetPathNameSafe(Mesh->GetSkeletalMeshAsset()));
    Sample->SetStringField(TEXT("heroBoundsExtent"), Mesh->Bounds.BoxExtent.ToString());
    Sample->SetStringField(TEXT("heroWorldTransform"), Mesh->GetComponentTransform().ToHumanReadableString());
    FVector Local = FVector::ZeroVector;
    if (Walker)
    {
        Local = BoardingReviewDock.InverseTransformPosition(Walker->GetActorLocation());
        const auto *Movement = Walker->GetCharacterMovement();
        const auto *Floor = Movement->CurrentFloor.HitResult.GetComponent();
        BoardingReviewRescues = Walker->OffDeckRecoveries();
        BoardingReviewToe |= Floor && Floor->GetName() == TEXT("BoardingRampToe");
        BoardingReviewRamp |= Floor && Floor->GetName() == TEXT("BoardingRampMain");
        Sample->SetStringField(TEXT("walkerLocal"), Local.ToString());
        Sample->SetStringField(TEXT("floor"), GetNameSafe(Floor));
        Sample->SetBoolField(TEXT("grounded"), Movement->IsMovingOnGround());
        Sample->SetBoolField(TEXT("boarding"), Walker->IsBoarding());
        Sample->SetBoolField(TEXT("seated"), Walker->IsSeated());
        Sample->SetNumberField(TEXT("offDeckRescues"), BoardingReviewRescues);
        Sample->SetBoolField(TEXT("capturePoseHold"), !Walker->IsActorTickEnabled());
        if (BoardingReviewRescues != 0)
            return Fail(TEXT("Boarding route required an off-deck rescue."));
        if (BoardingReviewStage <= 2)
        {
            const double Step = FVector::Distance(Walker->GetActorLocation(), BoardingReviewLast);
            BoardingReviewTravelCm += Step;
            BoardingReviewMaxStepCm = FMath::Max(BoardingReviewMaxStepCm, Step);
            BoardingReviewLast = Walker->GetActorLocation();
            const double Bound = Movement->MaxWalkSpeed * Dt + Movement->MaxStepHeight * 2. + 10.;
            if (Step > Bound || !Movement->CurrentFloor.IsWalkableFloor() || !Movement->IsMovingOnGround())
                return Fail(TEXT("Boarding movement lost physical support or exceeded an ordinary movement step at ") +
                            Local.ToString());
            const float Height =
                Mesh->GetSkeletalMeshAsset()->GetBounds().BoxExtent.Z * 2.f * Mesh->GetComponentScale().Z;
            if (Walker->GetHero().FitHeight > 0.f && !FMath::IsNearlyEqual(Height, Walker->GetHero().FitHeight, .5f))
                return Fail(TEXT("Boarding review hero reference height differs from its authored fit."));
        }
    }
    BoardingReviewSamples.Add(MakeShared<FJsonValueObject>(Sample));
    const auto Frame = [&](const TCHAR *Name)
    {
        const FString Path = Root / TEXT("Boarding") / (FString(Name) + TEXT(".png"));
        if (BoardingReviewPendingShot != Name)
        {
            // The prior side-on review camera was outside the narrow cockpit and
            // photographed its opaque hull. Review exactly the player's camera,
            // leaving the native spring arm and all occluding geometry active.
            PC->SetViewTarget(PC->GetPawn());
            BoardingReviewPendingShot = Name;
            BoardingReviewShotAt = FPlatformTime::Seconds() + .35;
            BoardingReviewShotRequested = false;
        }
        if (!BoardingReviewShotRequested && FPlatformTime::Seconds() >= BoardingReviewShotAt &&
            !FScreenshotRequest::IsScreenshotRequested())
        {
            APawn *ViewPawn = PC->GetPawn();
            if (!ViewPawn || PC->GetViewTarget() != ViewPawn)
                return Fail(TEXT("Boarding image is not using the actual possessed pawn's camera."));
            FMinimalViewInfo View;
            ViewPawn->CalcCamera(0.f, View);
            FVector RenderLocation;
            FRotator RenderRotation;
            PC->GetPlayerViewPoint(RenderLocation, RenderRotation);
            IFileManager::Get().MakeDirectory(*(Root / TEXT("Boarding")), true);
            FScreenshotRequest::RequestScreenshot(Path, true, false, false);
            auto Row = MakeShared<FJsonObject>(*Sample);
            Row->SetStringField(TEXT("name"), Name);
            Row->SetStringField(TEXT("path"), Path);
            Row->SetStringField(TEXT("cameraTransform"),
                                FTransform(View.Rotation, View.Location).ToHumanReadableString());
            Row->SetStringField(TEXT("cameraLocal"),
                                BoardingReviewDock.InverseTransformPosition(View.Location).ToString());
            Row->SetStringField(TEXT("cameraSource"), TEXT("POSSESSED_PAWN_NATIVE_CAMERA"));
            // Observe actual registered lights at each photograph, including departure.
            TArray<TSharedPtr<FJsonValue>> CabinLightReadback;
            if (const auto *Rig = Ship->GetVisualRig(); Rig && Rig->GetHull())
            {
                TInlineComponentArray<UPointLightComponent *> Lights(Rig->GetHull()->GetOwner());
                for (const auto *Light : Lights)
                {
                    if (!Light->GetName().StartsWith(TEXT("Boarding")))
                        continue;
                    auto Lamp = MakeShared<FJsonObject>();
                    Lamp->SetStringField(TEXT("name"), Light->GetName());
                    Lamp->SetBoolField(TEXT("visible"), Light->IsVisible());
                    Lamp->SetStringField(
                        TEXT("shipLocal"),
                        Ship->GetActorTransform().InverseTransformPosition(Light->GetComponentLocation()).ToString());
                    Lamp->SetNumberField(TEXT("lumens"), Light->Intensity);
                    Lamp->SetNumberField(TEXT("radiusCm"), Light->AttenuationRadius);
                    Lamp->SetNumberField(TEXT("sourceRadiusCm"), Light->SourceRadius);
                    Lamp->SetNumberField(TEXT("specularScale"), Light->SpecularScale);
                    Lamp->SetBoolField(TEXT("castShadows"), Light->CastShadows);
                    CabinLightReadback.Add(MakeShared<FJsonValueObject>(Lamp));
                }
            }
            Row->SetArrayField(TEXT("cabinLights"), CabinLightReadback);
            Row->SetStringField(TEXT("viewTarget"), GetPathNameSafe(PC->GetViewTarget()));
            Row->SetStringField(TEXT("renderViewLocation"), RenderLocation.ToString());
            Row->SetStringField(TEXT("renderViewRotation"), RenderRotation.ToString());
            Row->SetNumberField(TEXT("renderViewLagCm"), FVector::Distance(View.Location, RenderLocation));
            Row->SetNumberField(TEXT("fieldOfView"), View.FOV);
            FCollisionQueryParams CameraQuery(SCENE_QUERY_STAT(SSBoardingReviewCamera), true, ViewPawn);
            Row->SetBoolField(TEXT("cameraSphereBlocked"),
                              GetWorld()->OverlapBlockingTestByChannel(View.Location, FQuat::Identity, ECC_Camera,
                                                                       FCollisionShape::MakeSphere(5.f), CameraQuery));
            if (Walker)
            {
                const FVector Pelvis = Mesh->GetSocketLocation(Walker->GetHero().PelvisBone);
                FHitResult Obstruction;
                const bool Blocked =
                    GetWorld()->LineTraceSingleByChannel(Obstruction, View.Location, Pelvis, ECC_Camera, CameraQuery);
                Row->SetBoolField(TEXT("cameraToPelvisBlocked"), Blocked);
                Row->SetStringField(TEXT("cameraObstructionActor"), GetPathNameSafe(Obstruction.GetActor()));
                Row->SetStringField(TEXT("cameraObstructionComponent"), GetNameSafe(Obstruction.GetComponent()));
                Row->SetStringField(TEXT("cameraObstructionPoint"), Obstruction.ImpactPoint.ToString());
                Row->SetStringField(TEXT("pelvisWorld"), Pelvis.ToString());
                Row->SetNumberField(TEXT("cameraToPelvisCm"), FVector::Distance(View.Location, Pelvis));
                Row->SetNumberField(
                    TEXT("cameraPelvisForwardDot"),
                    FVector::DotProduct(View.Rotation.Vector(), (Pelvis - View.Location).GetSafeNormal()));
            }
            BoardingReviewFrames.Add(MakeShared<FJsonValueObject>(Row));
            BoardingReviewShotRequested = true;
        }
        return BoardingReviewShotRequested && !FScreenshotRequest::IsScreenshotRequested() &&
               IFileManager::Get().FileSize(*Path) > 0;
    };
    if (BoardingReviewStage == 1)
    {
        Walker->Move(FVector2D::ZeroVector, FVector2D::ZeroVector, false, Dt);
        if (Frame(TEXT("BoardingRear")))
            BoardingReviewStage = 2;
    }
    else if (BoardingReviewStage == 2)
    {
        const bool Chair = GM->IsWalkerAtPilotSeat(Walker);
        const bool Ready = BoardingReviewRouteShot == 0   ? Local.X > -1270
                           : BoardingReviewRouteShot == 1 ? Local.X > -650
                           : BoardingReviewRouteShot == 2 ? Local.X > -500
                           : BoardingReviewRouteShot == 3 ? Local.X > 450
                                                          : Chair;
        if (!Ready)
        {
            // Measured radius-34 capsule lane: avoid the right-hand passage trim, then center before the crest.
            const double TargetY = -10. * (1. - FMath::Clamp((Local.X - 180.) / 70., 0., 1.));
            const double Lateral = FMath::Clamp((TargetY - Local.Y) * .15, -.35, .35);
            Walker->Move(FVector2D(Lateral, 1), FVector2D::ZeroVector, false, Dt);
        }
        else
        {
            // Inspect the existing right-hand pane through the player's actual spring arm.
            // Stop on the ordinary route beside it; no placement, custom camera or collision bypass.
            if (BoardingReviewRouteShot == 2)
            {
                FRotator SideView = Ship->GetActorRotation();
                SideView.Yaw = FRotator::NormalizeAxis(SideView.Yaw + 90.f);
                SideView.Pitch = -6.f;
                SideView.Roll = 0.f;
                PC->SetControlRotation(SideView);
            }
            Walker->Move(FVector2D::ZeroVector, FVector2D::ZeroVector, false, Dt);
            const TCHAR *Names[] = {TEXT("BoardingRamp"),   TEXT("BoardingCabin"), TEXT("BoardingSystemsDisplay"),
                                    TEXT("BoardingStairs"), TEXT("BoardingChair"), TEXT("BoardingModeSelected")};
            if (Frame(Names[BoardingReviewRouteShot]))
            {
                ++BoardingReviewRouteShot;
                if (BoardingReviewRouteShot == 3)
                    PC->SetControlRotation(Ship->GetActorRotation());
                if (BoardingReviewRouteShot == 5)
                {
                    const auto AccountBefore = SS::EncodeAccount(GI->Session.account);
                    const auto RunBefore = SS::EncodeRun(GI->Session.run);
                    if (!Chair || !GM->HandleCockpitModeInput(true, false) ||
                        GM->GetSelectedDepartureMode() != ESSDepartureMode::FreeFlight ||
                        SS::EncodeAccount(GI->Session.account) != AccountBefore ||
                        SS::EncodeRun(GI->Session.run) != RunBefore || Walker->IsBoarding() ||
                        GM->IsDepartingStation() || GM->IsMenuOpen() || PC->GetPawn() != Walker)
                        return Fail(
                            TEXT("Cockpit mode edge did not change only the departure preference at the chair."));
                }
                else if (BoardingReviewRouteShot == 6)
                {
                    if (!Chair || !BoardingReviewToe || !BoardingReviewRamp || BoardingReviewTravelCm < 2200.)
                        return Fail(TEXT("Full measured ramp/interior route did not reach the actual chair."));
                    GM->SetActorTickEnabled(false); // Hold automatic handoff only while photographing the real sit.
                    GM->Interact();
                    if (!Walker->IsBoarding() || Walker->IsSeated() || PC->GetPawn() != Walker)
                        return Fail(TEXT("Chair Interact did not begin the visible production sit."));
                    BoardingReviewStage = 3;
                }
            }
        }
    }
    else if (BoardingReviewStage == 3)
    {
        if (Walker->IsActorTickEnabled())
            BoardingReviewSitSeconds += Dt;
        if (Walker->IsSeated())
            return Fail(TEXT("Variable frame timing skipped the required intermediate sit capture."));
        if (BoardingReviewSitSeconds >= .45)
        {
            Walker->SetActorTickEnabled(false);
            if (Frame(TEXT("BoardingSitMid")))
            {
                Walker->SetActorTickEnabled(BoardingReviewWalkerTick);
                BoardingReviewStage = 4;
            }
        }
    }
    else if (BoardingReviewStage == 4 && Walker->IsSeated())
    {
        Walker->SetActorTickEnabled(false);
        if (!Ship->CanAdoptBoardedPilot(Walker))
            return Fail(TEXT("The photographed seated hero is not valid for the native pilot handoff."));
        if (Frame(TEXT("BoardingSeated")))
        {
            BoardingReviewSeatedRelative =
                Mesh->GetComponentTransform().GetRelativeTransform(Ship->GetActorTransform());
            BoardingReviewSeatedBones = Mesh->GetComponentSpaceTransforms();
            Walker->SetActorTickEnabled(BoardingReviewWalkerTick);
            GI->AccountStorageBlocked = false; // Validated scratch UserDir; Free Flight commit is memory-only.
            BoardingReviewAwaitingDeparture = true;
            GM->SetActorTickEnabled(BoardingReviewModeTick);
            BoardingReviewStage = 5;
        }
    }
    else if (BoardingReviewStage == 5)
    {
        if (!GI->IsFreeFlight() || !GM->IsDepartingStation() || PC->GetPawn() != Ship || Walker ||
            GI->Session.run.wave != 1 || GI->Session.run.phase != SS::Phase::Approach)
            return Fail(TEXT("Native chair commit did not enter the selected Free Flight takeoff at Wave 1 Approach."));
        GI->AccountStorageBlocked = BoardingReviewStorageBlocked;
        if (!BoardingReviewHandoff)
        {
            if (!Ship->Pilot->GetComponentTransform()
                     .GetRelativeTransform(Ship->GetActorTransform())
                     .Equals(BoardingReviewSeatedRelative, .05f))
                return Fail(TEXT("Native handoff moved or resized the seated hero relative to its chair."));
            auto *Animation = Ship->Pilot->GetSingleNodeInstance();
            const auto &Pose = Ship->Pilot->GetComponentSpaceTransforms();
            if (!Animation || GetPathNameSafe(Animation->GetCurrentAsset()) != BoardingReviewPilotClip ||
                Pose.Num() != BoardingReviewSeatedBones.Num())
                return Fail(TEXT("Native handoff changed the hero animation or skeleton."));
            for (int32 Index = 0; Index < Pose.Num(); ++Index)
                BoardingReviewPoseErrorCm = FMath::Max(
                    BoardingReviewPoseErrorCm,
                    FVector::Distance(Pose[Index].GetLocation(), BoardingReviewSeatedBones[Index].GetLocation()));
            if (BoardingReviewPoseErrorCm > 1.)
                return Fail(TEXT("The first native pilot pose differs from the photographed seated pose by over 1cm."));
            BoardingReviewHandoff = true;
        }
        if (!Ship->IsTakingOff())
            return Fail(TEXT("Takeoff ended before its required rendered departure frame."));
        if (FVector::Distance(Ship->GetActorLocation(), BoardingReviewDock.GetLocation()) > 20. &&
            Frame(TEXT("BoardingTakeoff")))
        {
            BoardingReviewComplete = BoardingReviewFrames.Num() == 10;
            RestoreBoardingReviewGuards();
            WriteBoardingReviewResult(BoardingReviewComplete ? FString() : TEXT("Missing required boarding images."));
            return BoardingReviewComplete;
        }
    }
#endif
    return false;
}
