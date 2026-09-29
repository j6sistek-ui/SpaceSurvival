# PR66 native repair and harder playtest baseline

Date: 2026-09-29. Original audited PR head: `423b41f4c6790cbeaea151399ea0132c6091fe76`; base/main `9ac1d6f7f346e06a10c2e6eb3652830abdf3d25a`. Owner authorized repairing/adopting the harder D7/photo intent before play. PR66 stays open; station PR64, private assets, package and itch are outside this change. No difficulty reduction or new mechanic was introduced.

## Repairs

- Renamed the distant-field translation-unit constants to avoid a C4459 name collision with Chaos headers in the actual UE5.8 unity build. The original native compile failed; field geometry/density is unchanged.
- Volley admission plans clear members first, verifies every member's authored lifetime covers its pass, and checks summed authored costs. It spends only actual spawned costs. A refused volley falls back to the ordinary asteroid; no free/underpriced ring rocks or lifetime extension.
- Story transmissions use a bounded 16-entry FIFO carrying the original wave. Pending duplicates coalesce, chatter never queues, live menus freeze reading/delivery time, and run transitions/subtitle disabling clear pending dialogue. These are captions, not recorded speech.
- Added targeted native cases for fractional costs, insufficient budget, blocked ring members, short lifetime, real firing/damage responses, cue ordering/menu timing and sustained climax pressure.
- Added `CaptureSpaceLook.ps1 -DirectorReview`: four normal flight frames plus a temporary player-side rider close-up. Camera/HUD restore afterward; this option only operates in the development capture fixture.

Hard defaults retained: direct-candidate share .70, spacing .75 s (1.5 s in Wave1), enemy chance .26, enemy caps 3/5, budget growth .16, and the original PR66 volley chances/counts. Actual loaded `/Game/SpaceSurvival/Data/DA_Phase1` reported .26, 3/5 and .16 in rendered metadata.

## Native validation and retained failures

Worktree: `C:/Users/j6sis/.codex/worktrees/pr65-review/SpaceSurvival`. UE5.8.2, installed Windows toolchain. Docker is stopped; installed clang-format22 was used, with container checks left to GitHub CI. All owned Unreal processes were NullRHI or RenderOffscreen.

- `Scripts/Build.ps1 -Target Editor`: repaired build succeeded 27.83 s, focused-test build 4.65 s, capture correction build 12.22 s. Existing engine/Slate C4996 deprecations remain; no project compile error.
- Initial affected batch: 12/13 success, zero warning successes/not-run. `AdmittedBodiesOutliveAdmission` failed an old fixture assumption: its >22000 cm setup used an obsolete 450 cm/s placement floor while production now follows actual authored drift. The test now explicitly authors that speed for this distance case; production tuning and retirement assertions were not relaxed.
- Focused rerun: 2/2 success, zero warnings/failures/not-run (`AdmittedBodiesOutliveAdmission`, `DirectorVolleyAdmission`). Total **13 distinct affected tests pass across the two batches**, not 15 independent tests.
- Other passing cases: DirectorAdmissionFallThrough, DirectorAsteroidReadability, DirectorSustainedPressure, DirectorTrajectoryFairness, DirectorVillainLaunch, DirectorVillainVoice, DirectorVolley, WreckageBudgetAdmission, RequiredClimaxAdmission, AcceleratedTenWaveJourney, JourneyDeathAndFreshRun.
- Real-tick 39.5 s climax: Wave5 admitted44 Director asteroids, longest admission gap5.45 s, peak24 threats; Wave10 admitted33, gap4.00 s, peak24. The fixture uses high hull/shields to stay alive and measure continuity; this is not a balance or natural survival result.
- Actual `ASSShip::Fire` cannon projectile/sweep destroys the central volley rock; two actual starter-laser traces also destroy it while leaving the ring. Synthetic aim and fixture-only zero laser interval isolate damage/trace behavior; no claim about physical trigger input, aiming skill or natural firing cadence.
- CheckProject:38 structural checks pass; TestSourceDigests:13 pass. Changed-file native format and diff whitespace checks pass. Documentation/CI and final desktop build are recorded below when finished.

Local logs: `Artifacts/PR66Audit/Build*.log`, `Tests/index.json`, `Tests-Focused/index.json`. The original C4459 log, initial failed native case and all reruns are retained.

## Rendered evidence

First capture `e1e230feaea5487bb09a3087c127082c` produced all five images but failed because the validator still expected four; it is retained as failed. The close-up was behind the rider with HUD over it. Corrected the stage list and moved only the diagnostic camera to the player-facing side, hiding/restoring HUD.

Second capture `813718a6655a4ebeb7e2a594c8c459da`, label `PR66DirectorReview2`: **success**, process0, production save hashes preserved, binaries unchanged, no test save slots written. Five 1920x1080 frames under `Artifacts/EndgameSoak/813718a6655a4ebeb7e2a594c8c459da`: Cruise, Turn, Boost, Brake, VillainCloseup.

Lead inspected actual Phoenix, dense varied world asteroids/debris, distinct orange Director rocks, the separate readable Sable caption, and the visible Heavy Trooper with matching ThirdPersonIdle facing the player on the craft. The close-up is deliberately not the normal chase camera. One legacy metadata label incorrectly called that diagnostic camera a walking view; corrected in the subsequent source without changing gameplay. Capture uses an isolated profile and scripted input; no audio listening, physical-input, representative FPS or natural ten-wave survival claim.

## Playable integration

Pending at this source checkpoint. Intended existing desktop target is `C:/Users/j6sis/.codex/worktrees/flight-loop-reset/SpaceSurvival`, through `Play SpaceSurvival - Current` / `Play Development Build.cmd` or `Open Repaired Game Editor.cmd`. Final source/module identity and smoke receipt must be added before owner handoff.

Five existing modified/untracked Content/Python files in that checkout already byte-match the incoming PR versions; preserve them and all private asset folders during branch advancement. No rebuild/reimport of private art is required. The standalone packaged EXE and itch remain the September22 release.

## Acceptance limits

The formation has tested timing, clearance and weapon responses; this does not mathematically guarantee that every randomized combination with scenery/enemies is survivable. Physical controller feel, normal-health Waves1-10 and final difficulty acceptance remain open in ACT-12. Knight/craft replacement, attack runs and damage scars are separate existing work. No merge or publication performed.
