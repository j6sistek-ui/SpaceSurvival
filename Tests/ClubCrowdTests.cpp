#include "ClubCrowd.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
#include <vector>

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

using namespace SS::Club;

double Gap(double a, double b)
{
    const double gap = std::fabs(a - b);
    return std::min(gap, 1.0 - gap);
}

/** The plan's Normal night: 24 patrons, two skeletons, three dance styles, spots for every zone with spare room. */
Director NormalNight(std::uint32_t seed, int patrons = 24)
{
    Director director(seed);
    auto clip = [&](const std::string &id, Category category, Posture posture, double seconds, bool loop = true,
                    int style = 0, const std::string &skeleton = std::string(), bool mirror = false)
    {
        Clip c;
        c.id = id;
        c.category = category;
        c.posture = posture;
        c.seconds = seconds;
        c.loop = loop;
        c.style = style;
        c.skeleton = skeleton;
        c.mirrorSafe = mirror;
        if (category == Category::Bar)
            c.prop = Prop::Glass;
        director.AddClip(c);
    };
    for (int style = 1; style <= 3; ++style)
        for (int n = 0; n < 4; ++n)
            clip("dance_s" + std::to_string(style) + "_" + std::to_string(n), Category::Dancing, Posture::Standing,
                 8.0 + n * 3.0, true, style, std::string(), n % 2 == 0);
    clip("dance_alien_sway", Category::Dancing, Posture::Standing, 12.0, true, 0, "alien");
    for (int n = 0; n < 6; ++n)
        clip("bar_stand_" + std::to_string(n), Category::Bar, Posture::Standing, 10.0 + n);
    clip("bar_toast", Category::Bar, Posture::Standing, 4.0, false);
    clip("bar_pay", Category::Bar, Posture::Standing, 3.0, false);
    for (int n = 0; n < 6; ++n)
        clip("bar_stool_" + std::to_string(n), Category::Bar, Posture::Seated, 9.0 + n);
    for (int n = 0; n < 8; ++n)
        clip("lounge_" + std::to_string(n), Category::Lounge, Posture::Seated, 12.0 + n);
    for (int n = 0; n < 6; ++n)
        clip("social_" + std::to_string(n), Category::Social, Posture::Standing, 8.0 + n);
    clip("social_laugh", Category::Social, Posture::Standing, 3.5, false);
    clip("social_point", Category::Social, Posture::Standing, 2.5, false);
    clip("walk", Category::Moving, Posture::Standing, 1.1);
    clip("walk_drink", Category::Moving, Posture::Standing, 1.2);
    clip("walk_phone", Category::Moving, Posture::Standing, 1.3);
    clip("asleep_table", Category::Special, Posture::Seated, 20.0);
    clip("drunk_slump", Category::Special, Posture::Seated, 16.0);
    clip("head_on_arms", Category::Special, Posture::Seated, 18.0);

    auto spot = [&](Category category, Posture posture, double x, double y, int capacity = 1)
    {
        Spot s;
        s.category = category;
        s.posture = posture;
        s.position = {x, y, 0.0};
        s.capacity = capacity;
        director.AddSpot(s);
    };
    for (int row = 0; row < 3; ++row)
        for (int column = 0; column < 4; ++column)
            spot(Category::Dancing, Posture::Standing, column * 160.0, row * 160.0);
    for (int n = 0; n < 6; ++n)
        spot(Category::Bar, Posture::Seated, 1200.0, n * 70.0);
    for (int n = 0; n < 3; ++n)
        spot(Category::Bar, Posture::Standing, 1280.0, 500.0 + n * 80.0);
    for (int n = 0; n < 10; ++n)
        spot(Category::Lounge, Posture::Seated, -900.0 + (n % 5) * 90.0, 900.0 + (n / 5) * 300.0);
    for (int n = 0; n < 3; ++n)
        spot(Category::Social, Posture::Standing, 400.0 + n * 400.0, 1300.0, 3);
    spot(Category::Special, Posture::Seated, -1500.0, 0.0);
    spot(Category::Special, Posture::Seated, -1500.0, 300.0);

    for (int n = 0; n < patrons; ++n)
        director.AddPatron(n % 4 == 3 ? "alien" : "human", 1 + n % 3, {600.0, -800.0, 0.0});
    return director;
}

struct Night
{
    std::vector<Play> log;
    std::vector<std::array<int, CategoryCount>> samples;
};

