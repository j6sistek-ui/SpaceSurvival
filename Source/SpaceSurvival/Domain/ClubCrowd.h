#pragma once

// Engine-independent club crowd rules (docs/production/CLUB_AMBIENCE_PLAN.md). Decides which patron does what,
// where and with which clip; the Unreal director only applies the decisions. No UObject, rendering or time source:
// the caller passes the clock and the viewer position, so a seeded night replays exactly.

#include <array>
#include <cstdint>
#include <random>
#include <string>
#include <vector>

namespace SS
{
namespace Club
{
enum class Category : std::uint8_t
{
    Dancing,
    Bar,
    Lounge,
    Social,
    Moving,
    Special,
    Count
};
constexpr int CategoryCount = static_cast<int>(Category::Count);

enum class Posture : std::uint8_t
{
    Standing,
    Seated
};

enum class Prop : std::uint8_t
{
    None,
    Glass,
    Shot,
    Bottle,
    Tray
};

/** Detail tier by camera distance; the engine layer maps it to update rate, IK, head fill and mesh LOD. */
enum class Tier : std::uint8_t
{
    Hero,
    Near,
    Mid,
    Far
};

struct Vec3
{
    double x = 0.0, y = 0.0, z = 0.0;
};
double Distance(const Vec3 &a, const Vec3 &b);

struct Clip
{
    std::string id;
    Category category = Category::Dancing;
    Posture posture = Posture::Standing;
    Prop prop = Prop::None;
    /** Empty: any skeleton. Otherwise only patrons with the same skeleton id may play it. */
    std::string skeleton;
    /** Dance style (0 = any). A dancer keeps one style so the floor mixes styles instead of cloning one routine. */
    int style = 0;
    double seconds = 1.0;
    double weight = 1.0;
    bool loop = true;
    bool mirrorSafe = false;
};

struct Spot
{
    int id = 0;
    Category category = Category::Dancing;
    Posture posture = Posture::Standing;
    Vec3 position;
    int capacity = 1;
};

struct Range
{
    double min = 0.0, max = 0.0;
};

struct Settings
{
    /** Share of seated-or-standing patrons per category (Moving is a transition and is not targeted). */
    std::array<Range, CategoryCount> share{{{.30, .40}, {.15, .20}, {.20, .25}, {.15, .20}, {0, 1}, {0, .10}}};
    /** Seconds a patron stays in one activity before choosing another. */
    std::array<Range, CategoryCount> activitySeconds{{{45, 150}, {60, 240}, {120, 360}, {60, 180}, {0, 0}, {300, 900}}};
    /** How long one looping clip holds before the next pick inside the same activity. */
    Range loopHoldSeconds{15, 40};
    Range playRate{.9, 1.1};
    /** Two patrons closer than this (cm) never share a clip in a near-identical phase. */
    double syncRadius = 800.0;
    /** Minimum phase separation (fraction of the clip) when neighbours must share a clip. */
    double minPhaseGap = .25;
    /** Clips a patron must not repeat (the last N it played). */
    int noRepeatDepth = 2;
    double walkSpeed = 120.0;
    Range travelSeconds{3, 20};
    int heroCount = 8;
    double nearRadius = 1500.0;
    double midRadius = 3000.0;
};

struct Patron
{
    int id = 0;
    std::string skeleton;
    int style = 0;
    Category category = Category::Moving;
    int spot = -1;
    int clip = -1;
    std::vector<int> recentClips;
    double clipStart = 0.0;
    double startFraction = 0.0;
    double playRate = 1.0;
    bool mirrored = false;
    double clipEnds = 0.0;
    double activityEnds = 0.0;
    /** True while walking to the reserved spot; arrival starts the activity in `pendingCategory`. */
    bool travelling = false;
    Category pendingCategory = Category::Moving;
    Vec3 travelFrom;
    double departs = 0.0;
    double arrives = 0.0;
    Vec3 position;
    Tier tier = Tier::Far;
};

/** One instruction for the engine layer: play this clip on this patron, at this spot. */
struct Play
{
    int patron = 0;
    int clip = 0;
    int spot = -1;
    Category category = Category::Moving;
    double startFraction = 0.0;
    double playRate = 1.0;
    bool mirrored = false;
    bool travelling = false;
    double time = 0.0;
};

class Director
{
public:
    explicit Director(std::uint32_t seed, Settings settings = Settings());

    int AddClip(const Clip &clip);
    int AddSpot(const Spot &spot);
    int AddPatron(const std::string &skeleton, int style, const Vec3 &start);

    /** Advance to `now` (seconds, monotonic). Returns the clips that start this step, in patron order. */
    std::vector<Play> Update(double now, const Vec3 &viewer);

    /** Phase in [0,1) of the patron's current clip at `now`; one-shots clamp at 1. */
    double Phase(const Patron &patron, double now) const;
    int Occupancy(int spot) const;
    std::array<int, CategoryCount> CategoryCounts() const;

    std::uint32_t Seed() const
    {
        return seed;
    }
    const std::vector<Patron> &Patrons() const
    {
        return patrons;
    }
    const std::vector<Clip> &Clips() const
    {
        return clips;
    }
    const std::vector<Spot> &Spots() const
    {
        return spots;
    }
    const Settings &Config() const
    {
        return settings;
    }

private:
    std::uint32_t seed;
    Settings settings;
    std::mt19937 random;
    std::vector<Clip> clips;
    std::vector<Spot> spots;
    std::vector<Patron> patrons;
    std::vector<int> occupancy;

    /** [0,1) from the raw generator: std distributions differ between standard libraries, the engine does not. */
    double Unit();
    double Uniform(const Range &range);
    Category Planned(const Patron &patron) const;
    /** Reserves a spot and returns its index, or -1 when nothing compatible is free. */
    int ChooseActivity(const Patron &patron, Category &category);
    int ChooseClip(const Patron &patron, Category category, Posture posture, double now, double &startFraction);
    Play Start(Patron &patron, Category category, Posture posture, double now);
    void AssignTiers(const Vec3 &viewer);
};

const char *CategoryName(Category category);
} // namespace Club
} // namespace SS
