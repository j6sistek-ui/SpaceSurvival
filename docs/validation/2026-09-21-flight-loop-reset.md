# September 21 flight-loop reset validation

Status: implementation and validation in progress; no natural-play or owner-acceptance claim.

The candidate is `codex/flight-loop-reset`, based on `684db34` (PR #58), in the isolated `flight-loop-reset` worktree. This receipt concerns the new source and its own editor binaries. The original checkout's running editor, packaged game and itch release have not been updated. The canonical active report is RPT-20260921-01 in [KNOWN_ISSUES](../KNOWN_ISSUES.md).

## Connection and source diagnosis

The existing local Nwiro endpoint `http://localhost:5353/mcp` successfully negotiated protocol `2025-03-26` and identified `nwiro 1.0.0`; `tools/list` returned 482 tools. The first tool call listed the skill library and the next fetched all four skills: BlueprintBasicsSkill, DefaultOutdoorLightingSkill, MaterialBasicsSkill and UnrealSkillBestPracticesSkill. Project inspection identified SpaceSurvival in UE 5.8.2, with PIE stopped. This is a verified local HTTP MCP connection; the chat's native tool inventory did not expose Nwiro. Ignored connection/inspection receipts remain under the original checkout's `Artifacts/McpReview`.

Repository onboarding, CLAUDE, GAME_SCOPE, IMPLEMENT, project-adapted gameplay/debug/C++/Blueprint skills and relevant live skill guidance were read. Installed engine/plugin source supplied the version-specific API checks. Deep-space lighting defaults were preserved.

Confirmed defects included bypassing the supplied Blueprint hierarchy, holding the main flight animation at its last frame, an obsolete muzzle inside the larger hull, a hub-origin landing marker rather than the pad, minimum-speed braking inside the station zone, launch respawn, and raw boost force after domain rejection. The owner's exact original runtime remains unconfirmed. No single source finding is claimed to explain every reported symptom.

## Checks completed before final integration

- Initial compiler attempts exposed a UE pointer-array comparator mismatch and two new fixture API/type mistakes. These were corrected; Editor build 4 passed in 5.20 seconds and build 5 passed in 22.51 seconds. Those checkpoints are superseded by the final integration checks below.
- Native MSVC strict C++17 `/W4 /WX` domain run passed **766 assertions**, including station-departure boost consumption without wave advancement and rejection for an inactive run. Docker was stopped; local container GCC/ASan/UBSan were not run. Existing CI remains the container gate.
- Source structural checks: **35 passed**. Source digest tests: **13 passed**. Python compilation and content-source validation passed (26 meshes, 17 WAVs, unchanged original GLB). Canonical documentation checks passed at this checkpoint.
- The first `ControllerToPhysics` run failed overall. Mouse and gamepad behavioral assertions reached real physics rotation (mouse yaw 36.69°, pitch 18.26°; gamepad yaw 42.64°, pitch 16.55°), but loading the raw vendor Blueprint produced missing demo projectile/occupant compile errors and an AirBrake data-model warning. The fixture also exposed an invalid LocalPlayer outer; corrected to the engine. This failed run is retained at `Artifacts/ControllerTests/index.json` and `Artifacts/BuildLogs/ControllerTests.log`.
- The first presentation-author dry run preserved the source bytes and inventoried its component hierarchy, but stopped on an animation-data API assumption. No derivative was saved by that attempt. Its receipt is `Artifacts/PhoenixPresentation/dry-run.json`.

## Final integration checks

Editor build 7 passed in 11.59 seconds after correcting a missing Director include in the new station fixture. The first clean-derivative integration run (`Artifacts/ControlRigTests2`) performed five tests: controller-to-physics, controller-after-takeoff, Blueprint hierarchy and animation transitions passed their assertions, but all four carried runtime initialization warnings; parked collision failed because the supplied PhysicsAsset has one Body_Bone and no separate gear bodies. These are retained failures, not a clean gate. Narrow gear geometry/grounding inspection and pre-registration component-default repairs are in progress.

The first offscreen normal-stat Wave1 sequence (`Artifacts/EndgameSoak/2faa0187356c4471b1b013cccf812b3d`) completed with four stage views plus motion samples. Raw views visibly show the full Phoenix hierarchy and deployed airbrakes during braking. The old receipt hull field names the hidden Havolk fallback; this metadata defect is being corrected before final captures. No natural-input or performance acceptance follows from the scripted capture.

Editor build 8 passed in 17.15 seconds. The isolated `GearGeometryTests` run passed 1/1 cleanly against the revision-2 presentation derivative. Measurement of actual rigidly weighted gear vertices found the feet within 2.5 cm of the ship pivot when deployed, rather than the old 230 cm clearance. The subsequent native changes use 24 narrow bone-attached gear bounds, a 2.5 cm pad clearance, and scale the supplied landing/takeoff clip sequences to the native three-second transitions. These subsequent changes still require the next build and integration run.

The presentation author receipt records revision 2 complete, successful Blueprint compilation, all 30 supplied scene components retained, and original Blueprint/AirBrake bytes preserved. Component physics/collision/autostart defaults are disabled before registration, correcting the warnings from the earlier integration run. The private output is local licensed content, not a repository download.

The exact Photo 5 asteroid has 5,464,576 source/Nanite triangles; its 23,194-triangle fallback is not the full source count. A separate 500,000-triangle derivative is being generated with sampled cavity/silhouette checks, retained UV/material bindings and no scenery collision. Uniform world scale alone is not considered a geometry optimization. Author completion, derived placement inspection, station authoring, clean integration tests and rendered colony/arrival review remain pending.

The live material inspection found no exposed vector/color controls for Phoenix's four paint sections. The paint service now declares factory finish unavailable for customization and rejects disabled/stale choices before account mutation, rather than changing only the invisible classic hull. Existing classic-hull account colors are preserved. A dedicated capability fixture is written but awaits the next engine run; a Phoenix paint shader remains open work.

## Evidence limits

Synthetic raw input passes through the real player controller, PlayerInput and ShipCore/Chaos; it does not represent a person using a physical device. Scripted station fixtures explicitly request docking through normal interaction after reaching admission, and disclose any fixture positioning. Offscreen rendering does not validate representative frame rate, listening or natural gameplay. Physical input/comfort, a complete natural Waves 1–10 run, package/cook, clean-machine behavior and owner acceptance remain separate gates. The small native physics sphere still needs a coordinated hull-shape/query follow-up; enlarging it at the current pivot would intersect the pad.
