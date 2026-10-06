# Owner platform preview — October6, 2026

The owner replaced the dual-rock layout in Blender, added platform pieces, saved
again before closing, and requested its actual Unreal appearance. This is an
isolated preview, not an accepted layout or a replacement for the live station.

## Input and preservation

- Final input: `C:/Users/j6sis/Downloads/Wayfarer-Working-20261006.blend`,
  SHA256 `77854941d44fe6c49fd5558818f796b9f5a78c0a4c8a8b4c1aab4dd08d6169ce`.
- Final camera and all12,338 mesh rows match the prior live capture; final disk
  geometry was independently read with background Blender5.2.2 and left unchanged.
- Snapshot `7021c48bc2a34cf1ae3c8ab2029f67fe`: one moved Foundation, one removed Rear
  massif,24 additions. The additions exactly match their source geometry/topology/UVs.
- Foundation topology and UVs remain unchanged, but vertices were edited. A private
  GLB transfers that shape; exactly one mesh/node,150,192 triangles, no embedded
  textures/materials. GLB SHA256
  `40251acd748be6878b20e04ec085dc413ea640ecd51868eacbd3be5fcbe43948`.
- Excluded298 pre-existing hidden helper import-transform artifacts and5,143
  unchanged locked references. Collection visibility is not interpreted as deletion.
