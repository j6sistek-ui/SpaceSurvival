#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

// Engine-independent, deterministic rules. Presentation and durable save transactions
// belong to the Unreal adapter; no codec performs file I/O or consumes a save slot.
namespace SS
{
enum class Phase
{
    Hangar,
    Flight,
    Breathing,
    Wormhole,
    Climax,
    Approach,
    Docking,
    Station,
    Dead
};
enum class Upgrade
{
    Hull,
    Shield,
    Engine,
    Thrusters,
    Weapon
};
enum class Weapon
{
    RapidLaser,
    HeavyCannon
};
enum class Ship
{
    Starter,
    Agile
};
enum class Utility
{
    None,
    VectorThrusters,
    OverdriveCooling
};
constexpr int StationUtilityPrice = 150; // Default only; purchases use the validated definition.
struct UtilityDefinition
{
    Utility kind = Utility::VectorThrusters;
    int price = StationUtilityPrice;
    double maneuverMultiplier = 1.0, responseMultiplier = 1.0;
    double boostEfficiency = 1.0, coolingEfficiency = 1.0;
};
constexpr std::array<UtilityDefinition, 2> DefaultUtilityDefinitions()
{
    return {{{Utility::VectorThrusters, StationUtilityPrice, 1.30, 1.12, 1.0, 1.0},
             {Utility::OverdriveCooling, StationUtilityPrice, 1.0, 1.0, 1.35, 1.45}}};
}
// Canonical identity order; malformed rosters fall back together. Invalid numeric rows
// fall back individually; finite high values clamp to safe tuning limits. False reports correction.
bool NormalizeUtilityDefinitions(const std::array<UtilityDefinition, 2> &input,
                                 std::array<UtilityDefinition, 2> &output);

enum class Contract
{
    None,
    Pressure,
    Objective
};
enum class DamageType
{
    Kinetic,
    Energy,
    Electrical,
    Gravity,
    Thermal
};

struct Tuning
{
    std::array<UtilityDefinition, 2> utilities = DefaultUtilityDefinitions();
    double baseHull = 100.0;
    double baseShield = 60.0;
    double baseSpeed = 2400.0;
    double baseAcceleration = 3200.0;
    double baseManeuver = 1700.0;
    double baseResponse = 5.5;
    double baseWeaponDamage = 12.0;
    double waveSecondsMin = 36.0;
    double waveSecondsMax = 48.0;
    double waveSecondsGrowth = 3.0;
    double breathSecondsMin = 5.0;
    double breathSecondsMax = 9.0;
    double wormholeSeconds = 8.0;
    double climaxSeconds = 40.0;
    double dockingSeconds = 3.0;
    double regenerationDelay = 4.0;
    double safeHullRegenPerSecond = 7.0;
    double dangerHullRegenPerSecond = 0.65;
    double boostDrainPerSecond = 28.0;
    double boostRegenPerSecond = 16.0;
    double brakeHeatPerSecond = 32.0;
    double brakeCoolingPerSecond = 24.0;
    double dodgeCooldownSeconds = 1.6;
    int waveCredits = 75;
    int killCredits = 12;
    int upgradeBasePrice = 130;
    int upgradePriceStep = 90;
    int repairPrice = 35;
    int objectiveTarget = 6;
    int pressureContractReward = 150;
    int objectiveContractReward = 150;
    double pressureShieldMultiplier = 0.65;
    double contractPressureAddition = 0.15;
};

// Validate only the fixed Phase 1 contract magnitudes; identity/cadence remain native rules.
bool NormalizeContractTuning(Tuning &tuning);

struct EffectiveStats
{
    double maxHull = 100.0, maxShield = 60.0;
    double speed = 2400.0, acceleration = 3200.0, maneuver = 1700.0, response = 5.5;
    double weaponDamage = 12.0;
    double boostEfficiency = 1.0, coolingEfficiency = 1.0;
};

struct Run
{
    std::string id;
    bool active = false, xpAwarded = false;
    int wave = 1;
    Phase phase = Phase::Hangar;
    Ship ship = Ship::Starter;
    Weapon weapon = Weapon::RapidLaser;
    Utility utility = Utility::None;
    std::array<int, 5> tiers{{1, 1, 1, 1, 1}};
    double hull = 100.0, shield = 60.0;
    int credits = 0, totalCreditsEarned = 0, kills = 0, wavesCompleted = 0;
    int eventsCompleted = 0, contractsCompleted = 0, salvageCollected = 0;
    double phaseSeconds = 0.0, phaseDuration = 0.0, elapsedSeconds = 0.0;
    double damageAge = 100.0, boost = 100.0, brakeHeat = 0.0, dodgeCooldown = 0.0;
    double interferenceSeconds = 0.0, thermalSeconds = 0.0, gravitySeconds = 0.0;
    double criticalSeconds = 0.0, damageFeedback = 0.0;
    double weaponBuffSeconds = 0.0;
    Upgrade impairedSystem = Upgrade::Thrusters;
    bool brakeOverheated = false, boosting = false, braking = false;
    bool depotSeen = false, salvageEventSeen = false, distressEventSeen = false;
    bool salvageEventAccepted = false, distressEventAccepted = false;
    bool pendingReward = false, rewardCombat = false;
    bool stationRewardClaimed = false;
    Contract contract = Contract::None;
    int contractProgress = 0, contractTarget = 0, contractAcceptedWave = 0;
    bool contractResolved = false;
    std::uint32_t rng = 1;
};

struct RunHistoryEntry
{
    std::string id;
    int wave = 1, score = 0, xp = 0, kills = 0;
    int credits = 0; // Total credits earned during this run, before purchases.
    Ship ship = Ship::Starter;
    Weapon weapon = Weapon::RapidLaser; // Active weapon at the end of the run.
};
constexpr std::size_t MaxRunHistory = 10;

struct Account
{
    std::int64_t xp = 0;
    int level = 1, highestWave = 0, runs = 0, bestScore = 0;
    int lastScore = 0, lastXP = 0, lastWave = 0;
    std::string lastAwardedRunId;
    std::uint32_t tutorialFlags = 0;
    std::vector<RunHistoryEntry> history; // Newest first, at most MaxRunHistory.
    bool HeavyCannonUnlocked() const
    {
        return level >= 2;
    }
    bool AgileShipUnlocked() const
    {
        return level >= 3;
    }
};

struct Settings
{
    double masterVolume = 0.8, musicVolume = 0.6, effectsVolume = 0.8;
    double mouseSensitivity = 1.0, controllerSensitivity = 1.0, uiScale = 1.0;
    bool subtitles = true, cameraShake = true, motionBlur = false;
    bool invertPitch = false, toggleBoost = false, toggleBrake = false;
    int quality = 2, frameLimit = 120;
};

class Session
{
public:
    Run run;
    Account account;
    Settings settings;
    Tuning tuning;

