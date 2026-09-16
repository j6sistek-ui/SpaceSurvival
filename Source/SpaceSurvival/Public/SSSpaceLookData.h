#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SSSpaceLookData.generated.h"

class UMaterialInterface;
class UTextureCube;
class UStaticMesh;

/** Authored silhouette placement, expressed as a visual bounds center and radius in cm. */
USTRUCT(BlueprintType)
struct FSSSceneryPlacement
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere)
    TObjectPtr<UStaticMesh> Mesh;
    UPROPERTY(EditAnywhere)
    FVector Center = FVector(220000, 110000, 20000);
    UPROPERTY(EditAnywhere)
    FRotator Rotation = FRotator::ZeroRotator;
    UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
    float Radius = 100000.f;
};

/** Weighted small/middle scenery. Radius is a world-space visual radius, not mesh import scale. */
USTRUCT(BlueprintType)
struct FSSSceneryCandidate
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere)
    TObjectPtr<UStaticMesh> Mesh;
    UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
    float Weight = 1.f;
    UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
    float MinRadius = 1200.f;
    UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
    float MaxRadius = 6500.f;
};

/** An art-directed region. Major meshes should be coherent assemblies, not scattered kit parts. */
USTRUCT(BlueprintType)
struct FSSSpaceAreaRecipe
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere)
    FName Name;
    /** Complete group, up to eight placements; never randomly split into unrelated pieces. */
    UPROPERTY(EditAnywhere)
    TArray<FSSSceneryPlacement> Landmarks;
    UPROPERTY(EditAnywhere)
    TArray<FSSSceneryCandidate> Clutter;
    UPROPERTY(EditAnywhere, meta = (ClampMin = "0", ClampMax = "2"))
    float ClutterDensity = 1.f;
    UPROPERTY(EditAnywhere, meta = (ClampMin = "1000"))
    float ClusterRadius = 90000.f;
    /** World-fixed clear space at each cell center. Never tracks the reticle. */
    UPROPERTY(EditAnywhere, meta = (ClampMin = "1000"))
    float ClearRadius = 35000.f;
    UPROPERTY(EditAnywhere)
    FVector ClusterAxes = FVector(1.6, .55, .3);
    UPROPERTY(EditAnywhere)
    FLinearColor HazeColor = FLinearColor(.22f, .3f, .42f);
    UPROPERTY(EditAnywhere)
    float HazeDensity = .000025f;
    /** Per-zone height fog. Zero is a deliberately fogless region: open, hard-edged, high contrast.
     *  The engine divides the value it is given by 1000, so 0.0038 is roughly a moderate haze. */
    UPROPERTY(EditAnywhere, Category = "Area", meta = (ClampMin = "0"))
    float FogDensity = .0038f;
    UPROPERTY(EditAnywhere)
    FLinearColor KeyColor = FLinearColor(.95f, .87f, .73f);
    UPROPERTY(EditAnywhere)
    float KeyIntensity = 4.f;
    UPROPERTY(EditAnywhere)
    float AmbientIntensity = 20.f;
};

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
    /** Optional flight-only direction. Station lighting is restored on leaving flight. */
    UPROPERTY(EditAnywhere, Category = "Lighting")
    bool bOverrideFlightKeyDirection = false;
    UPROPERTY(EditAnywhere, Category = "Lighting")
    FRotator FlightKeyRotation = FRotator(-18, -145, 0);
    UPROPERTY(EditAnywhere, Category = "Dressing")
    TArray<TObjectPtr<UStaticMesh>> StructureMeshes;
    UPROPERTY(EditAnywhere, Category = "Dressing")
    TArray<FSSSceneryPlacement> StructureComposition;
    /** Optional world-stable regions. Empty retains the legacy licensed/source-only presentation. */
    UPROPERTY(EditAnywhere, Category = "Areas")
    TArray<FSSSpaceAreaRecipe> AreaRecipes;
    UPROPERTY(EditAnywhere, Category = "Areas", meta = (ClampMin = "300000"))
    float AreaCellSize = 500000.f;
    UPROPERTY(EditAnywhere, Category = "Areas")
    int32 AreaVariationSeed = 2718;
    /** Across all 27 resident cells, additionally bounded by 3072 minus the distant field count. */
    UPROPERTY(EditAnywhere, Category = "Areas", meta = (ClampMin = "0", ClampMax = "768"))
    int32 AreaClutterBudget = 384;
    UPROPERTY(EditAnywhere, Category = "Areas", meta = (ClampMin = "0", ClampMax = "64"))
    int32 AreaLandmarkBudget = 64;
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
