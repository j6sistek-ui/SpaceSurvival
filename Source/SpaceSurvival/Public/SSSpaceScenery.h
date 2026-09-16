#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSSpaceScenery.generated.h"
class UStaticMeshComponent;
class USSSpaceLookData;
struct FSSSpaceAreaRecipe;
struct FSSSpaceAreaBlend
{
    int32 First = 0;
    int32 Second = 0;
    float Alpha = 0.f;
};
/** World-stable cosmetic regions with a legacy distant-shell fallback. Never hazards or targets. */
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
    /** Runtime content injection also permits licensed-independent automation fixtures. */
    void ConfigureLook(USSSpaceLookData *Data);
    /** Persistent run identity varies normal play; explicit recipe previews ignore it. */
    void SetRunSeed(uint32 Seed);
    static FIntVector CellAt(const FVector &LogicalPosition, double CellSize);
    static FSSSpaceAreaBlend SampleAreaStyle(const USSSpaceLookData *Data, const FVector &LogicalPosition,
                                             int32 Preview = -1, int32 Variation = 0);
    int32 GetResidentCellCount() const
    {
        return Cells.Num();
    }
    int32 GetResidentClutterCount() const
    {
        return ResidentClutter;
    }
    int32 GetResidentLandmarkCount() const
    {
        return ResidentLandmarks;
    }
    int32 GetCurrentAreaIndex() const;
    const FSSSpaceAreaRecipe *GetActiveRecipe() const;
    FSSSpaceAreaBlend GetCurrentAreaBlend() const;

private:
    struct FCell
    {
        TArray<UStaticMeshComponent *> Parts;
        int32 Clutter = 0;
        int32 Landmarks = 0;
    };
    UPROPERTY()
    TObjectPtr<USSSpaceLookData> Look;
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> Structures;
    TArray<FVector> Anchors;
    TMap<FIntVector, FCell> Cells;
    FVector OriginOffset = FVector::ZeroVector;
    FIntVector LastCell = FIntVector(MAX_int32);
    int32 LastPreview = MIN_int32;
    int32 LastVariation = MIN_int32;
    int32 LastClutterBudget = -1;
    int32 ResidentClutter = 0;
    int32 ResidentLandmarks = 0;
    uint32 RunSeed = 0;
    int32 EffectiveVariation() const;
    void ClearGeometry();
    void RefreshCells();
    void BuildCell(const FIntVector &Id, int32 ClutterPerCell, int32 LandmarksPerCell);
    TWeakObjectPtr<AActor> Followed;
    FVector LastCenter = FVector::ZeroVector;
    FVector Parallax = FVector::ZeroVector;
    bool FlightVisible = false;
};
