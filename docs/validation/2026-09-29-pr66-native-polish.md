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
- CheckProject:38 structural checks pass; TestSourceDigests:13 pass. Changed-file native format and diff whitespace checks pass. Documentation gate passes; current-head GitHub CI is tracked on PR66. Final desktop build is recorded below.

Local logs: `Artifacts/PR66Audit/Build*.log`, `Tests/index.json`, `Tests-Focused/index.json`. The original C4459 log, initial failed native case and all reruns are retained.

## Rendered evidence

First capture `e1e230feaea5487bb09a3087c127082c` produced all five images but failed because the validator still expected four; it is retained as failed. The close-up was behind the rider with HUD over it. Corrected the stage list and moved only the diagnostic camera to the player-facing side, hiding/restoring HUD.

Second capture `813718a6655a4ebeb7e2a594c8c459da`, label `PR66DirectorReview2`: **success**, process0, production save hashes preserved, binaries unchanged, no test save slots written. Five 1920x1080 frames under `Artifacts/EndgameSoak/813718a6655a4ebeb7e2a594c8c459da`: Cruise, Turn, Boost, Brake, VillainCloseup.

Lead inspected actual Phoenix, dense varied world asteroids/debris, distinct orange Director rocks, the separate readable Sable caption, and the visible Heavy Trooper with matching ThirdPersonIdle facing the player on the craft. The close-up is deliberately not the normal chase camera. One legacy metadata label incorrectly called that diagnostic camera a walking view; corrected in the subsequent source without changing gameplay. Capture uses an isolated profile and scripted input; no audio listening, physical-input, representative FPS or natural ten-wave survival claim.

## Playable integration

**Ready for owner playtest:** existing desktop target `C:/Users/j6sis/.codex/worktrees/flight-loop-reset/SpaceSurvival`, branch `codex/pr66-playtest`, gameplay source `c68941bd90226005186be323ebc98783992619c7`. The subsequent commit changes documentation only. Native Editor build succeeded in36.07 s (`Artifacts/PR66Integration/Build.log`). Module SHA256: `496882822de663e30ff3a894282440529e92eb11346627af26dfbe53aebecb0c`.

Both existing desktop shortcuts were inspected: `Unreal Engine` names this repaired project and Survival map; `Play SpaceSurvival - Current` resolves to its existing `Play Development Build.cmd` under the real owner account. No shortcut change or visible launch was required. Direct alternatives are that checkout's `Play Development Build.cmd` and `Open Repaired Game Editor.cmd`.

Final offscreen smoke from this exact playable checkout: `1f96dbeccc964d858c7a54bf26976011`, label `PR66Playable`. All five images and fixture pass, process0,29.27 s wall time, peak17 threats; source HEAD/binaries/production saves preserved and zero fixture save slots. Actual Phoenix, incoming rocks, flight caption and braking presentation inspected. Legacy camera metadata label is corrected. Artifacts: `Artifacts/EndgameSoak/1f96dbeccc964d858c7a54bf26976011/{capture,fixture}.json` and five PNGs. This is the final normal-health scripted flight smoke, not a complete natural survival run.

Five existing modified/untracked Content/Python files byte-matched the incoming PR versions. Git correctly refused an overwrite, so the five were backed up under `Artifacts/PR66Integration/ExistingPython` and preserved in a path-scoped stash before switching. All five Git object hashes match afterward. The stash is retained for recovery; no asset folders or unrelated edits were stashed or deleted. No rebuild/reimport of private art is required. The standalone packaged EXE and itch remain the September22 release.

## Acceptance limits

The formation has tested timing, clearance and weapon responses; this does not mathematically guarantee that every randomized combination with scenery/enemies is survivable. Physical controller feel, normal-health Waves1-10 and final difficulty acceptance remain open in ACT-12. Knight/craft replacement, attack runs and damage scars are separate existing work. No merge or publication performed.

## September30 follow-up: truthful volley presentation, unchanged shoot-through pressure

Owner supplied a secondary audit and explicitly retained the need to shoot out of dense encounters. No ring-count cap, widened gap, weaker rock, lower spawn chance or lower budget was added. The omitted ring position is now documented as an empty placement, not a guaranteed Phoenix-width flight corridor.

- Fewer than three free threat slots refuses `SpawnVolley` before spawning/reserving/spending; the existing ordinary asteroid path remains available in the same admission interval.
- If spatial clearance leaves only the central attack, it remains shootable and dangerous but does not trigger a volley caption. A volley caption needs at least two actual rocks. The normal throw flare is retained for an actual attack.
- The older 'larger hull' fixture had no BeginPlay/private Phoenix, so it exercised the sphere fallback, not a compound flight hull. The corrected test installs a transient off-centre compound and asserts that the actual production bounds envelope increases by over1000cm while the root sphere stays unchanged. Each motion/hull scenario must admit at least one volley; the test cannot pass through only refusals. This measures geometry/admission, not registered Chaos contacts.
- Added occupied-cap regressions for one/two remaining slots, zero cost/reservation on refusal and actual Tick fallback spending. A fully blocked ring verifies the lone centre has no volley caption; a complete formation verifies captions are enabled.

Native `DirectorVolley` and `DirectorVolleyAdmission`: **2/2 success, zero warnings/failures/not-run**, report `Artifacts/PR66Followup/Tests/index.json`. Editor build passed4.75s (`Build2.log`) after correcting a nonexistent asteroid enum in the new test fixture; failed `Build.log` is retained. CheckProject38, changed-file clang-format22, documentation gate and whitespace pass. No broad suite or new rendered pass: existing art, camera and difficulty values are unchanged. Current desktop follow-up build is pending at this source checkpoint.
