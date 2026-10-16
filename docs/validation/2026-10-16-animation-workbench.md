# Animation workbench — October 16, 2026

Scope: the owner's RPT-20261016-03 request for a simple way to preview and arrange owned animations. A private copy of the character studio now contains one preview mannequin and a Level Sequence. No station crew, hero, source animation, rig, gameplay system or release was replaced.

## Saved example

- Map: `/Game/SpaceSurvival/Licensed/AnimationWorkbench_20261016/L_AnimationWorkbench`, SHA256 `84b83faaa555b925a7396155f45e43715ab17edacc31f03d0906cdce55f95403`.
- Sequence: same folder, `LS_Wrench_Start_Loop_End`, SHA256 `9ea31d7f4e799da13d0564c77a3bd3935d6ed6906786288fecfc79d466e6b0cc`.
- Source clips: `/Game/Space_Crew_Animation/Animations/Zero-Gravity/Maintainance/AS_ZeroG_Wrench_{Start,Loop,End}`. The source folder spelling is intentional.
- Source mannequin: `/Game/Space_Crew_Animation/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple`; all three clips share its skeleton.
- Four sections at 30 fps: Start 0–75, Loop 75–169, Loop 169–263, End 263–314. Separate small section offsets align the authored root positions; original clips are read-only references. Restore State is selected.
- The map has 11 actors. The preview mannequin is raised to170cm for the floating pose; a camera-cut track provides a ready-framed view. The placed sequence loops during ordinary Play.

## Evidence

Private evidence lives under `.agent/local/AnimationWorkbench_20261016`.

- First native playback: 2,807 sampled frames over24seconds, two sequence wraps, all three phases reached, pause/resume succeeded. Measured root displacement across the three internal joins was at most0.163cm,0.001cm and0.374cm; head displacement stayed below0.392cm. These sampled transitions are evidence for this example only.
- First framing was rejected: the zero-G pose sat too low and left of the camera. The private map was adjusted; original studio lighting/map remained unchanged.
- A fresh offscreen process reloads the saved map with11actors, three sequence bindings, the intended170cm mannequin height and clean packages. Saved-scene playback passes1,486samples/two wraps and pause/resume; all three corrected1600×900 views were inspected. Evidence is in `Reload/Playback.json` and its three PNGs.
- `Preservation.json` verifies209 prior files unchanged, including the original studio, station map `e3cee859`, combined editor DLL `a023f6a9`, existing bar assets and owner saves. New native assets remain private/local; the source PR contains guidance and this receipt.

Retained failures: switching maps after duplicating a World while retaining its Python reference triggered Unreal's World Memory Leaks fatal check. All209 protected files remained intact. A fresh process opening the private workbench directly succeeded. Python authoring/review also exposed renamed/unreflected APIs; installed engine headers identified `add_track`, `get_binding_id`, the reflected sequence-player property and `GameplayStatics.get_player_pawn`. The repaired path was evaluated natively. The failure logs remain under the prior tray `Settled` folder and the workbench `Native` folder.

## Limits and next action

There is no wrench prop, repair target or gameplay interruption policy in this teaching example. Maintenance crew placement, tool contact and station behavior remain RPT-20261016-14. Other catalog clips, skeletons and animation transitions are not accepted by this test. Physical editor clicks, owner usability feedback, performance and packaged play are unverified. No C++ changes or new build were needed for these private assets and documentation; the previously built combined module was used.

Open the [short guide](../production/ANIMATION_WORKBENCH.md). The active work and pending owner checks stay in `docs/KNOWN_ISSUES.md`; this receipt does not create a second task queue.
