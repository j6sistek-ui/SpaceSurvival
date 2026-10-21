#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSPlayableHeroTools.generated.h"

class UMaterial;
class USkeletalMesh;
class USkeletalMeshComponent;
class UAnimSequence;
class UWorld;

/** Scoped editor conversion and actual skin-surface checks for the supplied playable heroes. */
UCLASS()
class SPACESURVIVAL_API USSPlayableHeroTools : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Clear-coat pins are hidden from Python's material-property enum. No implicit save. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static bool ConfigureCoating(UMaterial *Material, float Amount, float Roughness);
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static bool PosePreview(USkeletalMeshComponent *Component, UAnimSequence *Clip, float Seconds);
    /** Evaluate the actual CPU-skinned surface in a transient world. No map/profile/asset writes. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static FString MeasureMotion(USkeletalMesh *Mesh, UAnimSequence *Clip, int32 Samples = 25);
    /** Check the imported render skin and compiled materials, without changing assets. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static FString InspectMesh(USkeletalMesh *Mesh);
    /** Bind the supplied low resolution cape/tabard proxies to this private cloth hero. No implicit save. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static FString ConfigureCloth(USkeletalMesh *Mesh, const FString &SourceJson);
    /** Read the live Chaos particle buffers on the game thread. No asset changes. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static FString ReadClothSimulation(USkeletalMeshComponent *Component);
    /** Repair cloth mappings on an explicitly copied review mesh. No implicit save or visual acceptance. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static FString RepairClothMappings(USkeletalMesh *Mesh);
    /** Report the live render-asset streaming budget without changing it. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static FString ReadStreamingBudget();
    /** Open the actual hangar/wardrobe in an explicitly isolated offscreen review profile only. */
    UFUNCTION(BlueprintCallable, Category = "Playable Hero Authoring")
    static bool BeginGameReview(UWorld *World, FName HeroId, bool ShowWardrobe = true);
};
