# Character workshop adoption — October 21, 2026

**Status: local authoring delivery; quality and runtime follow-up open.**
The owner authorized the character/assets batch, separate two-level room,
consecutive animation pairs, individual hair files and adult dancer identities.
Hidden background jobs were explicitly allowed. No visible editor was opened.
RPT-20261021-01 remains the canonical active record.

## Delivered identity and storage

- Hall: `/Game/SpaceSurvival/Licensed/CharacterWorkshop/L_EntertainmentWorkshop`,
  SHA256 `8b0838d6312e481a70a574dd1632736f24576131d544cf6552fba692571ccd8b`.
- Canonical imported content: 845 files / 2,548,324,299 bytes, all SHA-verified
  after adoption and again after native checks. 669 new paths; 176 changed paths
  preserved first under the exact D recovery directory in the [guide](../production/CHARACTER_WORKSHOP.md).
- Portable authoring: 30 files / 1,110,734,365 bytes, including four character
  blends, packed native body master, eight hair GLBs, eight source motions,
  seven adapted FBXs and instructions/input manifest. DeliveryManifest records
  individual hashes and is additional to that count.
- Names: Jinx/Quinn, Roxie/Rosie, Vesper/Satomi, Vexa/saved pink Eden and Riley hair.
  Four profiles are authored; they do not establish live NPC conversation binding.
- Existing game module SHA256:
  `2ca94427aec85f0040612d7a9b21620d8044fad6b4b2febec76d73ab775d533f`.
  No C++ source or binary was rebuilt. Existing station/config files, owner HEAD
  and index match the 18-file pre-adoption guard record. No ordinary Play/save
  session, packaged build, release or merge was performed.

## Checks actually performed

UE 5.8.3 / Blender 5.2.2. Native work first used a content-only isolated project;
the final checks use the real canonical project. Commandlets are NullRHI asset
checks; captures use a real offscreen RHI and are reported separately.

| Check | Result and limit |
| --- | --- |
| Source inventory | Merged Quinn contains the separate pack paths. Originals remain intact. Native body master packs all 18 images. |
| Blender fresh reload | Four files, one 95-bone rig each, seven actions each, all file images packed, separate original garments and Parise option; no dependency on D for opening these files. |
| Material appearance | Native skin parameters agree across body/head parts; saved pink hair present. Blender material conversion uses simplified skin/hair shaders and boundary matching, not shader equivalence. |
| Native pose evaluation | Twelve variants × seven clips × three sample times = 252 changing, finite pose samples on the actual mesh components; full motion/contact quality remains unapproved. |
| Consecutive sequences | Twenty saved sequences: five per girl; G1 then G2 and B1 then B2 use contiguous ranges. Actor bindings were rebuilt after switching workshop actors to the Stylized classes. |
| Real-RHI views | Final canonical ten-view run captures hall, four characters and five animation poses; no Blueprint compiler error in the final log. Output is 1280×720 despite requesting 1280×960. These are sampled editor poses, not continuous or player-input tests. |
| Ship | Three native meshes load; Overview actors preserve M_MainMat / M_InteriorNoMat overrides. Raw mesh defaults remain source grid materials. |
| Jetpack | Five Blueprint assets load with generated classes; no SpaceSurvival pawn, input or game-mode activation. Runtime functionality not tested. |
| Preservation | Native adoption hashes match; 176 prior native files backed up and verified before replacement; owner station/config/DLL/HEAD/index guards unchanged. |

## Rejected checks and corrections

- First namespace-relocation workbench failed material/dependency loading. It was
  not adopted. Automatic approval review blocked its temporary-copy deletion;
  it remains quarantined and no cleanup bypass was attempted.
- Blender mesh binding originally used bone orientation across differing FBX/GLTF
  bone-roll conventions, producing stretched arms. A ten-joint rigid positional
  alignment corrected this; approximately 0.000001 m alignment RMS. Re-rendered
  samples show intact arms. Original sources were not altered.
- Hall sectors initially used positional `Rotator` arguments incorrectly. Named
  yaw corrected the vertical sectors. Exposure and work lighting were adjusted
  after the first overexposed view.
- Instance-only clothing overrides reverted on vendor construction. Replacing
  workshop actors with dedicated Stylized variants and rebinding the sequences
  corrected the skin-as-clothing appearance after reload.
- Initial captures stayed idle, then reused the first pose. Forced animation-mode
  reinitialization plus serialized animation-data evaluation produced distinct
  poses. Those earlier captures are not proof of motion.
- Canonical loading exposed a missing XRBase function library: the vendor
  `ResetOrientationAndPosition` node failed and Vexa showed only her head. The
  installed built-in XRBase dependency fixes the compiler error and restores her
  complete appearance; final canonical captures confirm the saved pink hair.

## Remaining limits

Pole contact visibly misses; some feet float, and consecutive clips still need
root alignment/blending. Clothing has been fitted and weighted, not simulated.
Extreme pose intersections, skin seams, hair shading, continuous motion and
physical workshop traversal remain lead work before appearance acceptance.

The vendor collection has ten unresolved hard references: seven animation-notify
references to missing footstep dust and three demo Control Rig redirects.
Additional soft/editor references are absent. Vendor ABP Body_Weight / InHeels
warnings and UDIM first-tile warnings persist. Animation import reported an
invalid bind pose/rebinding at time zero; sampled deformation does not erase it.
Native assets are available for authoring, not approved as finished gameplay.

Canonical offscreen startup also triggered the existing prefab-library export
path; its overhead remains part of RPT-20261020-13, not a new performance pass.
No FPS/VRAM improvement, packaged compatibility, natural play or owner acceptance
is claimed.

## Source checks

`Scripts/CheckProject.py`: 50 structural checks pass.
`Scripts/CheckPrDocumentation.py --repo .`: canonical navigation/counts pass.
`python -m compileall -q Scripts ContentSource`: pass.
`ContentSource/ValidateSources.py`: 26 meshes, 17 WAVs and unchanged GLB pass.
These checks do not validate licensed character appearance or gameplay.

Private evidence: `.agent/local/CharacterBatch_20261021`, including AdoptionPlan,
Adopted, CanonicalGuards, PortableFinal, FinalNativeCanonical, ShipAssembly,
NativeVisual and CanonicalVisualFixed logs. The source PR excludes licensed
models, textures, native packs, raw logs and rendered images.
