#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SSCryoChamber.generated.h"

class UMaterialInstanceDynamic;
class UCapsuleComponent;
class UMaterialInterface;
class UMeshComponent;
class UNiagaraComponent;
class UNiagaraSystem;

USTRUCT()
struct FSSCryoPaneBinding
{
    GENERATED_BODY()

    UPROPERTY()
    TObjectPtr<UMeshComponent> Mesh;
    UPROPERTY()
    TObjectPtr<UMaterialInterface> Original;
    UPROPERTY()
    TObjectPtr<UMaterialInstanceDynamic> Dynamic;
    int32 Slot = 0;
    float NormalAmount = 0.f;
};

/** Cosmetic, single-player cycle. Geometry, materials and outlet transforms are authored content. */
UCLASS(Blueprintable)
class SSCRYORUNTIME_API ASSCryoChamber : public AActor
{
    GENERATED_BODY()

public:
    ASSCryoChamber();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cryo")
    FString DisplayName = TEXT("Cryogenic chamber");
    /** Every actor must contain at least one mesh slot exposing FreezeAmount. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "Cryo")
    TArray<TObjectPtr<AActor>> FrostSurfaces;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cryo")
    TObjectPtr<UNiagaraSystem> JetSystem;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo")
    TObjectPtr<UNiagaraComponent> LeftNozzle;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo")
    TObjectPtr<UNiagaraComponent> RightNozzle;
    /** Simple walking boundary; the imported comparison bodies have no collision. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Cryo")
    TObjectPtr<UCapsuleComponent> BodyCollision;
    /** Local console access point, independent of the chamber geometry origin. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cryo")
    FVector UsePoint = FVector(0, -100, 100);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cryo", meta = (ClampMin = "100", ClampMax = "400"))
    float UseDistance = 250.f;

    UFUNCTION(BlueprintCallable, Category = "Cryo")
    FString Interact(APawn *User);
    UFUNCTION(BlueprintPure, Category = "Cryo")
    bool CanUse(const APawn *User) const;
    UFUNCTION(BlueprintPure, Category = "Cryo")
    bool IsCooling() const
    {
        return bCooling;
    }
    UFUNCTION(BlueprintPure, Category = "Cryo")
    bool IsConfigured() const
    {
        return bConfigured;
    }
    UFUNCTION(BlueprintPure, Category = "Cryo")
    float GetFreezeAmount() const
    {
        return FreezeAmount;
    }
    UFUNCTION(BlueprintPure, Category = "Cryo")
    float GetCycleElapsed() const
    {
        return CycleElapsed;
    }
    UFUNCTION(BlueprintPure, Category = "Cryo")
    int32 GetBoundPaneCount() const
    {
        return Panes.Num();
    }
    UFUNCTION(BlueprintPure, Category = "Cryo")
    FVector GetUseLocation() const;

    static ASSCryoChamber *FindFocused(const APawn *User, const FVector &ViewDirection);
    static constexpr float CycleDuration = 4.f;

private:
    bool BindPanes();
    void SetFreeze(float Amount);
    void FinishCycle();
    void RestoreMaterials();
    UPROPERTY(Transient)
    TArray<FSSCryoPaneBinding> Panes;
    FTimerHandle FinishTimer;
    bool bConfigured = false;
    bool bCooling = false;
    double CycleStartedAt = 0.;
    float CycleElapsed = 0.f;
    float FreezeAmount = 0.f;
};
