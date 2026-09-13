#include "SurvivalCore.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <string>

namespace
{
int Checks = 0;
void Check(bool value, const char *expression, int line)
{
    ++Checks;
    if (!value)
    {
        std::cerr << "FAIL line " << line << ": " << expression << '\n';
        std::exit(1);
    }
}
#define CHECK(expression) Check((expression), #expression, __LINE__)
bool Near(double a, double b, double epsilon = 0.00001)
{
    return std::abs(a - b) <= epsilon;
}

std::string LegacyAccount(const SS::Account &a)
{
    std::ostringstream out;
    out << "SS ACCOUNT 1 " << a.xp << ' ' << a.level << ' ' << a.highestWave << ' ' << a.runs << ' ' << a.bestScore
        << ' ' << a.lastScore << ' ' << a.lastXP << ' ' << a.lastWave << ' ' << std::quoted(a.lastAwardedRunId) << ' '
        << a.tutorialFlags;
    return out.str();
}

SS::Session Fresh(const std::string &id = "test-run")
{
    SS::Session s;
    CHECK(s.StartRun(id));
    return s;
}

void FastTuning(SS::Session &s)
{
    s.tuning.waveSecondsMin = s.tuning.waveSecondsMax = 1.0;
    s.tuning.waveSecondsGrowth = 0.0;
    s.tuning.breathSecondsMin = s.tuning.breathSecondsMax = 0.5;
    s.tuning.wormholeSeconds = s.tuning.climaxSeconds = 1.0;
    s.tuning.dockingSeconds = 0.2;
    s.run.phaseDuration = 1.0;
}

void ReachStation(SS::Session &s, int target)
{
    int guard = 0;
    while (!(s.run.phase == SS::Phase::Station && s.run.wave == target) && guard++ < 1000)
    {
        if (s.run.phase == SS::Phase::Approach)
            CHECK(s.BeginDocking());
        else
            s.Tick(0.25, true);
    }
    CHECK(guard < 1000);
    CHECK(s.run.wavesCompleted == target);
}

void DamageAndRegeneration()
{
    auto s = Fresh();
    s.ApplyDamage(30.0);
    CHECK(Near(s.run.shield, 30.0));
    CHECK(Near(s.run.hull, 100.0));
    s.ApplyDamage(50.0);
    CHECK(Near(s.run.shield, 0.0));
    CHECK(Near(s.run.hull, 80.0));
    s.Tick(3.0, false);
    CHECK(Near(s.run.hull, 80.0));
    s.Tick(2.0, true);
    CHECK(s.run.hull > 80.0 && s.run.hull < 81.0);
    const double damaged = s.run.hull;
    s.Tick(1.0, false);
    CHECK(s.run.hull >= damaged + 6.9);
    s.Tick(5.0, false);
    CHECK(Near(s.run.hull, s.Stats().maxHull));
    CHECK(s.run.shield == 0.0);
    CHECK(s.Dodge());
    s.ApplyDamage(15.0); // Dodge must not confer damage immunity.
    CHECK(Near(s.run.hull, 85.0));
    CHECK(!s.Dodge());
    s.Tick(2.0, true);
    CHECK(s.Dodge());
    s.ApplyDamage(-10.0);
    s.ApplyDamage(std::numeric_limits<double>::infinity());
    CHECK(Near(s.run.hull, 85.0));
    auto energy = Fresh("energy");
    energy.ApplyDamage(20.0, SS::DamageType::Energy);
    CHECK(Near(energy.run.shield, 33.0));
    energy.ApplyDamage(40.0, SS::DamageType::Energy);
    CHECK(Near(energy.run.hull, 100.0 - (40.0 - 33.0 / 1.35)));
    energy.ApplyDamage(1.0, SS::DamageType::Electrical);
    CHECK(energy.run.interferenceSeconds > 0.0);
    energy.ApplyDamage(1.0, SS::DamageType::Gravity);
    CHECK(energy.run.gravitySeconds > 0.0);
    energy.ApplyDamage(1.0, SS::DamageType::Thermal);
    const double beforeBurn = energy.run.hull;
    energy.Tick(1.0, true);
    CHECK(energy.run.hull < beforeBurn);
}

void FlightMetersAndUtilities()
{
    auto s = Fresh();
    const auto baseline = s.Stats();
    s.TickFlight(2.0, true, false);
    CHECK(Near(s.run.boost, 44.0));
    CHECK(s.run.boosting);
    s.TickFlight(5.0, true, false);
    CHECK(Near(s.run.boost, 0.0) && !s.run.boosting);
    s.TickFlight(2.0, false, false);
    CHECK(Near(s.run.boost, 32.0));
    s.TickFlight(3.2, false, true);
    CHECK(s.run.brakeOverheated && !s.run.braking);
    CHECK(s.run.brakeHeat > 90.0);
    s.TickFlight(4.0, false, false);
    CHECK(s.run.brakeHeat < 25.0);
    s.TickFlight(0.1, false, true);
    CHECK(!s.run.brakeOverheated && s.run.braking);
    s.run.brakeHeat = 0.0;
    s.run.brakeOverheated = false;
    s.run.boost = 100.0;
    s.TickFlight(0.1, true, true);
    CHECK(s.run.braking && !s.run.boosting && s.run.boost == 100.0);
    CHECK(s.EquipUtility(SS::Utility::VectorThrusters));
    CHECK(s.Stats().maneuver > baseline.maneuver);
    CHECK(s.EquipUtility(SS::Utility::OverdriveCooling));
    CHECK(Near(s.Stats().maneuver, baseline.maneuver)); // Exactly one slot.
    s.run.brakeHeat = 0.0;
    s.TickFlight(2.0, true, false);
    CHECK(s.run.boost > 44.0);
    s.TickFlight(3.2, false, true);
    CHECK(!s.run.brakeOverheated);
    CHECK(s.ReplaceWeapon(SS::Weapon::HeavyCannon));
    CHECK(s.Stats().weaponDamage > baseline.weaponDamage * 4.0);
    CHECK(!s.EquipUtility(static_cast<SS::Utility>(100)));
    auto a = Fresh("frame-step");
    auto b = Fresh("frame-step");
    a.TickFlight(3.0, true, false);
    for (int i = 0; i < 180; ++i)
        b.TickFlight(1.0 / 60.0, true, false);
    CHECK(Near(a.run.boost, b.run.boost));
    a.run.hull = b.run.hull = 50.0;
    a.Tick(3.0, false);
    for (int i = 0; i < 180; ++i)
        b.Tick(1.0 / 60.0, false);
    CHECK(Near(a.run.hull, b.run.hull));
}

void WaveLifecycleAndEconomy()
{
    auto s = Fresh();
    FastTuning(s);
    CHECK(!s.Purchase(SS::Upgrade::Hull));
    for (int wave = 1; wave <= 4; ++wave)
    {
        CHECK(s.run.wave == wave && s.run.phase == SS::Phase::Flight);
        s.Tick(1.0, true);
        CHECK(s.run.phase == SS::Phase::Breathing && s.run.phaseDuration <= 20.0);
        const int credits = s.run.credits;
        s.FinishWave();
        CHECK(s.run.credits == credits);
        s.Tick(0.5, true);
    }
    CHECK(s.run.wave == 5);
    s.Tick(1.0, true);
    CHECK(s.run.phase == SS::Phase::Wormhole);
    s.Tick(1.0, true);
    CHECK(s.run.phase == SS::Phase::Climax);
    s.Tick(1.0, true);
    CHECK(s.run.phase == SS::Phase::Approach);
    CHECK(s.run.wavesCompleted == 5);
    CHECK(s.run.credits == 425); // Three tier-II purchases; repairs remain a choice.
    CHECK(s.BeginDocking());
    s.Tick(0.2, false);
    CHECK(s.run.phase == SS::Phase::Station);
    CHECK(s.Purchase(SS::Upgrade::Hull));
    CHECK(s.Purchase(SS::Upgrade::Shield));
    CHECK(s.Purchase(SS::Upgrade::Engine));
    CHECK(!s.Purchase(SS::Upgrade::Thrusters));
    CHECK(s.run.credits == 35);
    CHECK(s.Stats().maxHull > s.run.hull && s.Stats().maxShield > s.run.shield);
    CHECK(s.Repair());
    CHECK(Near(s.run.hull, s.Stats().maxHull) && Near(s.run.shield, s.Stats().maxShield));
    CHECK(!s.Repair());
    const double firstBlockPressure = s.PressureMultiplier();
    CHECK(s.LaunchFromStation());
    CHECK(s.run.wave == 6);
    ReachStation(s, 10);
    CHECK(s.PressureMultiplier() > firstBlockPressure);
    CHECK(s.AtSliceBoundary());
    const auto xp = s.account.xp;
    CHECK(!s.LaunchFromStation());
    CHECK(s.run.active && s.run.phase == SS::Phase::Station && s.account.xp == xp);
}

void UpgradeTiersAndRepair()
{
    auto s = Fresh();
    FastTuning(s);
    ReachStation(s, 5);
    s.AwardCredits(100000);
    const auto original = s.Stats();
    for (int track = 0; track < 5; ++track)
    {
        for (int tier = 2; tier <= 5; ++tier)
        {
            CHECK(s.Purchase(static_cast<SS::Upgrade>(track)));
            CHECK(s.run.tiers[static_cast<std::size_t>(track)] == tier);
        }
        const int credits = s.run.credits;
        CHECK(!s.Purchase(static_cast<SS::Upgrade>(track)) && s.run.credits == credits);
    }
    const auto upgraded = s.Stats();
    CHECK(upgraded.maxHull > original.maxHull && upgraded.maxShield > original.maxShield);
    CHECK(upgraded.acceleration > original.acceleration && upgraded.speed > original.speed);
    CHECK(upgraded.maneuver > original.maneuver && upgraded.response > original.response);
    CHECK(upgraded.weaponDamage > original.weaponDamage);
    s.run.impairedSystem = SS::Upgrade::Thrusters;
    s.run.criticalSeconds = 10.0;
    CHECK(s.Stats().maneuver < upgraded.maneuver);
    CHECK(s.run.tiers[3] == 5);
    CHECK(s.Repair());
    CHECK(Near(s.Stats().maneuver, upgraded.maneuver));
    CHECK(!s.Purchase(static_cast<SS::Upgrade>(50)));
    CHECK(s.UpgradePrice(SS::Upgrade::Hull, -1.0) == -1);
}

void Contracts()
{
    auto objective = Fresh("objective");
    FastTuning(objective);
    CHECK(!objective.AcceptContract(SS::Contract::Objective));
    ReachStation(objective, 5);
    CHECK(objective.AcceptContract(SS::Contract::Objective));
    CHECK(!objective.AcceptContract(SS::Contract::Pressure));
    CHECK(objective.LaunchFromStation());
    for (int i = 0; i < objective.tuning.objectiveTarget; ++i)
        objective.RecordKill();
    CHECK(objective.run.contractProgress == objective.tuning.objectiveTarget);
    ReachStation(objective, 10);
    CHECK(objective.run.contractsCompleted == 1 && objective.run.contract == SS::Contract::None);
    const int credits = objective.run.credits;
    CHECK(!objective.CompleteDocking());
    CHECK(objective.run.credits == credits);
    CHECK(!objective.AcceptContract(SS::Contract::Objective)); // No unreachable Wave11 objective.

    auto failure = Fresh("failure");
    FastTuning(failure);
    ReachStation(failure, 5);
    CHECK(failure.AcceptContract(SS::Contract::Objective));
    CHECK(failure.LaunchFromStation());
    ReachStation(failure, 10);
    CHECK(failure.run.contractsCompleted == 0);
    CHECK(failure.run.credits == 975); // No reward, no hidden financial penalty.

    auto pressure = Fresh("pressure");
    FastTuning(pressure);
    ReachStation(pressure, 5);
    const double capacity = pressure.Stats().maxShield;
    CHECK(pressure.AcceptContract(SS::Contract::Pressure));
    CHECK(Near(pressure.Stats().maxShield, capacity * 0.65));
    CHECK(pressure.run.shield <= pressure.Stats().maxShield);
    CHECK(pressure.LaunchFromStation());
    ReachStation(pressure, 10);
    CHECK(pressure.run.contractsCompleted == 1);
    CHECK(Near(pressure.Stats().maxShield, capacity));
    CHECK(Near(pressure.run.shield, capacity * 0.65)); // No free shield regeneration.
}

void DeathProgressionReset()
{
    auto s = Fresh("first-life");
    CHECK(!s.StartRun("overlapping-life"));
    FastTuning(s);
    ReachStation(s, 5);
    CHECK(s.LaunchFromStation());
    s.ApplyDamage(10000.0);
    CHECK(!s.run.active && s.run.phase == SS::Phase::Dead && s.run.xpAwarded);
    CHECK(s.account.runs == 1 && s.account.level == 2 && s.account.HeavyCannonUnlocked());
    CHECK(!s.account.AgileShipUnlocked());
    const auto xp = s.account.xp;
    s.EndRun();
    CHECK(s.account.xp == xp && s.account.runs == 1);
    CHECK(!s.StartRun("first-life"));
    CHECK(!s.StartRun("agile-locked", SS::Ship::Agile));
    CHECK(s.StartRun("second-life", SS::Ship::Starter, SS::Weapon::HeavyCannon));
    CHECK(s.run.wave == 1 && s.run.credits == 0 && s.run.contract == SS::Contract::None &&
          s.run.utility == SS::Utility::None);
    for (int tier : s.run.tiers)
        CHECK(tier == 1);
    CHECK(!s.run.depotSeen && !s.run.salvageEventAccepted && !s.run.distressEventAccepted);
    FastTuning(s);
    ReachStation(s, 5);
    CHECK(s.LaunchFromStation());
    ReachStation(s, 10);
    s.EndRun();
    CHECK(s.account.level >= 3 && s.account.AgileShipUnlocked());
    CHECK(s.StartRun("third-life", SS::Ship::Agile, SS::Weapon::HeavyCannon));
    const auto agile = s.Stats();
    s.run.ship = SS::Ship::Starter;
    const auto starter = s.Stats();
    CHECK(agile.maxHull < starter.maxHull && agile.speed > starter.speed && agile.maneuver > starter.maneuver &&
          agile.response > starter.response);
}

void SerializationAndValidation()
{
    auto s = Fresh("roundtrip");
    FastTuning(s);
    ReachStation(s, 5);
    s.run.depotSeen = true;
    s.run.salvageEventSeen = s.run.salvageEventAccepted = true;
    s.run.distressEventSeen = s.run.distressEventAccepted = true;
    s.run.eventsCompleted = 2;
    s.run.pendingReward = true;
    s.run.rewardCombat = true;
    s.run.weaponBuffSeconds = 8.5;
    CHECK(s.EquipUtility(SS::Utility::VectorThrusters));
    CHECK(s.AcceptContract(SS::Contract::Objective));
    SS::Run decoded;
    std::string error;
    const auto payload = SS::EncodeRun(s.run);
    CHECK(SS::DecodeRun(payload, decoded, error));
    CHECK(error.empty() && SS::EncodeRun(decoded) == payload);
    SS::Session resumed;
    resumed.run = decoded;
    resumed.account = s.account;
    CHECK(resumed.run.depotSeen && resumed.run.utility == SS::Utility::VectorThrusters);
    CHECK(resumed.run.pendingReward && resumed.run.rewardCombat);
    CHECK(Near(resumed.run.weaponBuffSeconds, 8.5));
    resumed.Tick(0.5, false);
    CHECK(Near(resumed.run.weaponBuffSeconds, 8.0));
    CHECK(resumed.run.contract == SS::Contract::Objective);
    CHECK(resumed.LaunchFromStation());
    resumed.ApplyDamage(100000.0);
    CHECK(resumed.run.phase == SS::Phase::Dead);
    const auto xpAfterDeath = resumed.account.xp;
    // Domain idempotency complements, but cannot replace, the adapter's durable
    // consume-before-resume transaction. Replayed data must not award XP twice.
    resumed.run = decoded;
    resumed.EndRun();
    CHECK(resumed.account.xp == xpAfterDeath && resumed.account.runs == 1);
    CHECK(!resumed.StartRun(decoded.id));
    SS::Account account;
    const auto accountPayload = SS::EncodeAccount(resumed.account);
    CHECK(SS::DecodeAccount(accountPayload, account, error));
    CHECK(SS::EncodeAccount(account) == accountPayload);
    SS::Settings settings;
    s.settings.uiScale = 1.5;
    s.settings.toggleBoost = true;
    s.settings.cameraShake = false;
    const auto settingsPayload = SS::EncodeSettings(s.settings);
    CHECK(SS::DecodeSettings(settingsPayload, settings, error));
    CHECK(SS::EncodeSettings(settings) == settingsPayload);

    const auto unchanged = SS::EncodeRun(decoded);
    CHECK(!SS::DecodeRun("SS RUN 999", decoded, error));
    CHECK(!SS::DecodeRun(payload + " extra", decoded, error));
    CHECK(!SS::DecodeRun(payload.substr(0, payload.size() / 2), decoded, error));
    CHECK(!SS::DecodeRun(std::string(9000, 'a'), decoded, error));
    CHECK(SS::EncodeRun(decoded) == unchanged); // Failure must be transactional.
    SS::Run bad = s.run;
    bad.hull = -1.0;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.phase = static_cast<SS::Phase>(99);
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.wave = 11;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.tiers[0] = 6;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.id = "path/traversal";
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.rng = 0;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.phase = SS::Phase::Flight;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.phase = SS::Phase::Flight;
    bad.wave = 10;
    bad.wavesCompleted = 9;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.boosting = bad.braking = true;
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    bad = s.run;
    bad.hull = std::numeric_limits<double>::quiet_NaN();
    CHECK(!SS::DecodeRun(SS::EncodeRun(bad), decoded, error));
    SS::Account badAccount = account;
    badAccount.level += 1;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(badAccount), account, error));
    SS::Settings badSettings = settings;
    badSettings.masterVolume = 1.1;
    CHECK(!SS::DecodeSettings(SS::EncodeSettings(badSettings), settings, error));
    badSettings = settings;
    badSettings.frameLimit = -1;
    CHECK(!SS::DecodeSettings(SS::EncodeSettings(badSettings), settings, error));
    auto badRng = payload.substr(0, payload.find_last_of(' ') + 1) + "-1";
    CHECK(!SS::DecodeRun(badRng, decoded, error));
    const auto legacyPayload = LegacyAccount(account);
    auto badTutorial = legacyPayload.substr(0, legacyPayload.find_last_of(' ') + 1) + "-1";
    CHECK(!SS::DecodeAccount(badTutorial, account, error));
}