- Four original maps plus the source rock and its material pass SHA256 preservation.
  Canonical Wayfarer remains `9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.

## Output

Open `Edit Owner Platform Preview.cmd` in the canonical project. Its dry-run resolves
the actual engine, project and private map without opening a window or changing data.

- Map: `/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006`.
- Map SHA256: `00c476601646261409a6e48c11072cd5d41ecdefce28df4af9504fd036516a37`.
- Mesh: `/Game/OutpostSandbox/OwnerPreview/SM_OwnerFoundation_20261006`.
- Imported local bounds agree with final Blender export within0.00000334cm.
- All25 moved/added transforms and26 total operations match the final manifest.
- This folder lies outside automatic SpaceSurvival cook roots and is not a MapsToCook
  entry or runtime reference. No package/publication was performed for this preview.

Full private inputs, manifest, guards and four1600x900 images live under
`.agent/local/SurvivalQuality/BlenderRender/UnrealPreview`:
`Images/01_Overview.png`, `02_LandingAndPlatform.png`, `03_PlatformSide.png`,
`04_StationEntrance.png`. The capture uses original Unreal materials/level lighting,
with no exposure/material overrides. Saved-map hash is unchanged after capture.

## Findings and limits

Lead and independent reviewer confirm the single rear rock, front platform, existing
globe/market/entrance and added side supports match the owner revision. The outer
ring uses `CyberpunkHolograms/MI_RoundShip`: green, translucent and scan-lined, with
its top12.75cm below the existing pad. The rear blue Megacube is also holographic.
These are material properties hidden by the textureless Blender preview.

No obvious new obstacle crosses the central entrance approach in the four views.
Dark overlapping side structures still need ground-level walking/clearance review.
Images establish appearance, not collision, gameplay or performance acceptance.
The live station is unchanged pending deliberate adoption.

The first GLB export included a factory Cube and was rejected before import. The
corrected file is verified as one mesh/node. Authoring and fresh reload/capture wrote
valid receipts and verified hashes, but both Unreal processes returned0xC0000005
after `LogExit: Exiting`; this previously observed shutdown failure is retained,
not reclassified as a clean exit. Original-map preservation and completed render
evidence remain separately verified.

## Owner-approved refinement, October 6 after 10:40 UTC

The owner subsequently saved all edits and quit Unreal, then approved six room
design targets. This supersedes the original preview hash above as the active
authoring baseline; the original preview receipt remains historical evidence.
The saved owner input is SHA256
`7b91bf543ce76952d3687a682a989a622b8a9378fd9d53ae347da1e4588e1e0b`, backed up under
`.agent/local/StationRefinement/OwnerBackup`. The canonical live map remains
unchanged. Per-room visual approval is still open under RPT-20261006-04.

Guarded authoring receipts are in `.agent/local/StationRefinement`:

- `Surfaces1.json`: three private platform variants remove coplanar overlap and
  provide clearances around the recessed home connector; actor transforms and
  the original assets remain intact. Entrance backing uses component overrides.
- `Social2.json`: corrected native rotations, complete bar, conversation groups,
  food and arcade arrangements; duplicate market islands retired reversibly.
- `Operations1.json` from the successful `Operations2.log` run: complete central
  workstation moved to T, four staffed desks, native seated Nyxar animation,
  retained R hologram bays, reception ring and seven information points.
- `SocialPolish1.json`: private textured material children, three blue display
  panes, supported bar fixtures and local lighting changes. Current map hash at
  this checkpoint is `e1f383e38b1734e201a00f69ab55cd2e6c8f93eb02f41871ce49dbe6bb943a5a`.

`RoomPass2/manifest.json` records nine actual 1600x900 Unreal views, clean process
exit and unchanged saved map. These views remain below the approved targets:
furniture distribution, legible screens/signage and light balance need another
pass. The first visual pass exposed positional Rotator argument ordering; the
helper now uses explicit pitch/yaw/roll keywords and Social2 reapplied only that
bounded furnishing pass. Failed receipts remain available.

`Geometry1.json` is native authoring evidence, not a gameplay traversal pass.
The changed room routes have clear static character-sized capsule sweeps; all
230 protected HomeHub transforms match the owner baseline. The apartment route
fails with 11 capsule obstructions and 35 incorrect floor samples against
`Owner platform/SM_Arco_Tubo`. That newly identified foundation obstruction still
requires repair and a fresh check. No pass is inferred from preserved transforms.

The supplied cargo ship has no usable boarding opening at the inspected side,
fore or aft positions. `CargoVariant/dry-run.json` passes the bounded private
doorway proposal with source hashes preserved. The first authoring attempt saved
the derivative but stopped before cutting because SaveMap did not switch the
active world; the retry explicitly loads and compares the private world before
editing. Native reload, doorway clearance and actual traversal remain required.

The optional service-anchor change in SSStationOutpost.cpp keeps interactions
with moved equipment while retaining old-map fallbacks. It postdates Build19
and requires a new native build. No package, publication, canonical-map adoption
or owner acceptance has occurred in this refinement checkpoint.

## Refinement follow-through, October 6 at 12:20 UTC

The following evidence supersedes the unresolved authoring defects above without
removing their failed receipts:

- `FoundationFix1.json`: the owner's ring had a simple convex collision shape
  filling its open center. A private mesh copy retains every visual vertex,
  material and transform, with accurate triangle collision. `Geometry3.json`
  has zero failed room/connector checks and preserves all 230 HomeHub transforms.
  The separate apartment instance was not loaded for that check, so this is
  partial authoring evidence, not an interior walking pass.
- `SocialFollowup1.json`: three complete conversation groups moved inward;
  three mounted table lights, two bar keys and larger vendor blade signs improve
  the existing layout. The center walking route remains open.
- `ServicePolish1.json`: private floor/ceiling finishes, corrected native display
  opacity and two-sided panes, and bounded existing fixture intensity. No actor
  transforms changed. Source textures and materials remain available unchanged.
- `ServiceGraphics1.json`: nine mesh-matched native screen variants and the
  three actual Goliath screens use private readable display derivatives. Exact
  service and room labels use the existing unlit font graph. The old Archive
  heading is retired. Map SHA at this checkpoint is
  `3cf0292c78537eb7b69c072afe4551f8328a0ace82c3580529c014b5396aa1a0`.

`RoomPass3/manifest_recovered.json` records ten valid images with unchanged map
bytes. Its post-capture geometry callback failed because `Scripts` was absent
from the Python import path; its task-owned editor was subsequently terminated.
These are usable appearance images, **not a clean-exit capture or geometry pass**.
The next capture uses protected output paths and cleanup in a `finally` block.

Cargo authoring/reload succeeds in a private full-ship derivative. The first
hatch repair passes 28 interior floor samples and six standing capsule sweeps.
The reverse rendered view then reveals a backing sheet missed by that original
range. `CargoOuterBoundary.json` identifies the private Plane3 sheet as the
outward blocker. Wider bidirectional checks and a finished doorway lining are
required before station placement. All original cargo assets are preserved.

Build20 compiles the optional station service anchors. Its focused cockpit/hero
batch reports six clean, one warning-bearing and two failed tests. Build21
compiles the bounded chair-support and parked-collision follow-up, but the chair
route still fails: `CockpitTests21` has one pass and one failure. The initially
requested parked-collision filter used the wrong test namespace and did not run;
it is not counted as coverage. The actual namespace is
`SpaceSurvival.Presentation.PhoenixParkedCollision`. Missing material properties
on the existing apartment `BP_Blinds` remain unsuppressed warnings in the earlier
FreeFlightLifecycle test. No packaged, natural-input or owner-acceptance pass is
implied by these source builds.

## Saved rooms and cargo berth, October 6 at 13:00 UTC

`CargoHatchFinish/finish.json` supersedes the incomplete hatch evidence above.
The remaining private backing sheet and artificial cap triangles were removed
only inside the measured opening. Four owned frame panels finish the sleeve.
A fresh reload passes 28 floor samples and 12 bidirectional character-capsule
sweeps, including both 75 cm and 88 cm half heights. Supplied cargo assets remain
unchanged. `CargoPlacement1.json` places the complete derivative at its berth
with a continuous 22 m by 3 m gangway; the framed opening is 220 cm clear.
These queries do not establish actual traversal. CargoReview3 and CargoPlacement1
both produced valid receipts but exited with 0xC0000005 after LogExit; those
teardown failures are retained separately from successful asset writes.

`Skyline2.json` records bounded existing-fixture accents without new fog or a
global exposure change. `DisplayWall1.json` records three complete 6 m by 3 m
Operations display assemblies and a 4.5 m by 3 m Archive pane. Private native
material derivatives retain kit graphics but prevent the animated field from
fading completely to black. The current saved preview SHA is
`5f335c3dd662b641354afc0ebd6e2b18f1ab2770c8630d1b636934b0f8ff20e8`.

`RoomPass5/manifest.json` captures seven actual 1600x900 Unreal views with clean
exit and unchanged map bytes. The Operations graphics remain visible in two
samples approximately 17.5 seconds apart. Actual cargo berth, gangway and cabin
views show a connected deck and open sleeve. Independent image review still
finds Operations desk distribution and Archive display hierarchy below the
approved targets. The right-facing Archive camera does not see the modified
left-side pane; that pane's appearance remains unverified from this batch.

The fully loaded apartment check in `RoomPass5/geometry.json` retains two
Floor7 route-height/threshold failures. Earlier Geometry3 did not load this
instance and must not be used to close them. RoomWalk1 failed on a canonical
path comparison before Play; RoomWalk2 failed on an unavailable Python spawn
function before walking. Both preserve maps and saves. A reflected-API preflight
and normal editor-pawn duplication replace that unsupported test setup in
RoomWalk3; actual walking is still pending at this checkpoint.

Build22 passes and `CockpitTests22` passes both PhoenixCockpitDeparture and
PhoenixParkedCollision with zero warnings. These exercise ordinary character
movement to the chair, the seated handoff, pause and save-failure rollback.
PhoenixBoarding1's scripted route passes but its fixed review camera sits
outside the cockpit wall, so its blocked chair images are rejected as player
view evidence. Build23 initially failed a TObjectPtr deduction in the revised
capture; Build23-Retry passes after the explicit APawn pointer correction.
PhoenixBoarding2 uses the player's actual camera and completes the eight-view
runtime fixture with clean exit; visual review remains required. No production
camera change is inferred from the first fixture's bad camera.

This work remains in the owner's separate editable preview. Canonical station,
published package, natural-input acceptance and individual room approval are
unchanged.

## Connected cargo route and room detail, October 6 after 13:00 UTC

The following receipts advance the separate preview without replacing the failed
checks above or accepting the room designs:

- `RoomComposition1.json`: two complete Operations desk groups, including their
  operators, lights and service anchors, move 300 cm forward and 300 cm inward.
  Three Archive case labels and their mounted lights are adjusted. All 8,026
  unrelated actor transforms are preserved. Static capsule/floor checks pass;
  the changed service approaches still need actual walking and fresh views.
  Saved map SHA becomes
  `235405852b0f908f46d8a2fdecd177661121441a090881cd0cf7fcc5598cf15b`.
- `SocialDetail1.json`: 22 owned bottles, four menu labels and two local shelf
  lights furnish the backbar. Existing actor transforms remain unchanged and
  new parts stay outside walking routes. Authoring succeeds; appearance is
  pending a rendered review. Saved map SHA becomes
  `a18478938dacb1d1768e0c713b4d5b15dfafb170c7acc0b018f8e431eb345457`.

`RoomWalk3.json` proves ordinary CharacterMovement through Social,
Operations, reception and the loaded Home apartment out and back, with zero
observed unsupported time, off-deck observations or movement discontinuities.
Those results bind the earlier `5f335c3d...` map and do not validate later desk
placements. Its cargo route fails immediately: the initial point is outside the
actual circular visitor pad, and the walker falls 114.6 cm before any cargo travel.
`CargoApronProbe2.json` confirms an unsupported gap between the pad and gangway.
RoomPass5's apparently connected deck image was insufficient physical evidence.

`CargoConnection1.json` repairs that real gap with a 10 m by 3 m apron extension
from the existing visitor pad to the original gangway. Textured deck panels,
matching rails and continuous simple collision provide support; the deck is
2 cm above the pad and old gangway at its joins. All 135 floor samples and both
standing-capsule sweeps pass. Protected assets remain unchanged. Saved map SHA is
`c176006ae0e09327c24234c9a046577d3386308634bf06ab6d182469072cc542`.

`RoomWalk4.json` binds that exact map and reports
`PASS_SCRIPTED_CHARACTER_MOVEMENT_ONLY`: all 15 outbound/return waypoints reached,
81.46 m travelled in 31.02 game seconds, zero falling or unsupported time, zero
off-deck observations and zero movement discontinuities. The route starts on
`Ground/Visitor berth 02` at (-1860, -3900, 0), crosses the new apron and gangway,
enters the cargo interior and returns. It uses one initial spawn and ordinary
CharacterMovement thereafter; the test did not move its start onto the ship to
bypass the missing connection. Five map hashes and three real save hashes remain
unchanged, and PIE stops. **The engine process exits 1**, with repeated existing
apartment `BP_Blinds` null-material PIE errors before the route. There are no
fixture-reported errors or crash in this run. The route success is retained with
that engine-error limitation, not relabelled a clean process or natural-input pass.
The new apron still requires its final rendered join review.

`SocialSeated1.json` then succeeds with process exit 0. It seats the two existing
Lounge conversation actors on the south sofas of two conversation groups using
a private four-second Nyxar clip. All 121 animation keys are checked: feet remain
about 0.60 cm above the floor, lowest hip skin is 42.30–42.36 cm above the floor
over the measured 41.29 cm cushion, and hands remain 1.07–1.12 cm above the posed
thigh surface. Only 12 rotation tracks change; bone translations/scales, source
assets and 8,120 protected actor transforms remain intact. Five native pose
readbacks and three full-player capsule aisle sweeps pass. This is authoring
evidence; relaxed appearance, sofa contact and the loop still require actual
rendered review. The SocialSeated1 checkpoint map SHA is
`3526bb5ed00e5957b148d8fee6b4e2692bdda47aa4a0820f69df4b3a51db1067`.

## Phoenix player-camera repair and remaining cabin light review

Actual-camera review of PhoenixBoarding2 exposes a production problem: the spring
arm retracts through the hero when its origin moves into the pilot chair during
sitting. The bounded repair holds the spring-arm origin at the standing chair
approach during that animation, retaining native rotation and collision. A
cancelled handoff restores the original relative camera anchor. Build24 includes
the repair and the existing cockpit test's camera/rollback assertions.

`Artifacts/EndgameSoak/776936029d5e470687f0331e64af5c72` is PhoenixBoarding3:
eight actual possessed-pawn camera views, native same-hero handoff, zero off-deck
rescues, restored fixture guards and process exit 0. Chair, mid-sit and seated
views keep the camera at ship-local (449.884, 0, 542.065) cm; seated camera-to-pelvis
distance is 421.22 cm, with no camera sphere overlap or render-view lag. Lead and
independent image review confirm the self-clipping is gone. The chair naturally
occludes the lower seated body, and the cabin is still too dark to accept its
presentation. The fixture discloses one initial placement, scripted input and
brief pose holds; it does not prove physical-input feel, uninterrupted transition
timing or performance.

Build25 succeeds, and its parked-collision test passes all lamp-toggle assertions
without warnings. Two measured ceiling-mounted, parked-only shadowed cabin lamps
use explicit lumens and zero volumetric scattering. Exterior fill, materials and
global exposure remain unchanged. PhoenixBoarding4's eight actual-camera views
show improved cabin visibility but an excessive white cockpit reflection.
Build26 changes only the cockpit lamp's specular scale to 0.15; the focused test
again passes without warnings.

PhoenixBoarding5 (`Artifacts/EndgameSoak/9dbf09238fa045c99356e9d4c1ceceb7`) exits 0
with eight actual possessed-pawn camera images, 23.42 m of ordinary walking,
zero rescues, same-hero native handoff and 0.2223 cm handoff pose error. Saves and
fixture guards are preserved. Lead and independent image review confirm a coherent
walking/seating camera and more readable cabin, with the chair naturally occluding
the lower seated body. The original glossy ceiling still has prominent highlights;
this is a remaining presentation limit. Scripted inputs and capture pose holds
do not establish physical-input feel or uninterrupted transition timing.
Canonical station adoption, packaging/publication and owner approval remain open.

## Lighting containment and final room dressing, October 6 at 14:15 UTC

`RoomPass6/manifest.json` records 13 actual 1600x900 Unreal views, process exit 0
and unchanged SocialSeated1 map bytes. Lead review confirms the seated characters'
sofa contact and feet, while identifying an obscured bar menu, a counter seam,
overbright bottles, oversized service labels and sparse room dressing. These are
appearance findings, not room approval. The inherited whole-level geometry check
still fails at Home route segment 26: the capsule from (6700, 4520, -170) to
(6700, 4700, -170) encounters loaded `SM_Sofa_2`. The successful RoomWalk3 apartment
route and this distinct failed static probe are both retained; neither supersedes
the other by assumption.

- `Compatibility1.json` enables Nanite usage on the project-owned
  `M_OutpostGraphite` without changing its graph, and disables Nanite on the one
  Main threshold frame component whose source slots use additive materials.
  Vendor hashes, transforms, materials and lighting remain unchanged. Map SHA is
  `9b5c8d3b968d47e3e91caad0d0fe40e7245737b52a6c13893cefd35fc1b7a16b`.
- `CargoLighting1.json` changes only the separate private `L_DockedCargo` map.
  Resident inventory finds 349 lights, 345 enabled and 325 enabled shadow casters.
  Four 16,384 cm-radius lights formerly reach surrounding station rooms; their
  radii become 3,500/3,500/2,500/2,500 cm. The 126 paired accent components on 63
  supplied Blueprint actors become non-shadow-casting with 300 cm radii. Original
  intensities, colors, materials, geometry, poses, principal cabin/walkway lights
  and supplied asset hashes are preserved. Exactly 130 components change.
  Private cargo SHA becomes
  `d4629f62ed803c7460d3cd900c140d52b7ba50360e71104de298c0a2c3bab7ba`;
  owner-map bytes are unchanged. Spatial route analysis reduces maximum caster
  overlap from 65 to 15 and station-room reach to zero. This is not per-pixel
  overlap or GPU/FPS measurement; persisted Blueprint overrides require reload.
- `SocialFinish1.json` mounts the complete menu on the refrigerator front, covers
  the measured 10 cm counter join with a 14 cm saddle, reduces two shelf keys from
  700 to 160 lumens and their specular scale from 0.35 to 0.08, and adds three small
  warm table practicals with supported meal/fruit/drink settings. Two three-unit
  native planter dividers frame the conversation groups while preserving the
  central player route. Native bounds, floor/capsule queries and source hashes
  pass; all seated and owner poses remain unchanged. Saved map SHA becomes
  `6aec669fa1379ad83856a736ddc5f7e6d2e80182b381b2c4610c3f7e977425b5`.
- `ServiceFinish1.json` fits five service labels to backed desk-front plaques and
  the Archive identity to a wall-backed plaque. Service roots/anchors and operators
  retain their positions. Four native 120 cm planters and six noncolliding floor
  inlays add bounded Operations/Archive detail. The existing reception staff lamp
  moves closer to its subjects with 1,100 lumens, 450 cm radius, specular scale
  0.15 and zero volumetric scattering; no shadow caster is added. Full room-route
  floor/capsule checks pass before and after, with 8,141 unrelated actor poses
  and protected source hashes unchanged. Saved map SHA becomes
  `762e366a4383aec3526d4b787b27f97b20a742dd0aa847ed7da498e21dab3d59`.

All four authoring processes exit 0. `RoomWalk5.json` binds the Compatibility1 map
and exercises only the changed Operations service approaches: south 22.7297 m in
11.3991 game seconds and north 22.7288 m in 11.4030 seconds. Every waypoint is
reached with zero falling, unsupported time, off-deck observations or movement
discontinuities. Each disconnected route receives one initial placement, then
uses ordinary CharacterMovement; all four moved services are approached without
transactions. Map/save hashes remain unchanged and PIE stops. **Process exit is
1** because existing apartment `BP_Blinds` null-material PIE errors remain; the
route fixture itself reports no errors. This fresh log has no observed prior
Graphite/additive-Nanite warning or VSM overflow message, which does not establish
all-camera performance or the final room-lighting appearance.

`RoomPass7Retry1.log` and `RoomPass7/manifest.json` subsequently record all 13 fresh
1600x900 images against the ServiceFinish1 map. The first RoomPass7 attempt refuses
stale output paths before writes; the retry corrects those fixture paths. Saved
owner and cargo map hashes are unchanged. Resident `LoadedLights3.json` and
`cargo_persisted_lighting.json` verify all 130 expected cargo component overrides
with zero mismatches. The changed service approaches still pass static checks;
the distinct inherited Home/sofa probe remains failed. **The process exits 1**,
and its log retains existing `BP_Blinds` material warnings and a VSM max-lights
overflow at 14:27:30 UTC. Containing the cargo lights therefore did not establish
that all station lighting warnings are resolved or that frame rate is accepted.

The owner subsequently rates the station **4/10**, improved from their previous
2/10 but below the approved concepts. The direction and cleanup are accepted;
individual rooms are not. The owner narrows the next aesthetic pass to the
**L social lounge first**, including a coherent owned pool-table scene with aliens
and heavy troopers whose poses/animation fit the activity. Actual views still
need material cleanup and stronger composition; extra dressing alone is not the
acceptance criterion. Preserve the saved architecture and other rooms while that
standard is established. The flat cyan ring/beam appearance is also rejected for
later physical fixture refinement. No canonical station replacement, package,
publication or overall room approval follows from these captures.

## L lounge ambient pool authoring, October 6 at 15:35 UTC

`OrbitLounge3.json` saves the bounded L lounge pass successfully; the lead observes
native process exit 0. This supersedes the ServiceFinish1 preview hash with
`b88d3d741443a408c72aa2c7f1918c5b7b08b0179425c7908ae6e724626d55d3`, independently
matched to the saved map bytes. The canonical Wayfarer hash remains
`9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.
The author receipt SHA256 is
`b98e6b82b2ec8080ee60361820e62922684e063f25cbd62cdf062b824499a6db`.

