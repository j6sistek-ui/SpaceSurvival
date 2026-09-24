# Outpost sandbox validation — 2026-09-24

Status: **PARTIAL — functional checks pass within the scopes below; visual quality is not accepted.**
This is a dated local evidence record, not a replacement for the active issue log or a release declaration.

## Identity and scope

- Branch: `codex/asteroid-outpost-sandbox`; working base `e05feead0d85b5bdf4e6860c930234f898980ccd`, with the sandbox implementation described by this draft branch and private content. The base commit alone does not contain the tested changes; the native file hashes below pin the tested runtime source.
- Review map: `/Game/OutpostSandbox/L_AsteroidOutpost`; separate from `/Game/SpaceSurvival/Maps/Survival`.
- Engine: Unreal Engine `5.8.2-56702186+++UE5+Release-5.8`, Windows editor. Native processes use `-NullRHI` for automation or `-RenderOffscreen` for rendered checks.
- Runtime evidence remains Play `20260924T073319Z`. Later saved authoring/capture checkpoints are identified separately below through WorkstationFinish1 and ReloadReady1, retaining the earlier rejected and failed attempts. Neither later renders nor source changes inherit the earlier runtime pass automatically.
- Local only. No packaged-build, itch publication, merged-change or live-station replacement claim is made.

The reviewed native source snapshot has these SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `Source/SpaceSurvival/Private/SSOutpostSandbox.cpp` | `8f43956a40332d68fbca70e5b33ad509a57741d610813dc1429abd5f805033e8` |
| `Source/SpaceSurvival/Public/SSOutpostSandbox.h` | `a69b0eb319af3c98fb9d62cd77c282edb8912dd7b929e0e33cb497a67d889585` |
| `Source/SpaceSurvival/Private/SSGameMode.cpp` | `337d64803ebd362abe97833e08c787ab2b54a37ac1b7c81b23ff2fa6512fef06` |

## Native build and focused automation

`Artifacts/Outpost/EditorBuild5.log` records `SpaceSurvivalEditor Win64 Development` compiling the outpost implementation/tests and linking successfully: **Result: Succeeded**. It contains two nonfatal toolchain/header warnings: MSVC `14.51.36257` is newer than Epic's preferred version, and engine `Character.h` emits C4996 for deprecated `APawn::GetMovementBase`. These are preserved as warnings; this receipt does not claim a warning-free build.

`Artifacts/Outpost/FocusedTestsBuild5.log` and `Artifacts/Outpost/TestsBuild5/index.json` record the bounded `SpaceSurvival.Outpost` suite:

| Test | Result | Verified behavior |
| --- | --- | --- |
| `CrewSupport` | Success | Crew moves on a supported deck, stops at its edge, and does not use another crew capsule as a substitute floor. |
| `DoorSafety` | Success | Closed leaves block a walking capsule; approaching/occupying pawns open or hold them; a physics-body crate in the leaf travel pocket prevents closing; clear doors close and block again. |
| `TerminalPaint` | Success | Use rechecks distance and visibility; only explicitly tagged hull slots receive private dynamic paint; untagged glazing retains its original material; repeat use advances the palette. |

Report totals: **3 succeeded, 0 succeeded with warnings, 0 failed, 0 not run**. These isolated test worlds do not establish full-map appearance, input feel, performance or the complete gameplay loop.

## Scripted play in the actual saved map

Receipt: `Artifacts/Outpost/Play/20260924T073319Z/runtime.json`.

- Result: **24/24 checks passed**, no recorded errors; status `PASS_SCRIPTED_MAP_ONLY`.
- Tested map SHA-256: `5db829dd68f5f20253a557450f1ba0c33e6d4da40535f9b97f30e01b993ae361`.
- Five rendered play images were recorded. The check named `runtime_frames` verifies those five images; it is not an FPS benchmark.
- Movement is injected through CharacterMovement. The actor starts at the authored PlayerStart; separate terminal, stair-bottom and boarding-bottom setups reposition it before each bounded scenario. No teleport was used during either measured stair ascent or measured cockpit walk.

The 24 named checks are retained here to make the pass scope explicit:

