#include "SSPhotoMode.h"
#include "SSAlienGallery.h"
#include "SSGameMode.h"
#include "SSStation.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/DateTime.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

bool USSPhotoMode::Enter()
{
    auto *PC = Cast<ASSPlayerController>(GetOwner());
    auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    if (bActive || !PC || !PC->GetPawn() || !PC->PlayerCameraManager || !GM || GM->IsMenuOpen() ||
        (GM->AlienGallery && GM->AlienGallery->IsActive()))
        return false;
    if (const auto *Walker = Cast<ASSWalker>(PC->GetPawn());
        Walker && (Walker->IsBoarding() || Walker->IsDisembarking()))
        return false;
    FActorSpawnParameters Spawn;
    Spawn.ObjectFlags |= RF_Transient;
    Camera = GetWorld()->SpawnActor<ACameraActor>(Spawn);
    if (!Camera)
        return false;
    PreviousView = PC->GetViewTarget();
    PC->GetPlayerViewPoint(EntryLocation, EntryRotation);
    Anchor = PC->GetPawn()->GetActorLocation();
    EntryLocation = Anchor + (EntryLocation - Anchor).GetClampedToMaxSize(RangeCm);
    EntryFOV = PC->PlayerCameraManager->GetFOVAngle();
    Camera->SetActorLocationAndRotation(EntryLocation, EntryRotation);
    Camera->GetCameraComponent()->SetFieldOfView(EntryFOV);
    // Match the live view, including the character camera's exposure settings.
    const auto &POV = PC->PlayerCameraManager->GetCameraCacheView();
    Camera->GetCameraComponent()->PostProcessSettings = POV.PostProcessSettings;
    Camera->GetCameraComponent()->PostProcessBlendWeight = POV.PostProcessBlendWeight;
    bWasPaused = UGameplayStatics::IsGamePaused(this);
    bCameraMovable = GetWorld()->bIsCameraMoveableWhenPaused;
    if (!bWasPaused && !PC->SetPause(true))
    {
        Camera->Destroy();
        Camera = nullptr;
        return false;
    }
    GetWorld()->bIsCameraMoveableWhenPaused = true;
    PC->SetViewTarget(Camera);
    bActive = bControls = true;
    bCapturePending = false;
    CaptureStatus.Empty();
    LastUpdate = FPlatformTime::Seconds();
    return true;
}

void USSPhotoMode::Exit()
{
    if (!bActive)
        return;
    auto *PC = Cast<ASSPlayerController>(GetOwner());
    if (PC)
    {
        PC->SetViewTarget(PreviousView.IsValid() ? PreviousView.Get() : PC->GetPawn());
        if (!bWasPaused)
            PC->SetPause(false);
    }
    GetWorld()->bIsCameraMoveableWhenPaused = bCameraMovable;
    bActive = bCapturePending = false;
    if (Camera)
        Camera->Destroy();
    Camera = nullptr;
    PreviousView.Reset();
}

void USSPhotoMode::EndPlay(const EEndPlayReason::Type Reason)
{
    Exit();
    Super::EndPlay(Reason);
}

void USSPhotoMode::MoveCamera(FVector WorldDelta)
{
    if (!bActive || !Camera || WorldDelta.ContainsNaN())
        return;
    const FVector Start = Camera->GetActorLocation();
    FVector End = Anchor + (Start + WorldDelta - Anchor).GetClampedToMaxSize(RangeCm);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SSPhotoCamera), true, GetOwner());
    Query.AddIgnoredActor(Camera);
    if (auto *PC = Cast<APlayerController>(GetOwner()))
        Query.AddIgnoredActor(PC->GetPawn());
    FHitResult Hit;
    // The camera cannot cross a wall even with a large input step. Keep its near plane outside surfaces.
    if (GetWorld()->SweepSingleByChannel(Hit, Start, End, FQuat::Identity, ECC_Visibility,
                                         FCollisionShape::MakeSphere(15.f), Query))
        End = Hit.bStartPenetrating ? Start : FMath::Lerp(Start, End, FMath::Max(0.f, Hit.Time - .001f));
    Camera->SetActorLocation(End);
}

void USSPhotoMode::ResetCamera()
{
    if (!bActive || !Camera)
        return;
    Camera->SetActorLocationAndRotation(EntryLocation, EntryRotation);
    Camera->GetCameraComponent()->SetFieldOfView(EntryFOV);
}

