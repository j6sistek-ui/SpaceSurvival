#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSStationVisualLayout.generated.h"

class UBlueprint;

// Components authored in the derived Blueprint are the station's visible layout.
// The parent station owns collision, services, docking and the moving bay ship.
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSStationVisualLayout : public AActor
{
    GENERATED_BODY()
public:
    ASSStationVisualLayout();
    virtual void OnConstruction(const FTransform &Transform) override;
    void EnforcePresentationOnly();
};

UCLASS()
class SPACESURVIVAL_API USSStationLayoutAuthoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Editor-only implementation; packaged builds contain no editor dependency.
    // An existing Blueprint is returned untouched unless reset was explicit.
    UFUNCTION(BlueprintCallable, Category = "Station Authoring")
    static UBlueprint *CreateStationVisualLayout(const FString &RecipeJson, bool bResetExisting = false);
    UFUNCTION(BlueprintCallable, Category = "Station Authoring")
    static FString DescribeStationVisualLayout(UBlueprint *Blueprint);

    // Author in an ordinary saved editor level, then apply its visual components.
    UFUNCTION(BlueprintCallable, Category = "Station Authoring")
    static bool OpenStationWorkshop(FString &Result);
    UFUNCTION(BlueprintCallable, Category = "Station Authoring")
    static bool ApplyStationWorkshop(FString &Result);
    UFUNCTION(BlueprintCallable, Category = "Station Authoring")
    static bool ExportStationWorkshop(const FString &FilePath, FString &Result);
};