| Group | Checks |
| --- | --- |
| Startup | `sandbox_game_mode`, `native_walker_controller`, `spawn_at_authored_player_start` |
| Entrance and doors | `native_door_visual_inventory`, `forward_walk_through_entrance`, `walking_floor_support`, `door_automatically_opened`, `native_door_visuals_follow_opening`, `native_door_visuals_noncolliding`, `native_door_physics_preserved` |
| Ambient actors | `crew_animation_advances`, `crew_route_moved`, `drone_routes_moved` |
| Local previews | `ship_paint_applied`, `wardrobe_preview_access`, `wardrobe_preview`, `equipped_hero_unchanged` |
| Access routes | `natural_stair_ascent`, `natural_walk_to_cockpit`, `cockpit_freeflight_available` |
| Preservation and images | `saved_map_unchanged`, `save_files_unchanged`, `native_door_source_unchanged`, `runtime_frames` |

The scripted entrance walk covered approximately 53m. The gallery ascent reached all 36 route waypoints with no teleport after its bottom setup; the cockpit walk reached all six waypoints with no teleport after its ramp-bottom setup. These establish the specific sampled routes, not unrestricted navigation everywhere.

Paint changed seven opted-in hull panels in the sampled parked ship. The wardrobe projected the replacement Squirrel while leaving the equipped walker unchanged. Both actions are **sandbox previews**: this pass does not equip an account appearance or persist ship paint.

The save-preservation check found an **empty** sandbox `Saved/SaveGames` directory before and after the run. It establishes that this scenario created no save files there; it does not test preservation of an existing owner save or save/resume across map travel.

The cockpit check found the reachable `Berth/COCKPIT / FREE FLIGHT` terminal. The harness deliberately does **not** use a travel terminal, start Survival, continue a saved run or take flight. Those destination transitions remain unexercised by this receipt.

## Visual review — not accepted

Capture 8 receipt: `Artifacts/Outpost/Captures/20260924T073905748662Z/manifest.json`; launcher log: `Artifacts/Outpost/RoofCapture8.log`.

- **13 raw 1600×900 views** were produced; manifest status `CAPTURED_NOT_ACCEPTED`, no recorded capture errors.
- Captured map SHA-256: `083e0863cd72a080df8284685d59e4d47e770adba38ccff98434a051fe8bb2ac`; the saved map was unchanged during capture.
- This is a later map snapshot than the scripted-play hash above. Functional results are not silently transferred to every later placement change.
- Views cover exterior arrival, player pad, market promenade, entrance, atrium, Engineering, wardrobe lounge, arcade, Operations, visitor berths, planet archive, observation gallery and market mini-kits.

Independent inspection of Engineering and Operations still found dark furniture faces competing with bright ceiling pools, difficult-to-read detailed surfaces, and a presentation below the owner's reference/quality target. More geometry and actor counts do not establish acceptance. The full 13-view batch is capture evidence, not a visual pass.

Focused rejected hypotheses remain part of the record: hiding structural supports, disabling shadows, forcing two-sided materials, and changing realtime/camera warmup did not visibly remove the reported rough/chipped appearance. Realtime diagnostic runs emitted an engine realtime-override ensure; their images are observations, not clean execution passes. No claim is made that these unsuccessful trials fixed the defect.

An isolated ceiling comparison at `Artifacts/Outpost/CeilingRoundTripDiagnostic/20260924T074230385129Z` compared the original mesh with a 4,967-triangle fallback reimport. A subsequent full-source conventional-mesh image at `Artifacts/Outpost/CeilingSourceDiagnostic/20260924T074759924302Z` retained the broad relief with 867,568 triangles. The relief therefore appears in the source mesh itself; this does not prove the entire room's unattractive appearance has one cause. These diagnostic assets are private and do not establish a reason to overwrite vendor geometry.

At this checkpoint, downward area lighting was only a reversible sample. Its subsequent saved adoption is recorded under DensityFinish1 below, superseding pending-integration status without establishing visual acceptance.

## Later material comparison — bounded improvement, not scene acceptance

The untouched P3 demonstration reference at `Artifacts/Outpost/SourceComputerReference/20260924T081254421673Z/01_SourceComputer.png` retains visibly distressed metal but recognizable display graphics. An offline comparison found zero differences between all 127 selected source actors and their native export for position, rotation, scale, mesh and per-slot materials. That excludes corruption of those recorded source placements; it does not prove the final room has no spatial conflicts.

