#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "InstanceDataTypes.h"
#include "SSDistantAsteroids.generated.h"

class UInstancedStaticMeshComponent;
class USSSpaceLookData;

/** Persistent solid asteroid belt, independent of wave pressure and the viewer transform. */
UCLASS()
class SPACESURVIVAL_API ASSDistantAsteroids : public AActor
{
    GENERATED_BODY()
public:
    ASSDistantAsteroids();
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;

    /** Call after spawning/replacing the flight pawn. Does not read or modify run state. */
    void Follow(AActor *InViewer);
    /** Visibility is presentation-only; it never recenters the field. */
    void SetFlightVisible(bool bVisible);
    int32 GetRockCount() const
    {
        return BuiltCount;
    }
    /** Initial spawn clearance; travel can reach any rock afterward. */
    double GetMinimumSurfaceDistance() const
    {
        return MinimumAnchorSurface;
    }

protected:
    virtual void BeginPlay() override;

private:
    void BuildField(int32 Count);
    void StreamCells();
    void AddCell(const FIntVector &Cell);
    struct FRockInstance
    {
        int32 Batch;
        FPrimitiveInstanceId Id;
    };
    TMap<FIntVector, TArray<FRockInstance>> Cells;
    FIntVector ResidentCenter = FIntVector(MAX_int32);
    int32 ConfiguredCount = -1;
    UPROPERTY()
    TArray<TObjectPtr<UInstancedStaticMeshComponent>> Batches;
    UPROPERTY()
    TObjectPtr<USSSpaceLookData> SpaceLook;
    TWeakObjectPtr<AActor> Viewer;
    double MinimumAnchorSurface = 0.0;
    int32 BuiltCount = -1;
    bool bFlightVisible = false;
};
