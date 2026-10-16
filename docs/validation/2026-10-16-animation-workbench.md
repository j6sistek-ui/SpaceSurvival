# Animation workbench — October 16, 2026

Scope: the owner's RPT-20261016-03 request for a simple way to preview and arrange owned animations. A private copy of the character studio now contains one preview mannequin and a Level Sequence. No station crew, hero, source animation, rig, gameplay system or release was replaced.

## Saved example

- Map: `/Game/SpaceSurvival/Licensed/AnimationWorkbench_20261016/L_AnimationWorkbench`, SHA256 `1c9f31b9bb1fd226a96a0c69db70834acc3e5a1560272fc0d74bf37e85089352`.
- Sequence: same folder, `LS_Wrench_Start_Loop_End`, SHA256 `9ea31d7f4e799da13d0564c77a3bd3935d6ed6906786288fecfc79d466e6b0cc`.
- Source clips: `/Game/Space_Crew_Animation/Animations/Zero-Gravity/Maintainance/AS_ZeroG_Wrench_{Start,Loop,End}`. The source folder spelling is intentional.
- Source mannequin: `/Game/Space_Crew_Animation/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple`; all three clips share its skeleton.
- Four sections at 30 fps: Start 0–75, Loop 75–169, Loop 169–263, End 263–314. Separate small section offsets align the authored root positions; original clips are read-only references. Restore State is selected.
- The map has 11 actors. The preview mannequin uses identity rotation and is raised to40cm for the floating pose; a camera-cut track provides a ready-framed view. The placed sequence loops during ordinary Play.

## Evidence

Private evidence lives under `.agent/local/AnimationWorkbench_20261016`.

- First native playback: 2,807 sampled frames over24seconds, two sequence wraps, all three phases reached, pause/resume succeeded. Measured root displacement across the three internal joins was at most0.163cm,0.001cm and0.374cm; head displacement stayed below0.392cm. These sampled transitions are evidence for this example only.
- Earlier previews were rejected: the first frame was too low/left, and the reframed version exposed a positional-Rotator argument error that pitched the mannequin onto its side. Identity rotation with named fields corrects it. Earlier map84b83faa and its1,486-sample playback remain historical; final map1c9f31b9 supersedes them. The final camera uses45degree horizontal FOV from570cm away and private studio exposure bias1.5. The horizontal-FOV interpretation was checked against installed CameraComponent.h and [Epic camera API documentation](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UCameraComponent) on October16. Original studio lighting/map remained unchanged.
- Upright preview: fresh reload verifies11actors, three sequence bindings, identity rotation,40cm height and clean packages. After the final saved camera/exposure correction, native playback passes1509samples/2wraps and pause/resume; all three final1600×900 views were inspected. Evidence is in `Final/CameraFit/Playback.json` and its three PNGs. `FinalUprightPreservation.json` confirms209 prior files and both newly saved asset hashes remain unchanged.
- `Preservation.json` verifies209 prior files unchanged, including the original studio, station map `e3cee859`, combined editor DLL `a023f6a9`, existing bar assets and owner saves. New native assets remain private/local; the source PR contains guidance and this receipt.

Retained failures: switching maps after duplicating a World while retaining its Python reference triggered Unreal's World Memory Leaks fatal check. All209 protected files remained intact. A fresh process opening the private workbench directly succeeded. Python authoring/review also exposed renamed/unreflected APIs; installed engine headers identified `add_track`, `get_binding_id`, the reflected sequence-player property and `GameplayStatics.get_player_pawn`. The repaired path was evaluated natively. The failure logs remain under the prior tray `Settled` folder and the workbench `Native` folder.

## Limits and next action

There is no wrench prop, repair target or gameplay interruption policy in this teaching example. Maintenance crew placement, tool contact and station behavior remain RPT-20261016-14. Other catalog clips, skeletons and animation transitions are not accepted by this test. Physical editor clicks, owner usability feedback, performance and packaged play are unverified. No C++ changes or new build were needed for these private assets and documentation; the previously built combined module was used.

Open the [short guide](../production/ANIMATION_WORKBENCH.md). The active work and pending owner checks stay in `docs/KNOWN_ISSUES.md`; this receipt does not create a second task queue.

## Action guide and interaction inventory

October16 CPU-only follow-up for RPT-20261016-03 uses the existing October15 catalog as an index, then rechecks selected source files directly. Twelve action sets contain38 clips:25 imported UASSETs and13 downloaded FBXs. The separate 200+Interactions pack has 205 downloaded FBX files in the scoped source directory; every listed file is present and SHA-256 recorded. The count includes base poses and variants, not 205 unique gameplay actions. Its broader import state is not inferred from similar filenames elsewhere.

For all 25 imported picks, the fresh embedded Asset Registry block identifies AnimSequence and matches the catalog duration and exact skeleton reference. For 13 FBX picks, fresh binary metadata confirms one animation take each and matching duration. File hashes were recorded before/after the selected-file inspection. Use-case names and suggested ordering are explicit inferences from asset names; motion/root travel, contact, retargeting and joins are not newly evaluated. H/M/L suffix meanings are not guessed. The existing floating-wrench workbench retains its separate native evidence above.

Private artifacts: `.agent/local/AnimationWorkbench_20261016/ActionGuide/Inventory.json`, `Checks.json`, `Review.html` and the read-only `build.py` recipe. The recipe executes only explicitly selected parser function definitions from the existing inventory scripts; it does not run their broad scans or alter their outputs. Static HTML parsing confirms 12 cards, 38 copy controls and 38 paths. A browser inspection attempt was rejected because local-file navigation is disallowed; no alternate browser/server workaround was attempted. Layout and clipboard behavior remain unverified. The Markdown guide is usable independently.

All 227 files in the current native guard remain unchanged, including saved station`c3dd6ea9` and editor module`b9a9d71e`. No Unreal launch, source clip import, rig/hero/squirrel edit, gameplay change or build was needed. Documentation/whitespace checks apply to this amendment; no new native, package, performance or owner-acceptance claim. More motion/contact evaluation remains in the canonical issue log.
