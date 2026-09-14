#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSSpaceScenery.generated.h"
class UStaticMeshComponent;
/** Distant, unreachable architecture silhouettes. Never registered as hazards or targets. */
UCLASS()
class SPACESURVIVAL_API ASSSpaceScenery : public AActor
{
    GENERATED_BODY()
public:
    ASSSpaceScenery();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    void Follow(AActor *Viewer);
    void SetFlightVisible(bool Visible);

private:
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> Structures;
    TArray<FVector> Anchors;
    TWeakObjectPtr<AActor> Followed;
    FVector LastCenter = FVector::ZeroVector;
    FVector Parallax = FVector::ZeroVector;
    bool FlightVisible = false;
};
