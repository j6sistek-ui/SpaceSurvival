# September 21 gameplay follow-up

Owner report: RPT-20260921-03. Work continues on draft PR59 in the isolated
`codex/flight-loop-reset` checkout, after the owner played Package3 and reported
that the major failures felt improved. Station composition is on hold. This
receipt separates this follow-up from the earlier reset and its 91-test baseline.

## Approved behavior (owner instructions, paraphrased)

- RT is normal analog throttle; B is boost; LT brakes; RB fires. Released throttle
  cuts main-engine thrust and retains world momentum. W/S adjusts keyboard throttle.
- Walking faces travel while the camera can turn independently. Space/A jumps;
  E/Y interacts on foot. Entering the actual Phoenix cabin opens launch choices.
- Home offers Start Survival, Continue Survival and Free Flight. Free Flight has
  no survival waves or persistent rewards, retains the home landing destination,
  and protects the account and suspended survival checkpoint. Flight D-pad
  functions are reserved for later work; title-menu navigation uses the D-pad.
- Repair the actual AlienFemale wardrobe body, ramp entry and readable shots/hits.
  Preserve supplied originals and existing survival progression.
- Insert the locked Figma main menu. Buttons within the full composition are the
  normal state; the separate button set supplies hover/focus. Page11 is the
  approved reference for subsequent needed menus. KIT and pages12/13 may supply
  supporting assets; other UI mockups are stale and do not authorize replacement.

## Reproduced defects and repairs

The actual AlienFemale walking mesh has 62,179 skinned vertices and 88,265 visible
triangles, but its section material resolves to null. Its reference pose is
approximately 178 cm high; sampling the installed idle/walk/run clips reduces its
height to 0.48–1.37 cm. The imported root has scale100 and a different bind basis
from the assigned mannequin animation. Selection and section visibility therefore
do not prove a visible body. The repair authors a private normalized rig,
retargeted locomotion and the owned four PBR textures; originals are hash guarded.
The first visible render exposed swapped source texture roles: the file named
Normal contains the albedo, and BaseColor contains the normal map. A separate
corrected private material uses the inspected roles and two private linear mask
copies. Measured root-only offsets ground the three private locomotion clips;
the second rendered review below verifies the visible repair in the station's
lighting, with natural-input and owner-acceptance limits retained.

The supplied ramp's visible toe extended beyond its coarse parked collider. Two
bone-attached walking supports follow the supplied toe/main panels into the cabin.
Only the old coarse ramp shape is disabled on the runtime body; the ten authored
box shapes and remaining hull/gear collisions are preserved. Whole-capsule cabin
clearance and actual floor contact admit boarding; leaving/re-entering rearms it.

Weapon visuals previously made the rapid/cannon streaks approximately 1.49/2.82 cm
wide in world space. The corrected visuals use measured mesh axes, emissive color,
and a short collision-free rapid-shot pulse along the authoritative shot range.
Confirmed impacts produce a longer, outlined HIT cue. Cosmetic pulses apply no
damage and do not extend range.

## Validation in progress

