# October 6 survival quality repair

Owner report: RPT-20261006-02 in [KNOWN_ISSUES](../KNOWN_ISSUES.md).
Working checkout: canonical `C:/Users/j6sis/SpaceSurvival`, branch
`codex/unified-editor-library`, based on `40c43217` with the changes in this PR.
This record is in progress. The published 0.1.22-alpha package has not changed.

## Standard and boundaries

- Keep the approved nose steering, camera, bumper evade/roll and five-wave station cadence.
- The field must be dense in actual rendered movement, stable when approached or revisited,
  and collidable. There must be navigable space without moving rocks away from the player.
- Ordinary small, medium and massive asteroids accept real laser/cannon damage and break.
  Structural wreckage/stations are outside that destruction request.
- Space has a dark background, readable stars and a distant celestial body. A bright full-screen
  colored cloud must not obscure spatial depth.
- Impact damage scales with closing speed and moves the actual physics body. Stationary contact
  is harmless. Existing Director hazard damage must not be charged a second time.
- Controller pause/settings remain over the game; selection and adjustment agree with visible
  bounds. Steering cannot also move an unpaused reward selection.
- Actual Pawn collision support must prevent apartment false rescues. The animated tail stays
  above a supported floor while its clear-air pose is preserved.
- Report native regressions, rendered captures and measured performance separately. None of
  them constitutes physical-controller use, listening acceptance, or unassisted human survival.

## Evidence retained so far

Raw receipts live beneath the existing `Artifacts` junction to
`M:/SpaceSurvival/Artifacts` or the explicitly named `.agent/local` paths below.
No owner-facing Unreal window was opened. The already-open editor
had no dirty maps/content and no Play session before clean closure. Owner clarified that no
station edits were intentional; none were attributed to them or discarded.

