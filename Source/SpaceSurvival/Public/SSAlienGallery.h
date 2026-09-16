#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Pawn.h"
#include "SSAlienGallery.generated.h"

class ULevelStreamingDynamic;
class APlayerController;

// Inspection only: no collision, damage, inventory, save or progression behavior.
UCLASS()
class SPACESURVIVAL_API ASSGalleryCamera : public APawn
{
    GENERATED_BODY()
public:
    ASSGalleryCamera();
    void Drive(APlayerController *PC, float DeltaSeconds);
    float TravelSpeed = 6000.f;
};

UCLASS()
class SPACESURVIVAL_API USSAlienGallery : public UActorComponent
{
    GENERATED_BODY()
public:
    USSAlienGallery();
    bool Enter(APlayerController *PC, bool Assets = false);
    void Leave();
    void SwitchScene();
    void ResetView();
    void Update(float DeltaSeconds);
    bool IsActive() const
    {
        return State != EState::Closed;
    }
    bool IsReady() const
    {
        return State == EState::Viewing;
    }
    FString Status() const;
    static const TCHAR *MapPath(bool Assets);
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
    enum class EState
    {
        Closed,
        Loading,
        Viewing,
        Unloading
    };
    EState State = EState::Closed;
    bool bAssets = false, bSwitchAfterUnload = false;
    double LoadStarted = 0;
    FTransform ReturnTransform, InitialView;
    FRotator ReturnRotation;
    TWeakObjectPtr<APlayerController> Controller;
    TWeakObjectPtr<APawn> ReturnPawn;
    UPROPERTY()
    TObjectPtr<ULevelStreamingDynamic> Level;
    UPROPERTY()
    TObjectPtr<ASSGalleryCamera> Camera;
    struct FActorState
    {
        TWeakObjectPtr<AActor> Actor;
        bool Hidden, Collision, Tick, PostProcessEnabled;
    };
    struct FComponentState
    {
        TWeakObjectPtr<UActorComponent> Component;
        bool Tick, Visible, AudioPaused;
    };
    TArray<FActorState> Actors;
    TArray<FComponentState> Components;
    bool StartLoad();
    void SuspendScene();
    void RestoreScene();
    FTransform FindInitialView() const;
};
