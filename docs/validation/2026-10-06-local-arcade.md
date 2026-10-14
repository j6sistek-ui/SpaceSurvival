# Local arcade assets — October 6, 2026

Seven decorative props are saved in the separate owner preview: four Acornaut
cabinet modes, Galaxy Pinball, Credit Exchange V2 and Rift Salvage V2. The owner
rejected the initial crane contents and rubbery credit terminal; the new V2
exports replace those candidates in the placement without changing Frozen1.
Native room capture is available; visual quality and owner acceptance remain open. No arcade gameplay,
account transaction, crane reward, RNG perk or Acornaut browser/HUD integration
is implemented.

## Selected exports and provenance

Dimensions are source X/Y/Z in metres. Native triangle counts come from the
actual Unreal import receipts, separately from Blender's source counts.

| Selected prop | Treatment | Dimensions, m | Blender triangles | Native triangles |
|---|---|---|---:|---:|
| Acornaut Normal | Blue upright; local Hunyuan chassis with authored panels/art | 1.098 × 0.987 × 1.888 | 29,128 | 29,118 |
| Acornaut Debris Field | Purple upright with protective corner guards | 1.100 × 0.992 × 1.888 | 31,240 | 31,230 |
| Acornaut Arcade | Amber upright with retro side columns | 1.145 × 0.987 × 1.900 | 29,504 | 29,430 |
| Acornaut Hyper Run | Cyan wide cabinet with authored seat/platform | 1.400 × 2.052 × 1.586 | 31,450 | 31,440 |
| Galaxy Pinball | Local Hunyuan chassis; authored planar field, rail, flippers and bumpers | 1.052 × 1.135 × 1.888 | 28,074 | 28,047 |
| CreditExchangeV2 | Entirely authored hard-surface metal replacement | 0.977 × 0.785 × 1.7665 | 17,834 | 16,898 |
| RiftSalvageV2 | Authored frame, mechanical claw and varied salvage contents | 1.160 × 1.142 × 2.101 | 41,480 | 40,916 opaque + 564 glass |

AsteroidArena and TokensKiosk remain source drafts. Initial CreditExchange
(23,386 triangles) and RiftSalvage (17,180 triangles) remain preserved but are
superseded by V2 for the room. The four Acornaut units reuse one generated upright
chassis; they are separate editable exports, not four independent AI generations.

The existing local ComfyUI service at `127.0.0.1:8188` ran three BiRefNet cutout
jobs and three Hunyuan3D geometry jobs. Native installed graphs were copied from
`M:/Local AI/Game Asset Studio/API`; seeds were 1006202601, 1006202603 and
1006202607. Geometry settings: 20 steps, CFG 6, Euler/normal, octree 256.
All six saved execution histories report success. The installed workflow creates
geometry; planar graphics, UVs, materials and hard-surface finishing were authored
locally in Blender/Pillow. No cloud generation, model download or host install
was used. ComfyUI was returned to its initial stopped state after generation;
subsequent Blender 5.2.2 renders used CPU.

| Local model under `M:/Local AI` | SHA256 |
|---|---|
| `checkpoints/hunyuan3d-dit-v2_fp16.safetensors` | `360bc281fc956d4acac0c3d36d5ec0ebf8cdddbf4b8892e894d12419388d479b` |
| `background_removal/birefnet.safetensors` | `9ab37426bf4de0567af6b5d21b16151357149139362e6e8992021b8ce356a154` |

Normal and Debris use HUD-free crops of the owner's attached artwork. Initial
Arcade/Hyper Run cards use `poster-arcade.jpg` and `poster-race.jpg` from the
**nested** checkout `C:/Users/j6sis/acornaut/tmp/zone-art-review`, whose verified
origin is `https://github.com/j6sistek-ui/AcornautSandbox.git` and HEAD is
`a0c9a0d3467160553fb726325c0689d0e7c501f0`. This differs from the outer `acornaut`
repository; it is not evidence of the current live website. Input hashes and crop
coordinates are retained in the artwork receipt.

