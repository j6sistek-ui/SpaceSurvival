# September 21 flight-loop reset validation

Status: **PARTIAL — Build 17, full flight suite clean.** A clean complete project automation run, station visual acceptance, natural play and owner acceptance remain open.

The candidate is the isolated `codex/flight-loop-reset` worktree, based on `684db34` (PR #58). Draft [PR #59](https://github.com/j6sistek-ui/SpaceSurvival/pull/59) remains at `111c011`; later editor builds include uncommitted repairs and must not be attributed to that commit. Licensed derivatives are local assets, not a GitHub download. Original vendor assets are preserved. No merge, package or itch update is recorded for this reset. [KNOWN_ISSUES](../KNOWN_ISSUES.md), RPT-20260921-01, owns current work and acceptance.

## Connection and diagnosis

The existing Nwiro endpoint `http://localhost:5353/mcp` negotiated protocol `2025-03-26` and identified `nwiro 1.0.0`; `tools/list` returned 482 tools. The first tool call listed the skill library; the next fetched BlueprintBasicsSkill, DefaultOutdoorLightingSkill, MaterialBasicsSkill and UnrealSkillBestPracticesSkill. Inspection identified SpaceSurvival in UE 5.8.2 with PIE stopped. This verifies local HTTP MCP access; the chat's native inventory did not expose Nwiro. Receipts are in the original checkout's ignored `Artifacts/McpReview`.

Repository onboarding, CLAUDE, GAME_SCOPE, IMPLEMENT and relevant project-adapted gameplay/debug/C++/Blueprint skills were read. Installed engine and ShipCore source supplied version-specific API checks.

Confirmed defects included bypassing the supplied Blueprint hierarchy, holding the main animation at its last frame, a muzzle inside the larger hull, landing guidance aimed at the hub origin, minimum-speed braking in the station zone, launch respawn and boost force after domain rejection. Testing also exposed undersized flight collision, oversized parked-foot collision and stale thruster timing. The owner's original runtime remains unconfirmed; these findings do not establish one cause for every reported symptom.

## Build and automation history

| Checkpoint | Result and retained evidence |
| --- | --- |
| Initial compilation/controller | Comparator and fixture API errors repaired; builds 4/5 passed in 5.20s/22.51s. First ControllerToPhysics run reached real mouse yaw/pitch 36.69°/18.26° and gamepad 42.64°/16.55°, but failed on raw vendor demo references, AirBrake metadata and an invalid fixture LocalPlayer outer. `Artifacts/ControllerTests/index.json`. |
| Presentation authoring | First dry run stopped on an animation-data API assumption before saving. Revision 2 later compiled and retained all 30 supplied scene components, with original Blueprint/AirBrake bytes preserved. |
| Builds 7–8 | Build 7 passed in 11.59s. `ControlRigTests2` had four assertion passes carrying initialization warnings and one parked-collision failure. Pre-registration defaults and measured gear collision replaced those assumptions. Build 8 passed in 17.15s; `GearGeometryTests` passed 1/1 cleanly. |
| Builds 9–11 | Builds 9/10 failed on a test-only const API mismatch and missing PhysicsCore dependency; both repaired. Build 11 passed in 22.62s. |
| Build 12 | Passed in 26.13s. `ResetIntegrationTests1`: **8/8 clean**, covering hull hazards/projectiles, physical hull collision, docking admission, asteroid/station collision, staff and wardrobe. Real wing impact reached 64.14°/s before gyro recovery; mass, centre-of-mass and inertia assertions passed. |
| Full suite 1 | `ResetFullTests1/index.json`: **78 clean passes, 8 failures, 0 omitted** of 86. Failures: BoostBrakeMovement, DirectionalDodgeCollision, ProjectileRelativeMotion, StationDeparturePause, AcceleratedTenWaveJourney, ShipPresentationSelection, StationServiceLabelView, PhoenixParkedCollision. |
| Build 13 | Passed in 19.19s. `ResetRegressionTests2`: **6 clean passes, 1 failure**. Brake, classic projectile, departure-pause, journey, hull-selection and label checks passed after repairs. Dodge still failed its conservative rotated-box oracle. |
| Build 14 | Passed in 26.34s. Actual convex-support dodge assertions passed in the subsequent full run. Private parked physics and asteroid material authoring completed. |
| Full suite 2 | **CRASHED; no final report.** `BuildLogs/ResetFullTests2.log` records ContactImpactResponse failure, then successful pause and accelerated-journey assertions. After AlienGalleryLifecycle teardown, garbage collection asserted `UObjectArray: Index >= 0`. |
| Triage 3 | `ResetTriageTests3/index.json`: **2 clean passes, 1 failure**. Isolated AlienGalleryLifecycle and PhoenixParkedCollision passed. All three exact-foot world capsule sweeps, clear starts, neighboring walking space and retained hull/ramp checks passed. ContactImpactResponse failed. |
| Build 15 / Triage 4 | Build passed in **11.50s**. `ResetTriageTests4`: **5 clean passes, 1 failure**. ClassicProjectileRelativeMotion, HullHazardContacts, HullProjectileContacts, AlienGalleryLifecycle and strengthened PhoenixParkedCollision passed. ContactImpactResponse failed. StationDeparturePause was not selected. |
| Build 16 / Triage 5 | Build passed in **8.15s**. `ResetTriageTests5`: **2 clean passes, 1 failure**. StationDeparturePause passed including immediate forced garbage collection, followed by AlienGalleryLifecycle. ContactImpactResponse retained a 30Hz-versus-120Hz forward-recovery discrepancy. |
| Build 17 / full flight suite | Build passed in **10.52s**. `ResetFlightTests6/index.json`: **24/24 clean, zero warnings/failures/omitted**. Includes controller-to-physics and after-takeoff control, boost/brake, frame-rate trajectories, hull hazards/projectiles, directional dodge, manual weapons, contact/swept-impact response and departure pause with forced GC. Contact response at 30/60/120/144Hz was exactly (0, −600, 0) cm/s, with quarter-second residual Y −209.963cm/s at every rate; original test tolerances were retained. |

The full-suite crash was traced using saved module offsets and installed Engine DLL exports to `FSubsystemCollectionBase::Deinitialize`, its destructor and `ULocalPlayer::~ULocalPlayer`, during garbage collection. Registering the pause fixture's local player initialized subsystems, but teardown omitted removal before destroying the world. Engine source requires deinitialization before UObject destruction. The fixture now removes its player first and explicitly collects garbage in StationDeparturePause. Triage 5 verifies this repair and the following gallery test; it does not replace a fresh complete run. Crash artifacts remain under `Artifacts/ResetFullUser2/Saved/Crashes/UECC-Windows-B995F3FB4218AEF1B507069891B63C70_0000`.

The contact/flight repair aligns thruster force application before physics, samples hazard motion after physics, and applies the contact velocity delta immediately. The native adapter now supplies bounded XYZ velocity-error commands through ShipCore instead of combining cruise trim with its zero-speed dampeners. The old combination alternated full braking and released braking around zero trim, depending on frame rate. Exponential response removes that discontinuity while retaining the actual rigid body, calibrated mass, force limits and gyro control. Build 17's complete flight suite validates these assertions; natural feel remains a separate gate.

Earlier portable/source checkpoints passed **766 MSVC strict C++17 domain assertions**, **35 structural checks**, **13 source-digest tests**, Python compilation and content-source validation (26 meshes, 17 WAVs, original GLB unchanged). Documentation checks passed then. Docker was stopped locally; local GCC/ASan/UBSan were not run. PR #59 at `111c011` passed container core and documentation jobs; its source job stopped on two inherited formatting differences, subsequently corrected locally. These historical checks do not validate later uncommitted changes.

## Phoenix assets and verified collision

Private `BP_PhoenixPresentation` preserves the supplied scene hierarchy while removing broken demo gameplay. Its revision-2 author disabled physics/collision/autostart defaults before registration and saved corrected private AirBrake data. Native tests exercise the actual rig and authored three-second landing/takeoff sequences. The native ship remains the flight authority.

| Private output | Measured scope and SHA256 |
| --- | --- |
| `DA_PhoenixFlightHull` | **11 shapes**: nine retained rigid hull shapes and two bounded nacelle envelopes. Three deployed-foot envelopes and open ramp excluded. Additional geometry welds into the calibrated root body without contributing mass. `f0651be8c446d9b41115290e7b4135eca7bf075a067229a390417f7f315c6464`. |
| `PA_PhoenixParked` | **10 original shapes** retain hull, mounts and deployed ramp; only oversized foot boxes **0, 10, 11** removed. **24 measured bone-attached part bounds** own animated gear contact. `4171a5c02e718da6909a75971f58065720dc0ebca332e25c9b5836640968e2a3`. |

Both live under `/Game/SpaceSurvival/Licensed/PhoenixPresentation`; receipts are `Artifacts/PhoenixPresentation/flight-hull-author.json` and `parked-physics-author.json`. Four flight inputs and both parked inputs were hash-preserved. Original PhysicsAsset SHA: `d983774bf4a08661cb19243842e8b96c5a63cc132fc2f188e2c5766c56198b79`; skeletal mesh SHA: `4a2b902bfa283124798c8a2f5aded96cb89d71da302c8d790d6719ac10be0134`. Runtime overrides the parked component's PhysicsAsset, leaving its source mesh unchanged.

The raw front-foot envelope spanned about **970cm** across a visible foot about **92cm** wide. Actual deployed vertices set Phoenix dock clearance to **2.5cm**, replacing 230cm. Triage 3/4 verify grounded feet, exact-foot walking contact, clear adjacent space and removal of parked collision before takeoff. The strengthened posed-triangle check rejects absent geometry and positively locates front-foot triangles at deck height before checking the neighboring clear column. This does not promise standing headroom everywhere beneath the fuselage.

StationPhoenixPaintCapability passed in full suite 1. Phoenix materials expose no supported per-section color controls; the service reports factory finish unavailable for customization and rejects disabled/stale choices before account mutation. Classic account colors remain intact. A Phoenix paint shader remains open.

## Asteroid station and rendered review

Revision-3 asteroid authoring preserved the Photo 5 source SHA `d816fe0e57174bcd50f9cc733489117adc48f2078a538e1bc7e29cf2bec399b9`. Its **5,464,576 source/Nanite triangles** differ from the old 23,194-triangle fallback. Private editor source remains available; cooked Nanite geometry is **500,640 triangles**, with a separate **150,192-triangle** double-sided ComplexAsSimple fallback preserving the hollow bowl. Geometry-output SHA: `f8df964cd725b624b1bc95cb6ace8e40c7efa5816e3e8bed662c6ab1849fdb77`.

The first transient 500k reduction stopped at an unavailable factory API before saving; 20k/50k/100k collision targets failed the fixed 1cm source-scale tolerance. The accepted fallback preserved all 175 sampled ray-hit states, maximum surface delta 0.773376cm and bounds delta 0.170021cm. At scale 145 the sampled displacement reaches **112.14cm**; sparse probes are not complete fidelity proof. Placement inspection checked 213 room/terrace samples and two cameras/target rays against built collision, with unchanged bytes. Native asteroid collision passed in the Build 12 focused run.

The first `BP_StationReset` compiled with **239 meshes, 30 box specifications and 10 services**, SHA `8de7710029369967b95ed2d7fb134bc95f2b403eb601414b393b512f0eb041ad`. Original station SHA `ea4484a491c2d47ff04a01f88e64aef688ac303bd1bcf56529623d9fcb5ba02c` was preserved. These counts describe that authored revision, not later recipe edits.

Station5 render **`351c8cbd27704d1ea843530265768460`** passed functional/integrity checks: scripted ordinary approach and `GameMode.Interact` docking request, approximately 2.99s docking, Squirrel standing on deck for 25s, zero off-deck rescues, no save-slot writes, actual Phoenix metadata and hidden fallback confirmed. It used seeded progress, upgraded equipment and enlarged durability; it is not natural progression or physical input.

**Lead and independent review rejected its visual quality:** overlit tan rock, light sculptures reading as consoles, and crate-like terrace structures. Functional success does not close that rejection. Console/UI pairs, bay details and colony architecture are being revised; another authored/rendered review is required.

Private rock material `/Game/SpaceSurvival/Licensed/StationReset/Materials/MI_StationAsteroid` was subsequently authored: brightness 0.18, saturation 0.1, tiling 2.5, roughness 0.65–0.95, specular 0.25, metallic 0, tint (0.55, 0.7, 1). Output SHA `c3a134c090cf516d5c0248d5902b6e3e792b225877384b3a043fcf0709f394af`; source SHA `48299379a1ed0cd3b726ccf7c8b152b69e8e498295f326156cd7045ec0eea4c5` preserved. `Artifacts/StationAsteroid/material-author.json` proves authoring, not visual acceptance; the rejected capture predates the correction.

Earlier Wave1 capture `2faa0187356c4471b1b013cccf812b3d` showed the full Phoenix and brake deployment. Its receipt incorrectly named the hidden fallback; later station metadata corrects that field. The older images remain evidence only for their captured revision.

### Revised station authoring and full suite 3

Build18 passed in1.93s after restricting NwiroIntegrationKit and UAssetBrowser to Editor targets; runtime gameplay was unchanged from Build17. Colony import completed with source preservation:307,944 Nanite triangles,46,918 fallback triangles, two PBR materials/six2K textures, dimensions15.24x18x10.67m and base pivot. Mesh SHA `8b8403de24faf61ebcf68eac44a076e25d8bafe32aac1aa12db0126b44ae3141`. Original Figur Blender SHA `3913fd79109fa0fa086e50fa1b35f14f15b585c1b3d1ce07086bea277a3ced72` remained unchanged. The private derivative removes the hanging mast beneath the ring; the source is retained.

Station author cycle2 saved282 meshes,45 box specifications and10 services, SHA `c3962ab9e152ccda42792c4816a66c524a847c10bb55dcb284c640cf2d6ff1b9`; original station bytes preserved. This includes actual curved console/UI pairs, distinct service bays, localized warm lights, gray rock override and grounded rounded buildings. No revised visual pass yet.

`ResetFullTests3` completed84/86 clean, two failures: AcceleratedTenWaveJourney (pad exit support/fallback) and StationResetCollision (expected native identities/bridge barrier). The same-binary `ResetStationTests7` passed Journey alone but repeated collision failures; this does not close the order-dependent arrival fault. Diagnostics and fixes remain in progress. Source36, recipe8, digest13, Python compilation/content-source checks, cook coverage129paths/35roots/no gaps and native formatting passed at this checkpoint.

## Evidence limits and remaining gates

- The complete flight suite is clean, including contact recovery across frame rates. A fresh complete project automation run after all repairs remains pending.
- Synthetic input traverses the real controller, PlayerInput and ShipCore/Chaos, but its fixture lacks a ViewportClient and bypasses production GameMode BeginPlay. Physical keyboard/mouse/controller use, Slate focus, capture, menu return, comfort and flight feel remain unverified.
- The accelerated ten-wave journey and seeded station capture disclose shortened phases, forced/seeded objectives, fixture positioning or durability changes. A complete natural Waves 1–10 run, both station visits, ordinary arrival/departure, save/resume and death-to-next-run acceptance remain open.
- Updated station appearance, synchronized listening, representative 60 FPS performance, final cook/package, clean-machine launch, release/update behavior and owner acceptance remain open. Offscreen screenshots and reduced triangle counts do not establish those gates.