Night Run(Director &director, double seconds, double step = .1)
{
    Night night;
    const Vec3 viewer{300.0, 200.0, 0.0};
    const auto &settings = director.Config();
    std::vector<int> previousSpot(director.Patrons().size(), -1);
    for (double now = 0.0; now <= seconds; now += step)
    {
        const std::vector<Play> plays = director.Update(now, viewer);
        for (const Play &play : plays)
        {
            const Patron &patron = director.Patrons()[play.patron];
            const Clip &clip = director.Clips()[play.clip];
            // Compatibility: skeleton, posture, dance style.
            CHECK(clip.skeleton.empty() || clip.skeleton == patron.skeleton);
            if (play.travelling)
                CHECK(clip.category == Category::Moving);
            else
            {
                CHECK(clip.posture == director.Spots()[play.spot].posture);
                CHECK(clip.category == director.Spots()[play.spot].category);
            }
            if (clip.category == Category::Dancing)
                CHECK(clip.style == 0 || clip.style == patron.style);
            // No neighbour shares this clip in a near-identical phase.
            for (const Patron &other : director.Patrons())
            {
                if (other.id == patron.id || other.clip != play.clip)
                    continue;
                if (Distance(other.position, patron.position) >= settings.syncRadius)
                    continue;
                if (clip.loop)
                    CHECK(Gap(director.Phase(other, now), play.startFraction) >= settings.minPhaseGap - 1e-9);
                else
                    CHECK(director.Phase(other, now) >= settings.minPhaseGap - 1e-9);
            }
            CHECK(play.playRate >= settings.playRate.min - 1e-9 && play.playRate <= settings.playRate.max + 1e-9);
            CHECK(play.startFraction >= 0.0 && play.startFraction < 1.0);
            CHECK(!play.mirrored || clip.mirrorSafe);
            night.log.push_back(play);
        }
        // Spot capacity is never exceeded and occupancy matches the patrons holding each spot.
        std::vector<int> held(director.Spots().size(), 0);
        for (const Patron &patron : director.Patrons())
            if (patron.spot >= 0)
                ++held[patron.spot];
        for (const Spot &spot : director.Spots())
        {
            CHECK(held[spot.id] == director.Occupancy(spot.id));
            CHECK(held[spot.id] <= spot.capacity);
        }
        if (std::fmod(now + 1e-6, 10.0) < step)
            night.samples.push_back(director.CategoryCounts());
    }
    return night;
}

void NoRepeatsAndNoClones()
{
    Director director = NormalNight(20261120u);
    const Night night = Run(director, 1800.0);
    CHECK(night.log.size() > 24 * 20);

    std::map<int, std::vector<int>> history;
    int changesOfActivity = 0;
    for (const Play &play : night.log)
    {
        std::vector<int> &seen = history[play.patron];
        // Never the same clip twice in a row, nor the one before that.
        if (!seen.empty())
            CHECK(seen.back() != play.clip);
        if (seen.size() >= 2)
            CHECK(seen[seen.size() - 2] != play.clip);
        changesOfActivity += play.travelling ? 1 : 0;
        seen.push_back(play.clip);
    }
    // People actually move between zones over a 30-minute night.
    CHECK(changesOfActivity >= 24 * 5);
    // Every patron took part.
    CHECK(history.size() == 24u);
}

void ManyNightsKeepTheRules()
{
    // The per-play checks inside Run hold across many different nights, not one lucky seed.
    for (std::uint32_t night = 1; night <= 24; ++night)
    {
        Director director = NormalNight(night * 7919u);
        Run(director, 1800.0);
    }
}

void MixStaysInRange()
{
    Director director = NormalNight(7u);
    const Night night = Run(director, 1800.0);
    const auto &share = director.Config().share;
    const int total = static_cast<int>(director.Patrons().size());
    std::array<double, CategoryCount> mean{};
    int counted = 0;
    for (std::size_t sample = 6; sample < night.samples.size(); ++sample) // skip the first minute
    {
        const auto &counts = night.samples[sample];
        int settled = 0;
        for (int c = 0; c < CategoryCount; ++c)
            settled += counts[c];
        CHECK(settled == total);
        for (int c = 0; c < CategoryCount; ++c)
        {
            // Never above the cap, even counting patrons who are walking there.
            if (static_cast<Category>(c) != Category::Moving)
                CHECK(counts[c] <= static_cast<int>(std::ceil(share[c].max * total)));
            mean[c] += counts[c];
        }
        ++counted;
    }
    for (int c = 0; c < CategoryCount; ++c)
        mean[c] /= counted * static_cast<double>(total);
    // Averages over the night land inside the plan's ranges (walkers count toward Moving, so allow a margin below).
    for (Category c : {Category::Dancing, Category::Bar, Category::Lounge, Category::Social})
    {
        const Range &range = share[static_cast<int>(c)];
        if (mean[static_cast<int>(c)] < range.min - .06 || mean[static_cast<int>(c)] > range.max + .01)
            std::cerr << CategoryName(c) << " mean share " << mean[static_cast<int>(c)] << '\n';
        CHECK(mean[static_cast<int>(c)] >= range.min - .06);
        CHECK(mean[static_cast<int>(c)] <= range.max + .01);
    }
    CHECK(mean[static_cast<int>(Category::Moving)] > 0.0 && mean[static_cast<int>(Category::Moving)] <= .12);
}