The previous generic emission clamp independently compressed each `Intensity EM` channel, destroying the vendor shader's relative image/effect balance. Existing native parameter evidence in `Artifacts/Outpost/NaniteDiagnostic/20260924T070031494093Z/state.json` identifies concrete examples:

| Graphic material | Native EM1 / EM2 / EM3 | Previous independent clamp | Common gain to peak 40 |
| --- | --- | --- | --- |
| `MI_Glass02_10` | 45,000 / 67,000 / 500,000 | 40 / 40 / 40 | 3.6 / 5.36 / 40 |
| `MI_Glass02_8` | 100,000 / 3,707,671 / 1 | 40 / 40 / 1 | 1.078844 / 40 / 0.00001078844 |

`Artifacts/Outpost/InteriorFinishComparison/20260924T082035571335Z/manifest.json` records four unsaved 1600x900 images on map SHA-256 `bac9e984a17e7750ee6e2535f2ab94c7e939a01cbcf76057a48ec379b0908b3b`. The first three use the same Operations camera. Source exposure and the common lighting/deck candidate stay fixed. The saved map hash remained unchanged; the manifest has no capture errors and status `CAPTURED_NOT_ACCEPTED`.

- `01_OriginalChannels`: restoring the original high emissive values causes severe screen bloom in this map's lighting/exposure.
- `02_PreservedRatios`: one common gain per original graphic material restores recognizable images without the original bloom; small source channels are scaled too.
- `03_CleanMetal`: exact owned non-`_Stains` P3 metal counterparts reduce some high-frequency speckling while retaining textured metal identity. The room still reads dark/distressed.
- `04_EngineeringClean`: the same bounded metal treatment was captured in Engineering; this is not acceptance of the workstation composition or whole room.

The lead reported process exit code 1 despite all four captures finishing. No Python error, fatal error or ensure was found in the reviewed log. The execution failure remains unexplained, so this is comparative image evidence, not a clean-run validation pass.

`OutpostInteriorFinishPreview.apply_clean()` is an idempotent component-material application scoped to Engineering and Operations in the private map or guarded fresh authoring world. It edits no vendor material or mesh and performs no save itself. Its later saved integration is evidenced by DensityFinish1 below; that supersedes this comparison checkpoint's pending-integration status, while whole-scene appearance remains unaccepted.

`OutpostEngineeringBacking.py` adds a separate mounted diagnostic-wall candidate: twelve owned kit pieces with native Graph1/Graph2 panes and matching frame pivots, electrical housings, uprights, cable headers and lamp meshes. Offline catalog bounds and exact asset paths pass: x3770..4630, y-4500..-4367, z30..395cm. It leaves Goliath, services, NPCs and floor routes untouched and adds no light actors. The helper checks actual transformed native bounds and frame/housing contacts when run. Those source checks were not a rendered or traversal pass. DensityFinish1 below subsequently applied and saved the twelve-part backing with native bounds checks; visual acceptance and a later full-map traversal remain separate.

## Saved density/finish and readability passes — applied, not visually accepted

The following receipts supersede the earlier **pending saved integration** statements for task-area lighting, private deck finishes, clean native metal and the Engineering backing. They do not supersede the failed comparisons or establish a new runtime pass.

| Saved pass | Pass receipt under `Artifacts/Outpost` | Saved map SHA-256 | Capture manifest under `Artifacts/Outpost/Captures` |
| --- | --- | --- | --- |
| DensityFinish1 | `density-pass-20260924T082854Z.json` | `9b979f9d1c38e743220729bf56a4aa4f2e67d4f76900e8d60138e05d550e4e60` | `20260924T082945261892Z/manifest.json` — 13 images |
| Readability1 | `readability-pass-20260924T084403Z.json` | `b5896562402469595f2ab362921a45f2d3468dab19a1d0ed0b011930e782a08c` | `20260924T084418949791Z/manifest.json` — six images |

Both manifests record raw 1600×900 images, no capture errors, unchanged source maps during capture and status **`CAPTURED_NOT_ACCEPTED`**. Native launch orchestration observed **exit 0 for both processes**; exit status is separate evidence and is not a field in these manifests. `DensityFinish1.log` and `Readability1.log` each record `PASS_AUTHOR_TIME_ONLY` with zero failures and zero deferred cases. These are placement probes, not a repeat of the 24 scripted-play checks.