The owned pool-table assembly replaces one repetitive conversation pocket; the
complete nearby dining group moves together. A Nyxar shooter and alien partner
face two heavy troopers. Three restrained ball materials, score glass, a private
green-shrub material, the compatible Nyxar animation and its LevelSequence are
the seven saved assets, all under `/Game/OutpostSandbox/StationRefinement`.
Six active planters receive supported soil/foliage and bounded component material
overrides; the three retired east-divider planters stay retired. Two owned light
fixtures replace the remaining agent-authored pendant assemblies, with local
light balance changes. Supplied assets, owner architecture, floors, global
exposure and other rooms are preserved by the author guards. All three central
aisle capsule sweeps remain clear at radius 34 cm and half-height 75 cm; these
static queries are not a fresh walking or performance pass.

Evidence is separated by what it actually measures:

- `OrbitPoolProbe1.json` reads native pool triangles and standing Nyxar bones,
  preserving all eight inspected source asset hashes. `OrbitPoolFit1/2.json`
  evaluate the pose against those captured data offline. Neither is playback or
  rendered contact evidence. `OrbitPoolIntegrationProbe1.json` fails on the
  Python skeleton accessor; Probe2 succeeds after using the reflected property
  and verifies that the trooper mesh and idle clip share their actual skeleton.
