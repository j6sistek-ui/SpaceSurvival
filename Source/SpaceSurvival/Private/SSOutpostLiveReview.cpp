#include "SSWave10Soak.h"
#include "SSGameMode.h"
#include "SSGameInstance.h"
#include "SSStation.h"
#include "SSOutpostSandbox.h"
#include "SSLandingPad.h"
#include "SSShip.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "UnrealClient.h"

void ASSWave10Soak::TickOutpostReview(float Dt)
{
#if WITH_DEV_AUTOMATION_TESTS && CSV_PROFILER && !CSV_PROFILER_MINIMAL
    auto *GM = Mode.Get();
    auto *GI = GM ? GM->GetGameInstance<USSGameInstance>() : nullptr;
    auto *PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!GI || !PC || !CaptureVisuals)
    {
        Stop(TEXT("Outpost review requires the real game mode, player and renderer."));
        return;
    }
    ++CapturedFrames;
    FlightSeconds += Dt;
    AllFramesForeground &= FApp::HasFocus();
    const double Now = FPlatformTime::Seconds();
    const double Elapsed = Now - OutpostStageAt;
    const auto Run = [&]() { return FString(UTF8_TO_TCHAR(SS::EncodeRun(GI->Session.run).c_str())); };
    const auto Account = [&]() { return FString(UTF8_TO_TCHAR(SS::EncodeAccount(GI->Session.account).c_str())); };
    const auto Next = [&]()
    {
        ++OutpostReviewStage;
        OutpostStageAt = Now;
    };
    const auto HomeReady = [&]()
    {
        return IsValid(GM->Hub) && GM->Hub->IsUsingOutpost() && IsValid(GM->Walker) && IsValid(GM->Ship) &&
               PC->GetPawn() == GM->Walker && GM->Hub->GetLandingPad() && !GM->Ship->IsActorTickEnabled() &&
               FVector::Dist(GM->Ship->GetActorLocation(), GM->Hub->PadDockPosition()) < 5.f;
    };
    const auto Frame = [&](const TCHAR *Name, FVector Camera, FVector Target)
    {
        if (VisualNames.Contains(Name))
            return true;
        if (StationReviewShot != FName(Name))
        {
            if (!IsValid(StationReviewCamera))
            {
                PreviousReviewViewTarget = PC->GetViewTarget();
                StationReviewCamera = GetWorld()->SpawnActor<ACameraActor>();
                if (!StationReviewCamera)
                {
                    Stop(TEXT("Unable to create isolated outpost review camera."));
                    return false;
                }
                StationReviewCamera->SetActorEnableCollision(false);
                StationReviewCamera->GetCameraComponent()->SetFieldOfView(82.f);
            }
            const FTransform T = GM->Hub->GetActorTransform();
            const FVector Position = T.TransformPosition(Camera);
            StationReviewCamera->SetActorLocationAndRotation(Position,
                                                             (T.TransformPosition(Target) - Position).Rotation());
            PC->SetViewTarget(StationReviewCamera);
            StationReviewShot = FName(Name);
            ReviewCameraReadyAt = Now + 2.;
        }
        if (Now >= ReviewCameraReadyAt && !FScreenshotRequest::IsScreenshotRequested())
            CaptureVisual(Name, float(FlightSeconds));
        return false;
    };
    if (!Started)
    {
        OutpostRunBefore = Run();
        OutpostAccountBefore = Account();
        GM->ClosePanel();
        OutpostStageAt = Now;
        Started = true;
        return;
    }
    // Practice and seeded runs deliberately update the scratch account last-run identity.
    // Require exact untouched home state before departure and exact restoration at stage6.
    const bool BoardingRequested = FParse::Param(FCommandLine::Get(), TEXT("SSSoakBoardingReview"));
    const bool ExpectedBoardingCommit = BoardingRequested && OutpostReviewStage == 3 && BoardingReviewAwaitingDeparture;
    if (OutpostReviewStage < 4 && !ExpectedBoardingCommit &&
        (Account() != OutpostAccountBefore || Run() != OutpostRunBefore))
    {
        Stop(TEXT("Outpost service inspection altered account or survival run."));
        return;
    }
    if (OutpostReviewStage == 0)
    {
        // Streaming, including the nested apartment Level Instance, must finish before probing it.
        if (!HomeReady() || Elapsed < 8.)
        {
            if (Elapsed > 45.)
                Stop(TEXT("Runtime station did not settle into its supported parked state."));
            return;
        }
        bool ApartmentPresent = false;
        for (TActorIterator<ASSOutpostDoor> It(GetWorld()); It; ++It)
            ApartmentPresent |=
                FVector::Dist(GM->Hub->GetActorTransform().InverseTransformPosition(It->GetActorLocation()),
                              FVector(6120, 4100, -120)) < 400.f;
        if (!ApartmentPresent)
        {
            if (Elapsed > 45.)
                Stop(TEXT("Streamed runtime apartment door is missing."));
            return;
        }
        if (Frame(TEXT("OutpostPad"), FVector(-5800, -2300, 600), FVector(-4200, 0, 250)))
            Next();
        return;
    }
    if (OutpostReviewStage == 1 || OutpostReviewStage == 9)
    {
        if (!HomeReady())
        {
            Stop(TEXT("Runtime outpost lost its possessed walker or real parked ship."));
            return;
        }
        const bool PitStop = OutpostReviewStage == 9;
        int32 &Checked = PitStop ? OutpostPitStopServicesChecked : OutpostServicesChecked;
        const TArray<ESSPanel> Panels =
            PitStop ? TArray<ESSPanel>{ESSPanel::Upgrades, ESSPanel::Repair, ESSPanel::Contracts, ESSPanel::Save}
                    : TArray<ESSPanel>{ESSPanel::Wardrobe, ESSPanel::Paint, ESSPanel::Launch, ESSPanel::Weapon};
        if (Checked < Panels.Num())
        {
            GM->ClosePanel();
            FVector Service;
            const ESSPanel Expected = Panels[Checked];
            if (!GM->Hub->ServicePosition(Expected, Service))
            {
                Stop(FString::Printf(TEXT("Outpost service anchor missing: %d"), int32(Expected)));
                return;
            }
            // Use the real pawn and visibility/range query. These placements are explicitly synthetic.
            auto *Walker = GM->Walker.Get();
            Walker->GetCharacterMovement()->StopMovementImmediately();
            const float Half = Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
            bool ApproachFound = false;
            for (int32 Index = 0; Index < 9 && !ApproachFound; ++Index)
            {
                const FVector Offset =
                    Index == 0 ? FVector::ZeroVector : FRotator(0, (Index - 1) * 45.f, 0).Vector() * 130.f;
                FHitResult Floor;
                FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostServiceReview), false, Walker);
                const FVector Sample = Service + Offset;
                if (!GetWorld()->LineTraceSingleByChannel(Floor, Sample + FVector(0, 0, 120),
                                                          Sample - FVector(0, 0, 220), ECC_Pawn, Query) ||
                    Floor.ImpactNormal.Z < .65f)
                    continue;
                Walker->SetActorLocation(Floor.ImpactPoint + FVector(0, 0, Half + 3), false, nullptr,
                                         ETeleportType::TeleportPhysics);
                auto *Terminal = GM->Hub->OutpostTerminalAt(Walker);
                FString ServiceLabel;
                ApproachFound = (Terminal && FVector::Dist2D(Terminal->GetActorLocation(), Service) < 60.f) ||
                                GM->Hub->NearestService(Walker->GetActorLocation(), ServiceLabel) == Expected;
            }
            if (!ApproachFound)
            {
                Stop(FString::Printf(TEXT("No supported visible use approach to outpost service %d"), int32(Expected)));
                return;
            }
            PC->SetViewTarget(Walker);
            const FString BeforeUseAccount = Account(), BeforeUseRun = Run();
            GM->Interact();
            if (Account() != BeforeUseAccount || Run() != BeforeUseRun)
            {
                Stop(TEXT("Opening a station service changed account or run state."));
                return;
            }
            if (GM->Panel != Expected)
            {
                Stop(FString::Printf(TEXT("Real outpost interaction opened panel %d, expected %d"), int32(GM->Panel),
                                     int32(Expected)));
                return;
            }
            ++Checked;
            OutpostStageAt = Now;
            return;
        }
        if (Elapsed > 2. && !FScreenshotRequest::IsScreenshotRequested())
        {
            const TCHAR *Name = PitStop ? TEXT("OutpostPitStop") : TEXT("OutpostServices");
            if (!VisualNames.Contains(Name))
                CaptureVisual(Name, float(FlightSeconds));
            else
            {
                GM->ClosePanel();
                if (PitStop)
                    OutpostReviewComplete =
                        OutpostServicesChecked == 4 && OutpostPitStopServicesChecked == 4 && OutpostFloorChecks == 27 &&
                        OutpostDepartureVerified && OutpostReturnVerified && OutpostPitStopSupported &&
                        (!ApartmentWalk || (ApartmentWalkPasses == 2 && ApartmentDoorClosures == 1));
                Next();
            }
        }
        return;
    }
    if (OutpostReviewStage == 2)
    {
        if (OutpostFloorChecks == 0)
        {
            TArray<FVector> Feet = {{4400, 1975, 0}, {4700, 1975, 0}, {4880, 1975, 0}};
            for (int32 Index = 0; Index < 6; ++Index)
                Feet.Add(FVector(4925 + Index * 50, 1975, -(Index + 1) * 20));
            Feet.Append({{5350, 1975, -120},
                         {5700, 1975, -120},
                         {5900, 1975, -120},
                         {5900, 2250, -120},
                         {5900, 2600, -120},
                         {5900, 3000, -120},
                         {5900, 3400, -120},
                         {5900, 3800, -120},
                         {5900, 4100, -120},
                         {6010, 4100, -120},
                         {6120, 4100, -120},
                         {6280, 4100, -120},
                         {6550, 4100, -120},
                         {6700, 4220, -120},
                         {6700, 4300, -120},
                         {6700, 4380, -145},
                         {6700, 4500, -170},
                         {6700, 4660, -170}});
            if (ApartmentWalk)
                ApartmentRoute = Feet;
            FCollisionQueryParams Query(SCENE_QUERY_STAT(OutpostHomeReview), false, GM->Walker);
            for (TActorIterator<ASSOutpostDoor> It(GetWorld()); It; ++It)
                Query.AddIgnoredActor(*It); // Geometry probes exclude moving doors; no door traversal claim.
            const auto *Capsule = GM->Walker->GetCapsuleComponent();
            const float Half = Capsule->GetScaledCapsuleHalfHeight();
            const float Step = GM->Walker->GetCharacterMovement()->MaxStepHeight;
            const FCollisionShape Shape =
                FCollisionShape::MakeCapsule(Capsule->GetScaledCapsuleRadius(), Half - Step * .5f);
            for (const FVector &Foot : Feet)
            {
                const FVector P = GM->Hub->GetActorTransform().TransformPosition(Foot);
                FHitResult Hit;
                const bool Floor = GetWorld()->LineTraceSingleByChannel(Hit, P + FVector(0, 0, 35),
                                                                        P - FVector(0, 0, 80), ECC_Pawn, Query);
                if (!Floor || FMath::Abs(Hit.ImpactPoint.Z - P.Z) >= 28.f || Hit.ImpactNormal.Z <= .65f)
                {
                    Stop(TEXT("Runtime apartment route lacks physical floor at ") + Foot.ToString());
                    return;
                }
                const FVector Center = P + FVector(0, 0, Half + Step * .5f + 4);
                if (GetWorld()->SweepSingleByChannel(Hit, Center, Center + FVector(0, 0, .1), FQuat::Identity, ECC_Pawn,
                                                     Shape, Query))
                {
                    Stop(TEXT("Runtime apartment upper capsule clearance blocked at ") + Foot.ToString() +
                         TEXT(" by ") + GetNameSafe(Hit.GetActor()));
                    return;
                }
                ++OutpostFloorChecks;
            }
        }
        if (ApartmentWalk && !TickApartmentWalk(Dt, ApartmentRoute))
            return;
        if (Frame(TEXT("OutpostApartment"), FVector(6450, 4570, 5), FVector(7650, 4850, 30)))
            Next();
        return;
    }
    if (OutpostReviewStage == 3)
    {
        if (BoardingRequested)
        {
            if (TickBoardingReview(Dt))
            {
                PC->SetViewTarget(GM->Ship);
                Next();
            }
            return;
        }
        // BeginFreeFlight only creates an in-memory Session backup, but refuses a blocked account.
        // Restore the guard synchronously; no persistence API is invoked or enabled across a tick.
        {
            TGuardValue<bool> AllowPractice(GI->AccountStorageBlocked, false);
            GM->StartFreeFlight();
        }
        if (!GI->IsFreeFlight() || !GM->Ship || PC->GetPawn() != GM->Ship)
        {
            Stop(TEXT("Public StartFreeFlight did not leave the outpost in the real ship."));
            return;
        }
        PC->SetViewTarget(GM->Ship);
        Next();
        return;
    }
    if (OutpostReviewStage == 4)
    {
        if (!GI->IsFreeFlight() || !IsValid(GM->Ship) || PC->GetPawn() != GM->Ship)
        {
            Stop(TEXT("Outpost departure lost its free-flight session or ship possession."));
            return;
        }
        GM->Ship->SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 1.f, false, false);
        if (GM->Ship->IsTakingOff())
            return;
        if (!OutpostDepartureVerified)
        {
            OutpostDepartureVerified = !GM->Ship->IsMoored();
            OutpostFlightStart = GM->Ship->GetActorLocation();
            OutpostStageAt = Now;
        }
        if (Now - OutpostStageAt > 3. && FVector::Dist(GM->Ship->GetActorLocation(), OutpostFlightStart) > 300.f &&
            !FScreenshotRequest::IsScreenshotRequested())
        {
            CaptureVisual(TEXT("OutpostFlight"), float(FlightSeconds));
            if (VisualNames.Contains(TEXT("OutpostFlight")))
                Next();
        }
        return;
    }
    if (OutpostReviewStage == 5)
    {
        GM->EndFreeFlight();
        GM->ClosePanel();
        Next();
        return;
    }
    if (OutpostReviewStage == 6)
    {
        if (!HomeReady() || Elapsed < 8.)
        {
            if (Elapsed > 45.)
                Stop(TEXT("Runtime station did not settle into its supported parked state."));
            return;
        }
        OutpostReturnVerified = !GI->IsFreeFlight() && Run() == OutpostRunBefore && Account() == OutpostAccountBefore;
        if (!OutpostReturnVerified)
        {
            Stop(TEXT("EndFreeFlight failed to restore the exact home account/run."));
            return;
        }
        if (Frame(TEXT("OutpostReturn"), FVector(3000, -400, 175), FVector(4200, 0, 1050)))
        {
            Next();
        }
        return;
    }
    if (OutpostReviewStage == 7 && Elapsed > 1.)
    {
        // Seed a station arrival in isolated memory. This checks active-run wiring, not the five-wave journey.
        auto &Session = GI->Session;
        if (!Session.StartRun("0a7b0570000000000000000000000005"))
        {
            Stop(TEXT("Could not seed isolated Wave5 station state."));
            return;
        }
        Session.run.wave = Session.run.wavesCompleted = 5;
        Session.run.phase = SS::Phase::Docking;
        if (!Session.CompleteDocking())
        {
            Stop(TEXT("Seeded station state failed the domain docking completion."));
            return;
        }
        GM->PreviousPhase = int32(SS::Phase::Station);
        GM->PreviousWave = 5;
        GM->EnterStation();
        Next();
        return;
    }
    if (OutpostReviewStage == 8)
    {
        if (!HomeReady() || Elapsed < 8. || GM->Walker->IsDisembarking())
            return;
        const auto *Movement = GM->Walker->GetCharacterMovement();
        OutpostPitStopSupported = !GM->Hub->IsHome() && GI->Session.run.active && GI->Session.run.wave == 5 &&
                                  GI->Session.run.phase == SS::Phase::Station && Movement->IsMovingOnGround() &&
                                  Movement->CurrentFloor.bBlockingHit &&
                                  GM->Hub->Walkable(GM->Walker->GetActorLocation()) &&
                                  GM->Walker->OffDeckRecoveries() == 0;
        if (!OutpostPitStopSupported)
        {
            Stop(TEXT("Seeded Wave5 outpost arrival lacks an active run or naturally supported possessed walker."));
            return;
        }
        Next();
        return;
    }
    if (OutpostReviewStage == 10 && Elapsed > 1.)
        Stop(TEXT(""));
#endif
}
