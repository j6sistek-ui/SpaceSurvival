#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SSContentTypes.h"
#include "Domain/SurvivalCore.h"
#include "SSPhase1Data.generated.h"

/** Existing station/run magnitudes. Original flat asset properties retain their serialized names. */
USTRUCT(BlueprintType)
struct FSSEconomyContentTuning
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "100000000"))
    int32 KillCredits = 12;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "1", ClampMax = "100000000"))
    int32 RepairPrice = 35;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "25000000"))
    int32 UpgradePriceStep = 90;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (ClampMin = "0", ClampMax = "100000000"))
    int32 StationRewardCredits = 25;
};

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
        // Preference order. The stand-in trooper is first while it is installed; the Acornaut is what
        // this repository actually ships; the squirrel waits here, inert, until its assets are imported.
        Heroes = {FSSHeroDefinition(ESSHeroIdentity::Trooper), FSSHeroDefinition(ESSHeroIdentity::Acornaut),
                  FSSHeroDefinition(ESSHeroIdentity::Squirrel)};
    }
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
    FSSEconomyContentTuning Economy;
    bool ApplyEconomyTuning(SS::Tuning &DomainTuning) const
    {
        // Leave room for the native +5-per-wave bonus and all four upgrade purchases.
        DomainTuning.waveCredits = FMath::Clamp(WaveCredits, 0, 99999955);
        DomainTuning.upgradeBasePrice = FMath::Clamp(UpgradeBasePrice, 1, 25000000);
        DomainTuning.killCredits = FMath::Clamp(Economy.KillCredits, 0, 100000000);
        DomainTuning.repairPrice = FMath::Clamp(Economy.RepairPrice, 1, 100000000);
        DomainTuning.upgradePriceStep = FMath::Clamp(Economy.UpgradePriceStep, 0, 25000000);
        return HasValidEconomyTuning();
    }
    int32 StationRewardCredits() const
    {
        return FMath::Clamp(Economy.StationRewardCredits, 0, 100000000);
    }
    int32 EventCompletionCredits(bool Combat) const
    {
        const auto Kind = Combat ? ESSEncounterKind::DistressCombat : ESSEncounterKind::SalvageCache;
        const int32 Amount = Encounter(Kind).CompletionCredits;
        // Old serialized arrays default-construct new fields before restoring their Kind.
        // Their unset sentinel must resolve by identity, never to another encounter's reward.
        return Amount == -1 ? FSSEncounterDefinition(Kind).CompletionCredits : FMath::Clamp(Amount, 0, 100000000);
    }
    UFUNCTION(BlueprintPure, Category = "Content")
    bool HasValidEconomyTuning() const
    {
        if (WaveCredits < 0 || WaveCredits > 99999955 || UpgradeBasePrice < 1 || UpgradeBasePrice > 25000000 ||
            Economy.KillCredits < 0 || Economy.KillCredits > 100000000 || Economy.RepairPrice < 1 ||
            Economy.RepairPrice > 100000000 || Economy.UpgradePriceStep < 0 || Economy.UpgradePriceStep > 25000000 ||
            Economy.StationRewardCredits < 0 || Economy.StationRewardCredits > 100000000 || Encounters.Num() != 3)
            return false;
        int32 Counts[3] = {};
        for (const auto &Entry : Encounters)
        {
            const int32 Kind = static_cast<int32>(Entry.Kind);
            if (Kind < 0 || Kind > 2 || Entry.CompletionCredits < 0 || Entry.CompletionCredits > 100000000 ||
                (Entry.Kind == ESSEncounterKind::MobileDepot && Entry.CompletionCredits != 0))
                return false;
            ++Counts[Kind];
        }
        return Counts[0] == 1 && Counts[1] == 1 && Counts[2] == 1;
    }
    // Authoring migration only: fill previously absent completion fields, preserving every authored value.
    UFUNCTION(BlueprintCallable, Category = "Content")
    bool InitializeLegacyEconomyDefaults()
    {
        bool Changed = false;
        for (auto &Entry : Encounters)
            if (Entry.CompletionCredits == -1 && static_cast<uint8>(Entry.Kind) <= 2)
            {
                Entry.CompletionCredits = FSSEncounterDefinition(Entry.Kind).CompletionCredits;
                Changed = true;
            }
        return Changed;
    }
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Content")
    FSSContractContentTuning Contracts;
    bool ApplyContractTuning(SS::Tuning &DomainTuning) const
    {
        DomainTuning.pressureShieldMultiplier = Contracts.ShieldMultiplier;
        DomainTuning.contractPressureAddition = Contracts.PressureAddition;
        DomainTuning.pressureContractReward = Contracts.PressureReward;
        DomainTuning.objectiveTarget = Contracts.ObjectiveTarget;
        DomainTuning.objectiveContractReward = Contracts.ObjectiveReward;
        return SS::NormalizeContractTuning(DomainTuning);
    }
    UFUNCTION(BlueprintPure, Category = "Content")
    bool HasValidContractTuning() const
    {
        SS::Tuning DomainTuning;
        return ApplyContractTuning(DomainTuning);
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
    /** Ordered by preference: the first entry this build actually has the assets for wears the slot. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, EditFixedSize, Category = "Content")
    TArray<FSSHeroDefinition> Heroes;
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
    FSSHeroDefinition Hero(ESSHeroIdentity Identity) const
    {
        for (const auto &Entry : Heroes)
            if (Entry.Identity == Identity)
                return Entry;
        return FSSHeroDefinition(Identity);
    }
    /** The authored entry for the hero the pawns are built with, whatever else is installed. */
    FSSHeroDefinition FallbackHero() const
    {
        return Hero(FSSHeroDefinition::Fallback().Identity);
    }
    /** The first hero in roster order whose mesh and this slot's clip are both present in this build.
     *  A hero whose assets are absent is skipped, exactly as an uninstalled stand-in always was. */
    FSSHeroDefinition SelectHero(ESSHeroSlot Slot) const
    {
        for (const auto &Entry : Heroes)
            if (Entry.Installed(Slot))
                return Entry;
        return FallbackHero();
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
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy", meta = (ClampMin = "0", ClampMax = "99999955"))
    int32 WaveCredits = 75;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy", meta = (ClampMin = "1", ClampMax = "25000000"))
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
