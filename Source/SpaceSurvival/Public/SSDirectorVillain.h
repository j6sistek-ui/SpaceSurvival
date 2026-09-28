#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSDirectorVillain.generated.h"

class ASSShip;
class UPointLightComponent;
class USceneComponent;
class USkeletalMeshComponent;
class UStaticMeshComponent;

/**
 * The Director made visible: a rival who holds ahead of the player and throws the run's threats at them.
 * Where he goes (DesiredLocation) is kept apart from what is drawn (ApplyDefinition), so a later mode can
 * hand the steering to a person without rebuilding the body. He has no collision and is not a threat;
 * the Director's own counts, budget and fairness rules never see him.
 */
UCLASS()
class SPACESURVIVAL_API ASSDirectorVillain : public AActor
{
    GENERATED_BODY()
public:
    ASSDirectorVillain();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Shown villains steer; hidden ones are parked and re-place themselves ahead when shown again. */
    void SetPresent(bool bValue);
    bool IsPresent() const
    {
        return bPresent;
    }
    /** A throw: flares the villain's light so an admission reads as his doing. */
    void Launch(const FVector &Target);
    /** Tells the world's villain, if there is one, that the Director just threw something. */
    static void NotifyLaunch(UWorld *World, const FVector &Target);
    /** Where he wants to be for this ship, before smoothing. */
    FVector DesiredLocation(const ASSShip *Ship) const;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> Root;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Craft;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USkeletalMeshComponent> Rider;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPointLightComponent> Glow;

private:
    void ApplyDefinition();
    ASSShip *FindShip() const;
    bool bPresent = false;
    bool bPlaced = false;
    float Age = 0.f;
    float FlareSeconds = 0.f;
};
