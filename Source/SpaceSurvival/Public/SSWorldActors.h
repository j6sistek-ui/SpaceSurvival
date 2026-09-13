#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/ActorComponent.h"
#include "Math/RandomStream.h"
#include "SSContentTypes.h"
#include "SSWorldActors.generated.h"

class ASSShip;
class ASSEncounterBeacon;
class USphereComponent;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UAudioComponent;

/** Common target/damage contract for weapon traces and environmental collisions. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSWorldBody : public AActor
{
    GENERATED_BODY()
public:
    ASSWorldBody();
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    virtual FVector GetVelocity() const override
    {
        return LinearVelocity;
    }
    UFUNCTION(BlueprintCallable)
    virtual void ReceiveWeaponHit(float Damage);
    UFUNCTION(BlueprintCallable)
    void Configure(ESSWorldKind InKind, float InRadius, float InDamage, int32 InWave = 1);
    UFUNCTION(BlueprintCallable)
    void SetLinearVelocity(FVector Value)
    {
        LinearVelocity = Value;
    }
    UFUNCTION(BlueprintCallable)
    void ApplyWorldForce(FVector Acceleration, float DeltaSeconds);
    UFUNCTION(BlueprintPure)
    ESSWorldKind GetKind() const
    {
        return Kind;
    }
    UFUNCTION(BlueprintPure)
    float GetBodyRadius() const
    {
        return BodyRadius;
    }
    UFUNCTION(BlueprintPure)
    virtual FString GetLabel() const;
    UFUNCTION(BlueprintPure)
    bool IsWeaponTarget() const;
    bool IsSolidHazard() const;
    bool IsEnemy() const;
    bool IsEnvironmentalField() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Presentation")
    TObjectPtr<UStaticMeshComponent> Visual;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Collision")
    TObjectPtr<USphereComponent> Collision;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Presentation")
    TObjectPtr<UStaticMeshComponent> ThreatIndicator;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tuning")
    float LifetimeSeconds = 65.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tuning")
    float TelegraphSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tuning")
    float GravityAcceleration = 650.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tuning")
    bool bPersistentAcrossWaves = false;

protected:
    virtual void BeginPlay() override;
    virtual void OnDefeated();
    void UpdateVisual();
    void ConfigureAudio();
    void UpdateFieldAudio(bool bDischarged);
    void PlayDestructionAudio();
    bool AdvanceElectricalPulse(float DeltaSeconds);
    ASSShip *FindShip() const;
    ESSWorldKind Kind = ESSWorldKind::SmallAsteroid;
    FVector LinearVelocity = FVector::ZeroVector;
    float BodyRadius = 110.f;
    float Health = 24.f;
    float CollisionDamage = 18.f;
    float Age = 0.f;
    // One gameplay clock also drives the visible charge/discharge phase.
    // Lazy initialization observes the Director's post-Configure reaction-time override.
    double FieldPulseRemaining = -1.0;
    double FieldPulseDuration = 1.0;
    double FieldPulseInterval = 1.8;
    bool bFieldHasDischarged = false;
    float ShipContactRemaining = 0.f;
    int32 Wave = 1;
    bool bDefeated = false;
    bool bWarningIssued = false;
    bool bHasPreviousShipPosition = false;
    FVector PreviousShipPosition = FVector::ZeroVector;
    FRandomStream LocalRandom;
    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> DynamicMaterial;
    UPROPERTY(Transient)
    TObjectPtr<UAudioComponent> FieldAudio;
};

/** Two archetypes share targeting and collision while retaining different approach geometry. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSEnemy : public ASSWorldBody
{
    GENERATED_BODY()
public:
    ASSEnemy();
    virtual void Tick(float DeltaSeconds) override;
    void SetObjectiveOwner(ASSEncounterBeacon *InOwner);
    UFUNCTION(BlueprintPure)
    bool IsChargingShot() const
    {
        return ShotCharge > 0.f;
    }

protected:
    virtual void OnDefeated() override;

private:
    float ShotCooldown = 2.f;
    float ShotCharge = 0.f;
    float SteeringPhase = 0.f;
    FVector ShotDirection = FVector::ForwardVector;
    TWeakObjectPtr<ASSEncounterBeacon> ObjectiveOwner;
};

/** World-space projectile: dodging or intervening geometry can defeat a shot. */
UCLASS()
class SPACESURVIVAL_API ASSProjectile : public ASSWorldBody
{
    GENERATED_BODY()
public:
    ASSProjectile();
    void Launch(FVector Direction, float Speed, float Damage, bool bFromPlayer, AActor *Source);
    virtual void Tick(float DeltaSeconds) override;
    virtual void ReceiveWeaponHit(float Damage) override;

private:
    bool bPlayerShot = false;
    TWeakObjectPtr<AActor> SourceActor;
};