void USSPhotoMode::Capture()
{
    if (!bActive || bCapturePending || FScreenshotRequest::IsScreenshotRequested())
        return;
    const FString Directory =
        FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("Screenshots/PhotoMode"));
    if (!IFileManager::Get().MakeDirectory(*Directory, true))
    {
        CaptureStatus = TEXT("Could not create the screenshot folder.");
        return;
    }
    LastScreenshot = Directory / (TEXT("SpaceSurvival_") + FDateTime::UtcNow().ToString(TEXT("%Y%m%d_%H%M%S")) +
                                  TEXT("_") + FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8) + TEXT(".png"));
    CaptureStarted = FPlatformTime::Seconds();
    bCapturePending = true;
    // DrawHUD also suppresses the Canvas layer; ShowUI=false alone only suppresses Slate.
    FScreenshotRequest::RequestScreenshot(LastScreenshot, false, false, false);
}

float USSPhotoMode::DistanceMetres() const
{
    return Camera ? FVector::Distance(Anchor, Camera->GetActorLocation()) / 100.f : 0.f;
}
float USSPhotoMode::FieldOfView() const
{
    return Camera ? Camera->GetCameraComponent()->FieldOfView : EntryFOV;
}

void USSPhotoMode::Update(bool AcceptInput)
{
    if (!bActive || !Camera)
        return;
    const double Now = FPlatformTime::Seconds();
    const float Dt = FMath::Clamp(float(Now - LastUpdate), 0.f, .05f);
    LastUpdate = Now;
    if (bCapturePending)
    {
        if (!FScreenshotRequest::IsScreenshotRequested() && IFileManager::Get().FileSize(*LastScreenshot) > 0)
        {
            bCapturePending = false;
            CaptureStatus = TEXT("Saved: Saved/Screenshots/PhotoMode/") + FPaths::GetCleanFilename(LastScreenshot);
        }
        else if (Now - CaptureStarted > 10.)
        {
            bCapturePending = false;
            CaptureStatus = TEXT("Screenshot was not saved. Please try again.");
        }
    }
    auto *PC = Cast<ASSPlayerController>(GetOwner());
    if (!PC || !AcceptInput)
        return;
    auto Pressed = [&](FKey K) { return PC->WasInputKeyJustPressed(K); };
    auto Down = [&](FKey K) { return PC->IsInputKeyDown(K); };
    auto Axis = [&](FKey K)
    {
        const float V = PC->GetInputAnalogKeyState(K);
        return FMath::Abs(V) > .18f ? V : 0.f;
    };
    if (Pressed(EKeys::Escape) || Pressed(EKeys::F8) || Pressed(EKeys::Gamepad_FaceButton_Right) ||
        Pressed(EKeys::Gamepad_DPad_Up))
    {
        Exit();
        return;
    }
    if (Pressed(EKeys::Home) || Pressed(EKeys::Gamepad_FaceButton_Left))
        ResetCamera();
    if (Pressed(EKeys::H) || Pressed(EKeys::Gamepad_FaceButton_Top))
        bControls = !bControls;
    float MX = 0, MY = 0;
    PC->GetInputMouseDelta(MX, MY);
    FRotator Rotation = Camera->GetActorRotation();
    Rotation.Yaw += MX * .15f + Axis(EKeys::Gamepad_RightX) * 90.f * Dt;
    Rotation.Pitch = FMath::Clamp(Rotation.Pitch + MY * .15f + Axis(EKeys::Gamepad_RightY) * 90.f * Dt, -89.f, 89.f);
    Camera->SetActorRotation(Rotation);
    FVector Motion = Rotation.Vector() * (float(Down(EKeys::W)) - float(Down(EKeys::S)) + Axis(EKeys::Gamepad_LeftY));
    Motion += FRotationMatrix(Rotation).GetUnitAxis(EAxis::Y) *
              (float(Down(EKeys::D)) - float(Down(EKeys::A)) + Axis(EKeys::Gamepad_LeftX));
    Motion.Z += float(Down(EKeys::E) || Down(EKeys::Gamepad_RightShoulder)) -
                float(Down(EKeys::Q) || Down(EKeys::Gamepad_LeftShoulder));
    const bool Fast = Down(EKeys::LeftShift) || Axis(EKeys::Gamepad_RightTriggerAxis) > .2f;
    const bool Slow = Down(EKeys::LeftControl) || Axis(EKeys::Gamepad_LeftTriggerAxis) > .2f;
    MoveCamera(Motion.GetClampedToMaxSize(1.f) * (Slow ? 70.f : Fast ? 900.f : 300.f) * Dt);
    const float Zoom = float(Pressed(EKeys::MouseScrollDown) || Pressed(EKeys::Gamepad_DPad_Right)) -
                       float(Pressed(EKeys::MouseScrollUp) || Pressed(EKeys::Gamepad_DPad_Left));
    if (Zoom != 0)
        Camera->GetCameraComponent()->SetFieldOfView(FMath::Clamp(FieldOfView() + Zoom * 5.f, 35.f, 100.f));
    if (Pressed(EKeys::Enter) || Pressed(EKeys::Gamepad_FaceButton_Bottom))
        Capture();
}
