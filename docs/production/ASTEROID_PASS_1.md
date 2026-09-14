# Asteroid behavior, density and particles — review pass 1

Owner requested this bounded first step, followed by review. No new automatic itch update.

- Decorative field: default384 instances, cap768, four mesh batches from the purchased asteroid pack. Sparse1400–2200cm-radius anchors and100–700cm small silhouettes replace uniformly large dressing; rocks close to the original central sightline are limited to220cm radius.
- Motion: slow individual0.2–0.8degree/second tumble around actual mesh bounds centers. Existing bounded parallax and minimum separation are retained. These rocks remain outside damage/weapon targeting and cannot become invisible collision hazards.
- Passing dust:512 world-stationary grains in a48m-wide recycled local region,1.5–5cm size, faded at the boundary and around the ship. No collision or extra damaging debris.
- Gameplay review found no new movement/admission blocker. Existing incoming hazard budgets, massive-body avoidance, medium fragmentation admission and pickup probabilities are retained.
- Small/medium destruction now emits12 cosmetic chips, inherits asteroid drift and fades within0.85s. Maximum8simultaneous bursts. Independent cosmetic RNG preserves fragment/drop sequences.
- Combined editor build and43Unreal tests passed, zero test warnings/failures/not-run. Burst once-only/cap/expiry and expanded density bounds/disable/restore tests pass. The initial density capture predates the breakup addition: in-combat visual readability of breakup remains unverified.

Initial current-renderer comparison: `Artifacts/EndgameSoak/ec68ff5fceef43f48b7f47d34c2ece3e`, normal-stat scripted29s Wave1, no firing and no saves. Cruise image inspected. This is not a natural input or performance result. The background remains dark, atmosphere is disabled and the visual target is not met yet.

## Review question

Does the mix of larger anchors, smaller rocks and passing dust feel like a field with depth while the travel direction remains readable? Compare cruise, turn, boost and brake before changing gameplay danger.

## Power-up direction

Owner likes the video's power-ups. Treat their visible silhouette/color/glow and collection feedback as a presentation reference for existing scoped pickups. New buff types, drop rates or progression changes are not implied. Schedule that as the next bounded presentation pass after asteroid review.
