# Bartender visibility and station warp evidence

## Natural bartender observation

2026-10-07, existing owner editor PID52864, loaded Build39, saved owner-preview
Main SHA `c45dd77376d5a90c90df410ffd733e528c1177d5a05d1c17264799e41037e8b9`.
This is an **unsaved editor test**, not a new saved or published build. Held T
and accepted central trials remain in the editor. The new shared NPC fill code
is not loaded in this binary.

`RootFemaleBartender1Review1` exits0. Its three actual2742×781 images and
`LiveOperationsPIEReview1_FemaleBartender1/manifest.json`, SHA
`aed23ca1072d433b9a3c5d3fac99fbc7cbfe10dbd215d0afce318bea3959bccc`, retain
93.001455 seconds,142 joint observations and three natural33-second loop
boundaries. The actual animation instance reports the private female
`A_FemaleBartender_Type02_Grounded` throughout; no pose, clock or animation was
forced. Exact female/counter state, source files, dirty packages, saved map,
player saves, viewport and rendering settings pass preservation. PIE is stopped.

Root and independent review see the selected female behind the bar in customer
and service-side views. Hands remain behind/below the worktop. The closest
recorded left/right hand anchors are51.19/45.65cm behind its rear edge; these
anchors do not establish palm contact. The low third picture contains no
rendered bartender, although its four foot/ball anchors project inside the
image. Technical capture success does not accept that foot view.

The subsequent native `RootBartender_Bounds1_Result.json` identifies a concrete
bounds discrepancy: the component box is centred atZ235.734493 with89cm vertical
half-extent, so its bottom isZ146.734493. Her mesh origin is approximatelyZ0 and
its scaled imported box covers approximatelyZ0–178. The component has no
physics-asset override, the source mesh has no physics asset, and fixed skeletal
bounds are disabled. No height or animation correction is justified from the
missing foot image. Skin contact, purposeful prop handling and owner acceptance
remain open.

`RootFemaleBartenderVisibility2Review1` exits0 with two actual2742×781 views;
manifest SHA `df71e1b17077c1d2b9423115918aa2e3c136f2e0f37452ee8541c4b13e562438`.
Only this female component enables fixed skeletal bounds and sets bounds scale4.
The same low camera now renders her feet and lower legs; the side view preserves
her appearance. Root and independent review accept visibility only. The native
box still follows the animated root nearZ235, but its356cm vertical half-extent
contains the captured anchors. This is a conservative component workaround, not
a correction to the imported mesh bounds or a default for other NPCs. The prior
142-sample envelope plus10cm allowance needs a uniform scale of3.9625; full skin
coverage, cost and continuous sole contact remain unverified. No height, clip,
material, counter or shared asset changed. Targeted preservation passes, PIE is
stopped, and these two component fields remain **unsaved**.

The durable `PlaceStationFemaleBartender.configure_visibility` helper is
female-only and idempotent. Its actual native adoption check reports
`changed:false`, preserving the accepted two fields without setters. Original
placement `apply` still expects the original male actor and must not be rerun
on the current female. The later closure recovery below preserves these fields.

## Warp assets and character sampling

The original P4 `SM_Door300X250_V1_Part1` is a300×250cm upright frame with seven
retained material slots. The owned NS1 portal and NiagaraExamples teleport
In/Out assets load as Niagara systems. The portal exposes size, colour, ring,
dot and light controls; motion, aperture, collision and cost are not yet
accepted. The selected systems remain unmodified.

`RootWarp_DepartureSource1_Result.json` and `RootWarp_ArrivalSource1_Result.json`
read each actual loaded SystemSpawn skeletal data interface through Nwiro's
native object inspector. Both use `SourceMode=Default`, an editor-only Manny
preview mesh, no cooked default mesh, no explicit source actor, no mesh user
parameter and no component/class filters. Merely mounting the burst on a gate
does not supply the player's animated mesh. The focused source repair attaches
each burst to the actual walker's registered skeletal component before
reinitialization/activation. It preserves the effect's world transform and
detaches the departure burst before teleport. Cancellation, walker/gate teardown
and the arrival timer deactivate and restore the authored gate attachments.
Shared Niagara assets and their data interfaces remain untouched. Actual skin
sampling and local-space appearance still require a runtime visual check.