| Check | Result and limits |
| --- | --- |
| Baseline | `EndgameSoak/dc471f5632934314a27df70f95ce04c2`: ordinary Wave 1, moving sequence. Sparse foreground, dominant colored nebula and weak stars confirmed visually. Screenshots are not timing evidence. |
| Editor builds | Builds 1, 3 and 5–10 succeeded. Build 2 exposed a private fixture-method call; build 4 exposed UE 5.8's `TObjectPtr` test-template mismatch. Both compile errors were repaired; failed logs retained. Build 9 took 99.17 seconds, build 10 took 11.14 seconds; installed engine-header deprecation warnings remain. |
| Native batch 1 | `SurvivalQuality/Tests1`: 11/15 passed. Four failures retained: hidden-field physics bodies, structure fixture lifecycle ordering, and first-frame animation comparison. |
| Native batch 2 | `SurvivalQuality/Tests2`: 11/12 passed, no warnings or omitted cases. All four prior failures passed. Real laser/cannon field hits, stable damage/destruction, isolated menu input, audio role assets and spatial limits passed. Scenery damage passed, but the new physical rebound assertion failed; resolved in batch 4. |
| Native batch 3 | `SurvivalQuality/Tests3`: seven tests met their assertions, three failed. Actual massive-rock destruction, live reward input and Director trajectory/volley cases passed. Failures isolated remaining solver rebound, three direct material slots retaining opaque overrides, and an obsolete journey floor-actor assertion. Known furnished-apartment Blueprint warnings were retained. |
| Native batch 4 | `SurvivalQuality/Tests4`: three tests met all assertions, none failed or omitted; the two isolated tests are clean. Real scenery impacts at 750 and 6000 cm/s recoil at -232.5 and -1020 cm/s respectively, with 11.625/51 damage and 58.125/255 cm retreat over 0.25 seconds. Dense geometry validates 6,144 instances, material fades and streaming clearance. The accelerated journey reaches Waves 1–10 and both stations, with 31 pre-existing `BP_Blinds` material warnings. It is not a clean warning-free suite or natural survival balance evidence. |
| Apartment support | `Integration.WalkerSupportRecovery` passed in batch 1 using actual Pawn support rather than the old center-line WorldStatic assumption. Owner apartment play remains to be repeated. |
| Actual apartment route | `EndgameSoak/4d34c48bfedd47fa8bb473e703a55aba` passes the normal CharacterMovement route into the furnished apartment and back: two passes, 50.529 seconds, zero rescues, one initial setup placement and zero subsequent placements. The automatic entry door reaches full opening and closes after return. The same guarded capture passes all four home/four pit-stop service openings, real Free Flight departure/return and a supported seeded Wave 5 station. It is scripted direct pawn input, not physical input or a natural full run. |
| Tail surface | Batch 2: 227 poses, 21,221 tail vertices including 242 mixed seam vertices, seven measured envelopes. Minimum tested world-plane distance changed from -44.4586 cm to +3.1710 cm; clear-air local poses remained unchanged. Actual moving rendered jump is a separate gate. |
| First repaired visuals | `EndgameSoak/724433aea9f3488587d818017d75299e`: actual dense near/middle rocks, dark stars and textured moon visible. Independent review rejected rainbow star speckling, repeated intersecting boulder chains and abrupt mid-distance appearance in sequence 073–080. Follow-up repairs require fresh captures. |
| Revised field | `EndgameSoak/d874935b167b4fca9574fee8a3de4388`: 80 moving sequence frames plus named captures; guarded capture passed. Independent review confirms calmer stars, solid approaching rocks and gradual far-field coverage. It also flags visible temporal-dither stippling and one abrupt brown-object appearance requiring distinction from a Director spawn. This is not a claim that every appearance discontinuity is resolved. |
| Menus | `EndgameSoak/46c9d347cfd041a193f3220ac4dc31da`: four 720p flight-pause/settings captures preserve the actual world and meet action bounds. Visual review found a stale world announcement, excessive pause-panel height and cramped hints; build 8 addresses these. Fresh final captures remain required. `MenuSettings/f716372fa6014032b98be2546b5703e8` passes actual native controller settings changes in an isolated profile, preserving production saves. |
| Menu fit before tab correction | `EndgameSoak/f9decdedf286455896bef584ad782dab` (720p, UI 1.4) and `e486c3acab6046a592f68d1ed3358c84` (1080p, UI 1.0) pass all four pause/graphics/audio/controls captures each. All 66 action bounds fit and their centers resolve correctly; actual paused flight world remains behind them. The initial visual review missed left-aligned tab labels and a pause subtitle/frame overlap; the owner correction and independent follow-up below supersede its earlier no-overlap assessment. No physical-controller feel claim. |
| Centered settings tabs | Independent review of all eight images in `EndgameSoak/e320ae8c3ecd4844bc9b5e794db9b6f3` (720p, UI 1.4) and `3ff5519d27d24d9eb3199b05dc281d6c` (1080p, UI 1.0) confirms GENERAL, GRAPHICS, AUDIO and CONTROLS centered horizontally and vertically within the tab art. Settings rows, values, sliders/toggles, wrapped guidance, Back and footer remain unclipped without new overlap. Both captures pass; each has 33 visible bounds inside the viewport with correct center-hit mappings. All eight frames retain the actual paused flight camera and preserved state. |
| Pause decorative overlap | The same independent review finds JOURNEY / PAUSED crossing the glowing top inner frame line in both pause images; the main heading and six actions remain clear. A narrow `SSHUDRefresh.cpp` fix places the subtitle below that rim, then positions the heading after its measured layout height plus a 10-pixel logical gap. Logical geometry at UI scales 0.8/1.0/1.4, formatting and diff checks pass; settings and the locked title layout are unchanged. Included in Editor15; fresh 720p render remains pending. |
| Rendered tail, first pass | `EndgameSoak/13766bce9b97494ab9fbe57641f7cd7b`: two actual jumps, minimum measured weighted-surface clearance 4.9807 cm and zero rescues. Capture gate failed because low screenshot cadence missed the fixture's narrowly timed landing-stage classification. Failure remains recorded; a dense fixed-step offline animation review is being prepared, separately from performance. |
| Audio | Four private owned-source derivatives imported with verified hashes/durations and bounded peak measurements. `CombatAudioPalette` and `SpatialThreatAudio` passed. No device-listening claim. Originals remain unchanged. |
| Source checks | 39 structural checks, Python compilation, all 26 source meshes/17 WAVs/unchanged GLB, eight benchmark-analyzer tests and canonical documentation navigation/counts passed. These do not establish gameplay readiness. |
| Native batch 5 | Five menu cases passed; Director arrival material assertions passed but its scalar-coverage expectation failed for three rock kinds. Failure remains in `SurvivalQuality/Tests5` pending correction. |
| Native batch 6 / Editor 11 | Editor build 11 succeeds in 56.37 seconds. `SurvivalQuality/Tests6` passes 5/5 clean: DenseFieldGeometry, DenseFieldDamage, DenseFieldIncrementalStreaming, AsteroidBreakup and DirectorArrivalPresentation. Incremental turnover preserves visible reference surfaces, stable retained poses, 125 cells and the 6,144-instance cap. Arrival failure was a 5.96e-8 float midpoint difference; explicit 1e-6 test tolerance repairs the assertion without changing runtime targets. Large regional breakup now retains proportionate fragments and actual near-hit debris within five metres. |
| Native fade authoring retry | Editor14 builds the strengthened native-mask assertions in4.53seconds. Dry run `FieldFade/6ac21e9d24614ee2b03b12404c689723` passes. Apply4 (`121a17c9d1664aa19b04605d46ae891b`) stalls after its first private parent/instance saves; generated shader inspection finds a vector-valued original mask feeding a scalar conditional on the next masked POM master. The owned process was stopped; failed log and backups retained. Explicit scalar coercion is required before retry; this attempt is not accepted content evidence. |
| Saved native-mask materials | Apply5 fails before saving because the engine exposes ComponentMask's input with an empty short name. After confirming that name in installed source, apply6 `FieldFade/9a4fb04fbd2e441982c4fb334fd6483d` succeeds:45meshes,23slot materials,25parent/instance targets, all original hashes preserved. Explicit red-channel coercion matches the original OpacityMask scalar conversion; compilation errors now reject before save. A transient invalid TextureIndex warning during the masked POM parent's update remains in the log. Fresh-load `SurvivalQuality/Tests7` passes DenseFieldGeometry,1/1 clean, including native dithering and clip0.333. Render acceptance is separate. |
| Offline field capture: motion rejected | `EndgameSoak/abed63cba4d04637b9c5ada75d8b1aee` passes its capture harness with 84 images, including 80 sequence frames, and 29 simulated seconds. Independent receipt/CSV inspection finds 77/84 image requests below 1 m/s and 1,467/1,741 CSV frames (84.3%) below that speed; the fixture counted 1,740 flight ticks. The ship was nearly stopped through most of the run. This does **not** establish moving-field or fade acceptance, despite the image-count pass. Its explicit offline 60 Hz clock also excludes performance and real-time smoothness claims. |
| Sequence motion guard / Editor15 | Editor15 succeeds in 16.82 seconds. Independent source review finds the new Wave1 Sequence route limited to that fixture: one initial placement on the actual field-local lane, a real compound-hull sweep of the first 200 m, then ordinary damped flight input with collisions, damage and resources active. Origin-aware travel, net displacement and forward progress must each reach 1 km; at least 12 seconds at or above 20 m/s before braking are required, and more than two seconds below 1 m/s during seconds 5–21 fails. Other fixture branches retain their paths. This is source/build evidence only; a fresh moving render and material-motion acceptance remain pending. |
| Rendered tail, second pass | `EndgameSoak/9a2cbf706f634d93a3ad15a5ccb18045` failed the declared fixed-timestep guard on entering motion, before either jump. Its single standing frame is not jump evidence. First-pass successful motion measurements and failed gate remain separate above. |
| Rendered tail, third pass | `EndgameSoak/80b1c1a1280c4c8bae8d18fc7df4dfdc` passes with 79 frames, two jumps, all six ascent/descent/landing phases, zero rescues and minimum measured skin-surface clearance 2.3684 cm. Tail review alone starts with the engine's 60 Hz fixed-step flags and verifies actual/declared clocks; it is an offline animation review, explicitly not natural-input or performance evidence. Actor-tick clock mutation was removed after the second failure. |
| Performance baseline pair | `EndgameSoak/bd1ecd121d6f43dfb35948f3471ba614` (2,048 rocks) and `d5a6273131b14a2c81572eaee7e78b0c` (6,144) both satisfy the same seeded environment-only benchmark contract: 1080p High, 15-second warmup, 60 measured seconds, real hull collision enabled and no collisions/health loss. Director attacks are intentionally disabled. Call of Duty was running concurrently on the GPU, so the observed 56.01/41.61 average FPS and GPU timings cannot establish a clean density comparison or the 60 FPS acceptance gate. All eight cell crossings nevertheless show repeatable game-thread spikes: 19.41–23.62 ms at 2,048, 46.65–60.18 ms at 6,144. Incremental cell work is required; reducing population is not the chosen remedy. |

