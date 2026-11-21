# Club ambience: living patron crowd

Owner-approved on 2026-11-20 (RPT-20261120-01). Live working doc with the full plan and checklists:
[Club Ambience: Living NPC Plan](https://claude.ai/artifact/LwB1UhhT5TdT5h9jzE4Cbf). This file is the repository
copy of the decisions and the setup steps; `docs/KNOWN_ISSUES.md` owns status.

## Decisions (defaults accepted 2026-11-20)

- **Crowd:** Quiet 13, Normal about 24, Packed 41 patrons. Staff are fixed roles and not random: bartender
  (Joy), server (Astra), bouncer, DJ. Performing dancers (Vexa and the others) are **not** counted; their
  routine work stays under RPT-20261021-01.
- **Mix of patrons:** dancing 30–40%, bar 15–20%, seated lounge 20–25%, standing social 15–20%, moving between zones
  5–10%, special (drunk, asleep, VIP) 0–2 each.
- **Variation rules:** weighted random clip pick, never one of the patron's last two clips; no two patrons within
  8 m start the same clip in a near-identical phase (at least a quarter of the clip apart); random start point; play
  rate 0.9–1.1; activity time ranges (dance 45–150 s, bar 1–4 min, seated 2–6 min, group 1–3 min); each dancer keeps
  one style; one logged seed per session replays a night exactly.
- **"Alive" acceptance:** every NPC readable in two seconds; no clones; props match poses; no feet in the floor or
  limbs in seats; something changes in view every 10–20 s; staff never idle; Packed holds 60 fps at 1080p on the
  owner's PC without the hide trim.
- **Density:** detail tiers by camera distance. Hero (the 8 nearest, full quality), Near (within 15 m, animation
  every 2nd–4th frame), Mid (to 30 m), Far (beyond). Later: shared poses or vertex-animated instances for Mid/Far.
  Reference: GTA VI club footage the owner supplied shows a full-detail foreground NPC against a dark, hazy,
  backlit crowd. Lighting and haze hide reduced detail at distance.

## What exists (phase 3, first code)

| Piece | File | State |
| --- | --- | --- |
| Rules: mix, spots, clip choice, no-repeat, no-sync, timers, travel, tiers, seed | `Source/SpaceSurvival/Domain/ClubCrowd.h/.cpp` | Portable C++17, unit tested |
| Tests: 24 simulated 30-minute nights plus edge cases | `Tests/ClubCrowdTests.cpp` | Pass under strict and ASan/UBSan builds (Linux g++) |
| Unreal layer: `ASSClubActivitySpot`, `FSSClubClipRow`, `ASSClubCrowdDirector` | `Source/SpaceSurvival/Public|Private/SSClubCrowd.*` | **Not yet compiled in Unreal** |

The director drives existing `ASSOutpostAmbientActor` patrons by setting `bAnimationManagedExternally`, so their
own route/gesture/chatter loop stops for patrons it owns. Staff and performers are never added to it.

## Setting it up in the editor (after an Editor build)

1. **Clip table:** create a Data Table with row type `SSClubClipRow`. Add each reviewed clip with its activity,
   posture, prop, style and loop flag. Start with 6–10 good clips per activity for the club skeletons.
2. **Spots:** place `SSClubActivitySpot` actors. Set activity, posture and capacity (group tables 3–4), with the
   arrow facing where the patron should look. Measure `SeatHeight` on seats.
3. **Director:** place one `SSClubCrowdDirector`, assign the clip table, and add the patron ambient actors with a
   dance style each (1–3). Leave `Spots` empty to use every spot in the level. Leave `Seed` at 0 for a new night each
   session; the log line `club crowd ... seed N` gives the seed to replay.

## Known limits of this first version

- Walkers move in a straight line between spots without pathfinding or collision. Spots need clear lines.
- No props are attached yet and seat heights are recorded but not fitted (phase 4).
- Clips are never mirrored (single-node playback); the row flag is stored for later.
- Arrivals and departures from the venue, bar orders handed to staff, and reactions to performers are phase 5.
- Detail tiers only change animation update rate; head-fill light and mesh LOD wait for the phase 6 profile.
