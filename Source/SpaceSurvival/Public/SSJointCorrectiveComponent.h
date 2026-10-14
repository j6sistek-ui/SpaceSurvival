#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSJointCorrectiveComponent.generated.h"

class USkeletalMeshComponent;

/** A bounded shoulder morph, authored at a downward arm pose. */
USTRUCT(BlueprintType)
struct FSSJointCorrective
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Corrective")
    FName Morph;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Corrective")
    FName Bone;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Corrective")
    FName EndBone;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Corrective")
    FName ReferenceBone;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Corrective", meta = (ClampMin = "0.1", ClampMax = "1"))
    float FullWeightProjection = .75f;
};

/** Opt-in pose correctives. Reads the animated arm relative to its chest; never writes bones. */
UCLASS(ClassGroup = (Presentation), meta = (BlueprintSpawnableComponent))
class SPACESURVIVAL_API USSJointCorrectiveComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    USSJointCorrectiveComponent();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Corrective")
    TArray<FSSJointCorrective> Correctives;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Corrective")
    TArray<float> CurrentWeights;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Transient, Category = "Corrective")
    bool bBindingValid = false;
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;

private:
    struct FBinding
    {
        int32 Bone = INDEX_NONE;
        int32 End = INDEX_NONE;
        int32 Reference = INDEX_NONE;
        FVector DownAxis = FVector::ZeroVector;
        FName Morph;
        float FullWeight = 1.f;
    };
    UPROPERTY(Transient)
    TObjectPtr<USkeletalMeshComponent> Mesh;
    TArray<FBinding> Bindings;
};