## Content and provenance

### Final material and moving-field review

Private field material usage repair `FieldFade/51b138a60c61483ba4651bf1c917baa0`
and arrival repair `DirectorArrival/90010e99f93c4d4d90f554c6c7d92046` save the
required instanced-mesh/Nanite permutations, including instance overrides. The
preceding inventory runs are399b4821/c905c41b. Original material hashes remain
unchanged; private outputs are backed up. This corrects actual default-material
fallbacks in the previous game log, not just an editor preview discrepancy.

Moving capture `EndgameSoak/bdc9de0c59cd470d8a697f2de7086e5c` passes84images,
including80sequence views,29simulated seconds,1673.86m accumulated travel,
1672.81m net displacement and21seconds above20m/s before braking. No pre-brake
stall occurred. Normal damage remains active: hull ends66.17 and shields0.
One initial fixture placement uses the actual field lane; no in-flight placement
or route-clearance assistance occurs. This is explicit offline60Hz scripted visual
evidence, not real-time performance or natural survival acceptance.

Independent review of12frames confirms passing landmarks/parallax, solid near
surfaces, dark sky/moon and removal of the earlier diagonal hatch. No large
near-field insertion/removal was identified in those samples; fine far-fade noise
and repetitive blue-heavy clusters remain aesthetic limits. The large brown rock
approaching during Cruise is a Director attack with real shield loss, not a field
spawn. Fresh logs contain no missing usage/default-material/shader-compile warning.
Engine EditorToolset/ToolsetRegistry Python initialization errors in editor `-game`
remain separately recorded; the run is not described as log-clean.

