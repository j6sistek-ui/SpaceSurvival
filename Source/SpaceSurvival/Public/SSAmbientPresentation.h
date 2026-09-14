#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSAmbientPresentation.generated.h"

class UStaticMeshComponent;
class UExponentialHeightFogComponent;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UNiagaraComponent;

/** Optional private-content atmosphere. Never participates in gameplay collision. */
UCLASS()
class SPACESURVIVAL_API ASSAmbientPresentation : public AActor
{
    GENERATED_BODY()
public:
    ASSAmbientPresentation();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    void Follow(AActor *Actor);
    void SetFlightVisible(bool Visible);

private:
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> CloudBanks;
    UPROPERTY()
    TArray<TObjectPtr<UMaterialInstanceDynamic>> CloudMaterials;
    UPROPERTY()
    TArray<TObjectPtr<UNiagaraComponent>> EngineTrails;
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Dust;
    UPROPERTY()
    TObjectPtr<UExponentialHeightFogComponent> VolumeFog;
    UPROPERTY()
    TObjectPtr<UMaterialInstanceDynamic> DustMaterial;
    TArray<FVector> DustPositions;
    TArray<FTransform> DustTransforms;
    TArray<float> DustSizes;
    FVector LastDustCenter = FVector::ZeroVector;
    bool DustInitialized = false;
    void UpdateDust(const FVector &Center, bool Visible);
    TWeakObjectPtr<AActor> Followed;
    bool FlightVisible = false;
    bool CloudAvailable = false;
    bool TrailsAvailable = false;
    bool RestartTrails = false;
};