void PersistentRunHistory()
{
    SS::Session s;
    s.account.xp = 500;
    s.account.level = SS::LevelForXP(s.account.xp);
    for (int index = 1; index <= 12; ++index)
    {
        const std::string id = "history-" + std::to_string(index);
        const SS::Ship ship = index % 2 ? SS::Ship::Agile : SS::Ship::Starter;
        const SS::Weapon weapon = index % 2 ? SS::Weapon::HeavyCannon : SS::Weapon::RapidLaser;
        CHECK(s.StartRun(id, ship, weapon));
        s.run.wave = 1 + index % 10;
        s.run.wavesCompleted = s.run.wave - 1;
        s.AwardCredits(100 + index);
        for (int kills = 0; kills < index % 3; ++kills)
            s.RecordKill();
        s.run.credits -= 50; // Account history reports earned credits, not balance.
        const int expectedXP = s.XPReward(), expectedScore = s.Score();
        const int wave = s.run.wave, kills = s.run.kills, credits = s.run.totalCreditsEarned;
        s.EndRun();
        CHECK(s.account.history.size() == std::min<std::size_t>(static_cast<std::size_t>(index), SS::MaxRunHistory));
        const auto &entry = s.account.history.front();
        CHECK(entry.id == id && entry.wave == wave && entry.score == expectedScore && entry.xp == expectedXP);
        CHECK(entry.kills == kills && entry.credits == credits && entry.ship == ship && entry.weapon == weapon);
        const auto once = SS::EncodeAccount(s.account);
        s.EndRun();
        CHECK(SS::EncodeAccount(s.account) == once);
    }
    CHECK(s.account.history.size() == 10);
    CHECK(s.account.history.front().id == "history-12" && s.account.history.back().id == "history-3");
    CHECK(s.account.runs == 12);
    CHECK(!s.StartRun("history-7"));
    const auto recorded = SS::EncodeAccount(s.account);
    s.run = SS::Run{};
    s.run.id = "history-7";
    s.run.active = true;
    s.run.phase = SS::Phase::Flight;
    s.EndRun(); // Replayed older retained run is also once-only.
    CHECK(SS::EncodeAccount(s.account) == recorded);
    CHECK(s.StartRun("abandoned-run"));
    s.run = SS::Run{}; // The explicit slice-abandonment adapter uses this reset.
    CHECK(SS::EncodeAccount(s.account) == recorded);

    SS::Account restored;
    std::string error;
    CHECK(SS::DecodeAccount(recorded, restored, error));
    CHECK(SS::EncodeAccount(restored) == recorded);
    CHECK(recorded.rfind("SS ACCOUNT 2 ", 0) == 0);
    const auto unchanged = SS::EncodeAccount(restored);
    CHECK(!SS::DecodeAccount(recorded.substr(0, recorded.size() - 2), restored, error));
    CHECK(!SS::DecodeAccount(recorded + " trailing", restored, error));
    CHECK(!SS::DecodeAccount(std::string(4097, 'x'), restored, error));
    CHECK(SS::EncodeAccount(restored) == unchanged);

    auto malformed = s.account;
    malformed.history.push_back(malformed.history.back());
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].id = malformed.history[0].id;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[0].id = "different-last-run";
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].id = "../unsafe";
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].wave = 11;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].score = -1;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].xp = -1;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].kills = 100000001;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].credits = -1;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].ship = static_cast<SS::Ship>(9);
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].weapon = static_cast<SS::Weapon>(-1);
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.history[1].xp = 100000000;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    malformed = s.account;
    malformed.runs = 1;
    CHECK(!SS::DecodeAccount(SS::EncodeAccount(malformed), restored, error));
    CHECK(SS::EncodeAccount(restored) == unchanged);

    // The legacy format did not contain per-run kills/credits/ship/weapon.
    // Migration preserves original values and does not fabricate history records.
    const std::string v1 = "SS ACCOUNT 1 175 2 6 1 3000 3000 175 6 \"legacy-run\" 7";
    SS::Account migrated;
    CHECK(SS::DecodeAccount(v1, migrated, error));
    CHECK(migrated.xp == 175 && migrated.level == 2 && migrated.highestWave == 6 && migrated.runs == 1);
    CHECK(migrated.lastAwardedRunId == "legacy-run" && migrated.lastScore == 3000 && migrated.lastXP == 175 &&
          migrated.lastWave == 6);
    CHECK(migrated.tutorialFlags == 7 && migrated.history.empty() && migrated.HeavyCannonUnlocked());
    const auto v2 = SS::EncodeAccount(migrated);
    CHECK(v2.rfind("SS ACCOUNT 2 ", 0) == 0);
    CHECK(SS::DecodeAccount(v2, restored, error));
    CHECK(SS::EncodeAccount(restored) == v2);
    CHECK(!SS::DecodeAccount("SS ACCOUNT 3 0", restored, error));
    CHECK(!SS::DecodeAccount(v2.substr(0, v2.find_last_of(' ') + 1) + "-1", restored, error));
    CHECK(!SS::DecodeAccount(v2.substr(0, v2.find_last_of(' ') + 1) + "11", restored, error));
    CHECK(!SS::DecodeAccount(v1 + " unexpected", restored, error));
    CHECK(!SS::DecodeAccount(v1.substr(0, v1.size() / 2), restored, error));
    CHECK(SS::EncodeAccount(restored) == v2);
    SS::Session afterMigration;
    afterMigration.account = migrated;
    CHECK(!afterMigration.StartRun("legacy-run"));
    CHECK(afterMigration.StartRun("after-migration"));
    afterMigration.ApplyDamage(1000.0);
    CHECK(afterMigration.account.history.size() == 1 && afterMigration.account.history[0].id == "after-migration");
    CHECK(afterMigration.account.runs == 2 && afterMigration.account.xp == 175);
    CHECK(SS::DecodeAccount(SS::EncodeAccount(afterMigration.account), restored, error));
}