Pause-spacing capture `EndgameSoak/52646553492d451f8fff4d1fd824b267` passes all
four720p/UI1.4 images. Lead review confirms the eyebrow now clears the decorative
frame, actions fit, and the live paused scene remains the background.

The field samples the existing owned asteroid Blueprint formations; bounded native instances
provide the runtime population rather than thousands of ticking Blueprint actors. Original
meshes and vendor materials remain inputs. Private material chains retain texture and parameter
choices while adding camera-distance masking for gradual visibility.

`Scripts/AuthorSurvivalSpace.py` creates the private sky derivative using the owned star/cubemap
assets and `Planet_Project` moon texture. The moon is distant sky scenery, not a traversable planet.
`AuthorFieldDistanceFade.py` has an inventory-only dry run; its application backs up private outputs
and preserves original material hashes. `PrepareCombatAudioPolish.py` and
`AuthorCombatAudioPolish.py` record source hashes, processing and import separately.

The measured squirrel envelope is stored in the Squirrel row of `DA_Phase1`. Its original mesh,
animation clips and all station map files are preserved. Private asset authoring receipts and
backups live under `SurvivalQuality` and `.agent/local/CombatAudioPolish`.

### Phoenix cockpit implementation and validation

The owner subsequently requested walking to the actual chair, visible seating and
departure in the selected Waves or Free Flight mode. The following native and rendered
checks supersede the unbuilt October6 10:02UTC checkpoint. Physical input and owner
acceptance remain separate.

Read-only geometry and collision evidence lives in
`.agent/local/SurvivalQuality/PhoenixCockpit`. The private landed interior collider
contains11,762 source triangles and replaces three coarse parked envelopes that
blocked the stairs. Its authoring dry run and apply exit0 in the empty Engine Entry
map; seven original asset hashes remain unchanged. Private collider SHA256:
`2b8a46035abd01a5004786d4c9ead261fb9056c6eb4926e6cfdffc891e298532`.

`CollisionFit1.log` and `SquirrelCollisionFit.json` measure32 idle/walk/jog/run poses
of the actual replacement mesh: maximum body/helmet height138.272cm at the unchanged
rendered scale1.51061452. Source hashes are preserved and the headless process exits0.
The former shared capsule was176cm high. Source changes fit this exact replacement
to150cm while retaining radius34cm, other heroes' dimensions and world sole height.
This is collision fitting, not a character or ship scale change.

`Capsule3` and `CapsuleGrid1` both use a required native Cube floor positive control
and exit0. The latter is explicitly a candidate collision query, not movement:
the unchanged34cm radius clears the right-hand doorway trim at Y=-10cm; the proposed
75cm half-height clears the stair crest where88cm did not. The route returns to the
centre before the stairs. No ceiling or trim triangles were removed. The subsequent
Build22 and actual-camera boarding checks below provide the separate walking and
seated-fit evidence; these static queries alone did not establish it.

