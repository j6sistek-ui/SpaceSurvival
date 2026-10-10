#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "TimerManager.h"
#include "SSStationWarpGate.generated.h"

class ASSStation;
class ASSWalker;
class UBoxComponent;
class UNiagaraComponent;
class UNiagaraSystem;
class UPrimitiveComponent;
class USceneComponent;
class UStaticMeshComponent;

/** Paired, same-pawn station transport. Content and supported endpoints are authored separately. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSStationWarpGate : public AActor
{
    GENERATED_BODY()
public:
    ASSStationWarpGate();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp")
    TObjectPtr<USceneComponent> GateRoot;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp")
    TObjectPtr<UStaticMeshComponent> Frame;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp")
    TObjectPtr<UBoxComponent> ActivationVolume;
    /** Point on the actual collision floor, with the desired arrival yaw. Capsule height is added at use. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp")
    TObjectPtr<USceneComponent> ArrivalPoint;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp|Visual")
    TObjectPtr<UNiagaraComponent> PortalVisual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp|Visual")
    TObjectPtr<UNiagaraComponent> DepartureVisual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Warp|Visual")
    TObjectPtr<UNiagaraComponent> ArrivalVisual;

    /** Root integration binds both endpoints to the current runtime station, not the decorative ship. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Warp")
    TObjectPtr<ASSStation> Station;
    /** Pair must be reciprocal, in the same world and bound to the same station. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Warp")
    TObjectPtr<ASSStationWarpGate> PairedGate;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warp")
    bool bEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warp", meta = (ClampMin = "0.1", ClampMax = "5.0"))
    float DepartureDelay = .6f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warp|Visual", meta = (ClampMin = "0.1", ClampMax = "10.0"))
    float ArrivalDisplaySeconds = 2.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warp|Visual")
    TObjectPtr<UNiagaraSystem> PortalEffect;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warp|Visual")
    TObjectPtr<UNiagaraSystem> DepartureEffect;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Warp|Visual")
    TObjectPtr<UNiagaraSystem> ArrivalEffect;

    /** Also used by the capsule-only overlap. Stepping out during the delay cancels; input is never disabled. */
    UFUNCTION(BlueprintCallable, Category = "Warp")
    bool TryActivate(ASSWalker *Walker);
    UFUNCTION(BlueprintPure, Category = "Warp")
    bool IsTransferPending() const;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Warp")
    FString LastFailure;

private:
    UFUNCTION()
    void EnteredVolume(UPrimitiveComponent *Component, AActor *OtherActor, UPrimitiveComponent *OtherComponent,
                       int32 OtherBodyIndex, bool bFromSweep, const FHitResult &SweepResult);
    UFUNCTION()
    void LeftVolume(UPrimitiveComponent *Component, AActor *OtherActor, UPrimitiveComponent *OtherComponent,
                    int32 OtherBodyIndex);
    bool Eligible(const ASSWalker *Walker, FString &Reason) const;
    bool ResolveArrival(const ASSWalker *Walker, FVector &Location, FRotator &Facing) const;
    void CompleteTransfer();
    void CancelTransfer(const FString &Reason = FString());
    void ReleaseLatchIfOutside();
    void StopArrivalVisual();
    bool AttachBurstToWalker(UNiagaraComponent *Visual, ASSWalker *Walker);
    void RestoreBurst(UNiagaraComponent *Visual, const FTransform &RestTransform);
    UFUNCTION()
    void BurstWalkerEndedPlay(AActor *Actor, EEndPlayReason::Type EndPlayReason);
    void Refuse(ASSWalker *Walker, const FString &Reason);

    FTransform DepartureRestTransform = FTransform::Identity;
    FTransform ArrivalRestTransform = FTransform::Identity;
    TWeakObjectPtr<ASSWalker> PendingWalker;
    TWeakObjectPtr<ASSStationWarpGate> PendingDestination;
    TWeakObjectPtr<ASSStationWarpGate> IncomingSource;
    TWeakObjectPtr<ASSWalker> LatchedWalker;
    TWeakObjectPtr<ASSStationWarpGate> LatchPartner;
    FTimerHandle DepartureTimer;
    FTimerHandle ArrivalTimer;
    bool bCompletingTransfer = false;
    bool bEndingPlay = false;
};
