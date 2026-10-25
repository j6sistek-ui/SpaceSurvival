#include "SSCryoPreview.h"
#include "SSCryoChamber.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "InputCoreTypes.h"

namespace
{
float Stick(float Value)
{
    return FMath::Abs(Value) <= .16f ? 0.f : FMath::Sign(Value) * (FMath::Abs(Value) - .16f) / .84f;
}
} // namespace

ASSCryoPreviewPawn::ASSCryoPreviewPawn()
{
    GetCapsuleComponent()->InitCapsuleSize(34.f, 88.f);
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("ReviewCamera"));
    Camera->SetupAttachment(GetCapsuleComponent());
    Camera->SetRelativeLocation(FVector(0, 0, 64));
    Camera->bUsePawnControlRotation = true;
    bUseControllerRotationYaw = true;
    GetCharacterMovement()->MaxWalkSpeed = 240.f;
}

void ASSCryoPreviewController::BeginPlay()
{
    Super::BeginPlay();
    SetInputMode(FInputModeGameOnly());
    bShowMouseCursor = false;
}

void ASSCryoPreviewController::SetupInputComponent()
{
    Super::SetupInputComponent();
    InputComponent->BindKey(EKeys::E, IE_Pressed, this, &ASSCryoPreviewController::Interact);
    InputComponent->BindKey(EKeys::Gamepad_FaceButton_Left, IE_Pressed, this, &ASSCryoPreviewController::Interact);
}

void ASSCryoPreviewController::PlayerTick(float DeltaSeconds)
{
    Super::PlayerTick(DeltaSeconds);
    NoticeSeconds = FMath::Max(0.f, NoticeSeconds - DeltaSeconds);
    auto *ReviewPawn = Cast<ASSCryoPreviewPawn>(GetPawn());
    if (!ReviewPawn || IsPaused() || DeltaSeconds <= 0.f)
        return;
    FVector2D Move(Stick(GetInputAnalogKeyState(EKeys::Gamepad_LeftX)),
                   Stick(GetInputAnalogKeyState(EKeys::Gamepad_LeftY)));
    Move.X += (IsInputKeyDown(EKeys::D) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::A) ? 1.f : 0.f);
    Move.Y += (IsInputKeyDown(EKeys::W) ? 1.f : 0.f) - (IsInputKeyDown(EKeys::S) ? 1.f : 0.f);
    Move = Move.GetClampedToMaxSize(1.f);
    const FRotator Yaw(0, GetControlRotation().Yaw, 0);
    ReviewPawn->AddMovementInput(Yaw.Vector(), Move.Y);
    ReviewPawn->AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Move.X);
    float MouseX = 0.f, MouseY = 0.f;
    GetInputMouseDelta(MouseX, MouseY);
    FRotator Look = GetControlRotation();
    Look.Yaw += MouseX * 1.7f + Stick(GetInputAnalogKeyState(EKeys::Gamepad_RightX)) * 90.f * DeltaSeconds;
    Look.Pitch = FMath::Clamp(FRotator::NormalizeAxis(Look.Pitch) - MouseY * 1.7f -
                                  Stick(GetInputAnalogKeyState(EKeys::Gamepad_RightY)) * 70.f * DeltaSeconds,
                              -80.f, 80.f);
    SetControlRotation(Look);
}

ASSCryoChamber *ASSCryoPreviewController::FocusedChamber() const
{
    return ASSCryoChamber::FindFocused(GetPawn(), GetControlRotation().Vector());
}

void ASSCryoPreviewController::Interact()
{
    if (IsPaused())
        return;
    if (auto *Chamber = FocusedChamber())
        Notice = Chamber->Interact(GetPawn());
    else
        Notice = TEXT("Walk up to a chamber and look at its access point.");
    NoticeSeconds = 4.f;
}

void ASSCryoPreviewHUD::DrawHUD()
{
    Super::DrawHUD();
    auto *Controller = Cast<ASSCryoPreviewController>(PlayerOwner);
    if (!Canvas || !Controller || !GEngine)
        return;
    const float Scale = FMath::Clamp(Canvas->ClipY / 1080.f, .75f, 1.5f);
    DrawText(TEXT("CRYO COMPARISON / WASD or left stick to walk / mouse or right stick to look"),
             FLinearColor(.65f, .85f, .9f), 24.f, 24.f, GEngine->GetSmallFont(), Scale);
    if (auto *Chamber = Controller->FocusedChamber())
    {
        const FString Prompt = Chamber->IsCooling() ? TEXT("Hypercooling...") : TEXT("E / X : Hypercool for 4 seconds");
        DrawText(Chamber->DisplayName + TEXT(" / ") + Prompt, FLinearColor(.4f, .95f, 1.f), 24.f,
                 Canvas->ClipY - 100.f * Scale, GEngine->GetSmallFont(), 1.2f * Scale);
    }
    if (Controller->NoticeSeconds > 0.f)
        DrawText(Controller->Notice, FLinearColor::White, 24.f, Canvas->ClipY - 65.f * Scale, GEngine->GetSmallFont(),
                 Scale);
}

ASSCryoPreviewGameMode::ASSCryoPreviewGameMode()
{
    DefaultPawnClass = ASSCryoPreviewPawn::StaticClass();
    PlayerControllerClass = ASSCryoPreviewController::StaticClass();
    HUDClass = ASSCryoPreviewHUD::StaticClass();
}
