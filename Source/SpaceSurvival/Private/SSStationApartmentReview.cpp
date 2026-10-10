#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSStation.h"
#include "SSOutpostSandbox.h"
#include "Components/CapsuleComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UnrealClient.h"

bool ASSWave10Soak::TickApartmentWalk(float Dt, const TArray<FVector> &Feet)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    auto *Walker = GM ? GM->Walker.Get() : nullptr;
    auto *Movement = Walker ? Walker->GetCharacterMovement() : nullptr;
    if (!GM || !GM->Hub || !GM->Hub->IsUsingOutpost() || !Walker || !Movement || !PC || PC->GetPawn() != Walker ||
        Feet.Num() != 27 || Walker->OffDeckRecoveries() != 0)
    {
        Stop(TEXT("Apartment walk lost the real possessed walker, authored route or zero-rescue condition."));
        return false;
    }
    if (ApartmentDoorClosures == 1)
        return true;
    ApartmentWalkSeconds += Dt;
    ApartmentWaypointSeconds += Dt;
    if (ApartmentWalkSeconds > 150. || ApartmentWalkSamples.Num() >= 12000)
    {
        Stop(TEXT("Apartment traversal exceeded its bounded motion duration or tick count."));
        return false;
    }
    const FTransform HubTransform = GM->Hub->GetActorTransform();
    const float Half = Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    if (!ApartmentWalkStarted)
    {
        for (TActorIterator<ASSOutpostDoor> It(GetWorld()); It; ++It)
            if (FVector::Dist(HubTransform.InverseTransformPosition(It->GetActorLocation()),
                              FVector(6120, 4100, -120)) < 400.f)
            {
                if (ApartmentDoor.IsValid())
                {
                    Stop(TEXT("Apartment walk found more than one entry door at the established route."));
                    return false;
                }
                ApartmentDoor = *It;
            }
        if (!ApartmentDoor.IsValid())
        {
            Stop(TEXT("Apartment walk cannot find the real automatic entry door."));
            return false;
        }
        ApartmentRoute = Feet;
        ApartmentWaypoint = 1;
        ApartmentWaypointSeconds = 0;
        GM->bAtTitleScreen = false;
        GM->ClosePanel();
        ApartmentControllerTickWasEnabled = PC->IsActorTickEnabled();
        PC->SetActorTickEnabled(false);
        PC->SetViewTarget(Walker);
        Movement->StopMovementImmediately();
        // One disclosed setup placement reaches the connector start. All subsequent travel is normal pawn input.
        Walker->SetActorLocation(HubTransform.TransformPosition(Feet[0]) + FVector(0, 0, Half + 3), false, nullptr,
                                 ETeleportType::TeleportPhysics);
        Movement->SetMovementMode(MOVE_Walking);
        ApartmentLastPosition = Walker->GetActorLocation();
        ApartmentWalkStarted = true;
        return false;
    }
    if (!ApartmentDoor.IsValid())
    {
        Stop(TEXT("The apartment entry door disappeared during traversal."));
        return false;
    }
    const FVector Position = Walker->GetActorLocation();
    const FVector LocalFeet = HubTransform.InverseTransformPosition(Position - FVector(0, 0, Half));
    const double Step = FVector::Dist(Position, ApartmentLastPosition);
    ApartmentMaxStepCm = FMath::Max(ApartmentMaxStepCm, Step);
    ApartmentLastPosition = Position;
    const double MovementBound = Movement->MaxWalkSpeed * Dt + Movement->MaxStepHeight * 2. +
                                 Walker->GetCapsuleComponent()->GetScaledCapsuleRadius() * 2. + 10.;
    if (Step > MovementBound)
    {
        Stop(FString::Printf(TEXT("Apartment walker displaced %.2fcm in %.3fs beyond ordinary movement %.2fcm."), Step,
                             Dt, MovementBound));
        return false;
    }
    FHitResult Floor;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSApartmentWalkSupport), false, Walker);
    const bool FloorHit = GetWorld()->LineTraceSingleByChannel(Floor, Position - FVector(0, 0, Half - 35),
                                                               Position - FVector(0, 0, Half + 100), ECC_Pawn, Query);
    const bool PhysicalSupport = Movement->CurrentFloor.IsWalkableFloor() ||
                                 (FloorHit && !Floor.bStartPenetrating && Floor.ImpactNormal.Z > .55f);
    if (!PhysicalSupport)
    {
        Stop(TEXT("Apartment walker lost physical floor support at ") + LocalFeet.ToString());
        return false;
    }
    ApartmentDoorMaximumOpen = FMath::Max(ApartmentDoorMaximumOpen, ApartmentDoor->OpenFraction);
    auto Sample = MakeShared<FJsonObject>();
    Sample->SetNumberField(TEXT("seconds"), ApartmentWalkSeconds);
    Sample->SetNumberField(TEXT("deltaSeconds"), Dt);
    Sample->SetNumberField(TEXT("frame"), double(GFrameCounter));
    Sample->SetNumberField(TEXT("waypoint"), ApartmentWaypoint);
    Sample->SetBoolField(TEXT("returning"), ApartmentWalkingBack);
    Sample->SetStringField(TEXT("feet"), LocalFeet.ToString());
    Sample->SetBoolField(TEXT("falling"), Movement->IsFalling());
    Sample->SetBoolField(TEXT("physicalSupport"), PhysicalSupport);
    Sample->SetNumberField(TEXT("stepCm"), Step);
    Sample->SetNumberField(TEXT("offDeckRescues"), Walker->OffDeckRecoveries());
    Sample->SetNumberField(TEXT("doorOpen"), ApartmentDoor->OpenFraction);
    ApartmentWalkSamples.Add(MakeShared<FJsonValueObject>(Sample));
    if (ApartmentWalkPasses == 2)
    {
        Walker->Move(FVector2D::ZeroVector, FVector2D::ZeroVector, false, Dt);
        ApartmentCloseSeconds += Dt;
        if (ApartmentCloseSeconds >= 3. && ApartmentDoor->OpenFraction < .05f)
        {
            if (ApartmentDoorMaximumOpen < .95f || !Movement->IsMovingOnGround())
            {
                Stop(TEXT("Apartment route did not observe a full automatic opening and grounded return."));
                return false;
            }
            ApartmentDoorClosures = 1;
            PC->SetActorTickEnabled(ApartmentControllerTickWasEnabled);
            return true;
        }
        if (ApartmentCloseSeconds > 10.)
            Stop(TEXT("Apartment automatic door did not close after the actual walker returned."));
        return false;
    }
    const FVector Goal = HubTransform.TransformPosition(ApartmentRoute[ApartmentWaypoint]);
    const FVector Delta = FVector(Goal.X - Position.X, Goal.Y - Position.Y, 0);
    const double Distance = Delta.Size();
    if (Distance < 22. && FMath::Abs(Position.Z - Half - Goal.Z) < 28.f && Movement->IsMovingOnGround())
    {
        const bool AtEnd =
            ApartmentWalkingBack ? ApartmentWaypoint == 0 : ApartmentWaypoint == ApartmentRoute.Num() - 1;
        if (AtEnd)
        {
            Walker->Move(FVector2D::ZeroVector, FVector2D::ZeroVector, false, Dt);
            const FString Name = ApartmentWalkingBack ? TEXT("ApartmentWalkBack") : TEXT("ApartmentWalkIn");
            if (!VisualNames.Contains(Name))
            {
                if (!FScreenshotRequest::IsScreenshotRequested())
                    CaptureVisual(*Name, float(FlightSeconds));
                return false;
            }
            ++ApartmentWalkPasses;
            if (!ApartmentWalkingBack)
            {
                ApartmentWalkingBack = true;
                --ApartmentWaypoint;
            }
        }
        else
            ApartmentWaypoint += ApartmentWalkingBack ? -1 : 1;
        ApartmentWaypointSeconds = 0;
        return false;
    }
    if (ApartmentWaypointSeconds > 14.)
    {
        Stop(FString::Printf(TEXT("Apartment walker stalled %s at waypoint%d, feet%s goal%s."),
                             ApartmentWalkingBack ? TEXT("returning") : TEXT("entering"), ApartmentWaypoint,
                             *LocalFeet.ToString(), *ApartmentRoute[ApartmentWaypoint].ToString()));
        return false;
    }
    const float Input = FMath::Min(1.f, float(Distance / FMath::Max(75., 320. * Dt + 35.)));
    PC->SetControlRotation(FRotator(-5, Delta.Rotation().Yaw, 0));
    Walker->Move(FVector2D(0, Input), FVector2D::ZeroVector, false, Dt);