DensityFinish1 applied 200 atrium parts, 69 promenade parts and the twelve-part Engineering backing, then passed the promenade's 11 route/22 floor probes. It adopted 19 downward task-area lights while hiding the original point emitters, applied 12 private floor/ceiling materials across 6,293 slots, and replaced 1,982 explicitly scoped P3 metal slots with four owned clean variants. The vendor-light pass changed 154 components, reduced shadow-enabled local lights from 165 to 16, and preserved original intensity units/values. Its conservative radius-sphere overlap estimate fell from 33 to 2; that model is **not** an actual VSM pixel count or performance result. Six existing market task lights were reused. The arcade received its private Nanite-compatible material, with the original material hash unchanged (`80167af982ba782e931a9eab8ca04b4c33b460cd24eb2daaac0a46296091b2bd`).

Readability1 saved the 73-part entrance refinement, raised the 13-metre globe to centre Z1170/bottom Z520 with lower halo Z560, and added **seven rear information faces at this checkpoint**. It added 13 local shadowless fills, reduced 39 task-light components' specular contribution and applied a separate warm material to three fixed archive projections. All 57 authored text actors received gain 4 through two private text materials, preserving the original font/alpha graph and the observation signs' one-sided rendering. The engine text source hash remained `19f3713406a78b0fb2c924181fd0d63750b237e49b78a39c6f2abab1fd9c743a`. Its six captures cover entrance, atrium, Engineering, wardrobe lounge, Operations and gallery. Later fourteen-face kiosks, distant-world and skyline-display changes are not validated by this saved receipt.

Focused scans of both logs found no `Error:`, fatal error, ensure failure, Python traceback or VSM one-pass overflow message. DensityFinish1 still recorded the original arcade's missing-Nanite-usage warning while initially loading the pre-repair map; preserve that warning even though its later private replacement passed the receipt's usage/source-hash guards. Both processes retain the three ShipCore startup/shutdown warnings. Absence of the VSM warning in these bounded captures does not establish representative performance or all-camera coverage. Native rendering and owner aesthetic acceptance remain **NOT MET**.

## TemporalCompare1 — rejected screenshot-delay diagnosis

`Artifacts/Outpost/TemporalCompare/20260924T085312253974Z/manifest.json` records two raw 1600×900 Operations images on saved map `b5896562402469595f2ab362921a45f2d3468dab19a1d0ed0b011930e782a08c`: `01_Default4` and `02_Accumulated64`. Both use camera `(6750, -240, 185)`, target `(8130, 100, 200)` and FOV82. The script changes **`r.HighResScreenshotDelay` from 4 to 64**; it does not establish that a gameplay temporal-quality setting was repaired.

Matched image review found no meaningful correction to the dark/chipped, fragmented-looking detailed surfaces. This hypothesis is rejected as a fix. The manifest records no errors, unchanged saved-map hash and `CAPTURED_NOT_ACCEPTED`; launch orchestration observed exit 0. `TemporalCompare1.log` has no error/fatal/ensure/traceback/VSM-overflow match and retains the three ShipCore lifecycle warnings. The comparison changed no saved scene assets and establishes neither visual nor performance acceptance.

## Vista1 — failed material-pin invocation retained

The subsequent `Artifacts/Outpost/Vista1.log` records a Python `AssertionError` in `OutpostDistantWorld` when connecting the Clamp expression using the pin name `Input`. `LogEditorPythonExecuter` explicitly reports that the script executed with errors. The lead observed process exit 0 and the map still at `b5896562402469595f2ab362921a45f2d3468dab19a1d0ed0b011930e782a08c`; **Vista1 is a failed authoring attempt despite that exit code**. Installed engine graph naming maps the Clamp input to the empty name. A source correction was prepared, but this failed run supplies no saved distant-world or visual acceptance evidence.

## Saved vista, hologram and surface refinements