Two separately authored landscape attract cards improve the small portrait
screen treatment without modifying Frozen1. They use the same nested checkout's
`bg-wide.jpg`, `hero-wide.jpg`, registered Hyper Run portal layers and scout ship.
The reviewed `AttractCardsV2/approved_v2` receipt pins every source and both outputs.
Their flat preview has clear text/focal subjects. `StationLoungeArcadeFinish1.json`
records both native screen-slot overrides, each with its new texture/material
instance and emission strength 0.8. Actual room evidence and its limits are below.

## Editable sources and native import

Private source files are under `.agent/local/ArcadeGeneration/final/<name>`:
editable `.blend`, textured `.glb`, delivery `.fbx`, actual CPU front/quarter
renders and `asset.json`. V2 also includes detail renders. CreditExchangeV2 keeps
97 source parts. RiftSalvageV2 keeps 33 named source parts, including gantry,
carriage, cable, claw body, three hinged fingers, separate glass and 20 prizes;
the prizes rest at the 0.865 m tray plane. These parts and pivots prepare future
authoring but are not a working crane.

Unreal uses combined static meshes with preserved material slots; the crane has
separate opaque and glass meshes. PBR materials are explicitly reconstructed from
manifest textures/scalars rather than assuming Blender shader transfer. Glass
uses opacity 0.035. Opaque collision is one exterior box per combined prop;
glass has no collision. Hyper Run's chair and crane internals are therefore not
individually usable/physical in Unreal. All bounds, metre-to-centimetre conversion,
ground origins and named slots passed the native importer's checks.

The first import saved 104 private packages: 8 meshes, 61 materials and 35
textures under `/Game/OutpostSandbox/StationRefinement/Arcade20261006`.
V2 added 47 arcade packages: 3 meshes, 29 materials and 15 textures under
`/Game/OutpostSandbox/StationRefinement/Arcade20261006V2`. The second placement
receipt lists **48** saved packages because it also saved one aisle-lamp material.
Finish1 then saved two attract-card textures and two material instances under
`/Game/OutpostSandbox/StationRefinement/ArcadeAttract20261006V2`. That is **155
arcade packages: 104 + 47 + 4**, including retained superseded candidates.
The separate lamp material and three pool-animation/sequence packages are not
part of that arcade count. Two new coffer actors reuse an owned ceiling mesh and
material; they add no new mesh/material packages.

## Placement evidence and retained failures

`StationLocalArcadePlacement2.json` reports a successful save of
`/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006` at SHA256
`6314b46ba40bb9eff75088f1b02a73db9d19ba334ef8c26e24c4cca5d7734b95`.
Seven new props occupy the arcade corner; two existing arcade units and the drinks
unit were repositioned. Forty floor samples, ten volume checks, ten standing
spaces and two capsule sweep routes passed with radius 34 cm / half-height 88 cm.
There were zero protected-transform changes among 8,243 protected actors.
These are placement queries, not a natural player walk or performance test.
The canonical live Wayfarer hash remained
`9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.

The Placement2 process result remains mixed: the lead observed exit `0xC0000005` after the
placement log's normal `LogExit: Exiting` and file closure. Saved assets and
preservation checks are evidence, but this is not a clean process pass. Fresh
reload/capture subsequently passed as recorded below; it does not erase the
earlier process failure. Initial import similarly has a
successful asset receipt but lead-observed exit 1, cause unconfirmed. The first
placement attempt failed before saving because a material setter's return value
was treated as a success boolean; the repair uses value readback. Its failed
receipt and unchanged pre-save map hash are retained.

Initial native imports retain degenerate-tangent/nearly-zero-tangent warnings.
V2 source validation removed collapsed geometry and repaired 561 degenerate UV
faces in the crane; both V2 exports report zero collapsed/degenerate UV triangles.
V2 native logs still warn about missing FBX smoothing-group metadata; imported
normals are used. This warning is retained for native visual review, not dismissed
by the source audit. Final quality, lighting/material parity and representative
performance are not established by the manifest checks or CPU studio renders.

## Fresh native finish and capture

`StationLoungeArcadeFinish1.json` saved the two landscape screen overrides and two
owned ceiling coffers. The lead observed native exit 0. At that pass the saved
owner preview hash was `38ade2223778bf2b425eae624bc8748683b73ab395788a02146afc7b1fc7ad50`,
superseding the Placement2 hash above. The later presentation below supersedes
that preview hash. The canonical live map is unchanged.

`StationPoolPickupV2Playback1/manifest.json` binds that exact map and Finish1
receipt. The fresh process captured 12 requested images with zero fixture errors,
verified 214 guarded files and three production saves unchanged, and stopped PIE.
It observed two natural ambient pool loops over 120.10687 game seconds before
capturing paused views; this is not evidence of functioning arcade games. The
lead separately observed native exit 0. The manifest's `native_process_exit` is
null because the in-process fixture cannot observe its eventual process exit.

Image 12, `12_ArcadeWide_ArcadeWide.png`, is an actual paused PIE view at sequence
time 54 seconds, SHA256
`1c7112b0c71688f07e30d570e7569bc29e9858651ac0559bb0d92ad8b5ee2c59`.
The image hash was checked and its pixels inspected. The cabinet row, new Hyper
Run portal graphic and Credit Exchange service display are present. This angle
also exposes limits: the Acornaut row is very dark, an NPC obscures most of the
Arcade face, the terminal's near-black side dominates the foreground, and the
crane is cropped at the right edge. Its interior and the full seven-prop material
finish cannot be accepted from this view. Root/owner visual review remains open;
no physical input, interaction, game, transaction or performance pass is claimed.

### Bounded arcade presentation and V3 room review

The owner explicitly likes the cyan ceiling trim and current general brightness.
The abandoned coffer-dimming code was removed completely from the retry;
Presentation2 preserves the native coffer material, intensity and existing room
lights. This supersedes any earlier proposal to reduce the trim.

`StationArcadePresentation2.json` reports a successful save and the lead observed
native exit 0. The preview advances from pool V3's
`ecb4ec3206c54b43fc9ff7e057ef2bd0ca891cfa5511fc319f1c03687850d050` to
**`66e4fe29816ba4e12f052df64f903b19b67e04819d4ac5baf068ceea70458427`**.
Canonical Wayfarer remains `9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.
The bounded change is:

