#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SSContentTypes.h"
#include "Domain/SurvivalCore.h"
#include "SSPhase1Data.generated.h"

/** Runtime tuning entry point. Asset content is authored by Scripts/AuthorContent.py. */
UCLASS(BlueprintType)
class SPACESURVIVAL_API USSPhase1Data : public UDataAsset
{
    GENERATED_BODY()
public:
    USSPhase1Data()
    {
        Utilities = {FSSUtilityDefinition(ESSUtilityKind::VectorThrusters),
                     FSSUtilityDefinition(ESSUtilityKind::OverdriveCooling)};
        Hazards = {
            FSSHazardDefinition(ESSWorldKind::SmallAsteroid),   FSSHazardDefinition(ESSWorldKind::MediumAsteroid),
            FSSHazardDefinition(ESSWorldKind::MassiveAsteroid), FSSHazardDefinition(ESSWorldKind::Wreckage),
            FSSHazardDefinition(ESSWorldKind::ElectricalStorm), FSSHazardDefinition(ESSWorldKind::GravityAnomaly)};
        Enemies = {FSSEnemyDefinition(ESSWorldKind::Pursuer), FSSEnemyDefinition(ESSWorldKind::Flanker)};
        Pickups = {FSSPickupDefinition(0), FSSPickupDefinition(1), FSSPickupDefinition(2), FSSPickupDefinition(3)};
        Encounters = {FSSEncounterDefinition(ESSEncounterKind::SalvageCache),
                      FSSEncounterDefinition(ESSEncounterKind::DistressCombat),
                      FSSEncounterDefinition(ESSEncounterKind::MobileDepot)};
    }
    // The same mapping is used by GameMode and engine tests. A malformed roster cannot
    // replace a utility identity or bypass its positive price through fallback.
    bool ApplyUtilityTuning(SS::Tuning &DomainTuning) const
    {
        auto input = SS::DefaultUtilityDefinitions();
        if (Utilities.Num() != 2)
        {
            DomainTuning.utilities = input;
            return false;
        }
        for (int32 i = 0; i < 2; ++i)
        {
            const auto &entry = Utilities[i];
            input[i] = {static_cast<SS::Utility>(entry.Kind),
                        entry.Price,
                        entry.ManeuverMultiplier,
                        entry.ResponseMultiplier,
                        entry.BoostEfficiency,
                        entry.CoolingEfficiency};
        }
        return SS::NormalizeUtilityDefinitions(input, DomainTuning.utilities);
    }
    UFUNCTION(BlueprintPure, Category = "Content")
    bool HasValidUtilityTuning() const
    {
        SS::Tuning DomainTuning;
        return ApplyUtilityTuning(DomainTuning);
    }
    UPROPERTY(EditAnywhere, BlueprintReadOnly, EditFixedSize, Category = "Content")
    TArray<FSSUtilityDefinition> Utilities;
    // Fixed Phase 1 rosters. Identity is read-only; tune presentation and numeric content.
    UPROPERTY(EditAnywhere, BlueprintReadOnly, EditFixedSize, Category = "Content")
    TArray<FSSHazardDefinition> Hazards;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, EditFixedSize, Category = "Content")
    TArray<FSSEnemyDefinition> Enemies;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, EditFixedSize, Category = "Content")
    TArray<FSSPickupDefinition> Pickups;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, EditFixedSize, Category = "Content")
    TArray<FSSEncounterDefinition> Encounters;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    FSSDirectorContentTuning DirectorContent;
    FSSHazardDefinition Hazard(ESSWorldKind Kind) const
    {
        for (const auto &Entry : Hazards)
            if (Entry.Kind == Kind)
                return Entry;
        return FSSHazardDefinition(Kind);
    }
    FSSEnemyDefinition Enemy(ESSWorldKind Kind) const
    {
        for (const auto &Entry : Enemies)
            if (Entry.Kind == Kind)
                return Entry;
        return FSSEnemyDefinition(Kind);
    }
    FSSPickupDefinition Pickup(int32 Kind) const
    {
        for (const auto &Entry : Pickups)
            if (Entry.Kind == Kind)
                return Entry;
        return FSSPickupDefinition(Kind);
    }
    FSSEncounterDefinition Encounter(ESSEncounterKind Kind) const
    {
        for (const auto &Entry : Encounters)
            if (Entry.Kind == Kind)
                return Entry;
        return FSSEncounterDefinition(Kind);
    }
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float CruiseSpeed = 2400.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float MinimumSpeed = 1000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float BoostMultiplier = 1.85f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float LateralSpeed = 1700.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float SteeringDegrees = 65.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float Response = 4.2f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float Acceleration = 3200.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flight")
    float DodgeImpulse = 2500.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
    float ChaseDistance = 650.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
    float MouseSensitivity = 0.143f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
    float ControllerSensitivity = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float BaseWeaponDamage = 12.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Survival")
    float BaseHull = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Survival")
    float BaseShield = 60.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    float WaveSecondsMin = 36.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    float WaveSecondsMax = 48.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    float WaveSecondsGrowth = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    float MinimumReactionSeconds = 3.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    int32 MaximumActiveThreats = 24;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Director")
    float BaseBudgetPerSecond = 1.5f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
    int32 WaveCredits = 75;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
    int32 UpgradeBasePrice = 130;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float LaserInterval = 0.12f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float CannonInterval = 0.85f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float WeaponRange = 14000.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float SoftAimDegrees = 5.f;
};
