#include "ClubCrowd.h"

#include <algorithm>
#include <cmath>
#include <numeric>

namespace SS
{
namespace Club
{
namespace
{
constexpr double Epsilon = 1e-9;

Vec3 Lerp(const Vec3 &a, const Vec3 &b, double t)
{
    return {a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t};
}
} // namespace

double Distance(const Vec3 &a, const Vec3 &b)
{
    const double x = a.x - b.x, y = a.y - b.y, z = a.z - b.z;
    return std::sqrt(x * x + y * y + z * z);
}

const char *CategoryName(Category category)
{
    switch (category)
    {
    case Category::Dancing:
        return "Dancing";
    case Category::Bar:
        return "Bar";
    case Category::Lounge:
        return "Lounge";
    case Category::Social:
        return "Social";
    case Category::Moving:
        return "Moving";
    case Category::Special:
        return "Special";
    case Category::Count:
        break;
    }
    return "Unknown";
}

Director::Director(std::uint32_t inSeed, Settings inSettings) : seed(inSeed), settings(inSettings), random(inSeed) {}

int Director::AddClip(const Clip &clip)
{
    Clip copy = clip;
    copy.seconds = std::max(copy.seconds, .05);
    copy.weight = std::max(copy.weight, 0.0);
    clips.push_back(copy);
    return static_cast<int>(clips.size()) - 1;
}

int Director::AddSpot(const Spot &spot)
{
    Spot copy = spot;
    copy.id = static_cast<int>(spots.size());
    copy.capacity = std::max(copy.capacity, 1);
    spots.push_back(copy);
    occupancy.push_back(0);
    return copy.id;
}

int Director::AddPatron(const std::string &skeleton, int style, const Vec3 &start)
{
    Patron patron;
    patron.id = static_cast<int>(patrons.size());
    patron.skeleton = skeleton;
    patron.style = style;
    patron.position = start;
    patron.travelFrom = start;
    patrons.push_back(patron);
    return patron.id;
}

double Director::Unit()
{
    return static_cast<double>(random()) / 4294967296.0;
}

double Director::Uniform(const Range &range)
{
    return range.min + (range.max - range.min) * Unit();
}

Category Director::Planned(const Patron &patron) const
{
    return patron.travelling ? patron.pendingCategory : patron.category;
}

int Director::Occupancy(int spot) const
{
    return spot >= 0 && spot < static_cast<int>(occupancy.size()) ? occupancy[spot] : 0;
}

std::array<int, CategoryCount> Director::CategoryCounts() const
{
    std::array<int, CategoryCount> counts{};
    for (const Patron &patron : patrons)
        if (patron.clip >= 0 || patron.travelling)
            ++counts[static_cast<int>(patron.category)];
    return counts;
}

double Director::Phase(const Patron &patron, double now) const
{
    if (patron.clip < 0)
        return 0.0;
    const Clip &clip = clips[patron.clip];
    const double advanced =
        patron.startFraction + std::max(0.0, now - patron.clipStart) * patron.playRate / clip.seconds;
    return clip.loop ? advanced - std::floor(advanced) : std::min(1.0, advanced);
}

int Director::ChooseActivity(const Patron &patron, Category &category)
{
    const int total = static_cast<int>(patrons.size());
    std::array<int, CategoryCount> planned{};
    for (const Patron &other : patrons)
        if (other.id != patron.id && other.spot >= 0)
            ++planned[static_cast<int>(Planned(other))];

    auto hasClips = [&](Category c, Posture posture)
    {
        return std::any_of(clips.begin(), clips.end(),
                           [&](const Clip &clip)
                           {
                               return clip.category == c && clip.posture == posture && clip.weight > 0.0 &&
                                      (clip.skeleton.empty() || clip.skeleton == patron.skeleton);
                           });
    };
    auto freeSpots = [&](Category c)
    {
        std::vector<int> open;
        for (const Spot &spot : spots)
            if (spot.category == c && spot.id != patron.spot && occupancy[spot.id] < spot.capacity &&
                hasClips(c, spot.posture))
                open.push_back(spot.id);
        return open;
    };

    // Weight each category by how far it sits below the middle of its share; full or capped categories drop out
    // unless nothing else can take the patron.
    std::array<double, CategoryCount> weights{};
    std::array<std::vector<int>, CategoryCount> candidates;
    double sum = 0.0, fallbackSum = 0.0;
    std::array<double, CategoryCount> fallback{};
    for (int c = 0; c < CategoryCount; ++c)
    {
        if (static_cast<Category>(c) == Category::Moving)
            continue;
        candidates[c] = freeSpots(static_cast<Category>(c));
        if (candidates[c].empty())
            continue;
        const Range &share = settings.share[c];
        const double cap = std::ceil(share.max * total - Epsilon);
        const double middle = (share.min + share.max) * .5 * total;
        fallback[c] = 1.0;
        fallbackSum += 1.0;
        if (planned[c] + 1 > cap)
            continue;
        weights[c] = std::max(0.0, middle - planned[c]) + .05;
        sum += weights[c];
    }
    if (sum <= 0.0)
    {
        weights = fallback;
        sum = fallbackSum;
    }
    if (sum <= 0.0)
        return -1;

    double pick = Unit() * sum;
    int chosen = -1;
    for (int c = 0; c < CategoryCount; ++c)
    {
        if (weights[c] <= 0.0)
            continue;
        chosen = c;
        pick -= weights[c];
        if (pick < 0.0)
            break;
    }
    const std::vector<int> &open = candidates[chosen];
    const int spot = open[std::min(static_cast<int>(Unit() * open.size()), static_cast<int>(open.size()) - 1)];
    ++occupancy[spot];
    category = static_cast<Category>(chosen);
    return spot;
}

int Director::ChooseClip(const Patron &patron, Category category, Posture posture, double now, double &startFraction)
{
    std::vector<int> pool;
    for (int index = 0; index < static_cast<int>(clips.size()); ++index)
    {
        const Clip &clip = clips[index];
        if (clip.category == category && clip.posture == posture && clip.weight > 0.0 &&
            (clip.skeleton.empty() || clip.skeleton == patron.skeleton))
            pool.push_back(index);
    }
    if (pool.empty())
        return -1;

    if (category == Category::Dancing && patron.style != 0)
    {
        std::vector<int> styled;
        for (int index : pool)
            if (clips[index].style == patron.style || clips[index].style == 0)
                styled.push_back(index);
        if (!styled.empty())
            pool.swap(styled);
    }

    // Phases already running nearby, per clip.
    const Vec3 &here = patron.travelling || patron.spot < 0 ? patron.position : spots[patron.spot].position;
    std::vector<std::vector<double>> nearby(clips.size());
    for (const Patron &other : patrons)
        if (other.id != patron.id && other.clip >= 0 && Distance(other.position, here) < settings.syncRadius)
            nearby[other.clip].push_back(Phase(other, now));

    // How far from every running copy each candidate could start: half the widest free arc for a loop; a one-shot
    // cannot be offset, so it only fits once every copy nearby is far enough along.
    std::vector<double> gaps(clips.size(), 0.0), starts(clips.size(), -1.0);
    for (int index : pool)
    {
        std::vector<double> phases = nearby[index];
        if (phases.empty())
        {
            gaps[index] = .5;
            continue;
        }
        if (!clips[index].loop)
        {
            const double least = *std::min_element(phases.begin(), phases.end());
            gaps[index] = least >= settings.minPhaseGap - Epsilon ? settings.minPhaseGap : 0.0;
            continue;
        }
        std::sort(phases.begin(), phases.end());
        double widest = phases.front() + 1.0 - phases.back(), from = phases.back();
        for (std::size_t i = 1; i < phases.size(); ++i)
            if (phases[i] - phases[i - 1] > widest)
            {
                widest = phases[i] - phases[i - 1];
                from = phases[i - 1];
            }
        gaps[index] = widest * .5;
        starts[index] = std::fmod(from + widest * .5, 1.0);
    }
    // Rules in priority order: never back-to-back; never in step with a neighbour; not one of the last N clips.
    // Relax "last N" one step at a time before giving up on the neighbour gap; repeats only when the pool is one clip.
    auto fresh = [&](int depth)
    {
        std::vector<int> result;
        const int from = std::max(0, static_cast<int>(patron.recentClips.size()) - depth);
        for (int index : pool)
            if (std::find(patron.recentClips.begin() + from, patron.recentClips.end(), index) ==
                patron.recentClips.end())
                result.push_back(index);
        return result;
    };
    std::vector<int> choices, fallback;
    for (int depth = std::max(settings.noRepeatDepth, 1); depth >= 1 && choices.empty(); --depth)
    {
        const std::vector<int> candidates = fresh(depth);
        if (fallback.empty())
            fallback = candidates;
        for (int index : candidates)
            if (nearby[index].empty())
                choices.push_back(index);
        if (choices.empty())
            for (int index : candidates)
                if (gaps[index] >= settings.minPhaseGap - Epsilon)
                    choices.push_back(index);
    }
    if (choices.empty())
    {
        if (fallback.empty())
            fallback = pool;
        double best = -1.0;
        for (int index : fallback)
            best = std::max(best, gaps[index]);
        for (int index : fallback)
            if (gaps[index] >= best - Epsilon)
                choices.push_back(index);
    }

    double sum = 0.0;
    for (int index : choices)
        sum += clips[index].weight;
    double pick = Unit() * sum;
    int chosen = choices.back();
    for (int index : choices)
    {
        pick -= clips[index].weight;
        if (pick < 0.0)
        {
            chosen = index;
            break;
        }
    }

    if (!clips[chosen].loop)
        startFraction = 0.0;
    else if (starts[chosen] < 0.0)
        startFraction = Unit();
    else
        startFraction = starts[chosen];
    return chosen;
}

Play Director::Start(Patron &patron, Category category, Posture posture, double now)
{
    Play play;
    play.patron = patron.id;
    play.spot = patron.spot;
    play.time = now;
    play.travelling = patron.travelling;
    double startFraction = 0.0;
    const int clip = ChooseClip(patron, category, posture, now, startFraction);
    play.clip = clip;
    play.category = category;
    patron.category = category;
    if (clip < 0)
    {
        // Nothing playable (no walk clip for this skeleton, say): hold the current pose and ask again shortly.
        patron.clipEnds = patron.travelling ? patron.arrives : now + 5.0;
        return play;
    }

    patron.clip = clip;
    patron.clipStart = now;
    patron.startFraction = startFraction;
    patron.playRate = Uniform(settings.playRate);
    patron.mirrored = clips[clip].mirrorSafe && Unit() < .5;
    patron.recentClips.push_back(clip);
    const std::size_t keep = static_cast<std::size_t>(std::max(settings.noRepeatDepth, 1));
    if (patron.recentClips.size() > keep)
        patron.recentClips.erase(patron.recentClips.begin(),
                                 patron.recentClips.end() - static_cast<std::ptrdiff_t>(keep));
    if (patron.travelling)
        patron.clipEnds = patron.arrives;
    else if (clips[clip].loop)
        patron.clipEnds = now + Uniform(settings.loopHoldSeconds);
    else
        patron.clipEnds = now + clips[clip].seconds / patron.playRate;

    play.startFraction = patron.startFraction;
    play.playRate = patron.playRate;
    play.mirrored = patron.mirrored;
    return play;
}

namespace
{
void Emit(std::vector<Play> &plays, const Play &play)
{
    if (play.clip >= 0)
        plays.push_back(play);
}
} // namespace

std::vector<Play> Director::Update(double now, const Vec3 &viewer)
{
    std::vector<Play> plays;
    // Move every walker first, so each decision below sees the same positions for everyone.
    for (Patron &patron : patrons)
        if (patron.travelling)
        {
            const double span = std::max(patron.arrives - patron.departs, Epsilon);
            patron.position = Lerp(patron.travelFrom, spots[patron.spot].position,
                                   std::clamp((now - patron.departs) / span, 0.0, 1.0));
        }
    for (Patron &patron : patrons)
    {
        if (patron.travelling)
        {
            if (now + Epsilon < patron.arrives)
                continue;
            patron.travelling = false;
            patron.position = spots[patron.spot].position;
            const Category category = patron.pendingCategory;
            patron.activityEnds = now + Uniform(settings.activitySeconds[static_cast<int>(category)]);
            Emit(plays, Start(patron, category, spots[patron.spot].posture, now));
            continue;
        }

        if (patron.spot < 0)
        {
            // Start of the night: placed directly, no walk-in.
            Category category = Category::Moving;
            const int spot = ChooseActivity(patron, category);
            if (spot < 0)
                continue;
            patron.spot = spot;
            patron.position = spots[spot].position;
            patron.activityEnds = now + Uniform(settings.activitySeconds[static_cast<int>(category)]);
            Emit(plays, Start(patron, category, spots[spot].posture, now));
            continue;
        }

        if (now + Epsilon >= patron.activityEnds)
        {
            Category next = Category::Moving;
            const int previous = patron.spot;
            const int spot = ChooseActivity(patron, next);
            if (spot < 0)
            {
                patron.activityEnds = now + 5.0;
            }
            else
            {
                --occupancy[previous];
                patron.travelFrom = spots[previous].position;
                patron.spot = spot;
                patron.pendingCategory = next;
                patron.travelling = true;
                patron.departs = now;
                const double walk = Distance(patron.travelFrom, spots[spot].position) / settings.walkSpeed;
                patron.arrives = now + std::clamp(walk, settings.travelSeconds.min, settings.travelSeconds.max);
                Emit(plays, Start(patron, Category::Moving, Posture::Standing, now));
                continue;
            }
        }

        if (now + Epsilon >= patron.clipEnds)
            Emit(plays, Start(patron, patron.category, spots[patron.spot].posture, now));
    }
    AssignTiers(viewer);
    return plays;
}

void Director::AssignTiers(const Vec3 &viewer)
{
    std::vector<int> order(patrons.size());
    std::iota(order.begin(), order.end(), 0);
    std::stable_sort(order.begin(), order.end(), [&](int a, int b)
                     { return Distance(patrons[a].position, viewer) < Distance(patrons[b].position, viewer); });
    int heroes = 0;
    for (int index : order)
    {
        Patron &patron = patrons[index];
        const double distance = Distance(patron.position, viewer);
        if (heroes < settings.heroCount && distance <= settings.nearRadius)
        {
            patron.tier = Tier::Hero;
            ++heroes;
        }
        else if (distance <= settings.nearRadius)
            patron.tier = Tier::Near;
        else if (distance <= settings.midRadius)
            patron.tier = Tier::Mid;
        else
            patron.tier = Tier::Far;
    }
}
} // namespace Club
} // namespace SS