    bool StartRun(const std::string &id, Ship ship = Ship::Starter, Weapon weapon = Weapon::RapidLaser);
    void Tick(double dt, bool danger);
    void TickFlight(double dt, bool boostHeld, bool brakeHeld);
    bool Dodge();
    void ApplyDamage(double amount, DamageType type = DamageType::Kinetic);
    bool Purchase(Upgrade upgrade, double discount = 1.0);
    int UpgradePrice(Upgrade upgrade, double discount = 1.0) const;
    bool Repair();
    int DepotShieldRepairPrice() const;
    bool RepairShieldAtDepot();
    int UtilityPrice(Utility utility) const;
    bool CanPurchaseUtility(Utility utility) const;
    bool PurchaseUtility(Utility utility);
    bool EquipUtility(Utility utility);
    bool ReplaceWeapon(Weapon weapon);
    bool AcceptContract(Contract contract);
    void RecordKill();
    void AwardCredits(int amount);
    void FinishWave();
    bool BeginDocking();
    bool CompleteDocking();
    bool LaunchFromStation();
    void EndRun();
    EffectiveStats Stats() const;
    double DamageScale() const;
    double PressureMultiplier() const;
    int Score() const;
    int XPReward() const;
    bool IsFlying() const;
    bool AtSliceBoundary() const;

private:
    double RandomRange(double minimum, double maximum);
    void BeginWave();
    void ResolveContract();
};

// Strict, versioned codecs. On failure output is unchanged and error is populated.
// Account v2 stores history and reads v1 without inventing unavailable old records.
// The run/settings formats remain v1; the outer Unreal SaveGame wrapper is unchanged.
// DecodeRun restores values only: adapter must durably consume the suspended slot
// before allowing play, and invalidate it on death before presenting progression.
std::string EncodeAccount(const Account &account);
std::string EncodeRun(const Run &run);
std::string EncodeSettings(const Settings &settings);
bool DecodeAccount(const std::string &text, Account &output, std::string &error);
bool DecodeRun(const std::string &text, Run &output, std::string &error);
bool DecodeSettings(const std::string &text, Settings &output, std::string &error);
int LevelForXP(std::int64_t xp);
} // namespace SS