- Credit Exchange moves to the east service edge at approximately
  `(5375.5, -3080, 0)` cm, yaw 90 degrees, with its standing point at
  `(5285.5, -3080, 0)`. Four native floor samples, one volume, one standing space,
  two existing approach sweeps and two additional service-route sweeps pass.
  Placement queries use the native default capsule, radius 34 / half-height 88 cm.
- Three mounted, ceiling-supported RectLights illuminate cabinet faces locally:
  two at 1,400 lm / 520 cm attenuation and one at 1,600 lm / 600 cm, all 4,100 K.
  These are localized additions, not an exposure or general-light adjustment.
- One new opaque, two-sided frosted material replaces slot 1 on the two existing
  center lamps and supplies the new fixtures' lens faces. The native center lens
  has four upward-facing triangles and no downward-facing triangles; the
  two-sided override addresses visibility from below without changing geometry.
  Existing center-light intensity is unchanged.

The receipt checks 8,257 existing actor snapshots with only the credit transform
and two center-lamp material overrides allowed, and preserves 196 protected
source packages. Exactly one new material is saved:
`/Game/OutpostSandbox/StationRefinement/ArcadePresentation20261006/M_FrostedTwoSidedDiffuser`,
SHA256 `5a1d28e6812c825edd69496e3f1c87029ad96e4e37290dcbf6ff52558d8c9da9`.
This lighting material is separate from the 155 arcade-package count above.
The recipe SHA256 is `56a967dc0447124ef83a3e5f8929a8c8d37fd0318db0e9205ecdc9c0caee422d`;
the author receipt SHA256 is
`959df40c779dcb66222591afc334fe4497d00bed9eeebd8753c3dbbece8de809`.

`StationPoolPickupV3Capture1/manifest.json` binds that exact saved map and produces
13 actual paused PIE images, including five room/arcade views. It reports zero
fixture errors, 218 guarded files and three production saves unchanged, ship
state unchanged, and PIE stopped. The lead independently observed native exit 0.
Its manifest SHA256 is
`e367d2648a35e8bd852dd7d0c3fb1076183e489a7fa64c9ec636081953f26eaa`.
This is explicitly a paused V3 pose capture: `autoplay.tested=false`; it does not
repeat or replace the earlier two-loop V2 playback evidence.