Build44 `-NoLink` succeeds after two compile actions in18.21seconds. Its log SHA
is `19d26e8beeff1ded1cd82ea9c9f52d1b406fd8ab4c669ed94d4252be9be69f10`.
Installed engine deprecation warnings and newer-than-preferred MSVC remain;
no project-source warning is reported in this compile. This builds object files
only. The Build39 DLL stays SHA
`582d1fb955480af2d399d19bd393de0340d87657f02f7dafa1f0c658e7472390`,
and Main staysc45. No link, reload or restart was attempted.

Source review then found `IsMoored` is depot-only: normal ShowHangar and
EnterStation call `FinishDocking`, which disables ship ticking instead. The
gate now requires the actual same-world mode-owned ship in that parked state,
retaining all station/pair, phase, possession, transition and floor guards.
Root and independent source review pass. Build45 `-NoLink` compiles the one
changed unit successfully in6.96seconds; log SHA
`cd4f8a88d73bfd2274faece94d6f5f2759c84051c3709f974f6e5f7fe5ad4c45`.
Normal flight/takeoff keep or restore ticking. No gameplay acceptance follows
from this source correction.

The colon-containing subobject route is rejected by `read_asset`; the native
object inspector accepts the already-loaded reference. Python's reflected class
lookup enumerates these interfaces, but its base wrapper does not expose their
derived properties. Failed reads are retained and are not asset-load failures.

The current owner preview uses `ASSOutpostSandboxGameMode`, derived from
`AGameModeBase`. It is not an actual moored `ASSGameMode` station visit. Its
decorative Phoenix cannot establish runtime warp endpoints or travel behavior.
Actual runtime verification, natural travel both ways, cancellation, obstruction,
pause, controls, visual quality and performance remain unverified. No package or
publication changed.

## Runtime placement source

The six-file source integration adds `SSStationWarpPlacement.cpp`, station-owned
pair lifetime, two post-docking game-mode hooks and a read-only landed-ramp query.
Both home hangar and mid-run station entry use the real mode-owned Phoenix after
`FinishDocking`. No decorative preview ship is treated as a runtime endpoint.
The rig query requires the two existing registered bone-attached ramp colliders.

Placement checks the loaded welcome floor and adopted berth deck, the assembled
hull envelope, each frame footprint and jamb support, both approaches, arrival
floor and the actual capsule passage through the original frame. Deferred gates
remain disabled until both validate. Peer review identified that a component's
physics-state flag alone was insufficient; the final code also requires a valid
actual frame `BodyInstance`. A failed check destroys the incomplete pair and
preserves ordinary walking. No original frame, Niagara or station-map asset was
edited by this integration.

Root and independent source review pass. Native checks still required after the
editor is available: original frame aperture and both placements, portal scale
and moving mesh effects, natural transfer each way, exit latch, occupied arrival,
leave/pause/menu cancellation and teardown. A compile cannot prove any of these.
The current station map and owner-preview map are different review contexts.

Build46 `-NoLink` succeeds with14 actions in196.00seconds; log SHA
`98a431b9e51d0d6b7ceb21a4ad6514b6492536f87e2f797ac5a1627492d93b75`.
This includes the new placement unit and affected station, game mode and rig
units. Engine deprecations, newer-than-preferred MSVC, the existing Tripo
Interchange dependency warning and existing `SSFlightAutomationTests` /
`SSHUDRefresh` deprecations remain. No error is reported. The six affected files
pass installed clang-format `--dry-run --Werror`;41 structural checks, Python
compileall and diff checks also pass. Mainc45 and the Build39 DLL582 are verified
byte-unchanged afterward. There is no linked, loaded, rendered or packaged result
for this integration yet, and no Unreal invocation was made during closure.

## Temporary editor closure

At22:18UTC the owner asked to close Unreal. Root saved all nine dirty packages
through native `OBJ SAVEPACKAGE` into separate ignored recovery files:
`.agent/local/EditorCloseRecovery20261007T2216`. Each file exists and has a
recorded SHA256; the map is25,357,327bytes, SHA
`16818b1bb54d7ee6794501a2684bdf450760834d5f434af6c1a0c58423ef05a9`.
Manifest SHA is
`5c59de491fad85a2bba00b7a272425d319853ed31a06b40fc71b46ae5f70943d`.
Original Content hashes and loaded world name stay unchanged, PIE is stopped,
and dirty map/content lists are empty. This saves the current working scene
separately, including unapproved held T; it does not overwrite Mainc45 or accept
that display trial. Copies have not yet been reloaded. The owner was told it is
safe to close; subsequent work must remain source-only until reopening.
