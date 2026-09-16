#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSAmbientPresentation.generated.h"

class UStaticMeshComponent;
class UExponentialHeightFogComponent;
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UNiagaraComponent;
class UPointLightComponent;
class USkyLightComponent;
class USSSpaceLookData;
class ADirectionalLight;
class ASSSpaceScenery;

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
    TArray<TObjectPtr<UStaticMeshComponent>> EngineCores;
    UPROPERTY()
    TArray<TObjectPtr<UMaterialInstanceDynamic>> EngineCoreMaterials;
    UPROPERTY()
    TArray<TObjectPtr<UPointLightComponent>> EngineLights;
    UPROPERTY()
    TObjectPtr<UInstancedStaticMeshComponent> Dust;
    UPROPERTY()
    TObjectPtr<UExponentialHeightFogComponent> VolumeFog;
    UPROPERTY()
    TObjectPtr<UMaterialInstanceDynamic> DustMaterial;
    UPROPERTY()
    TObjectPtr<USkyLightComponent> AmbientLight;
    UPROPERTY()
    TObjectPtr<USSSpaceLookData> SpaceLook;
    TArray<FVector> DustPositions;
    TArray<FTransform> DustTransforms;
    TArray<float> DustSizes;
    FVector LastDustCenter = FVector::ZeroVector;
    FVector CloudTravel = FVector::ZeroVector;
    FVector LastCloudCenter = FVector::ZeroVector;
    bool CloudPositionInitialized = false;
    bool DustInitialized = false;
    void UpdateDust(const FVector &Center, const FVector &Velocity, bool Visible);
    TWeakObjectPtr<AActor> Followed;
    bool FlightVisible = false;
    bool CloudAvailable = false;
    bool TrailsAvailable = false;
    bool RestartTrails = false;
    TWeakObjectPtr<ADirectionalLight> FlightKey;
    FRotator PreviousKeyRotation = FRotator::ZeroRotator;
    FLinearColor PreviousKeyColor = FLinearColor::White;
    float PreviousKeyIntensity = 0.f;
    TWeakObjectPtr<ASSSpaceScenery> RegionScenery;
    UPROPERTY()
    TObjectPtr<UMaterialInstanceDynamic> RegionSkyMaterial;
    bool AreaStyleInitialized = false;
    FLinearColor CurrentHazeColor = FLinearColor::White;
    FLinearColor CurrentKeyColor = FLinearColor::White;
    float CurrentHazeDensity = 0.f;
    float CurrentKeyIntensity = 0.f;
    float CurrentAmbientIntensity = 0.f;
    void UpdateAreaStyle(float DeltaSeconds);
};
