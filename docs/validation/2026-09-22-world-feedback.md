# World-space and interaction feedback — September 22, 2026 UTC

Scope: RPT-20260921-05, first source-only batch. User requested focused, batched validation to preserve weekly usage. No full automation panel was run. Original editor, vendor assets, account/checkpoint data and Package 4 are unchanged.

## Changes and evidence

- Fixed initial asteroid belt transforms; removed shell recycling/scale fading/viewer-relative translation. Uses existing private SolidScenery simple-collision meshes, independent of Director pressure. The initial belt is finite; existing regional cells provide farther world scenery.
- Retained scenery/atmosphere visibility across flight, approach, docking and station; initialized at home and retained sky/scenery identity at takeoff. This routing is compiled, not yet visually accepted.
- Explicit title state separates startup/return-to-title from home pause. Home pause offers Resume walking; return-to-title explicitly discards only unsuspended in-memory run state.
- Removed alien-gallery service and original Acornaut wardrobe option, preserving source assets and enum/save IDs. Old Acornaut preference resolves to current default. Current Squirrel/title artwork preserved.
- Removed automatic launch popup at cabin entry. E/Y opens provisional cabin flight options. The full cockpit flow is not implemented: source parked collision envelopes fill cockpit/interior areas, and Phoenix hides its pilot. Do not count this as walking to/sitting in the chair.
- Beacon interactions now report out-of-range, absent and already-accepted signal states. Owner failure scenario has not been reproduced; this is feedback improvement, not closure of the report.

## Focused validation

| Receipt | Result |
|---|---|
| `Artifacts/BuildLogs/WorldFeedback-Build1.log` | Editor build passed, 35.02 s. Engine Niagara C4996 warnings remain baseline. |
| `Artifacts/WorldFeedback/Focused1/index.json` | 2 passed, 1 failed, zero warnings/omitted, 4.623351 s. Home pause/title/retired-save selection and actual walking/explicit boarding passed. Field position/scale checks passed; actual rock trace failed. |
| `Artifacts/BuildLogs/WorldFeedback-Build2.log` | Editor build passed, 16.01 s. |
| `Artifacts/WorldFeedback/Focused2/index.json` | 1 passed, 1 failed, zero warnings/omitted, 1.094990 s. Gallery service labels passed. Moving the ship/attached rig away from the trace did not fix the rock collision failure; the initial fixture-only hypothesis was insufficient. |
| `Artifacts/BuildLogs/WorldFeedback-Build3.log` | Editor build passed, 9.26 s. Installed engine `UInstancedStaticMeshComponent::ShouldCreatePhysicsState` rejects compiling meshes. Added the same editor-only compilation readiness guard already used by the landing pad; cooked meshes need no such wait. |
| `Artifacts/WorldFeedback/Focused3/index.json` | Asteroid case passed, zero warnings/failures/omitted, 0.865177 s. Actual Visibility trace hit the field; approach, visibility changes, refollow and origin shift preserve transforms. Diagnostic: compiling=0, physics=1. |

Four distinct affected cases passed across these focused runs. Previous failures are preserved, not overwritten. Structural 37, documentation navigation, changed-file native clang-format and diff whitespace checks passed. No source package, full suite, performance benchmark, natural play, physical controller or rendered continuity acceptance is claimed.

## MCP / resources

Read-only Nwiro skill listing and applicable Blueprint/lighting skills succeeded. Asset registry confirms BP_AsteroidField_Arch/Globular/Linear. Existing AuthorAsteroidDepth.py samples their layouts; no vendor Blueprint was rewritten. Read-only inspection confirms the first private rock uses default/simple collision with a convex hull. No source asset writes or owner-editor interruption occurred.

## Delivery boundary

PR59 remains draft/unmerged. Package 4/source79553fc remains the playable archive and does not contain this follow-up. Speed/debris-size and stick-layout changes await the two owner choices. Lead retains full cockpit boarding, visual atmosphere/field acceptance and beacon repro; jump clip/lowest-priority enemy-follow camera remain open. See KNOWN_ISSUES for the sole active work list.
