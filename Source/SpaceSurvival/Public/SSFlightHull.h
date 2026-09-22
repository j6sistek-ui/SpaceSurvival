#pragma once
#include "CoreMinimal.h"
#include "Components/ShapeComponent.h"
#include "Engine/DataAsset.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSFlightHull.generated.h"

/** Cooked, fixed flight geometry in native ship coordinates. The animated rig owns parked geometry. */
UCLASS()
class SPACESURVIVAL_API USSFlightHullProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(Instanced)
    TObjectPtr<class UBodySetup> Body;
    UPROPERTY()
    FString SourceReceipt;
};

/** Extra contact geometry welded into the existing ShipCore body, with no independent simulation. */
UCLASS()
class SPACESURVIVAL_API USSFlightHullComponent : public UShapeComponent
{
    GENERATED_BODY()
public:
    USSFlightHullComponent();
    bool Initialize(USSFlightHullProfile *InProfile);
    virtual UBodySetup *GetBodySetup() override;
    virtual void UpdateBodySetup() override;
    virtual FPrimitiveSceneProxy *CreateSceneProxy() override;
    virtual FBoxSphereBounds CalcBounds(const FTransform &LocalToWorld) const override;
    virtual bool IsZeroExtent() const override;

private:
    UPROPERTY()
    TObjectPtr<USSFlightHullProfile> Profile;
};

UCLASS()
class SPACESURVIVAL_API USSFlightHullAuthoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Editor implementation only. Dry-run returns measured source/selection; save requires script ownership checks. */
    UFUNCTION(BlueprintCallable, Category = "Flight Authoring")
    static FString AuthorPhoenixFlightHull(bool bApply = false, bool bReplaceOwnedAsset = false);

    /** Preserve the supplied hull/ramp; measured animated gear replaces only its three coarse foot boxes. */
    UFUNCTION(BlueprintCallable, Category = "Flight Authoring")
    static FString AuthorPhoenixParkedPhysics(bool bApply = false, bool bReplaceOwnedAsset = false);
};
