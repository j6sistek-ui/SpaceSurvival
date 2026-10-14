#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSAsteroidBurst.generated.h"
class UInstancedStaticMeshComponent;
/** Short cosmetic breakup; deliberately not a damageable/targetable world body. */
UCLASS(Transient, NotBlueprintable)
class SPACESURVIVAL_API ASSAsteroidBurst : public AActor
{
    GENERATED_BODY()
public:
    ASSAsteroidBurst();
    static ASSAsteroidBurst *SpawnBurst(UWorld *World, FVector Position, FVector Drift, float Radius,
                                        TOptional<FVector> ImpactPoint = {});
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UInstancedStaticMeshComponent> Chips;

private:
    void Initialize(FVector Drift, float Radius, TOptional<FVector> ImpactPoint);
    FVector InheritedVelocity = FVector::ZeroVector;
    TArray<FVector> Directions;
    TArray<FVector> Offsets;
    TArray<FQuat> Rotations;
    TArray<float> Scales;
    FVector MeshOrigin = FVector::ZeroVector;
    float Age = 0.f, StartRadius = 0.f;
    float Duration = .85f, SpreadSpeed = 650.f;
};