- The saved clip spans 14 seconds at 30 Hz with 421 sampled poses/cue transforms.
  Native pose readbacks at frames 0, 75, 105, 204, 210, 215, 285 and 420 have maximum
  position error 0.00006334 cm. Its source mesh/animation hashes are preserved.
  The measured felt is at Z 80.06 cm. At the authored seven-second contact, the
  cue tip reaches the south tangent of the 2.837515 cm-radius ball centered at
  (4800, -3225, 82.897515) cm. The fitted bridge skin is 0.5158 cm above the felt
  at contact, and sampled feet stay at least 0.5863 cm above the floor. These are
  measured pose/skin-fit calculations and native clip readbacks, not proof that
  the played character visibly grips the cue correctly.
- The saved persistent sequence enables autoplay and indefinite looping, with
  no camera/input tracks. Four prop tracks hold 421 samples each. The initial
  Unreal AddKey path rounds through float32; direct double-value assignment
  corrects it, and all final key readbacks have zero recorded value error.
  Authored ball contacts occur at 7.0, 7.7 and 8.2 seconds, settle by 9.75, then
  lift 12/15/18 cm and return smoothly before 13.8. All 421 frames pass the
  measured felt-bound and ball-spacing checks. This is ambient choreography,
  not a playable billiards system or simulated collision result.

