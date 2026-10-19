#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSPhotoMode.generated.h"

/** Single-player photo camera. It never possesses a pawn or changes its transform. */
UCLASS()
class SPACESURVIVAL_API USSPhotoMode : public UActorComponent
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable)
    bool Enter();
    UFUNCTION(BlueprintCallable)
    void Exit();
    UFUNCTION(BlueprintCallable)
    void MoveCamera(FVector WorldDelta);
    UFUNCTION(BlueprintCallable)
    void Capture();
    UFUNCTION(BlueprintCallable)
    void ResetCamera();
    void Update(bool AcceptInput);
    bool IsActive() const
    {
        return bActive;
    }
    bool ShowControls() const
    {
        return bActive && bControls && !bCapturePending;
    }
    float DistanceMetres() const;
    float FieldOfView() const;
    const FString &Status() const
    {
        return CaptureStatus;
    }
    static constexpr float RangeCm = 4000.f;

    UPROPERTY(BlueprintReadOnly)
    TObjectPtr<class ACameraActor> Camera;
    UPROPERTY(BlueprintReadOnly)
    FVector Anchor = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly)
    FString LastScreenshot;

protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
    bool bActive = false, bControls = true, bCapturePending = false;
    bool bWasPaused = false, bCameraMovable = false;
    TWeakObjectPtr<AActor> PreviousView;
    FVector EntryLocation = FVector::ZeroVector;
    FRotator EntryRotation = FRotator::ZeroRotator;
    float EntryFOV = 80.f;
    double LastUpdate = 0., CaptureStarted = 0.;
    FString CaptureStatus;
};
