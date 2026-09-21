#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSShipVisualRig.generated.h"

class APawn;
class ASSShip;
class UAnimSequence;
class UBoxComponent;
class UNiagaraComponent;
class USceneComponent;
class USkeletalMeshComponent;
struct FSSHullDefinition;

/** Adapts the supplied ship Blueprint's complete component rig to the native ship.
 *  The Blueprint is an unpossessed, non-physical presentation child. ASSShip retains all input,
 *  movement, targeting and damage authority; no vendor input or flight Tick runs. */
UCLASS()
class SPACESURVIVAL_API USSShipVisualRig : public UActorComponent
{
    GENERATED_BODY()
public:
    USSShipVisualRig();
    bool Initialize(ASSShip *Ship, const FSSHullDefinition &Definition);
    bool HasBlueprintRig() const;
    USkeletalMeshComponent *GetHull() const;
    /** Bounds of the assembled visible hull in the requested space, excluding VFX and demo helpers. */
    FBox GetHullBoundsInSpace(const FTransform &Space) const;
    /** Parked hull and measured bone-attached gear shapes query only; never another simulated body. */
    void SetStationCollision(bool Enabled);
    void UpdateFlight(FVector2D Steering, FVector2D Strafe, float Power, bool Boost, bool Brake);
    void PlayLanding(float Duration = 3.f);
    void PlayTakeoff(float Duration = 3.f);
    /** Authored muzzle VFX only. The native weapon path remains the sole damage source. */
    void PlayFiring();
    bool GetMuzzleWorldPosition(FVector &Position) const;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    void ReleaseRig();
    void PlayHullSequence(UAnimSequence *First, UAnimSequence *Then);
    void SetAirBrake(bool Deployed);
    UPROPERTY(Transient)
    TObjectPtr<APawn> RigPawn;
    UPROPERTY(Transient)
    TObjectPtr<USkeletalMeshComponent> Hull;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UBoxComponent>> GearColliders;
    UPROPERTY(Transient)
    TArray<TObjectPtr<USkeletalMeshComponent>> AirBrakes;
    UPROPERTY(Transient)
    TArray<TObjectPtr<USceneComponent>> EnginePivots;
    TArray<FQuat> EngineRestRotations;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UNiagaraComponent>> Exhausts;
    TArray<FVector> ExhaustRestScales;
    UPROPERTY(Transient)
    TArray<TObjectPtr<USceneComponent>> Muzzles;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UNiagaraComponent>> MuzzleFlashes;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> LandingOn;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> LandingOff;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> BattleEnter;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> BattleExit;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> AirBrakeClip;
    UPROPERTY(Transient)
    TObjectPtr<UAnimSequence> PendingClip;
    FVector2D SteeringInput = FVector2D::ZeroVector, StrafeInput = FVector2D::ZeroVector;
    float DrivePower = 0.f, SequenceSeconds = 0.f, SequencePlayRate = 1.f;
    bool Boosting = false, Braking = false, Landing = true, Parked = false;
};