void SeedReplaysExactly()
{
    Director first = NormalNight(99u), second = NormalNight(99u), other = NormalNight(100u);
    const Night a = Run(first, 600.0), b = Run(second, 600.0), c = Run(other, 600.0);
    CHECK(first.Seed() == 99u);
    CHECK(a.log.size() == b.log.size());
    bool identical = true;
    for (std::size_t i = 0; i < a.log.size() && i < b.log.size(); ++i)
        identical &= a.log[i].clip == b.log[i].clip && a.log[i].patron == b.log[i].patron &&
                     a.log[i].startFraction == b.log[i].startFraction && a.log[i].playRate == b.log[i].playRate;
    CHECK(identical);
    bool differs = a.log.size() != c.log.size();
    for (std::size_t i = 0; !differs && i < a.log.size(); ++i)
        differs = a.log[i].clip != c.log[i].clip || a.log[i].startFraction != c.log[i].startFraction;
    CHECK(differs);
}

void TiersFollowTheViewer()
{
    Director director = NormalNight(3u);
    director.Update(0.0, {0.0, 0.0, 0.0});
    const auto &patrons = director.Patrons();
    int heroes = 0;
    double furthestHero = 0.0, nearestOther = 1e18;
    for (const Patron &patron : patrons)
    {
        const double distance = Distance(patron.position, {0.0, 0.0, 0.0});
        if (patron.tier == Tier::Hero)
        {
            ++heroes;
            furthestHero = std::max(furthestHero, distance);
            CHECK(distance <= director.Config().nearRadius);
        }
        else
        {
            nearestOther = std::min(nearestOther, distance);
            if (distance > director.Config().midRadius)
                CHECK(patron.tier == Tier::Far);
        }
    }
    CHECK(heroes == director.Config().heroCount);
    CHECK(furthestHero <= nearestOther + 1e-9);
}

void OneShotsAndSmallPools()
{
    // One clip only: repeats are allowed rather than freezing the patron.
    Director tiny(1u);
    Clip loop;
    loop.id = "only";
    loop.category = Category::Lounge;
    loop.posture = Posture::Seated;
    loop.seconds = 5.0;
    tiny.AddClip(loop);
    Spot seat;
    seat.category = Category::Lounge;
    seat.posture = Posture::Seated;
    tiny.AddSpot(seat);
    tiny.AddPatron("human", 0, {});
    int plays = 0;
    for (double now = 0.0; now < 200.0; now += .5)
        plays += static_cast<int>(tiny.Update(now, {}).size());
    CHECK(plays >= 4);

    // A skeleton with no clips gets no spot and no plays; nothing crashes.
    Director empty(2u);
    Clip alienOnly = loop;
    alienOnly.skeleton = "alien";
    empty.AddClip(alienOnly);
    empty.AddSpot(seat);
    empty.AddPatron("human", 0, {});
    CHECK(empty.Update(0.0, {}).empty());
    CHECK(empty.Patrons()[0].spot == -1);
    CHECK(empty.Occupancy(0) == 0);

    // A one-shot ends after its own length at the chosen speed.
    Director single(5u);
    Clip shot = loop;
    shot.loop = false;
    shot.seconds = 4.0;
    single.AddClip(shot);
    single.AddSpot(seat);
    single.AddPatron("human", 0, {});
    const std::vector<Play> first = single.Update(10.0, {});
    CHECK(first.size() == 1u);
    const Patron &patron = single.Patrons()[0];
    CHECK(std::fabs(patron.clipEnds - (10.0 + 4.0 / patron.playRate)) < 1e-9);
    CHECK(single.Phase(patron, 10.0 + 40.0) == 1.0);
}
} // namespace

int main()
{
    NoRepeatsAndNoClones();
    ManyNightsKeepTheRules();
    MixStaysInRange();
    SeedReplaysExactly();
    TiersFollowTheViewer();
    OneShotsAndSmallPools();
    std::cout << "PASS " << Checks << " club crowd checks\n";
    return 0;
}