Vista2 applied the corrected material pins and saved map `90cc7f5b701ba20d97dc42942f08fd5dd984340f16fc79780c2998db3c30f042` (`vista-pass-20260924T090054Z.json`). It includes fourteen text faces across seven kiosks, a decorative 320m blue world, 26 native skyline display pairs and the first rim/scan archive material. Its 13-view manifest is `Captures/20260924T090103997593Z/manifest.json`, with no capture errors and an unchanged saved map. **The process returned -1073741819 after its shutdown log; this is saved/captured evidence, not a clean execution pass.** The reviewed log contains no error/fatal/ensure/traceback explaining that exit.

RoomFinish1 then failed before saving because the material helper treated the scalar setter's false return as failure. Installed UE5.8 `MaterialEditingLibrary.cpp` lines1485–1493 always return false after executing the scalar assignment. The correction validates actual parameter readback; it does not suppress a failed assignment. Preserve `RoomFinish1.log` as a failed Python attempt despite process exit0.

RoomFinish2 completed with **exit0**, saved `968c44412aa5c9f9ee6c6d8b44919cd86141760da1fa65986bf77bfbddfacf8f` (`roomfinish-pass-20260924T091134Z.json`), and captured Engineering, wardrobe and Operations in `Captures/20260924T091141344136Z`. Exactly ten panes/twenty slots use verified native graphic or clear-glass derivatives; source hashes and inherited textures remain unchanged. Three archive figures now use a faint body, brighter Fresnel rim and moving horizontal scans. Independent review confirms recognizable figures and selected instrument graphics, but other panes remain dark, small or occluded. Material assignment is verified; whole-room display readability is not accepted. This run's clean-panel ceilings exposed glossy undersides and were rejected for that appearance.

SatinFinish1 corrects those panels' orientation and surface finish. It completed with **exit0**, saved `2043e031c421c260b354e5e52a0a12f5533c26ef9491e7bfe70ea307dae54e53` (`satinfinish-pass-20260924T091802Z.json`), and captured four affected views in `Captures/20260924T091807554975Z`. Forty-six clean ceiling panels face their relief downward, preserving their previous transformed bounds and structural clearance. Sixty-eight perimeter kit panels remain. Twenty-six smooth promenade panels replace the rendered central strip at Z0; forty original decorative tiles remain hidden. The underlying walking collision, vendor assemblies, guidance and NPC placements are unchanged.

The two satin derivatives retain the owned textures/colors and set inspected roughness channels to0.72, cap metallic channels at0.45, and render both sides of the turned ceiling tray. Native source material hashes remain unchanged. Eleven promenade capsule samples and22 floor probes pass, and the capture's broader author-time audit reports zero failures/deferred checks. Raw image review confirms a clearer central path and framed ceiling relief without the prior mirror-like underside. This is a bounded visual improvement, not AAA acceptance.

RoomFinish2 and SatinFinish1 manifests record no errors, unchanged maps during capture and `CAPTURED_NOT_ACCEPTED`. Their reviewed logs contain no error/fatal/ensure/traceback. These later decorative/material passes do not repeat or expand the older24-case scripted-play evidence. Existing worn workstation surfaces, dark or occluded displays, natural play and performance remain open.

## WorkstationFinish1 and ReloadReady1 — saved material correction and load readiness

`WorkstationCompare1.log` completed with exit0 and four raw matched-view images at `Artifacts/Outpost/WorkstationCompare/20260924T092715449439Z`. Map `2043e031c421c260b354e5e52a0a12f5533c26ef9491e7bfe70ea307dae54e53` remained unchanged. Direct native inspection confirmed the original Access01 material already had `Activate Cov1=true`: its cleaned base was covered by the kit's damaged texture layer. Disabling that layer reveals the graphic; a common8x gain preserves its three image/effect channels. This is a material finding, not an incorrectly rotated workstation. The comparison also exposed three immediate post-load market collision-probe failures; its capture manifest did not yet incorporate the placement result, so its clean process exit is not a placement pass.

A first standalone flag inspector failed on the unavailable Python `creation_method` property (`InspectMarketReload.log`, process exit0 with Python error). The replacement inspector explicitly records unavailable bindings and retains native trace evidence.

