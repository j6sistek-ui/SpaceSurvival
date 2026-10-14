#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSSoftTissueComponent.generated.h"

class USkeletalMeshComponent;

/** A skin-weighted rest anchor, in the imported mesh's centimetre coordinates. */
USTRUCT(BlueprintType)
struct FSSSoftTissueAnchor
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anchor")
    FName Bone;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anchor")
    FVector RestPosition = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Anchor", meta = (ClampMin = "0"))
    float Weight = 1.f;
};

USTRUCT(BlueprintType)
struct FSSSoftTissueRegion
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
    FName MorphPrefix;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
    TArray<FSSSoftTissueAnchor> Anchors;
    /** Direction of the three authored morphs in imported reference-mesh space. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
    FVector MorphAxisSigns = FVector(1, -1, 1);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding", meta = (ClampMin = "0.01"))
    float CentimetresPerMorphUnit = 1.f;
    /** Effective moving mass; visual material density does not drive these springs. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spring", meta = (ClampMin = "0.05", ClampMax = "5"))
    float MassKg = .55f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spring", meta = (ClampMin = "10", ClampMax = "2000"))
    float Stiffness = 135.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spring", meta = (ClampMin = "0.1", ClampMax = "2"))
    float DampingRatio = .3f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spring", meta = (ClampMin = "0", ClampMax = "2"))
    float Strength = .9f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spring")
    FVector AxisResponse = FVector(1.5, .8, 1);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spring", meta = (ClampMin = "0.1", ClampMax = "3"))
    float MaxOffsetCm = 1.6f;
};

/** Opt-in, acceleration-driven morph springs. Body and garment must share paired morphs.
 * Single-player cosmetic component; owns only its XYZ morph overrides, never pose/lift curves. */
UCLASS(ClassGroup = (Presentation), meta = (BlueprintSpawnableComponent))
class SPACESURVIVAL_API USSSoftTissueComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    USSSoftTissueComponent();
    /** Empty selects the owner's first skeletal mesh. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Soft Tissue")
    FName MeshComponentName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Soft Tissue")
    bool bDynamicsEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Soft Tissue")
    TArray<FSSSoftTissueRegion> Regions;
    /** Actual authored-axis offsets, useful for tuning in PIE (centimetres). */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Soft Tissue")
    TArray<FVector> CurrentOffsetsCm;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Soft Tissue")
    bool bBindingValid = false;
    UFUNCTION(BlueprintCallable, Category = "Soft Tissue")
    void ResetDynamics();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;

private:
    struct FAnchorBinding
    {
        int32 BoneIndex = INDEX_NONE;
        FTransform InverseReference;
        FVector Position;
        float Weight = 0;
    };
    struct FRegionState
    {
        TArray<FAnchorBinding> Bindings;
        FName Morphs[3];
        FVector PreviousAnchor = FVector::ZeroVector;
        FVector PreviousVelocity = FVector::ZeroVector;
        FVector Acceleration = FVector::ZeroVector;
        FVector Offset = FVector::ZeroVector;
        FVector Velocity = FVector::ZeroVector;
        float PreviousDelta = 0;
        int32 Samples = 0;
    };
    UPROPERTY(Transient)
    TObjectPtr<USkeletalMeshComponent> Mesh;
    TArray<FRegionState> States;
};
