#include "SurvivalCore.h"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <locale>
#include <sstream>

namespace SS
{
namespace
{
constexpr int MaxCounter = 100000000;
bool Finite(double value, double low, double high)
{
    return std::isfinite(value) && value >= low && value <= high;
}
bool ValidId(const std::string &value, bool allowEmpty = false)
{
    if (value.empty())
        return allowEmpty;
    if (value.size() > 128)
        return false;
    for (const unsigned char c : value)
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_'))
            return false;
    return true;
}
template <class E> bool EnumIn(E value, int last)
{
    return static_cast<int>(value) >= 0 && static_cast<int>(value) <= last;
}
int SaturatingAdd(int current, int increment)
{
    return static_cast<int>(std::min<std::int64_t>(MaxCounter, static_cast<std::int64_t>(current) + increment));
}
bool TravelPhase(Phase phase)
{
    return phase == Phase::Flight || phase == Phase::Breathing || phase == Phase::Wormhole || phase == Phase::Climax ||
           phase == Phase::Approach;
}
bool HasAwardedRun(const Account &account, const std::string &id)
{
    return account.lastAwardedRunId == id ||
           std::any_of(account.history.begin(), account.history.end(),
                       [&id](const RunHistoryEntry &entry) { return entry.id == id; });
}
std::ostringstream Writer(const char *kind, int version = 1)
{
    std::ostringstream stream;
    stream.imbue(std::locale::classic());
    stream << "SS " << kind << ' ' << version << ' ' << std::setprecision(17);
    return stream;
}
bool Header(std::istringstream &stream, const char *expected, std::string &error, int maximumVersion = 1,
            int *actualVersion = nullptr)
{
    std::string magic, kind;
    int version = 0;
    if (!(stream >> magic >> kind >> version) || magic != "SS" || kind != expected || version < 1 ||
        version > maximumVersion)
    {
        error = "Unsupported or malformed save header";
        return false;
    }
    if (actualVersion)
        *actualVersion = version;
    return true;
}
bool FinishRead(std::istringstream &stream, std::string &error)
{
    if (stream.fail())
    {
        error = "Truncated or invalid save value";
        return false;
    }
    stream >> std::ws;
    if (!stream.eof())
    {
        error = "Unexpected trailing save data";
        return false;
    }
    return true;
}
bool ValidateRun(const Run &r)
{
    if (!ValidId(r.id) || !EnumIn(r.phase, 8) || !EnumIn(r.ship, 1) || !EnumIn(r.weapon, 1) || !EnumIn(r.utility, 2) ||
        !EnumIn(r.contract, 2) || !EnumIn(r.impairedSystem, 4))
        return false;
    if (r.wave < 1 || r.wave > 10 || r.wavesCompleted < 0 || r.wavesCompleted > 10 || r.wavesCompleted > r.wave)
        return false;
    if (r.active && (r.phase == Phase::Hangar || r.phase == Phase::Dead || r.xpAwarded || r.hull <= 0.0))
        return false;
    if (!r.active && r.phase != Phase::Hangar && r.phase != Phase::Dead)
        return false;
    if (r.phase == Phase::Dead && (r.hull != 0.0 || !r.xpAwarded))
        return false;
    if (r.phase == Phase::Station && ((r.wave != 5 && r.wave != 10) || r.wavesCompleted != r.wave))
        return false;
    if ((r.phase == Phase::Approach || r.phase == Phase::Docking) &&
        ((r.wave != 5 && r.wave != 10) || r.wavesCompleted != r.wave))
        return false;
    if (r.phase == Phase::Wormhole && r.wave != 5)
        return false;
    if (r.phase == Phase::Flight && r.wave == 10)
        return false;
    if (r.phase == Phase::Climax && r.wave != 5 && r.wave != 10)
        return false;
    if ((r.phase == Phase::Flight || r.phase == Phase::Wormhole || r.phase == Phase::Climax) &&
        r.wavesCompleted != r.wave - 1)
        return false;
    if (r.phase == Phase::Breathing && (r.wavesCompleted != r.wave || r.wave % 5 == 0 || r.phaseDuration > 20.0))
        return false;
    if (r.boosting && r.braking)
        return false;
    for (int tier : r.tiers)
        if (tier < 1 || tier > 5)
            return false;
    const int counters[] = {r.credits,          r.totalCreditsEarned, r.kills, r.eventsCompleted, r.contractsCompleted,
                            r.salvageCollected, r.contractProgress};
    for (int value : counters)
        if (value < 0 || value > MaxCounter)
            return false;
    if (r.credits > r.totalCreditsEarned || r.contractTarget < 0 || r.contractTarget > 10000 ||
        r.contractAcceptedWave < 0 || r.contractAcceptedWave > 10)
        return false;
    if (r.contract == Contract::None &&
        (r.contractTarget != 0 || r.contractProgress != 0 || r.contractAcceptedWave != 0))
        return false;
    if (r.contract != Contract::None && (r.contractAcceptedWave != 5 || r.contractTarget < 1))
        return false;
    const double times[] = {r.phaseSeconds,    r.phaseDuration,       r.elapsedSeconds,   r.damageAge,
                            r.dodgeCooldown,   r.interferenceSeconds, r.thermalSeconds,   r.gravitySeconds,
                            r.criticalSeconds, r.damageFeedback,      r.weaponBuffSeconds};
    for (double value : times)
        if (!Finite(value, 0.0, 100000000.0))
            return false;
    if (!Finite(r.hull, 0.0, 1000000.0) || !Finite(r.shield, 0.0, 1000000.0) || !Finite(r.boost, 0.0, 100.0) ||
        !Finite(r.brakeHeat, 0.0, 100.0) || r.rng == 0)
        return false;
    if ((r.salvageEventAccepted && !r.salvageEventSeen) || (r.distressEventAccepted && !r.distressEventSeen))
        return false;
    return true;
}
} // namespace

int LevelForXP(std::int64_t xp)
{
    // Early sidegrade unlocks at 150 and 450 XP. No permanent stat multipliers.
    if (xp < 150)
        return 1;
    if (xp < 450)
        return 2;
    return static_cast<int>(std::min<std::int64_t>(1000, 3 + (xp - 450) / 600));
}

double Session::RandomRange(double minimum, double maximum)
{
    run.rng ^= run.rng << 13;
    run.rng ^= run.rng >> 17;
    run.rng ^= run.rng << 5;
    return minimum + (maximum - minimum) * (static_cast<double>(run.rng) / 4294967295.0);
}

bool Session::StartRun(const std::string &id, Ship ship, Weapon weapon)
{
    if (run.active || !ValidId(id) || HasAwardedRun(account, id) || !EnumIn(ship, 1) || !EnumIn(weapon, 1))
        return false;
    if ((ship == Ship::Agile && !account.AgileShipUnlocked()) ||
        (weapon == Weapon::HeavyCannon && !account.HeavyCannonUnlocked()))
        return false;
    run = Run{};
    run.id = id;
    run.active = true;
    run.ship = ship;
    run.weapon = weapon;
    run.rng = 2166136261u;
    for (unsigned char c : id)
    {
        run.rng ^= c;
        run.rng *= 16777619u;
    }
    if (run.rng == 0)
        run.rng = 1;
    run.hull = Stats().maxHull;
    run.shield = Stats().maxShield;
    account.highestWave = std::max(account.highestWave, 1);
    BeginWave();
    return true;
}

void Session::BeginWave()
{
    run.phase = run.wave == 10 ? Phase::Climax : Phase::Flight;
    run.phaseSeconds = 0.0;
    const double low = std::max(1.0, tuning.waveSecondsMin);
    const double high = std::max(low, tuning.waveSecondsMax);
    run.phaseDuration = run.wave == 10
                            ? std::max(1.0, tuning.climaxSeconds)
                            : RandomRange(low, high) + std::max(0.0, tuning.waveSecondsGrowth) * (run.wave - 1);
    account.highestWave = std::max(account.highestWave, run.wave);
}

bool Session::IsFlying() const
{
    return run.active && TravelPhase(run.phase);
}
bool Session::AtSliceBoundary() const
{
    return run.active && run.phase == Phase::Station && run.wave == 10;
}

EffectiveStats Session::Stats() const
{
    EffectiveStats stats;
    auto tier = [this](Upgrade upgrade)
    {
        int value = std::clamp(run.tiers[static_cast<std::size_t>(upgrade)], 1, 5);
        if (run.criticalSeconds > 0.0 && run.impairedSystem == upgrade)
            value = std::max(1, value - 2);
        return value - 1;
    };
    const bool agile = run.ship == Ship::Agile;
    stats.maxHull = tuning.baseHull * (agile ? 0.88 : 1.0) * (1.0 + tier(Upgrade::Hull) * 0.45);
    stats.maxShield =
        tuning.baseShield * (1.0 + tier(Upgrade::Shield) * 0.50) * (run.contract == Contract::Pressure ? 0.65 : 1.0);
    stats.speed = tuning.baseSpeed * (agile ? 1.12 : 1.0) * (1.0 + tier(Upgrade::Engine) * 0.13);
    stats.acceleration = tuning.baseAcceleration * (agile ? 1.10 : 1.0) * (1.0 + tier(Upgrade::Engine) * 0.22);
    stats.maneuver = tuning.baseManeuver * (agile ? 1.18 : 1.0) * (1.0 + tier(Upgrade::Thrusters) * 0.20);
    stats.response = tuning.baseResponse * (agile ? 1.16 : 1.0) * (1.0 + tier(Upgrade::Thrusters) * 0.12);
    stats.weaponDamage = tuning.baseWeaponDamage * (run.weapon == Weapon::HeavyCannon ? 4.2 : 1.0) *
                         (1.0 + tier(Upgrade::Weapon) * 0.35);
    if (run.weaponBuffSeconds > 0.0)
        stats.weaponDamage *= 1.35;
    if (run.utility == Utility::VectorThrusters)
    {
        stats.maneuver *= 1.30;
        stats.response *= 1.12;
    }
    if (run.utility == Utility::OverdriveCooling)
    {
        stats.boostEfficiency = 1.35;
        stats.coolingEfficiency = 1.45;
    }
    if (run.interferenceSeconds > 0.0)
        stats.response *= 0.80;
    return stats;
}

double Session::DamageScale() const
{
    return 1.0 + 0.12 * (run.wave - 1);
}
double Session::PressureMultiplier() const
{
    return 1.0 + (run.wave - 1) * 0.13 + (run.contract == Contract::Pressure ? 0.15 : 0.0);
}

void Session::Tick(double dt, bool danger)
{
    if (!run.active || !Finite(dt, 0.0, 120.0))
        return;
    // Bounded substeps keep recovery/timer transitions stable through frame hitches.
    while (dt > 0.0000001 && run.active)
    {
        const double step = std::min(dt, 0.05);
        dt -= step;
        run.elapsedSeconds += step;
        run.damageAge = std::min(1000000.0, run.damageAge + step);
        run.dodgeCooldown = std::max(0.0, run.dodgeCooldown - step);
        run.interferenceSeconds = std::max(0.0, run.interferenceSeconds - step);
        run.gravitySeconds = std::max(0.0, run.gravitySeconds - step);
        run.criticalSeconds = std::max(0.0, run.criticalSeconds - step);
        run.damageFeedback = std::max(0.0, run.damageFeedback - step);
        run.weaponBuffSeconds = std::max(0.0, run.weaponBuffSeconds - step);
        if (run.thermalSeconds > 0.0)
        {
            const double heatStep = std::min(step, run.thermalSeconds);
            run.thermalSeconds -= heatStep;
            ApplyDamage(2.0 * heatStep, DamageType::Kinetic);
            if (!run.active)
                break;
        }
        if (run.damageAge >= tuning.regenerationDelay)
        {
            const double rate = danger ? tuning.dangerHullRegenPerSecond : tuning.safeHullRegenPerSecond;
            run.hull = std::min(Stats().maxHull, run.hull + std::max(0.0, rate) * step);
        }
        if (run.phase == Phase::Flight || run.phase == Phase::Breathing || run.phase == Phase::Wormhole ||
            run.phase == Phase::Climax || run.phase == Phase::Docking)
        {
            run.phaseSeconds += step;
            if (run.phaseSeconds + 0.0000001 >= run.phaseDuration)
            {
                if (run.phase == Phase::Breathing)
                {
                    ++run.wave;
                    BeginWave();
                }
                else if (run.phase == Phase::Wormhole)
                {
                    run.phase = Phase::Climax;
                    run.phaseSeconds = 0.0;
                    run.phaseDuration = std::max(1.0, tuning.climaxSeconds);
                }
                else if (run.phase == Phase::Docking)
                    CompleteDocking();
                else
                    FinishWave();
            }
        }
    }
}

void Session::TickFlight(double dt, bool boostHeld, bool brakeHeld)
{
    if (!Finite(dt, 0.0, 120.0))
        return;
    if (!IsFlying())
    {
        run.boosting = false;
        run.braking = false;
        return;
    }
    while (dt > 0.0000001)
    {
        const double step = std::min(dt, 0.05);
        dt -= step;
        const EffectiveStats stats = Stats();
        if (run.brakeOverheated && run.brakeHeat <= 25.0)
            run.brakeOverheated = false;
        run.braking = brakeHeld && !run.brakeOverheated;
        // Brake takes priority when both are pressed: no boost drain against braking.
        run.boosting = boostHeld && !run.braking && run.boost > 0.0;
        if (run.boosting)
            run.boost = std::max(0.0, run.boost - tuning.boostDrainPerSecond * step / stats.boostEfficiency);
        else if (!boostHeld)
            run.boost = std::min(100.0, run.boost + tuning.boostRegenPerSecond * step * stats.boostEfficiency);
        if (run.braking)
        {
            run.brakeHeat = std::min(100.0, run.brakeHeat + tuning.brakeHeatPerSecond * step / stats.coolingEfficiency);
            if (run.brakeHeat >= 100.0)
            {
                run.brakeOverheated = true;
                run.braking = false;
            }
        }
        else
            run.brakeHeat =
                std::max(0.0, run.brakeHeat - tuning.brakeCoolingPerSecond * step * stats.coolingEfficiency);
        if (run.boost <= 0.0)
            run.boosting = false;
    }
}

bool Session::Dodge()
{
    if (!IsFlying() || run.dodgeCooldown > 0.0)
        return false;
    run.dodgeCooldown = std::max(0.1, tuning.dodgeCooldownSeconds);
    return true;
}

void Session::ApplyDamage(double amount, DamageType type)
{
    if (!IsFlying() || !Finite(amount, 0.0, 1000000.0) || amount <= 0.0 || !EnumIn(type, 4))
        return;
    const double shieldMultiplier = type == DamageType::Energy ? 1.35 : 1.0;
    const double absorbed = std::min(run.shield, amount * shieldMultiplier);
    run.shield -= absorbed;
    run.hull = std::max(0.0, run.hull - (amount - absorbed / shieldMultiplier));
    run.damageAge = 0.0;
    run.damageFeedback = 0.5;
    if (type == DamageType::Electrical)
        run.interferenceSeconds = std::max(run.interferenceSeconds, 2.5);
    if (type == DamageType::Gravity)
        run.gravitySeconds = std::max(run.gravitySeconds, 2.0);
    if (type == DamageType::Thermal)
        run.thermalSeconds = std::max(run.thermalSeconds, 1.5);
    if (amount >= 45.0 && RandomRange(0.0, 1.0) < 0.12)
    {
        run.impairedSystem = Upgrade::Thrusters;
        run.criticalSeconds = 12.0;
    }
    if (run.hull <= 0.0)
        EndRun();
}

int Session::UpgradePrice(Upgrade upgrade, double discount) const
{
    if (!EnumIn(upgrade, 4) || !Finite(discount, 0.1, 1.0))
        return -1;
    const int tier = run.tiers[static_cast<std::size_t>(upgrade)];
    if (tier >= 5 || tier < 1)
        return -1;
    return std::max(
        1, static_cast<int>(std::ceil((tuning.upgradeBasePrice + tuning.upgradePriceStep * (tier - 1)) * discount)));
}

bool Session::Purchase(Upgrade upgrade, double discount)
{
    // Adapter must additionally validate depot proximity and the offered subset.
    if (!run.active || (run.phase != Phase::Station && !(IsFlying() && run.depotSeen)))
        return false;
    const int price = UpgradePrice(upgrade, discount);
    if (price < 0 || run.credits < price)
        return false;
    run.credits -= price;
    ++run.tiers[static_cast<std::size_t>(upgrade)];
    // Buying capacity never secretly repairs damage or replenishes shield.
    return true;
}

bool Session::Repair()
{
    if (!run.active || run.phase != Phase::Station || run.credits < tuning.repairPrice)
        return false;
    const EffectiveStats stats = Stats();
    if (run.hull >= stats.maxHull && run.shield >= stats.maxShield && run.criticalSeconds <= 0.0 &&
        run.interferenceSeconds <= 0.0 && run.thermalSeconds <= 0.0)
        return false;
    run.credits -= tuning.repairPrice;
    run.criticalSeconds = run.interferenceSeconds = run.thermalSeconds = run.gravitySeconds = 0.0;
    run.hull = Stats().maxHull;
    run.shield = Stats().maxShield;
    run.brakeHeat = 0.0;
    run.brakeOverheated = false;
    return true;
}

int Session::DepotShieldRepairPrice() const
{
    // Shield-only depot service costs 60% of station full service, rounded up.
    // Bound integer tuning before multiplication; even invalid zero/negative tuning
    // cannot turn the moving depot into a free shield source.
    return (std::clamp(tuning.repairPrice, 1, MaxCounter) * 3 + 4) / 5;
}

bool Session::RepairShieldAtDepot()
{
    // The adapter must also authorize the current depot and live proximity.
    if (!IsFlying() || !run.depotSeen)
        return false;
    const double capacity = Stats().maxShield;
    const int price = DepotShieldRepairPrice();
    if (!Finite(capacity, 0.0, 1000000.0) || capacity <= 0.0 || !Finite(run.shield, 0.0, capacity) ||
        run.shield >= capacity || run.credits < price)
        return false;
    run.credits -= price;
    run.shield = capacity;
    return true;
}

bool Session::CanPurchaseUtility(Utility utility) const
{
    return run.active && run.phase == Phase::Station &&
           (utility == Utility::VectorThrusters || utility == Utility::OverdriveCooling) && utility != run.utility &&
           run.credits >= StationUtilityPrice;
}

bool Session::PurchaseUtility(Utility utility)
{
    // Recheck current state at commit; a vendor row may predate another purchase or departure.
    if (!CanPurchaseUtility(utility))
        return false;
    run.credits -= StationUtilityPrice;
    run.utility = utility;
    return true;
}

bool Session::EquipUtility(Utility utility)
{
    if (!run.active || !EnumIn(utility, 2))
        return false;
    run.utility = utility;
    return true;
}

bool Session::ReplaceWeapon(Weapon weapon)
{
    if (!run.active || !EnumIn(weapon, 1))
        return false;
    run.weapon = weapon; // A run reward may offer the otherwise locked starting weapon.
    return true;
}

bool Session::AcceptContract(Contract contract)
{
    if (!run.active || run.phase != Phase::Station || run.wave != 5 || run.contract != Contract::None ||
        !EnumIn(contract, 2) || contract == Contract::None)
        return false;
    run.contract = contract;
    run.contractProgress = 0;
    run.contractTarget = contract == Contract::Objective ? std::max(1, tuning.objectiveTarget) : 5;
    run.contractAcceptedWave = run.wave;
    run.contractResolved = false;
    run.shield = std::min(run.shield, Stats().maxShield);
    return true;
}

void Session::RecordKill()
{
    if (!IsFlying())
        return;
    run.kills = SaturatingAdd(run.kills, 1);
    if (run.contract == Contract::Objective)
        run.contractProgress = SaturatingAdd(run.contractProgress, 1);
    AwardCredits(std::max(0, tuning.killCredits));
}

void Session::AwardCredits(int amount)
{
    if (!run.active || amount <= 0 || amount > MaxCounter)
        return;
    run.credits = SaturatingAdd(run.credits, amount);
    run.totalCreditsEarned = SaturatingAdd(run.totalCreditsEarned, amount);
}

void Session::FinishWave()
{
    if (!run.active || (run.phase != Phase::Flight && run.phase != Phase::Climax))
        return;
    if (run.wave == 5 && run.phase == Phase::Flight)
    {
        run.phase = Phase::Wormhole;
        run.phaseSeconds = 0.0;
        run.phaseDuration = std::max(1.0, tuning.wormholeSeconds);
        return;
    }
    if (run.wavesCompleted >= run.wave)
        return;
    run.wavesCompleted = run.wave;
    AwardCredits(std::max(0, tuning.waveCredits) + 5 * (run.wave - 1));
    if (run.contract == Contract::Pressure && run.wave > run.contractAcceptedWave)
        ++run.contractProgress;
    run.phaseSeconds = 0.0;
    if (run.wave % 5 == 0)
    {
        run.phase = Phase::Approach;
        run.phaseDuration = 0.0;
    }
    else
    {
        run.phase = Phase::Breathing;
        const double low = std::clamp(tuning.breathSecondsMin, 0.0, 20.0);
        const double high = std::clamp(tuning.breathSecondsMax, low, 20.0);
        run.phaseDuration = RandomRange(low, high);
    }
}

bool Session::BeginDocking()
{
    if (!run.active || run.phase != Phase::Approach)
        return false;
    run.phase = Phase::Docking;
    run.phaseSeconds = 0.0;
    run.phaseDuration = std::max(0.1, tuning.dockingSeconds);
    run.boosting = run.braking = false;
    return true;
}

bool Session::CompleteDocking()
{
    if (!run.active || run.phase != Phase::Docking)
        return false;
    run.phase = Phase::Station;
    run.phaseSeconds = run.phaseDuration = 0.0;
    run.stationRewardClaimed = false;
    ResolveContract();
    return true;
}

void Session::ResolveContract()
{
    if (run.contract == Contract::None || run.contractResolved || run.wave <= run.contractAcceptedWave)
        return;
    if (run.contractProgress >= run.contractTarget)
    {
        AwardCredits(std::max(0, tuning.contractReward));
        ++run.contractsCompleted;
    }
    // Standard failure loses only the disclosed reward. Reduced shields are a
    // temporary handicap and restoring capacity never grants free shield energy.
    run.contract = Contract::None;
    run.contractProgress = run.contractTarget = run.contractAcceptedWave = 0;
    run.contractResolved = true;
}

bool Session::LaunchFromStation()
{
    if (!run.active || run.phase != Phase::Station || run.wave >= 10)
        return false;
    ++run.wave;
    run.boost = 100.0;
    run.brakeHeat = 0.0;
    run.brakeOverheated = false;
    BeginWave();
    return true;
}

int Session::Score() const
{
    const std::int64_t score = run.wavesCompleted * 500LL + run.kills * 75LL + run.totalCreditsEarned +
                               run.eventsCompleted * 200LL + run.contractsCompleted * 300LL;
    return static_cast<int>(std::min<std::int64_t>(MaxCounter, score));
}

int Session::XPReward() const
{
    const std::int64_t reward = run.wavesCompleted * 30LL + std::max(0, run.wave - 1) * 5LL + run.kills * 3LL +
                                run.eventsCompleted * 20LL + run.contractsCompleted * 25LL;
    return static_cast<int>(std::min<std::int64_t>(MaxCounter, reward));
}

void Session::EndRun()
{
    if (!run.active || run.xpAwarded)
        return;
    run.active = false;
    run.phase = Phase::Dead;
    run.hull = 0.0;
    run.boosting = run.braking = false;
    if (!HasAwardedRun(account, run.id))
    {
        account.lastScore = Score();
        account.lastXP = XPReward();
        account.lastWave = run.wave;
        account.xp = std::min<std::int64_t>(1000000000000LL, account.xp + account.lastXP);
        account.level = LevelForXP(account.xp);
        account.highestWave = std::max(account.highestWave, run.wave);
        account.bestScore = std::max(account.bestScore, account.lastScore);
        account.runs = SaturatingAdd(account.runs, 1);
        account.lastAwardedRunId = run.id;
        account.history.insert(account.history.begin(),
                               RunHistoryEntry{run.id, run.wave, account.lastScore, account.lastXP, run.kills,
                                               run.totalCreditsEarned, run.ship, run.weapon});
        if (account.history.size() > MaxRunHistory)
            account.history.resize(MaxRunHistory);
    }
    run.xpAwarded = true;
}

std::string EncodeAccount(const Account &a)
{
    auto out = Writer("ACCOUNT", 2);
    out << a.xp << ' ' << a.level << ' ' << a.highestWave << ' ' << a.runs << ' ' << a.bestScore << ' ' << a.lastScore
        << ' ' << a.lastXP << ' ' << a.lastWave << ' ' << std::quoted(a.lastAwardedRunId) << ' ' << a.tutorialFlags
        << ' ' << a.history.size();
    for (const auto &entry : a.history)
        out << ' ' << std::quoted(entry.id) << ' ' << entry.wave << ' ' << entry.score << ' ' << entry.xp << ' '
            << entry.kills << ' ' << entry.credits << ' ' << static_cast<int>(entry.ship) << ' '
            << static_cast<int>(entry.weapon);
    return out.str();
}

bool DecodeAccount(const std::string &text, Account &output, std::string &error)
{
    error.clear();
    if (text.size() > 4096)
    {
        error = "Account payload too large";
        return false;
    }
    std::istringstream in(text);
    in.imbue(std::locale::classic());
    int version = 0;
    if (!Header(in, "ACCOUNT", error, 2, &version))
        return false;
    Account a;
    std::int64_t tutorialFlags = 0;
    in >> a.xp >> a.level >> a.highestWave >> a.runs >> a.bestScore >> a.lastScore >> a.lastXP >> a.lastWave >>
        std::quoted(a.lastAwardedRunId) >> tutorialFlags;
    if (version == 2)
    {
        int count = 0;
        if (!(in >> count) || count < 0 || count > static_cast<int>(MaxRunHistory))
        {
            error = "Invalid run history count";
            return false;
        }
        a.history.reserve(static_cast<std::size_t>(count));
        for (int index = 0; index < count; ++index)
        {
            RunHistoryEntry entry;
            int ship = 0, weapon = 0;
            if (!(in >> std::quoted(entry.id) >> entry.wave >> entry.score >> entry.xp >> entry.kills >>
                  entry.credits >> ship >> weapon))
            {
                error = "Truncated or invalid run history entry";
                return false;
            }
            entry.ship = static_cast<Ship>(ship);
            entry.weapon = static_cast<Weapon>(weapon);
            a.history.push_back(entry);
        }
    }
    if (!FinishRead(in, error))
        return false;
    if (a.xp < 0 || a.xp > 1000000000000LL || a.level != LevelForXP(a.xp) || a.highestWave < 0 || a.highestWave > 10 ||
        a.lastWave < 0 || a.lastWave > a.highestWave || a.runs < 0 || a.runs > MaxCounter || a.bestScore < 0 ||
        a.bestScore > MaxCounter || a.lastScore < 0 || a.lastScore > a.bestScore || a.lastXP < 0 ||
        a.lastXP > MaxCounter || !ValidId(a.lastAwardedRunId, true) || (a.runs > 0 && a.lastAwardedRunId.empty()) ||
        tutorialFlags < 0 || tutorialFlags > 4294967295LL)
    {
        error = "Account values violate invariants";
        return false;
    }
    a.tutorialFlags = static_cast<std::uint32_t>(tutorialFlags);
    if (a.history.size() > static_cast<std::size_t>(a.runs))
    {
        error = "Run history exceeds account run count";
        return false;
    }
    std::int64_t historyXP = 0;
    for (std::size_t index = 0; index < a.history.size(); ++index)
    {
        const auto &entry = a.history[index];
        if (!ValidId(entry.id) || entry.wave < 1 || entry.wave > a.highestWave || entry.score < 0 ||
            entry.score > a.bestScore || entry.xp < 0 || entry.xp > MaxCounter || entry.kills < 0 ||
            entry.kills > MaxCounter || entry.credits < 0 || entry.credits > MaxCounter || !EnumIn(entry.ship, 1) ||
            !EnumIn(entry.weapon, 1))
        {
            error = "Run history entry violates invariants";
            return false;
        }
        for (std::size_t previous = 0; previous < index; ++previous)
            if (a.history[previous].id == entry.id)
            {
                error = "Duplicate run history ID";
                return false;
            }
        historyXP += entry.xp;
    }
    if (historyXP > a.xp)
    {
        error = "Run history XP exceeds account XP";
        return false;
    }
    if (!a.history.empty())
    {
        const auto &latest = a.history.front();
        if (latest.id != a.lastAwardedRunId || latest.wave != a.lastWave || latest.score != a.lastScore ||
            latest.xp != a.lastXP)
        {
            error = "Latest run history differs from account summary";
            return false;
        }
    }
    // v1 cannot reconstruct ship, weapon, kills or earned credits. Preserve its
    // exact progression/summary with empty history; the next death appends v2 data.
    output = a;
    return true;
}

std::string EncodeRun(const Run &r)
{
    auto out = Writer("RUN");
    out << std::quoted(r.id) << ' ' << r.active << ' ' << r.xpAwarded << ' ' << r.wave << ' '
        << static_cast<int>(r.phase) << ' ' << static_cast<int>(r.ship) << ' ' << static_cast<int>(r.weapon) << ' '
        << static_cast<int>(r.utility) << ' ';
    for (int tier : r.tiers)
        out << tier << ' ';
    out << r.hull << ' ' << r.shield << ' ' << r.credits << ' ' << r.totalCreditsEarned << ' ' << r.kills << ' '
        << r.wavesCompleted << ' ' << r.eventsCompleted << ' ' << r.contractsCompleted << ' ' << r.salvageCollected
        << ' ' << r.phaseSeconds << ' ' << r.phaseDuration << ' ' << r.elapsedSeconds << ' ' << r.damageAge << ' '
        << r.boost << ' ' << r.brakeHeat << ' ' << r.dodgeCooldown << ' ' << r.interferenceSeconds << ' '
        << r.thermalSeconds << ' ' << r.gravitySeconds << ' ' << r.criticalSeconds << ' ' << r.damageFeedback << ' '
        << r.weaponBuffSeconds << ' ' << static_cast<int>(r.impairedSystem) << ' ' << r.brakeOverheated << ' '
        << r.boosting << ' ' << r.braking << ' ' << r.depotSeen << ' ' << r.salvageEventSeen << ' '
        << r.distressEventSeen << ' ' << r.salvageEventAccepted << ' ' << r.distressEventAccepted << ' '
        << r.pendingReward << ' ' << r.rewardCombat << ' ' << r.stationRewardClaimed << ' '
        << static_cast<int>(r.contract) << ' ' << r.contractProgress << ' ' << r.contractTarget << ' '
        << r.contractAcceptedWave << ' ' << r.contractResolved << ' ' << r.rng;
    return out.str();
}

bool DecodeRun(const std::string &text, Run &output, std::string &error)
{
    error.clear();
    if (text.size() > 8192)
    {
        error = "Run payload too large";
        return false;
    }
    std::istringstream in(text);
    in.imbue(std::locale::classic());
    if (!Header(in, "RUN", error))
        return false;
    Run r;
    int phase = 0, ship = 0, weapon = 0, utility = 0, impaired = 0, contract = 0;
    std::int64_t rng = 0;
    in >> std::quoted(r.id) >> r.active >> r.xpAwarded >> r.wave >> phase >> ship >> weapon >> utility;
    for (int &tier : r.tiers)
        in >> tier;
    in >> r.hull >> r.shield >> r.credits >> r.totalCreditsEarned >> r.kills >> r.wavesCompleted >> r.eventsCompleted >>
        r.contractsCompleted >> r.salvageCollected >> r.phaseSeconds >> r.phaseDuration >> r.elapsedSeconds >>
        r.damageAge >> r.boost >> r.brakeHeat >> r.dodgeCooldown >> r.interferenceSeconds >> r.thermalSeconds >>
        r.gravitySeconds >> r.criticalSeconds >> r.damageFeedback >> r.weaponBuffSeconds >> impaired >>
        r.brakeOverheated >> r.boosting >> r.braking >> r.depotSeen >> r.salvageEventSeen >> r.distressEventSeen >>
        r.salvageEventAccepted >> r.distressEventAccepted >> r.pendingReward >> r.rewardCombat >>
        r.stationRewardClaimed >> contract >> r.contractProgress >> r.contractTarget >> r.contractAcceptedWave >>
        r.contractResolved >> rng;
    if (!FinishRead(in, error))
        return false;
    r.phase = static_cast<Phase>(phase);
    r.ship = static_cast<Ship>(ship);
    r.weapon = static_cast<Weapon>(weapon);
    r.utility = static_cast<Utility>(utility);
    r.impairedSystem = static_cast<Upgrade>(impaired);
    r.contract = static_cast<Contract>(contract);
    if (rng < 1 || rng > 4294967295LL)
    {
        error = "Run RNG outside supported range";
        return false;
    }
    r.rng = static_cast<std::uint32_t>(rng);
    if (!ValidateRun(r))
    {
        error = "Run values violate invariants";
        return false;
    }
    output = r;
    return true;
}

std::string EncodeSettings(const Settings &s)
{
    auto out = Writer("SETTINGS");
    out << s.masterVolume << ' ' << s.musicVolume << ' ' << s.effectsVolume << ' ' << s.mouseSensitivity << ' '
        << s.controllerSensitivity << ' ' << s.uiScale << ' ' << s.subtitles << ' ' << s.cameraShake << ' '
        << s.motionBlur << ' ' << s.invertPitch << ' ' << s.toggleBoost << ' ' << s.toggleBrake << ' ' << s.quality
        << ' ' << s.frameLimit;
    return out.str();
}

bool DecodeSettings(const std::string &text, Settings &output, std::string &error)
{
    error.clear();
    if (text.size() > 4096)
    {
        error = "Settings payload too large";
        return false;
    }
    std::istringstream in(text);
    in.imbue(std::locale::classic());
    if (!Header(in, "SETTINGS", error))
        return false;
    Settings s;
    in >> s.masterVolume >> s.musicVolume >> s.effectsVolume >> s.mouseSensitivity >> s.controllerSensitivity >>
        s.uiScale >> s.subtitles >> s.cameraShake >> s.motionBlur >> s.invertPitch >> s.toggleBoost >> s.toggleBrake >>
        s.quality >> s.frameLimit;
    if (!FinishRead(in, error))
        return false;
    if (!Finite(s.masterVolume, 0.0, 1.0) || !Finite(s.musicVolume, 0.0, 1.0) || !Finite(s.effectsVolume, 0.0, 1.0) ||
        !Finite(s.mouseSensitivity, 0.1, 5.0) || !Finite(s.controllerSensitivity, 0.1, 5.0) ||
        !Finite(s.uiScale, 0.75, 2.0) || s.quality < 0 || s.quality > 4 || s.frameLimit < 0 || s.frameLimit > 360)
    {
        error = "Settings values violate invariants";
        return false;
    }
    output = s;
    return true;
}
} // namespace SS