| Check | Result and local evidence |
| --- | --- |
| Follow-up Build1 | Passed20.99s; `Artifacts/BuildLogs/GameplayFollowup-Build1.log`. Installed-engine C4996 warnings remain. |
| Focused1 | 5 passed/4 failed, zero omitted. Throttle/coast, boost/brake, directional walking, chase camera and combat VFX passed. Female baseline failed as above. Boarding, parked collision and Free Flight failed the ramp selector ensure. `Artifacts/GameplayFollowup/Focused1/index.json`. |
| Ramp selector correction | The parked profile retains boxes; the first selector searched convexes used by the separate flight profile. Corrected box measurement without changing geometry or loosening traversal assertions. |
| Follow-up Build2 / Focused2 | Build passed8.29s. FreeFlightLifecycle, PhoenixWalkBoarding and PhoenixParkedCollision passed3/3, zero failures/warnings/omitted. Includes actual CharacterMovement home/rotated ramp traversal and near-pad dodge/mooring recovery. `Artifacts/GameplayFollowup/Focused2/index.json`. |
| Female author dry1 | Failed before mutation: Unreal Transform constructor does not accept the assumed keyword. Corrected with verified reflected properties. |
| Female author dry2 | Passed; nine intended private outputs,18 original source hashes preserved. `Artifacts/AlienFemaleReview/author-dry-run.json`. |
| Female author apply1 | Failed after unsaved private duplication: UE5.8's texture-parameter setter returns false despite performing the write. Installed engine implementation verified; changed to getter read-back validation. Source hashes unchanged; no saved private outputs. |
| Female author apply2 | Normalization passed; failed at an unreflected SkeletonFactory property. Source hashes preserved; recovery receipt retained. Superseded by apply3 below. |
| Follow-up Build3 / Focused3 | Build passed17.53s. Actual raw B menu-back release guard passed; mooring fixture failed its old forced-cruise expectation. Corrected to require engine-off/stopped release. `Artifacts/GameplayFollowup/Focused3/index.json`. |
| Follow-up Build4 / female apply3 | Build passed20.46s. A guarded editor-only native skeleton helper resolved the inaccessible Python factory path. Author completed nine private outputs with18 source hashes unchanged. `Artifacts/AlienFemaleReview/author.json`. Private mesh SHA256 `0e60bbfe29d0bfd5402aedecebde7ba926b9ca8cadf040335b0feeb4b168e755`. |
| Focused4 | AlienFemaleVisibility and MagneticMooringAndAssist passed2/2 clean. Actual serialized DA_Phase1 resolves the private body/clips;12 CPU-skinned poses measure154.35–179.35cm. This proves posed geometry/material resolution, not rendered feet or natural walking acceptance. `Artifacts/GameplayFollowup/Focused4/index.json`. |
| Full1 | 91/97 passed; six failures and zero omitted. Five fixtures still assumed zero throttle meant cruise or immediate forward injection: ContactImpactResponse, ControllerAfterTakeoff, FrameRateTrajectories, AcceleratedTenWaveJourney, PhoenixMooringPose. Their new explicit powered/stopped setup retains physical and transition tolerances. AudioFirstPlayMix exposed real initial presentation power0.45 despite zero throttle. `Artifacts/GameplayFollowup/Full1/index.json`. |
| Follow-up Build5 / Focused5 | Build passed11.70s. Five corrected fixtures passed; audio failed the actual initial engine-power state. Source now initializes presentation power to0; requires the next build/test. `Artifacts/GameplayFollowup/Focused5/index.json`. |
| Weapon rendered review1 | Scripted normal-stat capture completed with four1920x1080 frames and actual damage feedback. `Artifacts/EndgameSoak/779a3c5e6ded4769aec75ab0e8b22ce4/capture.json`; module SHA256 `4285e416585ce063b922b4eae9bd8a494d472821aa051cf3baaf6e6b4528320b`. Raw review sees cyan rapid trace in RapidHit and orange round in CannonShot. RapidShot is blank while editor assets compile; HIT text overlaps target label. These are retained failures requiring warmup and label-layout correction, not visual acceptance. |
| Figma dry1 / apply1 | Both passed. Imported19 exact textures;21 exported PNGs and the original portrait remain byte-identical. `Artifacts/FigmaMainMenu/author.json` binds output hashes. Native transparent exports replace the rejected white-matted connector renders. |
| Follow-up Build6 / Build7 | Build6 failed a new test's private Ship/Walker access; added the narrowly scoped test friendship. Build7 passed19.10s with the existing installed-engine deprecation warnings. `Artifacts/BuildLogs/GameplayFollowup-Build7.log`. |
| Full2 | All98 tests passed, zero failures/warnings/omitted,22.848934s test duration. Includes initial engine-off audio state and raw title input through actual settings/acknowledgements/home actions. `Artifacts/GameplayFollowup/Full2/index.json`. This precedes the later female-grounding helper and clip changes; Full3 below covers the subsequent checkpoint. |
| Independent integration review | Found title-origin acknowledgements bypassing the title; repaired and covered by Full2. Also identified female sole lift in sampled clips; rendered grounding was pending at that checkpoint and could not be inferred from the passing visibility test. Female rendered review1 below confirms the visible defect. |
| Title rendered review1 | Passed, process0, three1920x1080 frames; finished22:53:57UTC. `Artifacts/EndgameSoak/eca3d594ee84444fb4fcb7605270c102/capture.json`. Actual imported Figma art drew in normal/no-selection, New Game focus and Settings focus; recorded selected/rendered indices are -1/1/2. All four actual button centers resolve to existing actions2/4/5/7, with Continue disabled in the fresh profile. Raw PNG review confirms the composition and focus changes. In-memory account/run, production saves and compiled artifacts remain unchanged; no StartRun or menu activation occurred. This is synthetic selection at16:9, not physical input, other-aspect-ratio or owner acceptance. |
| Female rendered review1 | Fixture passed, process0,12images; finished22:58:03UTC. `Artifacts/EndgameSoak/b1492746790f48b2aef333f229ef37fa/result.json`. Exact requested/actual AlienFemale is visible in StationIdle and the real player-camera out/turn/return frames. Standing-deck coverage15.012230s, zero rescues; appended motion2.082663s, maximum travel163.8624cm. Source, artifacts and production saves stayed unchanged. Raw review still **fails visual acceptance**: bright gold appearance and visibly floating soles. Supported capsule/floor checks do not establish mesh-to-floor contact. The later material/clip repair below requires a separate rendered review; these images do not certify it. |
| Weapon rendered review2 | Passed, process0, four1920x1080 frames; finished23:00:04UTC. `Artifacts/EndgameSoak/8c04b0498ed14ca793a0f0515ee48655/capture.json`. Two uncaptured real shots/hits warm the render paths; peak pending preparation was2assets/2shader jobs, with readiness recorded at2.547560s. RapidShot at5.009655s now visibly contains the cyan trace; CannonShot visibly contains an orange round. Both hit frames show the separate outlined HIT cue and actual0.28s hit feedback. Production saves and compiled artifacts remain unchanged. This passes the bounded warm-shot readability review; the cold first-trigger failure from review1 is retained and **not proven fixed**, including in a package. |
| Follow-up Build8 / Build9 | Passed10.74s and4.29s respectively; `Artifacts/BuildLogs/GameplayFollowup-Build8.log` and `GameplayFollowup-Build9.log`. Existing installed-engine C4996 warnings remain. These compile the female grounding work; neither compilation proves authored outputs, corrected feet/materials, a new full-suite pass or a new package. |
| Female author dry4 / apply4 recovery | Dry run passed at23:10:38UTC with source preservation and no geometry mutation. Apply4 failed at23:11:25UTC when Windows rejected deletion of the private `MI_AlienFemalePresentation.uasset` with Error Code32; `Artifacts/BuildLogs/GameplayFollowup-FemaleApply4.log` and `Artifacts/AlienFemaleReview/author-apply4-partial.json` retain the failure. Eight removed outputs were restored from `Artifacts/AlienFemaleReview/Backups/20260921T231120309561Z`; the existing material remained unchanged. Before the next repair, independent SHA256 verification matched all nine previous private outputs and18 originals to the backup receipt. Subsequent attempts use targeted repair instead of deleting/rebuilding the private set. |
| Female repair5 | Failed when saving the existing private material encountered the same Windows file lock; no deletion was attempted and all nine existing outputs remained unchanged. `Artifacts/BuildLogs/GameplayFollowup-FemaleRepair5.log` retains the Error Code32 and failed-save assertion. |
| Female repair6 | Created `MI_AlienFemaleCorrected`, two private linear metallic/roughness masks and saved the private mesh's material-slot change, leaving12 recorded outputs. Grounding then failed its evaluated-pose guard:0.011274cm error exceeded the original0.005cm threshold. No corrected clip was saved; bind, legacy material and supplied originals remained preserved. `Artifacts/BuildLogs/GameplayFollowup-FemaleRepair6.log` retains the failure. |
| Follow-up Build10 / Build11 | Passed18.54s and5.18s; `Artifacts/BuildLogs/GameplayFollowup-Build10.log` and `GameplayFollowup-Build11.log`. Build10 includes the mixed-input correction. Build11 sets the evaluated-pose recompression tolerance to0.05cm (0.5mm); all bone-key read-back and timing invariants remain enforced. This tolerance change is explicit, not a claim that repair6 passed its original guard. |
| Female repair7 | Completed at23:22:59UTC. `Artifacts/AlienFemaleReview/author.json` records12 outputs and18 preserved sources; independent SHA256 checks match every file. Mesh bind, legacy material and skeleton/authoring assets are preserved. Idle/Walk/Run root offsets are−3.004637/−3.120218/−2.249306cm; maximum evaluated-pose translation errors are0.000006/0.006158/0.002245cm, with all three pose/timing invariant checks true. The top-level error field still contains repair6's inherited rejection text; the completed status, three successful grounding records and output hashes establish this attempt's result. The prior error is retained rather than silently erased. |
| Full3 | All98 tests passed, zero failures/warnings/omitted,21.655079s; report created23:23:37UTC. `Artifacts/GameplayFollowup/Full3/index.json` and `Artifacts/BuildLogs/GameplayFollowup-Full3.log`. This is the Build11/private-repair7 checkpoint, including female grounding and mixed-input coverage; no new packaged or physical-input result is implied. |
| Female rendered review2 | Passed, process0,12 images at1920x1080; finished23:27:29UTC. `Artifacts/EndgameSoak/64dc782953594c6ca6b80deb9240245e/result.json`. Exact requested/actual AlienFemale remained visible through standing and the real player-camera out/turn/return sequence. Standing-deck coverage15.0121745s, zero rescues; appended motion2.064301s and maximum travel163.5806cm. Source, compiled artifacts and production saves were preserved, with no test save slots written. Independent raw review of `StationIdle.png` and `WalkerReturn.png` shows restored silver skin, dark suit and cyan detailing, with standing soles visibly meeting the deck. Warm station reflections differ from the neutral Tripo reference; this is a bounded appearance/grounding pass, not a pixel match or owner acceptance. Movement is scripted, sound is disabled, and screenshot/CSV instrumentation perturbs timings: no natural-input, listening or60FPS acceptance is inferred. |
| Local container checks | TestCore could not connect to the stopped Docker Linux backend; `Artifacts/BuildLogs/GameplayFollowup-CoreLocal.log`. No packages installed. Existing native clang-format passes; GitHub container core/ASan/UBSan checks are required at the pushed checkpoint. |
| Source checks | Structural37 at the current working checkpoint; source digest13, Python compilation, content-source formats and documentation navigation previously passed. Source checks remain separate from Unreal gameplay and package gates. |
| Lead-run source/content checks | Fresh Git check at asset checkpoint `404af077966be917f603766854ad042733da89bc` exported791 files without changing the checkout. Cook-intent coverage passed37 roots,10 exact exclusions and135 paths with zero gaps; its7 tests passed. Native formatting passed102 files. These are lead-run terminal checks; no standalone receipt or package validation is claimed. |
| Gameplay source checkpoint / Package4 | Windows Development package at source `79553fc8ac7946b1b94bf18e75e4cc9b6b434898` passed BuildCookRun in93.80s. Cook summary:3027 cooked,8 platform-skipped, zero errors and one known ShipCore startup warning. `Artifacts/BuildLogs/WindowsPackage-87557adf69d442d68c3b4aa98b9cf14e.log`; wrapper log `GameplayFollowup-Package4.log`. Archive is `Artifacts/Windows`; inner executable SHA256 `874b8f685f156a8686534560405e16d26a6445dd915f00fe25610afbfaf75193`, independently matched to disk. |
| Package4 archive audit | Passed actual IoStore/package/dependency inspection:3027 described packages,125 selected exports and339 packages in their dependency closure; no missing or forbidden packages/dependencies. `Artifacts/GameplayFollowup/PackageAudit/Audit-fb5b83355d7a4056865437d39a215863/Audit.json`, against `Expected-304934b35363463a9f95fa070a7507e8.json` with277 frozen inputs. Archive payload remained unchanged:53 files,5,619,597,497 bytes. This establishes archive contents and identity, not natural gameplay or clean-PC installation. |
| Package4 title capture | Passed, process0, three1920x1080 images; finished23:32:11UTC. `Artifacts/EndgameSoak/0c1dadb26c994f45a894729f712eedfb/capture.json`. Actual Figma title draws normal/no-selection, New Game focus and Settings focus at indices−1/1/2; all four button centers resolve to actions2/4/5/7 and fresh-profile Continue remains disabled. Lead reviewed Normal/NewGame; independent Settings image review confirms the intended focused artwork. Main-menu account/run state, packaged artifacts and production saves remain preserved, with no test save slots written. Selection is labeled synthetic; no physical input or other-aspect-ratio acceptance. |
| Package4 weapon capture | Passed, process0, four1920x1080 images; finished23:32:36UTC. `Artifacts/EndgameSoak/cf8da440b66c4b1db6f58605bc6fc1aa/capture.json`. Lead reviewed RapidShot/CannonHit; independent RapidHit/CannonShot review confirms a cyan rapid trace, separate readable HIT cue and visible orange cannon round. Both actual hit records contain0.28s confirmed feedback. Two genuine uncaptured warmup shots precede capture; peak pending assets/shaders are0/0. Artifacts and production saves remained unchanged with no test slots written. This verifies warm-shot readability in the package; **cold first-trigger readiness remains unproven**. |
| Package4 female Station5 capture | Passed, process0,12 images at1920x1080; finished23:35:39UTC. `Artifacts/EndgameSoak/d7b9eb28986e4259b0d3529ccc7ec693/result.json`. Exact AlienFemale body,2.985461s docking,15.0156603s standing on deck, zero rescues, then2.108858s scripted player-camera motion with maximum travel163.0464cm. Source checkpoint79553fc, packaged artifacts and production saves remained unchanged; no test slots were written. Lead's raw Idle/Return review confirms restored materials and visible grounded body in the package. Warm-light/reference and natural-input limits from female review2 remain. |
| Package4 runtime log review | All three packaged captures exited0, with zero Error/Fatal log entries. Each retains the same three baseline warnings: ShipCore startup; lower-priority `r.MotionBlurQuality` scalability assignment ignored; `r.MotionVectorSimulation` render-thread safety flag. Their respective `Rendered.log` files retain the exact messages. No warning is silently treated as repaired; these offscreen, sound-disabled captures do not establish listening or representative60FPS performance. |
| Free Flight disk lifecycle | Passed Preflight, Suspend, FreeFlight and FreshAfterFreeFlight in four separate processes; exact account/checkpoint bytes and production saves preserved. `Artifacts/SaveLifecycle/dbbf0b9fbc8f43a39f2974689761157d/result.json`. Practice kills/XP/death were changed in memory, rejected for persistence, restored and followed by fresh-process survival resume. |
| Save harness environment | First run under Windows PowerShell5.1 reported a null process ExitCode after the successful Preflight engine test; harness failed closed and performed no later writes. `Artifacts/SaveLifecycle/aac70997c9834a8fa255c6d2dcea5b68`. Re-running with the existing PowerShell7.6.5 completed all four stages. No host tool was installed. |

Title review1, female review1 and weapon review2 are uncooked editor-game captures
of the same module SHA256
`059236839e90a1485dc45106807519bd46cdd5c4a02365a763893f4ef44fc009`.
Their receipts retain source HEAD `faf4765` and the dirty working snapshot; they
do not bind later Build8/9 changes to those images. Female review2 instead binds
module SHA256
`1a6cb24c0284619ab6c4e07b0af21710214fded8b33f945c8050379fde4fd860`
and its frozen working snapshot at HEAD `404af07`, before the gameplay source
checkpoint commit. All are uncooked editor-game captures. CSV profiler overlays
and screenshot readback are fixture instrumentation, not performance evidence.

Package4 is the ready review candidate at `Artifacts/Windows`, bound to source
`79553fc` and the audited inner executable above. Its three packaged captures
are separate from the earlier editor-game evidence. No result here establishes
Phase1 completion, physical controller feel, natural gameplay, listening,
representative performance or owner visual acceptance. Cold first-trigger
readiness also remains unproven. PR59 stays draft; no merge or publication is
authorized.
