# September22 arcade flight baseline

Owner approved left-stick nose steering, right-stick camera, bumper tap sideways dash/bank and hold fast roll. Acceleration/steering/response increased; ordinary cruise remains60m/s and engine-off coasting remains. Asteroid launch-only belt replaced by deterministic500m cells:2048 rocks/debris in shared mesh batches,125 resident cells,900m draw distance, stable nearby instances, exact regeneration on revisit, solid physics/shot collision. Director budget/difficulty and orange3x hazards unchanged.

Editor builds1/2 passed. Focused1: ControllerToPhysics, DistantAsteroidIsolation and MenuBackBoostRelease pass; ControllerTestingPreset initially failed because vendor roll shaping attenuated the authored rate. Adapter now sets roll multiplier1; Focused2 passes that case. First failure retained under Artifacts/ArcadeResponse. The test observes actual physics movement, tap bank/return, sustained roll, camera independence,9km world travel/all six directions, reachable shot collision, deterministic revisit and rebasing. Synthetic input is not physical-controller feel acceptance.

Owner defers character work. Read-only light review found combined squirrel50508vertices/1section, segmented110734vertices/9sections, neither with tail bones; no rig, selection or deletion performed. Caped character remains reserved. Owner map actor-removal edit is retained in this baseline.

Package8/source89b1f3c built successfully in2m16s (0cook errors/1known warning). Inner EXE SHA b23859ceff3286c7e8e341aa5139218f14659882105a753e40e5e561b4462e87. Auditf877c6ced1a34860b803d7c1e9bac2ea passes350frozen inputs,158exports/372dependency closure;53archive files/5628135247bytes.

Single packaged flight capture1a84862919ce444fafdf1092580781fe produced four reviewed frames at5/12/19/25s: gray world rocks visible ahead and through the turn, orange Director hazards distinct, Phoenix rig and prior HUD present. Capture FAILED: the scripted pilot never fires/dodges and died before the29s endpoint (wall26.887s). No crash; process0, save preservation and artifact identity guards pass. This failure remains a balance/acceptance limitation, not a passing survival test. No repeated capture or full-panel validation was used to hide it.

Final controller measurements:40.44degrees yaw in0.5s, bumper tap29.16degree bank/10m lateral travel; held right80.12degrees and left79.73degrees over0.75s. Tap levels afterward; sustained roll holds attitude. These are fixture measurements, not owner feel acceptance.

Authorized itch release0.1.21-alpha payload prepared as51files/5223849464bytes; dry-run passes. Publication is being recorded separately. No full-suite rerun, natural ten-wave acceptance, listening or representative performance claim. Earlier GPU-memory warnings and boarding/art/animation follow-ups remain open in KNOWN_ISSUES.

## Density correction before publication

Owner rejected the first sparse field and requires tradeoffs before density/quality changes. The0.1.21-alpha upload was interrupted at about10percent; butler status still reported live0.1.20-alpha/build1993461. Prepared0.1.21 payload remains immutable and is not the replacement candidate.

The correction shrinks field cells from800m to500m at the same2048-object budget (about4.1x objects per spatial volume), restores baked Arch/Globular/Linear Blueprint patterns and places the existing regional debris/panel/beam assets into approximately one third of nearby slots. Fixed position/scale, collision and deterministic revisit remain. The rendering tradeoff is more on-screen coverage; no representative FPS acceptance is claimed. Focused field regression passes after both debris and cluster changes. Raw editor frames eee7488a show nearby grouped rocks and wreckage across cruise/turn, including large close silhouettes. This is an improvement over the rejected uniform scatter, not owner approval or a claim of exact restoration of the old composition. The non-firing/non-evasive29s survival capture again failed by death; preserved as failed evidence.

Owner accepts a mostly forward Survival route if necessary to preserve challenging wave quality. Free Flight must remain unrestricted, and both modes need a field solution; wave quality first. No steering restriction has been imposed in this candidate. Character work remains deferred. Replacement release is0.1.21-alpha.1; build/publication pending.
