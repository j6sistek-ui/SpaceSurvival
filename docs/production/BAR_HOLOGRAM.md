# Bar hologram and serving tray

The owner's rough waitress model is a separate65cm teal hologram on the right-hand bar counter. It is decorative and does not replace Astra. The supplied34cm metal tray is beside it. Astra now has separate saved tray settings; normal/shared service, cancellation and three configuration fallbacks pass native review.

## Move or tune the saved display

1. In the Unreal Outliner, search **Move this display**.
2. Select **Bar/Waitress hologram/Move this display** and move/rotate it. The attached figure follows. Scaling the parent scales both pieces.
3. To change the effect, open **MI_WaitressHologram** under `/Game/SpaceSurvival/Licensed/StationAssets/BarHologram_20261016/WaitressHologram`. Adjust **Tint**, **BodyOpacity**, or **BodyGlow**. Rim and scan controls are also exposed.

The folder in the Outliner is **Bar/Owner hologram and tray**. The independent **Bar/Serving tray** actor can be moved separately. Display and tray collision are disabled; they do not add an obstacle to the existing bar service route.

Native review: `C:/Users/j6sis/SpaceSurvival/.agent/local/Waitress_20261015/BarHologram_20261016/Review.html`. Saved tray map`e3cee859` supersedes display-only`d3eb3a23`; combined module`a023f6a9`; local development content only. The owner's pending appearance check stays in KNOWN_ISSUES and does not gate other work.

## Inputs and storage

The two owner-created Tripo GLBs remain intact. Private originals, extracted maps, scaled Blender/FBX derivatives and evidence live in `.agent/local/Waitress_20261015/BarHologram_20261016`. Native derivatives live under `/Game/SpaceSurvival/Licensed/StationAssets/BarHologram_20261016`; they remain local, outside the source PR. The projector reuses `/Game/CyberpunkRestaurant/Meshes/SM_Hologram_Projector_01`, with the vendor mesh/materials unchanged.

| Source | SHA256 | Imported use |
| --- | --- | --- |
| cosplay waitress 3d model.glb | `c76fa699821f1ca0928995516ccedd901a360dcf1866d664478c92a56054a160` | Static48,206-triangle figure,65cm high, one2K base-color map |
| round metal tray 3d model.glb | `2f08647fa275bb2ff75077721e0b3f6acdb3bec1fabed715c8350087e416b753` | Static1,081-triangle tray,34cm across; color, metallic/roughness and normal maps |

Tray source maps are4K; native maximum texture size is2K for this small prop while the full source data remains intact. Metallic/roughness use the source blue/green channels respectively; the normal map's green channel is flipped for the native material. No generated replacement mesh or paid service is used.

## Bounded reproduction

Use the already-installed Blender and Unreal tools. Do not install host packages or run these through the owner's open Blender session.

```powershell
& '<installed Blender>/blender.exe' -b --factory-startup --python Scripts/StationRecipes/BarHologram/ExportAssets.py -- --model '<owner model.glb>' --tray '<owner tray.glb>' --output '<new empty private directory>'
```

The exporter verifies the exact supplied GLB hashes and refuses an existing output directory. It exports scaled copies; it never writes the original files. Set `SS_BAR_HOLOGRAM_SOURCE` to that output directory for `Scripts/StationRecipes/BarHologram/ImportAssets.py`, executed in an isolated Unreal editor outside PIE. The import is fresh-create only and refuses an existing native destination. It creates only the two meshes/textures/materials; it does not place actors, change rigs or save a map. Do not rerun it against the current installed destination.

Placement was separately backed up, compared with all9,480 original actor transforms/labels/tags, saved, unloaded and reloaded. The native material uses translucent unlit shading, texture detail, a Fresnel rim and time-driven height scanlines; no vertex displacement or global exposure changes. Refer to the [validation receipt](../validation/2026-10-16-bar-hologram-and-tray.md) for actual evidence and remaining work. Gameplay tray carrying/serving is separately verified below; importing or placing the prop alone did not establish it.

## Serving tray configuration

Astra exposes **Bar → Tray** settings for a paired carry/serve animation, hand socket, tray grip and glass placement. The **ServingTray** component owns the mesh. These are optional: a missing mesh/socket or incompatible animation pair keeps the original hand-held glass service. The tray is shown while returning with an order and serving, then hidden for drinking, cancellation and returning home. Original carry/serve and drink clips remain assigned as fallbacks.

The saved fit uses `hand_l`, the owner tray mesh, separate `TrayPose/A_Waitress_TrayCarry_CandidateV2` and `A_Waitress_TrayServe_CandidateV2` clips, grip translation `(15.391144, -0.917641, -1.302555)` in hand space, and glass placement `(0, 0, 0.769705)` at0.8scale in tray space. These clips change left-arm/hand rotations only; original clips and bone translations/scales are preserved. Runtime review is recorded separately from import/save success.
