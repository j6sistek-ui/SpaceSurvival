#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSDistantAsteroids.generated.h"

class UInstancedStaticMeshComponent;

/** Unreachable background dressing, deliberately outside the damage/target actor hierarchy. */
UCLASS()
class SPACESURVIVAL_API ASSDistantAsteroids : public AActor
{
    GENERATED_BODY()
public:
    ASSDistantAsteroids();
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;

    /** Call after spawning/replacing the flight pawn. Does not read or modify run state. */
    void Follow(AActor *InViewer);
    /** Lead must disable for station approach, docking and on-foot/hangar views. */
    void SetFlightVisible(bool bVisible);
    int32 GetRockCount() const
    {
        return BuiltCount;
    }
    /** Conservative world-space distance from viewer to the nearest rendered mesh bound. */
    double GetMinimumSurfaceDistance() const
    {
        return MinimumAnchorSurface - ParallaxOffset.Size();
    }

protected:
    virtual void BeginPlay() override;

private:
    void BuildField(int32 Count);
    UPROPERTY()
    TArray<TObjectPtr<UInstancedStaticMeshComponent>> Batches;
    TWeakObjectPtr<AActor> Viewer;
    FVector PreviousViewerPosition = FVector::ZeroVector;
    FVector ParallaxOffset = FVector::ZeroVector;
    FQuat FieldBasis = FQuat::Identity;
    double MinimumAnchorSurface = 0.0;
    TArray<TArray<FTransform>> RestTransforms;
    TArray<TArray<FTransform>> AnimatedTransforms;
    double SpinSeconds = 0.0;
    int32 BuiltCount = -1;
    bool bFlightVisible = false;
};
