#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSShipPresentation.generated.h"

class UStaticMeshComponent;
class UStaticMesh;

// Displays the existing purchased upgrades; owns no equipment or gameplay rules.
UCLASS()
class SPACESURVIVAL_API USSShipPresentation : public UActorComponent
{
    GENERATED_BODY()
public:
    USSShipPresentation();
    void SetHull(UStaticMeshComponent *InHull);
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;

private:
    void LoadModuleAssets();
    void Refresh();
    UPROPERTY(Transient)
    TObjectPtr<UStaticMeshComponent> Hull;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UStaticMeshComponent>> Modules;
    UPROPERTY(Transient)
    TMap<FString, TObjectPtr<UStaticMesh>> ModuleAssets;
    TArray<FString> SelectedAssets;
    bool AssetsLoaded = false;
};