An independent reviewer inspected images 09–13 and checked all five image hashes
against the manifest, comparing the matched prior V2 views and the approved L
lounge concept. Credit Exchange no longer masks the pool in the reverse view;
its service display reads clearly in the close view. Cabinet silhouettes,
individual colors, controls and attract cards are materially more visible in the
arcade view, and the center diffuser is visible from below. The cyan trim and
general brightness are retained as owner-approved choices, not defects.

The independent whole-room rating is approximately **6.5–7/10**, not owner
acceptance. Large uninterrupted floor areas, sparse social/table activity and
broad blank wall panels still leave a density/composition gap to the concept.
Fine detail remains subdued in the crane interior and dark pinball/purchased
cabinet; some small labels look soft at the captured distance. These screenshots
do not establish arcade function, physical input, collision, performance,
packaged quality or complete-room acceptance. A focused ordinary arcade walk is
recorded separately below.

`StationArcadeWalk1.json` then passes on that same `66e4fe29...8427` saved map;
the lead observed native exit 0. One continuous ordinary CharacterMovement route
visits the four south cabinets, pinball, crane, relocated credit alcove and lounge
exit. The actual selected squirrel pawn walks **91.365 m in 41.807 game seconds**
over 2,984 ticks, with zero falling time, unsupported time, off-deck observations
or movement discontinuities. All seven approach targets and the exit are reached.
The fixture uses one initial spawn, then normal `AddMovementInput`; runtime
capsule radius/half-height are 34/75 cm and walk speed is 320 cm/s. Five maps and
three production saves remain unchanged, and PIE stops. This is scripted native
movement through the changed approaches, not physical controller input, arcade
interaction, a full-station repeat or a performance acceptance test.

Retained failed attempts are not counted as passes. The first presentation probe
exited 3 before Python because the installed Derived Data Cache graph had no
writable nodes in that launch environment; its retry succeeded without a map
change. Presentation1 then failed before saving on the abandoned coffer graph
connection, preserved preview `38ade222...ad50`, and saved no assets. The lead
observed `0xC0000005` (`-1073741819`) after its normal `LogExit: Exiting` line.
Exact helper, wrapper and failed receipt bytes are preserved under
`FrozenArcadePresentation1`; the successful retry does not erase that history.

## Recipes, checks and local evidence

The 14 Python recipes and one YAML file in
[`ContentSource/LocalArcade20261006`](../../ContentSource/LocalArcade20261006)
were read and syntax/credential-marker checked. No credential literals were
found. Absolute paths identify local weights, attached references, the nested
art checkout and installed Windows fonts; these are machine-specific authoring
recipes, not portable runtime dependencies. Some recipes are compact and retain
historical output locations. Future asset changes require a new versioned output
folder. The subsequent source-only safety repair below prevents accidental reruns
from replacing the frozen exports or their receipts.

Python compileall passed. V2 filesystem import preflight passed for 2 manifests,
3 native FBX parts and 26 pinned files. Freeze verification preserved all seven
V1 manifests and 62 unique source files. No C++ build is implied by these
authoring/documentation checks. The lead owns PR integration and acceptance.

The October 6 recipe review found two rerun hazards: V1 writers and its freezer
could replace existing frozen files, and the V2 crane copied textures before its
export-time freeze check. A source-only repair adds fail-before-write checks to
all ten V1 recipes, including callable image/render writers, and moves the V2
check ahead of crane texture copies and all build/export/render entry points.
The V2 check rejects either the global freeze receipt or a frozen asset manifest.
V1 texture-directory creation now also occurs after the freeze check. No model,
recipe body, Blender render or Unreal process ran for this repair.

