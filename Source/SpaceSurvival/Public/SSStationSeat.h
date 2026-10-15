#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSStationSeat.generated.h"

class ASSWalker;
class UAnimSequence;

/** One cushion position on existing furniture. +X faces out; origin is the cushion surface. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSStationSeat : public AActor
{
    GENERATED_BODY()
public:
    ASSStationSeat();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seating")
    FString DisplayName = TEXT("seat");
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Seating")
    TObjectPtr<AActor> Furniture;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seating")
    bool bEnabled = true;
    /** One compatible looping pose per supported skeleton; never apply another body's clip. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seating")
    TArray<TObjectPtr<UAnimSequence>> SeatedAnimations;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seating", meta = (ClampMin = "0"))
    float PelvisHeight = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seating", meta = (ClampMin = "30", ClampMax = "200"))
    float Reach = 145.f;
    /** Local floor destinations, tried in order. Z is resolved against a walkable floor. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Seating")
    TArray<FVector> StandOffsets = {FVector(95, 0, 0), FVector(95, -65, 0), FVector(95, 65, 0)};
    UFUNCTION(BlueprintPure, Category = "Seating")
    bool IsAvailable(const ASSWalker *Walker) const;
    static ASSStationSeat *Find(const ASSWalker *Walker);
    UAnimSequence *ClipFor(const ASSWalker *Walker) const;
    bool CanReach(const ASSWalker *Walker) const;
    bool FindExit(const ASSWalker *Walker, FTransform &Out) const;
    TWeakObjectPtr<ASSWalker> Occupant;
};