`WorkstationFinish1.log` completed with exit0. Receipt `workstationfinish-pass-20260924T093533Z.json` identifies saved map **`4c277b736bc903e3917c4344f2b081ab405531e60a0644b1a5de26c4bff910d2`**, and `Captures/20260924T093538607298Z/manifest.json` contains one raw Engineering image, no errors and unchanged map during capture. The helper preflights29 actors/42slots, then assigns three private material children to three confirmed cleaned-base/damaged-overlay slots. Only Access01 additionally changes EM1/EM2/EM3 from1/1.5/1 to8/12/8. Parameter readbacks, native source hashes and geometry/collision guards pass. The brown obstruction is removed and the central graphic is visible; the room's broader finish remains below the target.

The immediate `market-reload-flags.json` inspection found all three selected instanced components already set to `BlockAll`, Pawn=Block, QueryAndPhysics, actor collision enabled, with their expected instances and simple collision elements; their rays initially missed. `market-warmed-flags.json` records all three hitting after normal editor processing, without collision or geometry mutation. This is a loading-readiness issue in the author-time diagnostic, not evidence that replacing collision geometry repaired anything.

Installed UE5.8 `AutomationBlueprintFunctionLibrary.cpp:702-733` shows `FinishLoadingBeforeScreenshot` flushes async loading, finishes asset compilation and streams resources. Installed `InstancedStaticMesh.cpp:4733-4735` disables physics-state creation while the mesh compiles; `StaticMeshCompiler.cpp:413-417` and `StaticMeshComponent.cpp:3322-3340` recreate component collision after compilation. The author-time validator now invokes that engine barrier before its first trace. **ReloadReady1**, a fresh hidden native process, completed with exit0: `reload-ready.json` records before-barrier probes `[false,false,false]`, after-barrier probes `[true,true,true]`, `PASS_AUTHOR_TIME_ONLY` with zero failures/deferred cases, and unchanged saved map4c277b73. No retry-until-pass loop, flag toggling, added blocker, reduced test or level save was used. `reload-ready-placement.json` preserves the full audit.

Each new capture now keeps its placement audit in the capture directory and records its status/counts in the manifest. A failed/deferred placement audit causes a failed capture status rather than being lost in an overwritten shared receipt. WorkstationFinish1 and ReloadReady1 logs contain no Python error/fatal/ensure; retained earlier failed attempts remain above. The diagnostic barrier does not establish runtime performance or natural walking acceptance.

## Bounded native source review and remaining gates

A read-only review of `SSOutpostSandbox.cpp/.h` and the `SSGameMode.cpp` OutpostEntry addition found no additional confirmed critical defect in the inspected terminal, door, ambient movement or local-preview paths. This is source review, not proof of runtime behavior beyond the checks above.

The source routes explicit `OutpostEntry=LaunchMenu` and `OutpostEntry=FreeFlight` through the existing gameplay entry points; ordinary game startup retains its title-screen branch. Native travel, destination controller behavior, preservation of a populated survival save, and return flow still need a focused exercise. The sandbox pause/input code was inspected but physical keyboard/mouse/controller operation was not established by injected movement.

Still unverified or unaccepted in this record:

- Owner acceptance of the scene's composition, materials, lighting, atmosphere and density.
- Physical input, pause/resume and natural free exploration through all rooms and services.
- End-to-end terminal travel, cockpit seat/takeoff, Survival start/continue and preservation of a populated save.
- Representative runtime performance, frame pacing, audio review and packaged behavior.
- Any map/lighting/placement candidates authored after the identified play/capture snapshots.

Active priorities and closure decisions remain in [KNOWN_ISSUES.md](../KNOWN_ISSUES.md); source/build/release distinctions remain in [PROJECT_STATE.md](../PROJECT_STATE.md). This receipt does not declare Phase 1 or the outpost redesign complete.
## Source and draft-handoff checks

Final scoped checks on September24: `CheckProject.py` passes38structural checks; `ValidateSources.py --check-only` passes26meshes/17WAVs and unchanged GLB; `TestOutpostReadability.py` passes4tests; `CheckPrDocumentation.py` passes repository navigation/counts and the exact prepared PR body; `git diff --check` passes. The first compileall invocation could not write a Python cache through the restricted worktree junction; rerunning with scoped workspace permission passes `python -m compileall -q Scripts ContentSource`. No code workaround or dependency installation was used. Native runtime source remains identical to the three pinned hashes above, so EditorBuild5 and its three-test results remain the applicable compile/native checks. No repeated full gameplay suite or package was run.
