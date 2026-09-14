#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Subsystems/WorldSubsystem.h"
#include "SSVFXPresentation.generated.h"

class UNiagaraComponent;
class UNiagaraSystem;

UENUM(BlueprintType)
enum class ESSCombatVFX : uint8
{
    RapidBolt,
    CannonBolt,
    EnemyBolt,
    RapidMuzzle,
    CannonMuzzle,
    EnemyMuzzle,
    RapidImpact,
    CannonImpact,
    EnemyImpact,
    EnemyExplosion,
    WormholeMouth
};

USTRUCT(BlueprintType)
struct FSSCombatVFXDefinition
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, Category = "Effect")
    ESSCombatVFX Kind = ESSCombatVFX::RapidBolt;
    UPROPERTY(EditAnywhere, Category = "Effect")
    TObjectPtr<UNiagaraSystem> System;
    UPROPERTY(EditAnywhere, Category = "Effect")
    FVector Scale = FVector(1.f);
    UPROPERTY(EditAnywhere, Category = "Effect")
    FRotator RotationOffset = FRotator::ZeroRotator;
    UPROPERTY(EditAnywhere, Category = "Budget", meta = (ClampMin = "0.02", ClampMax = "8"))
    float MaximumSeconds = .6f;
    UPROPERTY(EditAnywhere, Category = "Budget", meta = (ClampMin = "0", ClampMax = "32"))
    int32 ActiveLimit = 8;
    UPROPERTY(EditAnywhere, Category = "Budget", meta = (ClampMin = "100", ClampMax = "5000"))
    float BoundsRadius = 1500.f;
    // Optional bindings must exactly match the Niagara system's exposed names/types.
    UPROPERTY(EditAnywhere, Category = "Parameters")
    FName ParticleScaleParameter;
    UPROPERTY(EditAnywhere, Category = "Parameters", meta = (ClampMin = "0.01", ClampMax = "10"))
    float ParticleScale = 1.f;
};

/** Licensed presentation only; these values cannot change combat or progression. */
UCLASS(BlueprintType)
class SPACESURVIVAL_API USSCombatVFXData : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category = "Effects")
    TArray<FSSCombatVFXDefinition> Effects;
    UPROPERTY(EditAnywhere, Category = "Budget", meta = (ClampMin = "0", ClampMax = "64"))
    int32 MaximumActive = 48;
    UPROPERTY(EditAnywhere, Category = "Budget", meta = (ClampMin = "1000", ClampMax = "60000"))
    float MaximumDistance = 22000.f;
};

/** Scene ownership makes detached bursts participate in world-origin shifts. */
UCLASS(Transient, NotBlueprintable)
class SPACESURVIVAL_API ASSCombatVFXAnchor : public AActor
{
    GENERATED_BODY()
public:
    ASSCombatVFXAnchor();
};

USTRUCT()
struct FSSCombatVFXInstance
{
    GENERATED_BODY()
    UPROPERTY()
    TObjectPtr<UNiagaraComponent> Component;
    TWeakObjectPtr<AActor> FollowOwner;
    ESSCombatVFX Kind = ESSCombatVFX::RapidBolt;
    float Age = 0.f;
    float MaximumSeconds = .6f;
    bool bAttached = false;
};

/** Preloaded, collisionless and capped Niagara; the existing actors retain all damage authority. */
UCLASS()
class SPACESURVIVAL_API USSCombatVFXSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase &Collection) override;
    virtual void Deinitialize() override;
    virtual void OnWorldBeginPlay(UWorld &InWorld) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual TStatId GetStatId() const override;
    bool AttachProjectile(AActor *Projectile, bool bFromPlayer, bool bHeavy);
    void PlayMuzzle(AActor *Source, FVector Position, FVector Direction, bool bFromPlayer, bool bHeavy);
    void PlayImpact(FVector Position, FVector Normal, bool bFromPlayer, bool bHeavy);
    void PlayEnemyExplosion(FVector Position, float BodyRadius);
    bool AttachAnomaly(AActor *Owner);

protected:
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;

private:
    UPROPERTY()
    TObjectPtr<USSCombatVFXData> Presentation;
    UPROPERTY()
    TObjectPtr<ASSCombatVFXAnchor> Anchor;
    UPROPERTY()
    TArray<FSSCombatVFXInstance> Active;
    TSet<ESSCombatVFX> ValidScaleBindings;
    UNiagaraComponent *Spawn(ESSCombatVFX Kind, FVector Position, FRotator Rotation, AActor *FollowOwner = nullptr,
                             float Size = 1.f);
};

/** Narrow authoring/audit bridge, using installed Niagara APIs rather than inferred parameter tokens. */
UCLASS()
class SPACESURVIVAL_API USSVFXPresentationLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category = "Presentation Audit")
    static FString DescribeSystem(UNiagaraSystem *System);
    UFUNCTION(BlueprintCallable, Category = "Presentation Authoring")
    static bool PreparePrivateSystem(UNiagaraSystem *System, bool bLocalSpace);
};