Failed `OrbitLounge1/2.json` receipts remain intact. Attempt1 stops before saves
on the transform-key precision check and also records the unsupported Python
`get_sequence_player`/`QualifiedFrameTime` names; reflected `sequence_player`
and `QualifiedTime` are used in the corrected capture helper. Attempt2 stops
before saves when the inherited shrub vector parameter rejects the first
override path. Attempt3 verifies explicit private overrides and the corrected
native authoring/readback path before saving.

The subsequent `OrbitPlayback1/manifest.json` succeeds against that exact saved
map, with zero fixture errors and native process exit 0 independently observed
by the lead. Ordinary SIE time advances for 28.10897 seconds through two autoplay
wraps before any pause or scrub. Its 270 samples record the actual PIE sequence
player, six resolved actor/component bindings, cue and three ball transforms,
and seven native shooter bone transforms. The right hand travels 30.18 cm;
the cue and all balls move. This establishes played motion rather than only
a timer or authored key presence.

After those two loops, the actual player is paused and scrubbed to 6.5, 7.0,
7.5 and 11.5 seconds. Two camera actors prepared before SIE resolve to native
PIE duplicates and produce eight 1600x900 images. These are explicitly paused
sequence views, not screenshots of uninterrupted natural play. All 21 guarded
map/asset/source/evidence files and three save files are unchanged, and PIE stops.
The ship snapshots are empty before and after: this sandbox has no `SSShip`
actors, so that preservation check is not evidence of a flying or boarded ship.
The manifest intentionally leaves process exit null and visual acceptance pending;
the later external process result and review are recorded here separately.

Independent review of all eight images rates the staging approximately 6.5/10
but the hands 4/10: the bridge palm faces upward and the rear hand remains open
instead of gripping the cue. Those visible defects remain unresolved despite
the successful fit/readback/playback checks. A bounded hand-animation correction
and fresh captures are pending, together with the full-lounge composition review.
Loop timing and continuity have recorded transform evidence, but full-speed
visual seam/gesture quality and physical-input feel are not accepted. The owner
has not approved L lounge or any other room. No canonical station replacement,
packaged build, publication or Phase 1 acceptance is claimed.

## Lounge route, room review and revised grip, October 6 follow-through

`RoomWalk6.json`, from `RoomWalk6Retry1.log`, exercises the OrbitLounge3 layout
from the entrance around the pool and back along the bar aisle: 51.8652 m in
22.0386 game seconds, zero falling/unsupported time, zero off-deck observations
and zero movement discontinuities. It uses one initial native spawn and ordinary
CharacterMovement thereafter. Map/save hashes remain unchanged, PIE stops, and
the lead observes process exit 0. The first `RoomWalk6.log` remains a failed
missing-wrapper setup attempt; it is not counted as walking coverage.

`OrbitRoomSaved1/manifest.json` records four fresh saved-map views of the lounge,
bar, reverse angle and booth, with unchanged map bytes, zero fixture errors and
process exit 0. Independent whole-room review rates this revision approximately
5.5–6/10: the foliage now reads green, but the center remains dark and repeated
advertising screens weaken the composition. These findings preserve the gap to
the approved target rather than accepting the room from its pool vignette alone.

`OrbitGrip3.json` subsequently saves the private `A_Nyxar_OrbitPool_GripV2` clip,
rebinds the one shooter animation section, and retains the earlier clip. All 421
cue samples and the shooter actor location/rotation/scale exactly match
OrbitLounge3. Eight native pose readbacks pass with maximum error 0.00006334 cm.
The author checks numeric transform tuples and reports zero unexpected actor
moves. Four local return-light actors have 70 cm radii, no shadows and intensity
keys from 0 to 12 lumens during the existing magnetic-return interval. Required
Nanite usage is persisted on the three private ball materials. The new clip,
sequence and three materials are the five saved assets; supplied assets and
canonical station remain unchanged. The author process exits 0, and the saved
owner-map SHA becomes
`361129283bf11cf80f8b4a88a650f7e65f76b1e63ff21e15f5d88e116755466b`.

Failed `OrbitGrip1.json` (wrong Python time-unit enum, process exit 1) and
`OrbitGrip2.json` (stringified Transform identity comparison, process exit 0 but
failed author receipt) both stop before saves and remain retained. The latter
guard is corrected to exact numeric tuples, not a relaxed movement tolerance.
Grip3's copied `sequence.clip` metadata still names the earlier clip; its
`animation.private_clip` names GripV2, and the author script directly verifies
the section assignment before saving. Do not use that stale copied field as
proof of the loaded runtime clip.

`OrbitPlayback2/manifest.json` subsequently succeeds against the Grip3 map with
263 native samples over 28.10821 ordinary SIE seconds, two natural autoplay wraps
and eight paused sequence views at the same four phases and two cameras. There
are zero fixture errors; all 20 guarded files and three save files are unchanged,
PIE stops, and the lead independently observes process exit 0. Native component
readback confirms all four return lights are 0 lumens at 6.5, 7.0 and 7.5 seconds,
then 12 lumens at 11.5 seconds. These are actual sequence-driven intensities,
separate from a claim about their artistic appearance or GPU cost.