Source adds chair-only interaction, a visible1.4second same-rig pose blend, selected
mode at the existing physical computer, save-failure rollback, Wave5 continuation,
and held-controller-A suppression across possession. The opt-in
`-SSSoakBoardingReview` captures the ordinary walking/sit/handoff/takeoff path through
the existing isolated OutpostReview, with temporary fixture flags disclosed and
restored. Build22 and its two focused boarding/parked-collision cases pass without
automation warnings. The first boarding capture used an exterior fixture camera and
was rejected as seating evidence. The second used the real player camera and exposed
the camera collapsing toward the character as its origin entered the chair back.
Build24 anchors that camera origin at the standing approach during seating, preserving
the normal camera rotation, collision and cancellation restoration.

`CockpitTests24` passes the affected departure test. Actual-camera capture
`EndgameSoak/776936029d5e470687f0331e64af5c72` passes the eight-view walking, sitting,
same-hero handoff and selected Free Flight departure fixture with protected saves.
The seated camera remains behind the character; the physical chair correctly occludes
the lower body. The cabin was still too dark, so visual acceptance remained open.

Build25 succeeds in19.13seconds. Two shadowed, inverse-square cabin lamps use measured
ceiling positions and enable only while parked. `CockpitLightsTests25` passes
`PhoenixParkedCollision`, one test with zero failures, warnings or omitted cases;
it covers off, parked, takeoff and repark lighting states. Boarding4's actual-camera
review confirms increased cabin visibility but exposes an overly bright cockpit
ceiling reflection. Build26 succeeds in8.67seconds with only the cockpit lamp's
specular scale reduced to0.15; its diffuse intensity and rear lamp are unchanged.
`CockpitLightsTests26` again passes the single affected test without warnings.
Installed engine-header deprecation warnings remain in compilation; no engine
modification is included.

`EndgameSoak/9dbf09238fa045c99356e9d4c1ceceb7` (`PhoenixBoarding5`) exits0 with
eight images from the possessed pawn's actual camera. The character travels23.42m
with ordinary CharacterMovement, zero rescues and one disclosed initial placement.
The native handoff retains the same hero with0.2223cm pose error, then departs in
the selected Free Flight mode. Map/save/build guards remain intact. Lead and
independent review of all eight images find a coherent walk/sit/takeoff camera,
readable cabin and softer cockpit reflection. The original glossy ceiling still
has prominent highlights; visual owner acceptance remains open. Camera collision
is retained, and the chair naturally hides part of the seated lower body.

The boarding fixture briefly holds game/character ticking for the photographed
sit poses, restores them before native departure, and temporarily permits the
chair's account commit only inside its validated scratch save directory. These
disclosures exclude physical-input, uninterrupted-transition timing and FPS claims.

### Affected save-lifecycle fixture isolation

`FreeFlightIsolation26.log` stops before Unreal because this machine's `Artifacts`
directory is a C: to M: junction, rejected by the existing no-reparse-path guard.
The bounded repair adds explicit `-WorkspaceLocalArtifacts` to
`Scripts/TestSaveLifecycle.ps1`; it selects only the real workspace directory
`.agent/local/SaveLifecycle/<GUID>`. PowerShell, native test and C# fault gate
must agree on that explicit mode and retain the marker, root, backend, token and
production-save guards. Default paths and the reparse rejection remain intact.

`SaveLifecycleLocalPathChecks.json` records successful parser/C# compilation and
ten root/marker/reparse checks, including the allowed local ancestor and rejected
production, sibling, nested and junction paths. Build27 compiles only the changed
native test path and succeeds in7.51seconds; it adds no further gameplay change
after Build26. Build success is not save lifecycle evidence.

The fresh `FreeFlightIsolation27` run reaches the isolated native backend, but
**fails** in its fourth child. Receipt
`.agent/local/SaveLifecycle/0add00143f324fef89369943c471320e/result.json` retains
clean Preflight, Suspend and FreeFlight phases, followed by
`FreshAfterFreeFlight` process exit3 in `ASSGameMode::EnterStation`. The first
three phases prove rejected practice-session survival writes, preserved temporary
account/checkpoint bytes and allowed practice-settings persistence; they do not
prove fresh-process resume. Production save hashes remain unchanged. Root-cause
repair and a fresh full isolation run are required; Station2 discard is also
pending. No pass is inferred from partial phase success.