/** Authored Wave 5 passage presentation. The game mode alone owns phase progression. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSWormholePassage : public ASSWorldBody
{
    GENERATED_BODY()
public:
    ASSWormholePassage();
    void BeginPassage(ASSShip *Ship, float Duration);
    virtual void Tick(float DeltaSeconds) override;
    virtual void ApplyWorldOffset(const FVector &InOffset, bool bWorldShift) override;
    virtual void ReceiveWeaponHit(float Damage) override {}
    virtual FString GetLabel() const override
    {
        return TEXT("WORMHOLE PASSAGE · MAINTAIN CONTROL");
    }

private:
    UPROPERTY()
    TArray<TObjectPtr<UStaticMeshComponent>> PassageRings;
    TWeakObjectPtr<ASSShip> PassageShip;
    FVector PassageForward = FVector::ForwardVector;
    FVector EntryPoint = FVector::ZeroVector;
    float PassageDuration = 8.f;
    float PassageElapsed = 0.f;
    float CourseLength = 18000.f;
};

/** Pickup kinds: 0 credits, 1 hull repair, 2 shield, 3 temporary weapon buff. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSPickup : public ASSWorldBody
{
    GENERATED_BODY()
public:
    ASSPickup();
    void ConfigurePickup(int32 InKind, float InAmount, ASSEncounterBeacon *Objective = nullptr);
    virtual void Tick(float DeltaSeconds) override;
    virtual void ReceiveWeaponHit(float Damage) override {}
    UFUNCTION(BlueprintPure)
    int32 GetPickupKind() const
    {
        return PickupKind;
    }
    UFUNCTION(BlueprintPure)
    float GetAmount() const
    {
        return Amount;
    }
    virtual FString GetLabel() const override;

private:
    int32 PickupKind = 0;
    float Amount = 30.f;
    bool bCollected = false;
    TWeakObjectPtr<ASSEncounterBeacon> ObjectiveOwner;
};

/** Offers are interaction opportunities; accepting creates objectives, never implicit success. */
UCLASS(Blueprintable)
class SPACESURVIVAL_API ASSEncounterBeacon : public ASSWorldBody
{
    GENERATED_BODY()
public:
    ASSEncounterBeacon();
    void ConfigureEncounter(ESSEncounterKind InKind, int32 InWave);
    virtual void Tick(float DeltaSeconds) override;
    virtual void ReceiveWeaponHit(float Damage) override {}
    UFUNCTION(BlueprintCallable)
    bool TryAccept();
    UFUNCTION(BlueprintPure)
    bool IsDepot() const
    {
        return EncounterKind == ESSEncounterKind::MobileDepot;
    }
    UFUNCTION(BlueprintPure)
    TArray<int32> GetOffers() const
    {
        return Offers;
    }
    UFUNCTION(BlueprintPure)
    float GetDiscount() const
    {
        return Discount;
    }
    UFUNCTION(BlueprintPure)
    float GetInteractionRadius() const
    {
        return InteractionRadius;
    }
    UFUNCTION(BlueprintPure)
    FString GetEncounterLabel() const;
    virtual FString GetLabel() const override
    {
        return GetEncounterLabel();
    }
    UFUNCTION(BlueprintPure)
    bool IsAccepted() const
    {
        return bAccepted;
    }
    UFUNCTION(BlueprintPure)
    bool IsResolved() const
    {
        return bResolved;
    }
    UFUNCTION(BlueprintPure)
    int32 GetObjectiveRemaining() const
    {
        return ObjectiveRemaining;
    }
    UFUNCTION(BlueprintPure)
    bool IsPlayerInRange() const;
    void RegisterObjectiveProgress();
    void FailObjective();

private:
    ESSEncounterKind EncounterKind = ESSEncounterKind::SalvageCache;
    TArray<int32> Offers;
    float Discount = .8f;
    float InteractionRadius = 2100.f;
    float ObjectiveSeconds = 0.f;
    int32 ObjectiveRemaining = 0;
    bool bAccepted = false;
    bool bResolved = false;
    bool bAnnounced = false;
};

/** Threat spending and spatial admission are separate from authoritative wave timing. */
UCLASS(ClassGroup = (SpaceSurvival), meta = (BlueprintSpawnableComponent))
class SPACESURVIVAL_API USSSurvivalDirectorComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    USSSurvivalDirectorComponent();
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;
    UFUNCTION(BlueprintCallable)
    void Configure(int32 InWave, bool bInClimax);
    UFUNCTION(BlueprintCallable)
    void ResetEncounter();
    UFUNCTION(BlueprintCallable)
    void SetBreathing(bool bValue);
    UFUNCTION(BlueprintPure)
    float GetPressure() const
    {
        return Pressure;
    }
    UFUNCTION(BlueprintPure)
    int32 GetActiveThreatCount() const;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fairness")
    float MinimumReactionSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fairness")
    int32 MaximumActiveThreats = 24;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Fairness")
    float PlayerClearanceRadius = 350.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tuning")
    float BaseBudgetPerSecond = 1.5f;

private:
    ASSShip *FindShip() const;
    bool FindSafeSpawn(float Radius, FVector &Location, bool bField = false) const;
    ASSWorldBody *SpawnHazard(ESSWorldKind Kind, float Radius);
    ASSEnemy *SpawnEnemy(ESSWorldKind Kind, ASSEncounterBeacon *Objective = nullptr);
    void SpawnWreckagePassage();
    void OfferEncounter(ESSEncounterKind Kind);
    void CleanTrackedActors();
    int32 Wave = 1;
    bool bClimax = false;
    bool bBreathing = false;
    bool bDepotOffered = false;
    bool bSalvageOffered = false;
    bool bDistressOffered = false;
    bool bCompoundGravitySpawned = false;
    bool bCompoundAsteroidSpawned = false;
    bool bCompoundEnemySpawned = false;
    float Pressure = 0.f;
    float AvailableBudget = 0.f;
    float SpawnCooldown = 0.f;
    float WaveAge = 0.f;
    FVector2D SafeLane = FVector2D::ZeroVector;
    mutable FRandomStream Random;
    TArray<TWeakObjectPtr<ASSWorldBody>> Spawned;
};