Initial lead review sees the corrected palm-down bridge and a more believable
shot stance. The rear grip still looks somewhat loose, including during the
magnetic return. Independent review of the full new batch is pending; the hand
quality issue remains open. The ambient pool scene is a candidate for owner
review, not an accepted room. Successful traversal/playback does not establish
physical-input, performance or Phase 1 acceptance.

## Superseded return effect and alternating-match direction, October 6 at 16:17 UTC

The owner's new direction explicitly replaces the magnetic/levitating ball
reset. A shooter should scratch, visibly pick up and place the cue ball by hand,
then yield to an opposing character's shot and scratch. Uneven pauses and
conversational behavior should make it read as an ongoing match. Balls must not
float or return by magic. This remains ambient station animation, not a playable
pool minigame. The prior two-loop playback receipts remain valid historical
evidence of that earlier implementation, not acceptance of the superseded effect.

Before this direction change, `OrbitGrip4.json` succeeds and the lead observes
process exit 0. It saves the private `A_Nyxar_OrbitPool_GripV3` clip and rebinds the
existing sequence, changing only six right ring/pinky tracks. All actor poses and
cue samples remain preserved; the receipt reports no unexpected actor moves.
Eight native pose readbacks pass. Owner-map SHA becomes
`763a0533cb91d7203c7d1bc2fbd4f1b5a6ff9ea525c5c6aa11ef9db45955863a`, while canonical
Wayfarer remains `9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.
No Playback3 run is claimed: another capture of the discarded reset is deferred
in favor of building the newly requested alternating match. The hand correction
therefore has authoring/readback evidence, not fresh rendered acceptance.
The currently saved map still contains the superseded return behavior until that
replacement is authored and validated; no room, live-build or package acceptance
is implied.

## Grounded match and whole-lounge follow-up, October 6 at 18:03 UTC

`StationPoolMatch1.json` succeeds and the lead observes native process exit0.
The owner preview is saved as
`2e64c159a545d45f58386e6f9007c680a6877300952d1e55ba4eb993eeb8b711`.
Canonical Wayfarer remains unchanged. Five private assets are saved: two native
character clips, the new60second sequence and two lounge display instances.
The original table, characters, animations and material sources remain unchanged.

The new ambient sequence alternates Nyxar and a heavy trooper: shot, scratch,
enclosed return to an exterior tray, visible hand pickup and placement, then the
opponent's turn. Both characters retain their cues; unequal conversational pauses
break up the turns. The old sequence, four return lights and four magnetic emitters
are removed from this preview. Original assets and earlier receipts remain intact.
The opaque return hardware encloses the decorative bags and internal ball transfer;
this is authored scenic movement, not a simulated or playable pool table. There is
no visible floating reset or scale/visibility teleport in the authored path.

Both clips pass10 native raw-pose readbacks, maximum discrepancies0.0000633cm and
0.0000536cm. The complete offline3602-pose fit and two121-frame held streams pass;
sampled recovery poses clear the original wood. Exact placement retains less than
0.1cm fingertip contact with the felt. These measured checks do not establish
rendered hand quality or full-speed animation acceptance.

The same save adds two physically supported1150-lumen,3800K aisle fixtures, three
seated guests in the existing facing sofas, and distinct owned Cosmo/DigitalPanel
graphics on two formerly repeated advertising panes. Native source/material
readbacks and numeric preservation checks pass. All8230 existing actor transforms
remain unchanged during that room pass. The three central aisle capsule traces
remain clear before/after; this is a static check, not a repeat walking pass.

An earlier17cm-pocket derivative was abandoned before any private mesh or level
save. Four retained author receipts exit0 but report failure: unsupported optional
StaticMaterial access, then bounded subdivision failures while correcting long
rail faces. The original11.39cm pockets and table mesh remain intact. The final
return tray solution avoids that geometry change. No failed author attempt is
counted as a successful mesh edit.

`StationPoolMatchPlayback1/manifest.json` subsequently succeeds, with actual native
process exit0 observed separately. Ordinary autoplay runs120.107553game seconds,
1148native samples and two natural60second wraps. Across both turns,77Nyxar and
78trooper held-ball samples track the native left hand within0.038026cm and
0.045347cm respectively. The two other balls remain static; retired return lights
remain off. Source, saved assets, map and production saves remain unchanged.

The16 screenshots are paused evaluations of the actual PIE sequence after those
natural loops, not an uninterrupted video. Both independent reviews inspect all
four room views and rate the whole lounge6–6.5/10. Bar/occupied booths improve;
mirrored COSMOS graphics, faint headings, dark ceiling/unlit-looking central lamps
and pale return hardware remain visible defects. Shot/release poses read coherently;
pickup/carry cameras obscure the hand/ball, so those motions remain visually
unverified despite the contact measurements. A lower free-hand-side capture is
needed; another table geometry pass is not justified by this evidence.

The log still contains existing apartment BP_Blinds material access errors and
VSM light-overlap warnings. Fixture success/process0 do not establish a clean
engine, representative performance or natural owner gameplay. The owner has not
approved any room. No new package, upload or merge is implied.

## Display and fixture correction, October 6 at 18:25 UTC

`StationSocialVisualFinish1.json` succeeds; actual native author process exits0.
Saved owner preview SHA is
`a93824711de0ddae9f7283b404bd0324616a93f5fec8c05e8d97e52982fec148`.
Three new private materials mirror the COSMOS emission UV chains and activate
the existing lamp texture mask. Two private headings face inward with the existing
readable text material. Two110-lumen upward keys reveal the ceiling; all32return
parts use the existing room graphite material. Previous clip/sequence/display
assets and canonical Wayfarer remain byte-identical. Only the two headings change
existing actor transforms.

`StationSocialVisualFinishCapture1` captures four matched room views and four
paused pickup/carry views. Its fixture succeeds with eight images and unchanged
guarded files/saves, but the actual process exits1; apartment BP_Blinds errors
remain in the log. This is capture-only evidence, not another natural playback run.
The COSMOS lettering and headings now read correctly; return hardware has the
intended dark finish. Ceiling light reveals overly plain panels/hotspots, and
central fixture presentation remains weak.

The new pickup views still obscure hand/ball contact. More importantly, the owner
rejects the visible sideways lean and cue penetrating the character. This is a
real pose defect, not a camera-only issue. The65degree sideways pelvis rotation
and inherited cue displacement are being replaced in a separate private revision
with a modest squat/step and cue outside the hip. Existing successful numerical
contact checks do not close that visual failure. Room/arcade work continues in
parallel; no owner approval is recorded.

## Grounded pickup V2 and arcade integration, October 6 at 19:33 UTC

`StationPoolPickupV2_1.json` saves only two new private animation clips and a
versioned sequence; native author exits0. The earlier sequence is retained with
autoplay disabled. Saved map SHA becomes
`fa94a32ad8b7ee4a22aa5a243d6b62eb879cc37b10fa5021e004149f16996b79`.
The65degree sideways pickup becomes a modest forward squat with a step; cues are
parked laterally outside the actual pelvis. Original table/room/assets stay intact.

Arcade import/placement and a fresh ceiling/card finish subsequently save preview
`38ade2223778bf2b425eae624bc8748683b73ab395788a02146afc7b1fc7ad50`.
Seven decorative props include four distinct Acornaut modes, pinball, rebuilt
Credit Exchange and an alien salvage crane. The two rejected prototypes remain
unplaced. Two native ceiling coffers and two landscape screen cards join the room.
The [separate arcade receipt](2026-10-06-local-arcade.md) records exact package counts,
private provenance, static circulation checks, failed/mixed process outcomes and
the clean fresh native reload. No minigame or credit transaction is implemented.

`StationPoolPickupV2Playback1/manifest.json` observes120.106870game seconds,
two natural60second loops and1148native samples before12paused actual PIE views.
Maximum held-ball error is0.0489cm. Fixture succeeds; the lead separately observes
native process exit0. All214guardedfiles and3production saves remain unchanged;
PIE stops. Existing apartment Blueprint material errors are retained.

Lead and independent image reviews find the extreme lean and visible cue-through-
torso defect repaired, but carry frames03/07 still bend the free arm behind the body.
Neither small measured hand error nor process0 establishes natural animation.
The whole room remains6–6.5/10: cabinet fronts are dark, Credit Exchange's rear
blocks the reverse pool view, and cyan coffer trim dominates the composition.
Those findings trigger bounded carry-path and arcade-presentation follow-ups.
This is not owner room approval, natural gameplay, audio or performance acceptance.

## Forward carry and arcade presentation, October 6 at 20:19 UTC

`StationPoolPickupV3_1.json` saves two private clips and a versioned sequence;
native process exits0. Map becomes
`ecb4ec3206c54b43fc9ff7e057ef2bd0ca891cfa5511fc319f1c03687850d050`.
Only the carrying arm/held-ball path changes; V2 timing, grounded body/feet and
cue placement remain intact. The first offline fit's abrupt elbow swivel is
retained as a failure; interpolated poles reduce the maximum frame displacement
to4.18/3.84cm at30Hz. Native hand/contact checks pass; they are not visual acceptance.

`StationArcadePresentation2.json` subsequently saves map
`66e4fe29816ba4e12f052df64f903b19b67e04819d4ac5baf068ceea70458427`,
one private two-sided diffuser material, perimeter Credit Exchange placement and
three supported local arcade RectLights. Native process exits0. Owner explicitly
likes the brighter ceiling trim/general light; those properties remain unchanged.
The abandoned Presentation1 coffer edit failed before saving, followed by a native
post-LogExit crash; its receipt/log are retained. No rejected dimming reaches disk.

`StationPoolPickupV3Capture1/manifest.json` passes13actual rendered views: eight
paused pickup/carry/release poses and five room/arcade/prop views. Native process
exits0;218guardedfiles,3production saves and ship population remain unchanged,
and PIE stops. This is paused-pose evidence, not a new natural two-loop run.
Lead/independent reviews confirm forward carrying arms, readable arcade fronts,
unobstructed pool sightline and visible diffuser faces. The carried cue ball remains
hard to distinguish from gloves/bright hands; stance and timing need natural-motion
judgment. Room rating is6.5–7/10; sparse social floor, blank wall composition and
crane/terminal detail remain below the approved target. Owner approval is open.

`StationArcadeWalk1.json` passes an ordinary91.365m CharacterMovement route to all
four mode cabinets, pinball, crane, relocated credit terminal and back out.
Native process exits0; zero falling, unsupported time, off-deck observations or
movement discontinuities; maps/saves remain unchanged. This does not exercise
arcade gameplay, transactions, physical devices or representative performance.
Existing apartment Blueprint errors remain recorded rather than suppressed.

Owner's new bar references favor futuristic metal/glass and framed practicals
while preserving the ceiling. The real downloaded Bar Counter People FBX has10
bartender and35customer clips on a different rig; retargeting to the selected
female alien is being assessed. No animation integration or complete rebuild is
claimed from the file inventory.

## Occupied table settings and bar inventory, October 6 at 20:38 UTC

`StationLoungeTableSettings2.json` saves three existing-kit table props and moves
one coffee-cup asset, leaving furniture, crew, lighting and original assets intact.
Actual native process exits0; map SHA becomes
`75421e6bb0ee55f75189a136b6c44a2a7e7ac4578f2ce3fb2ce9913bacda69f3`.
The first wrapper failed before backup/save because its resolved-path check rejected
the legitimate Rocket content junction. Version2 validates the exact Rocket,
CyberpunkRestaurant and CyberPunkBarAssetSet01 mounts and all201protected assets;
it does not allow arbitrary external roots. Attempt1's failure and original scripts
remain retained.

`StationLoungeTableSettingsCapture2/manifest.json` has three fresh actual editor
images at1600x900, all238guardedfiles/3production saves unchanged and no PIE.
Actual process exits0. Root and
independent review see supported, non-intersecting table settings. The purchased
CoffeeGlasses mesh is visibly a stack of cups; it reads as service supplies rather
than two individual drinks. This modest detail addition does not resolve the broad
empty floor or repetitive seated silhouettes.

Read-only bar probes preserve sources/map. Exact triangle intersections in
`StationBarNativeProbe2.json` identify the broad serving surface at107.55418cm and
recessed points at92.24733cm. Earlier bounding-box116.01cm and upward-face-band
~82cm interpretations are not the usable broad worktop; do not lift the bar based
on either. Existing counter props were grounded to bounding-box height and need
surface correction. The owner wants futuristic metal/glass/framed practicals and
explicitly approves the current ceiling.

The embedded female-rig probe confirms61normalized bones and a current Nyxar
placeholder behind the bar. The repaired female asset needs the game's intended
178cm presentation scale, not a skeleton reshaped to reach the counter.
`StationBartenderCandidates1.json` fails before saving at imported-object counting,
despite native logs parsing/compressing all45takes. Actual process exits0; all
protected sources/maps/saves are unchanged. The in-memory asset enumeration is
corrected by the separate Candidates2 attempt below; no bartender replacement is
saved to the station by either candidate author.

## Female bartender candidates and corrected pose fixture, October 6

`StationBartenderCandidates2.json` succeeds; the lead observes native process
exit 0. Eleven new private assets under `BartenderCandidates20261006_V2` contain
the source mesh/skeleton, three selected source takes, two IK rigs, one retargeter
and three female preview clips. All 257 protected original/private source packages,
target character files, maps and 3 production saves remain unchanged. The owner
preview stays at 75421e6b; this is candidate authoring, not a saved NPC replacement.
The other 42 imported takes remain unsaved. No source skeleton is reshaped.

The native female mesh height 97.928821 cm uses the game's existing 178 cm presentation
fit, uniform scale 1.817646714. Types 01/02/03 retain durations 31.8333/33/31 seconds;
each has 13 native pose samples. Sampled working-hand heights span approximately
81.83–122.62cm across the three clips. That supports assessing the existing
107.554 cm worktop, not changing body proportions or raising the counter. Individual
working contacts, held objects, feet and loop transitions still require fitting.

`StationBartenderCandidatesCapture1/manifest.json` reports six captures and
preservation success, but its images are rejected. A positional `Rotator` argument
rotates the transient review actor out of its intended upright orientation; the
first image shows an empty floor and the recorded head height is near the floor.
The fixture's successful numeric pose comparison did not catch that shared
orientation error. Original receipt/images remain intact and are not quality
evidence for the animation.

The corrected `StationBartenderCandidatesCapture2/manifest.json` succeeds with
six actual paused PIE poses, two phases of each clip. Explicit pitch0/yaw−90/roll0
and native world head-above-feet checks now guard the review actor. Maximum sampled
bone discrepancy is 0.012322 cm; all 297 guarded files and 3 production saves remain
unchanged, and PIE stops. The lead observes actual process exit 0. These are
transient studio views, not six views of an integrated bartender. Bright studio
highlights and cropped feet limit shading/contact judgment. Full clips, selected
actions, prop attachment and actual room placement remain unaccepted.

Owner direction remains a futuristic metal/glass bar with framed bottle shelving
and practical trim using owned resources. The existing brighter ceiling and room
lighting are approved and preserved. Whole-room review remains6.5–7/10, not owner
approval. No new package, canonical-map replacement or release is established.

The first bounded `StationBarPresentation1.json` author attempt stops before any
material or map save because the coffee-machine footprint fails the unchanged
0.08cm flatness/top guard. Preservation passes; map 75421e6b remains unchanged.
The lead observes a native 0xc0000005 exit after LogExit; the cause of that late
process crash is unconfirmed. Failed scripts/receipt are retained. Attempt 2 also
refuses before saves, with native exit 0 and preservation success. Its measured
support search exposes the rear lip at 112.27235 cm while the machine's center/front
sit over 107.55418 cm, a 4.71817 cm mismatch. Attempt 3 searches forward on actual
triangles, keeping the same 0.08 cm tolerances, full-footprint containment and 13 cm
maximum adjustment. Support passes in Attempt 3, which then fails before saves on
an unsupported direct scalar-parameter property read; native exit 0 and preservation
pass. Attempt 4 uses the already-probed editor-property accessor and also checks
the remaining text/material reads. Failed recipes remain frozen.

## Saved bar presentation, October 6 author checkpoint

`StationBarPresentation4.json` succeeds; the lead observes actual native exit 0.
Receipt SHA256 is
`7698fc88e3c96d3750ca1f1de197886cd5e8401e9e80e0dce8b12ba8f55b6b39`.
The saved owner preview becomes
`3b28fe63c673256b295eb974bd6b1d3c605b48120502e456dc1100e21a4f3752`.
Four new private bar materials and the map are saved. All 321 protected source
packages, six other maps and three production saves remain unchanged; canonical
Wayfarer retains9c83968d. No bartender actor is replaced by this pass.

The pass applies graphite/satin finishes to the existing counter and stools,
adds 39 attached fascia/display/sign parts, including two shelf legs resting on the
actual Engineering floor, and refreshes the existing venue lettering. The six
existing actor moves are four countertop props and two seam pieces. Counter/stool
transforms, owner architecture, existing lights and approved ceiling are preserved.
Center-aisle and bar-frontage capsule queries pass; these are static clearance
checks, not another ordinary walking or performance pass.

All four prop footprints meet the original 0.08 cm support tolerance. The coffee
machine's horizontal adjustment is 4 cm forward, and its base is lowered from
116.01 cm to the actual 107.554 cm worktop. The measured five-point height spread
is under0.000005cm. Its previous rear corners landed on the112.272cm lip. Both
native counters keep their original height.
The actual highest worktop triangles have local normal Z−1, confirming why a
positive-winding-only surface-band estimate missed them. The seam cap is flush
with the broad worktop. No support tolerance was weakened to obtain this result.

`StationBarPresentationCapture4/manifest.json` subsequently passes four actual
saved-editor views; the lead observes native exit 0. All 346 guarded files and
three production saves remain unchanged; PIE is never started. Fresh views show
cleaner counter/shelving, visible strips and supported coffee-machine placement.
Lead and independent reviews still identify distressed/plank-style stools and
broad flat front inserts as weak matches to the sci-fi references. Independent
bar assessment is about6/10; the whole room remains6.5–7/10 and unapproved.
Source/material readbacks and process success do not close these visible gaps.

Earlier room images are older evidence, and the six bartender
studio poses are unsaved staging; neither should be presented as the newly saved
bar. Current saved / unsaved staging / older image identity and exceptions must
precede images sent for owner review. Whole-room acceptance remains open.
