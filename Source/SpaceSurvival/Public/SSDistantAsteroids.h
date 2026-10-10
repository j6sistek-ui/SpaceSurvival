#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "InstanceDataTypes.h"
#include "SSDistantAsteroids.generated.h"

class UInstancedStaticMeshComponent;
class USSSpaceLookData;
class UStaticMesh;

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
    void SetRunSeed(uint32 Seed);
    /** Uses the trace's component and instance index; never damages a neighbouring rock. */
    bool ApplyWeaponHit(const FHitResult &Hit, float Damage, bool &bDestroyed);
    int32 GetRockCount() const
    {
        return BuiltCount;
    }
    int32 GetResidentCellCount() const
    {
        return Cells.Num();
    }
    int32 GetPendingCellCount() const
    {
        return PendingCells.Num();
    }
    FIntVector GetResidentCenter() const
    {
        return ResidentCenter;
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
    void RemoveCell(const FIntVector &Cell);
    int32 AddMeshBatch(UStaticMesh *Mesh);
    int32 RockBatchCount = 0;
    TMap<UStaticMesh *, int32> MeshBatches;
    struct FRockInstance
    {
        int32 Batch;
        FPrimitiveInstanceId Id;
        int32 Ordinal;
        FVector Center;
        float Radius;
        float Health;
        bool bAsteroid;
    };
    TMap<FIntVector, TArray<FRockInstance>> Cells;
    // One cell per modulo-five slot keeps incremental turnover at the same resident budget.
    TArray<FIntVector> PendingCells;
    // Only hit identities consume memory. Destroyed and partially damaged rocks survive cell eviction.
    TMap<FIntVector, TMap<int32, float>> DamageByCell;
    uint32 RunSeed = 0;
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
