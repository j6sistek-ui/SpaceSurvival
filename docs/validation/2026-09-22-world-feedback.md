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

PR59 remains draft/unmerged. Package 4/source79553fc remains the playable archive and does not contain this follow-up. Owner subsequently approved 60m/s/matched acceleration, 3x Director asteroids with distinct material/color, and left-stick steering/right-stick strafe. A later right-stick camera question is pending clarification. Lead retains full cockpit boarding, visual atmosphere/field acceptance and beacon repro; jump clip/lowest-priority enemy-follow camera remain open. See KNOWN_ISSUES for the sole active work list.

## Approved arcade follow-up

Effective cruise/acceleration are 6000 cm/s and 8000 cm/s squared via an added Data Asset multiplier, preserving serialized base values and upgrade relationships. RT release still coasts; boost remains separate. Small/medium/massive Director asteroids use 3x radius, matching mesh/collision size, expanded lateral admission for the largest rocks, and an orange M_Hazard dynamic material on every slot. Wreckage passages, fields, enemies and fixed-world scenery are not size-multiplied. First approved flight mapping swaps the sticks; walking is unchanged. Owner subsequently raised right-stick camera look, awaiting clarification.

| Receipt | Result |
|---|---|
| ArcadeFeedback-Build1.log | Failed: new isolated admission fixture accessed private ship velocity. No runtime error; fixed with scoped test friendship. |
| ArcadeFeedback-Build2.log | Editor passed24.63s; installed engine deprecation warnings retained. |
| Artifacts/ArcadeFeedback/Focused1/index.json | 8/8 clean3.701120s: AnalogThrottleAndCoast, ControllerToPhysics, ControllerAfterTakeoff, ControllerPitchParity, LiveRewardInput, BoostBrakeMovement, DirectorAsteroidReadability and WreckageBudgetAdmission. |

The admission case exercises actual production SpawnHazard at 60m/s, including all three sizes, visible/collision radius, safe-lane clearance, reaction-time lead, material slots and retirement allowance. The throttle case reaches >55m/s without boost and preserves engine-off momentum. These fixtures do not establish subjective flight feel or rendered material appearance.


## Final owner clarification and retained failures

Supersedes initial stick swap/camera-follow speculation: Temporary testing preset: LS X = sideways strafe, LS Y = pitch; LB/RB = manual left/right roll; RS = camera-only free-look; A = fire; X = flight interaction/landing; RT/LT/B = throttle/brake/boost. No controller vertical strafe. Walking unchanged. Released free-look gently returns behind the ship; released roll retains hull attitude. Pause Controls/preset/remapping is explicitly deferred.

Build3 passed41.13s. Focused2 passed7/9; roll movement/retained attitude and a coast-versus-vertical-thrust fixture assumption failed. Build4/Focused3 and Build5/Focused4 retained both failures while measuring the actual route: held bumper, manual flag and40deg/s tuning arrived correctly, but resting-body roll advanced only1.075degrees over45frames. The strafe fixture mixed pre-existing6000cm/s coasting momentum with its new-thrust assertion. Follow-up checks remain bounded to these failures.

### Rendered field follow-up — FAILED

Artifacts/EndgameSoak/704746d51fd64fd0b8a12b46ea4e929c/capture.json is failed. Four Cruise/Turn/Boost/Brake images exist; the scripted non-evasive Wave1 path died before29seconds. Lead reviewed Cruise/Turn/Brake: orange Director surfaces are visibly distinct from darker world rocks. These establish bounded appearance, not survival fairness or complete environment/transition acceptance. Actual damage stayed enabled. The editor-game log also retains engine EditorToolset/ToolsetRegistry Python startup AttributeErrors, separate from gameplay death. Package4 remains unchanged at this checkpoint.


## Final source verification

Build9 passed8.75s. FinalAffected passed **9/9**, zero warnings/failures/omitted,4.598423s: ControllerToPhysics, ControllerAfterTakeoff, ControllerPitchParity, LiveRewardInput, AnalogThrottleAndCoast, ControllerTestingPreset, MenuBackBoostRelease, ChaseFraming and DistantAsteroidIsolation. Director size/material/wreckage admission previously passed Focused1; inherited fragment presentation passed Focused2. No full-suite rerun.

Root cause of the roll failure: the held command reached the real gyroscope, but the stationary Chaos body reported awake=0 and zero angular velocity. Setting sleep properties in BeginPlay was too late: the registered component already owned its physics actor. The final constructor initializes this one controlled body's custom sleep multiplier to zero before creation. No global solver setting, vendor asset or plugin is changed. Trial explicit wakes and gyro tick-order changes did not solve it and were removed. Final roll result:11.921degrees after45frames, awake=1,22.655deg/s angular velocity; release damped to a retained17.862degree attitude, and LB reversed it. The40deg/s command retains the vendor0.6 roll shaping, producing a gentle approximately24deg/s steady roll.

The lateral-only fixture now starts the strafe segment at rest, distinguishing commanded acceleration from pre-existing coasting momentum. It measures Y1275.815cm/s and zero induced vertical velocity. The failed histories Focused2–7 remain preserved. Focused8 first passed roll/coast2/2 in1.550456s; FinalAffected then checked the directly affected paths after the shared body initialization change. This is synthetic raw input/physics evidence, not physical-controller feel acceptance.

Source37, canonical documentation navigation, changed-file native formatting and diff whitespace checks pass. Packaging is the next checkpoint; this paragraph does not itself replace Package4.