Exact prior bytes of the eleven changed scripts were copied and hash-verified in
[FrozenRecipeBackups/20261006-freeze-guards](../../.agent/local/ArcadeGeneration/FrozenRecipeBackups/20261006-freeze-guards).
The backup manifest and validation receipt retain every before/after recipe
SHA256, so the earlier generation recipes remain available without rewriting
historical receipts. `py_compile` passed for all eleven scripts. AST inspection
and execution of only the extracted first guard statements passed for sixteen
write entry points; two additional checks verified the V2 per-asset fallback.
The [guard validation receipt](../../.agent/local/ArcadeGeneration/FrozenRecipeBackups/20261006-freeze-guards/guard_validation.json)
has SHA256 `bf09d4120da3534e1009971e4ffd6ee42ff5108b370f2cf50b357fa39938a46a`.
Frozen1's seven manifests/62 unique sources and V2's two manifests/24 unique
sources still match their recorded hashes; V2's recorded review-render hashes
also match. Frozen1 receipt SHA256 remains
`a008fe9c6d4c6d6a39d496f152717cfc52bb523ff34bb104ba68ecc97dab228a`;
V2 remains `22cc55e3706cad0fef9fed042a369ef047a2e718005d0b5407cfed6dffbd723b`.
This repair changes source safety only, not the imported assets, saved map,
visual quality or owner-acceptance state.

Local raw artifacts are intentionally ignored; these links resolve in the owner
checkout and do not imply that their binary contents are published on GitHub:

- [Frozen1 manifest](../../.agent/local/ArcadeGeneration/FROZEN_MANIFEST.json) and
  [Frozen V2 manifest](../../.agent/local/ArcadeGeneration/FROZEN_V2_MANIFEST.json).
  V2 manifest SHA256: `22cc55e3706cad0fef9fed042a369ef047a2e718005d0b5407cfed6dffbd723b`.
- [Generation histories and raw render receipts](../../.agent/local/ArcadeGeneration/receipts),
  [exact art crops](../../.agent/local/ArcadeGeneration/receipts/acornaut_art_provenance.json),
  [nested source clarification](../../.agent/local/ArcadeGeneration/receipts/Frozen1VisualReview.md),
  [V2 review](../../.agent/local/ArcadeGeneration/receipts/V2Review.md).
- [Initial native import](../../.agent/local/StationRefinement/StationLocalArcadeImport1.json),
  [failed first placement](../../.agent/local/StationRefinement/StationLocalArcadePlacement1.json),
  [V2 import and saved placement](../../.agent/local/StationRefinement/StationLocalArcadePlacement2.json),
  [placement process log](../../.agent/local/StationRefinement/StationLocalArcadePlacement2.log).
- [Credit V2 quarter](../../.agent/local/ArcadeGeneration/final/CreditExchangeV2/CreditExchangeV2_quarter.png),
  [crane V2 detail](../../.agent/local/ArcadeGeneration/final/RiftSalvageV2/RiftSalvageV2_detail.png),
  [new attract-card provenance](../../.agent/local/ArcadeGeneration/AttractCardsV2/approved_v2/manifest.json).
- [Saved native finish](../../.agent/local/StationRefinement/StationLoungeArcadeFinish1.json),
  [fresh capture manifest](../../.agent/local/StationRefinement/StationPoolPickupV2Playback1/manifest.json),
  [actual ArcadeWide image](../../.agent/local/StationRefinement/StationPoolPickupV2Playback1/12_ArcadeWide_ArcadeWide.png),
  [fresh process log](../../.agent/local/StationRefinement/StationPoolPickupV2Playback1.log).
- [Saved bounded presentation](../../.agent/local/StationRefinement/StationArcadePresentation2.json),
  [V3 capture manifest](../../.agent/local/StationRefinement/StationPoolPickupV3Capture1/manifest.json),
  [current arcade view](../../.agent/local/StationRefinement/StationPoolPickupV3Capture1/11_ArcadeWide_ArcadeWide.png),
  [current reverse view](../../.agent/local/StationRefinement/StationPoolPickupV3Capture1/10_RoomReverse_RoomReverse.png),
  [crane close view](../../.agent/local/StationRefinement/StationPoolPickupV3Capture1/12_CraneFront_CraneFront.png),
  [credit close view](../../.agent/local/StationRefinement/StationPoolPickupV3Capture1/13_CreditFront_CreditFront.png).
- [Native presentation probe](../../.agent/local/StationRefinement/StationArcadePresentationProbe1.json),
  [failed first presentation](../../.agent/local/StationRefinement/StationArcadePresentation1.json),
  [frozen failed-attempt inputs](../../.agent/local/StationRefinement/FrozenArcadePresentation1).
- [Focused ordinary arcade walk](../../.agent/local/StationRefinement/StationArcadeWalk1.json)
  and [frozen route wrapper](../../.agent/local/StationRefinement/run_arcade_walk1.py).
