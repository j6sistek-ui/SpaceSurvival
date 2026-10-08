#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SSNPCHeadFillComponent.generated.h"

class UPointLightComponent;
class USceneComponent;
class USkeletalMeshComponent;

/** Explicit NPC mesh enrollment. Owns no animation, movement or Tick; never scans the world for receivers. */
UCLASS(ClassGroup = (Presentation), meta = (BlueprintSpawnableComponent))
class SPACESURVIVAL_API USSNPCHeadFillComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    USSNPCHeadFillComponent();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void OnComponentDestroyed(bool bDestroyingHierarchy) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability")
    TObjectPtr<USkeletalMeshComponent> ReceiverMesh;
    /** Null uses the owner's actor frame. Component-owned staff can name their own mesh frame instead. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability")
    TObjectPtr<USceneComponent> OffsetFrame;
    /** Ambient actors supply their existing NPCHeadFill subobject; enrolled plain meshes create one owned light. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "NPC Readability")
    TObjectPtr<UPointLightComponent> HeadFillLight;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability")
    bool bEnableHeadFill = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability")
    FName HeadFillSocket = TEXT("head");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability")
    FVector HeadFillOffset = FVector(45.f, 0.f, 15.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability", meta = (ClampMin = "0", ClampMax = "100"))
    float HeadFillLumens = 40.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability",
              meta = (ClampMin = "60", ClampMax = "140"))
    float HeadFillRadius = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NPC Readability", meta = (ClampMin = "0", ClampMax = "20"))
    float HeadFillSourceRadius = 12.f;

    /** Refresh after mesh/material/socket/profile changes. Does not touch the mesh's pose, clip or bounds. */
    UFUNCTION(BlueprintCallable, Category = "NPC Readability")
    void RefreshReadabilityLighting();
    UFUNCTION(BlueprintCallable, Category = "NPC Readability")
    void DisableAndRestoreReceiver();
    /** Explicitly enroll one existing NPC receiver, without replacing its actor or sequence binding. Caller owns
     * saving. */
    UFUNCTION(BlueprintCallable, Category = "NPC Readability")
    static USSNPCHeadFillComponent *EnrollNPCMesh(USkeletalMeshComponent *Mesh);
    static USSNPCHeadFillComponent *EnrollNPCMeshInFrame(USkeletalMeshComponent *Mesh, USceneComponent *Frame,
                                                         const FVector &Offset);

protected:
    virtual void OnRegister() override;
    virtual void OnUnregister() override;

private:
    // Serialized with the mesh/light so save and PIE duplication retain the original channel mask.
    UPROPERTY()
    TObjectPtr<USkeletalMeshComponent> OwnedReceiver;
    UPROPERTY()
    bool bOwnsReceiverChannel = false;
    UPROPERTY()
    bool bPreviousChannel2 = false;
    UPROPERTY()
    bool bCreatedLight = false;
    bool ReceiverEligible() const;
    bool EnsureLight();
};
