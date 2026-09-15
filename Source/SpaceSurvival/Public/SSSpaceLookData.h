#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SSSpaceLookData.generated.h"

class UMaterialInterface;
class UTextureCube;
class UStaticMesh;

/** Editable licensed space presentation; no simulation, collision or progression data. */
UCLASS(BlueprintType)
class SPACESURVIVAL_API USSSpaceLookData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category = "Sky")
    TObjectPtr<UMaterialInterface> SkyMaterial;
    UPROPERTY(EditAnywhere, Category = "Sky")
    TObjectPtr<UTextureCube> AmbientCubemap;
    UPROPERTY(EditAnywhere, Category = "Sky", meta = (ClampMin = "0"))
    float AmbientIntensity = 20.f;
    /** Licensed cubemap compositions. Visual travel is independent of wave cadence. */
    UPROPERTY(EditAnywhere, Category = "Regions")
    TArray<TObjectPtr<UTextureCube>> RegionSkies;
    UPROPERTY(EditAnywhere, Category = "Regions")
    TObjectPtr<UTextureCube> RegionStars;
    UPROPERTY(EditAnywhere, Category = "Regions", meta = (ClampMin = "60"))
    float RegionSeconds = 180.f;
    UPROPERTY(EditAnywhere, Category = "Lighting")
    FLinearColor KeyColor = FLinearColor(.95f, .87f, .73f);
    UPROPERTY(EditAnywhere, Category = "Lighting", meta = (ClampMin = "0"))
    float KeyIntensity = 4.f;
    UPROPERTY(EditAnywhere, Category = "Dressing")
    TArray<TObjectPtr<UStaticMesh>> StructureMeshes;
    /** Normalized construction-script samples, baked from owned field Blueprints by the editor. */
    UPROPERTY(EditAnywhere, Category = "Dressing")
    TArray<FVector> AsteroidArchSamples;
    UPROPERTY(EditAnywhere, Category = "Dressing")
    TArray<FVector> AsteroidGlobularSamples;
    UPROPERTY(EditAnywhere, Category = "Dressing")
    TArray<FVector> AsteroidLinearSamples;
    UPROPERTY(EditAnywhere, Category = "Cloud")
    TObjectPtr<UMaterialInterface> CloudMaterial;
    UPROPERTY(EditAnywhere, Category = "Cloud")
    FVector CloudScale = FVector(1000, 1000, 600);
    UPROPERTY(EditAnywhere, Category = "Cloud")
    FVector CloudOffsetA = FVector(85000, 42000, -30000);
    UPROPERTY(EditAnywhere, Category = "Cloud")
    FVector CloudOffsetB = FVector(140000, -80000, 45000);
    UPROPERTY(EditAnywhere, Category = "Cloud", meta = (ClampMin = "0.000001"))
    float FogDensity = .0001f;
    UPROPERTY(EditAnywhere, Category = "Cloud", meta = (ClampMin = "1000"))
    float FogDistance = 240000.f;
};