Build28 succeeds in7.01seconds with only the lifecycle fixture's missing normal
PlayerState initialized. The earlier controller-destruction crash does not recur.
`FreeFlightIsolation28`, fixture
`841d14dbe1f94f779f995206d6799e3f`, again passes the first three phases; the fourth
process exits0 but its automation report is **Fail**, with three log errors and
no guarded success receipt. The harness correctly rejects it. Its
`FreshAfterFreeFlight/Report/index.json` exists; the missing item is the success
receipt, not the automation report. Production save hashes remain unchanged.

Read-only diagnosis ties the errors to `USkeletalMeshComponent::SnapshotPose`'s
`SkelMesh != nullptr` check. This standalone fixture never begins Play;
`ShowHangar` spawns the parked ship, whose pilot mesh normally initializes in
`ASSShip::BeginPlay`, while `WearHero` initializes only the walker. Continue then
reaches `EnterStation`'s unconditional pilot pose snapshot. The report has no
failed gameplay assertion, but the missing fixture initialization prevents a
clean receipt. The log separately records the Scout skeleton's missing
`/Engine/EngineMeshes/Humanoid` dependency. These are retained failures, not proof
of a defect during ordinary initialized gameplay. Completing this bounded fixture
repair and rerunning fresh resume, plus Station2 discard, remain required. The
owner's current priority is the L lounge quality pass; no broader test rerun is
implied by this diagnosis.

### Weapon readability after timing repair

`EndgameSoak/4e20d3765a544573b01edc2e7dfb7b5b` (`WeaponQuality24`) succeeds and exits0,
preserving the production save/build guards. All four RapidShot/RapidHit/CannonShot/
CannonHit images exist. The real hit path reduces a normal55HP target to43 with the
rapid laser and4.599998 with the cannon; each hit image records actual0.28second
damage feedback. Two uncaptured real shots warm rendering before review.

This is9.092simulation seconds of scripted flight with ordinary starter stats,
scenery collision and one target at a time. Target AI and Director are paused for
the isolated shot check. It does not prove cold first-trigger readiness, unlocks,
natural combat balance, physical controls, device audio or performance. Earlier failed
timing/occlusion receipts remain above; this success supersedes their pending repair.

## Research used

Consulted October 6, 2026: Epic's [instanced mesh documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-static-mesh-component-in-unreal-engine),
[physics sub-stepping](https://dev.epicgames.com/documentation/en-us/unreal-engine/physics-sub-stepping-in-unreal-engine),
and [performance profiling](https://dev.epicgames.com/documentation/en-us/unreal-engine/introduction-to-performance-profiling-and-configuration-in-unreal-engine).
Installed UE 5.8.2 source was checked for collision-state creation, solver synchronization,
animation copying and input-capture behavior. Advice was not treated as a runtime pass.

## Still required

Apartment traversal and tail motion now pass their bounded native/rendered checks.
Centered settings tabs and fit pass independent rendered review at both sizes;
the final 720p/UI1.4 pause capture and moving-field evidence are recorded above.
Incremental streaming reduces matched handoff CPU peaks by about80percent without
thinning, as detailed in [Performance](../PERFORMANCE.md). The earlier failed
normal-speed `3cf519d467da4356bf8a34d35ad9684e` capture and rejected, nearly
stationary `abed63cba4d04637b9c5ada75d8b1aee` capture remain historical failures;
neither supplies the later successful moving-field claim.

Editor17 built successfully in12.89seconds. Its subsequent weapon-readability
capture `a7d7ccf385db41eaa69f17264c06c5d8` did not reach its target-damage check:
the two-frame warmup crossed its0.5second deadline at0.533seconds. The fixture
deadline ordering repair is validated by WeaponQuality24 above. Earlier diagnostics
identified a target hidden behind camera-side geometry; the fixture now requires
camera, muzzle and real-aim visibility and actual target health loss. This bounded
weapon-feedback pass is separate from listening and natural combat acceptance.

The separately requested owner-platform preview is documented in
[its own receipt](2026-10-06-owner-platform-preview.md); the live station has not
been replaced by that preview. Phoenix walk-to-chair departure has native and actual
camera and cabin-lighting evidence above; affected save-lifecycle checks, physical
controls and owner feel remain under validation, followed by a current packaged candidate.
Physics rebound and affected Director/Waves1–10 orchestration assertions pass, subject
to the fixture and known apartment-warning limits above.
Human survival balance, device input, sound preference and owner acceptance remain distinct.
No merge or new itch upload is authorized by this repair request.