#endif
    return false;
}

void ASSWave10Soak::AddApartmentWalkResult(const TSharedRef<FJsonObject> &Result) const
{
    Result->SetBoolField(TEXT("apartmentWalkComplete"), ApartmentWalkPasses == 2 && ApartmentDoorClosures == 1);
    Result->SetNumberField(TEXT("apartmentWalkPasses"), ApartmentWalkPasses);
    // The runtime walker is replaced by the later departure/pit-stop stages; samples retain this walker's exact counts.
    int32 Rescues = 0;
    for (const auto &Value : ApartmentWalkSamples)
        Rescues = FMath::Max(Rescues, int32(Value->AsObject()->GetNumberField(TEXT("offDeckRescues"))));
    if (ApartmentDoorClosures != 1)
        if (const auto *GM = Mode.Get(); GM && GM->Walker)
            Rescues = FMath::Max(Rescues, GM->Walker->OffDeckRecoveries());
    Result->SetNumberField(TEXT("apartmentOffDeckRescues"), Rescues);
    Result->SetNumberField(TEXT("apartmentSetupPlacements"), ApartmentWalkStarted ? 1 : 0);
    Result->SetNumberField(TEXT("apartmentDoorClosures"), ApartmentDoorClosures);
    Result->SetNumberField(TEXT("apartmentDoorMaximumOpen"), ApartmentDoorMaximumOpen);
    Result->SetNumberField(TEXT("apartmentWalkSeconds"), ApartmentWalkSeconds);
    Result->SetNumberField(TEXT("apartmentMaximumTickTravelCm"), ApartmentMaxStepCm);
    Result->SetBoolField(TEXT("apartmentScriptedDirectInput"), true);
    Result->SetNumberField(TEXT("apartmentPlacementsAfterSetup"), 0);
    Result->SetArrayField(TEXT("apartmentWalkSamples"), ApartmentWalkSamples);
}