void DeterminismAndDefensiveInputs()
{
    auto a = Fresh("determinism");
    auto b = Fresh("determinism");
    CHECK(a.run.phaseDuration == b.run.phaseDuration);
    a.FinishWave();
    b.FinishWave();
    CHECK(a.run.phaseDuration == b.run.phaseDuration && a.run.rng == b.run.rng);
    a.tuning.breathSecondsMin = 100.0;
    a.tuning.breathSecondsMax = 200.0;
    a.Tick(20.0, false);
    a.FinishWave();
    CHECK(a.run.phaseDuration <= 20.0);
    const auto elapsed = a.run.elapsedSeconds;
    a.Tick(-1.0, false);
    a.Tick(std::numeric_limits<double>::quiet_NaN(), false);
    CHECK(a.run.elapsedSeconds == elapsed);
    const int credits = a.run.credits;
    a.AwardCredits(-50);
    CHECK(a.run.credits == credits);
    SS::Session empty;
    CHECK(!empty.StartRun(""));
    CHECK(!empty.StartRun("bad id"));
    CHECK(!empty.StartRun("locked", SS::Ship::Starter, SS::Weapon::HeavyCannon));
    CHECK(!empty.Repair() && !empty.Dodge());
}
} // namespace

int main()
{
    DamageAndRegeneration();
    FlightMetersAndUtilities();
    WaveLifecycleAndEconomy();
    UpgradeTiersAndRepair();
    Contracts();
    DeathProgressionReset();
    SerializationAndValidation();
    PersistentRunHistory();
    DeterminismAndDefensiveInputs();
    std::cout << "PASS " << Checks
              << " portable gameplay-domain assertions. Unreal integration and gameplay feel are unverified.\n";
    return 0;
}
