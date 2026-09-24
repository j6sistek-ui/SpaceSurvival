# Replacement squirrel rig authoring

Owner-scoped recipe for the Tripo `sci-fi_squirrel_3d_model`, exactly 75,183 triangles.
This is not a generic automatic character-rigging tool. No dependencies are installed.
Source art and outputs remain private under `.agent/local/ReplacementHero/`.
See [handoff](HANDOFF.txt) for the files, usage and integration limits.

## Reproduce

Use the installed Unreal 5.8 editor and Blender 5.2.2. Run on a checkout containing
the private original `/Game/TripoModels` assets. Preserve the output directory
before rerunning if it contains manual edits; these scripts overwrite their own outputs.

1. Unreal Python commandlet: `-run=pythonscript -script=<repo>/Tools/HeroRig/ExportCandidates.py -RenderOffscreen -AllowCommandletRendering -unattended -DisablePlugins=UAssetBrowser`.
   Do not use NullRHI for this export: the skeletal exporter required a render mesh.
   No asset packages are saved or overwritten by the export script.
2. Run Blender `--background --factory-startup --python <script>` for `Inspect.py`,
   `Survey.py`, `Repair.py`, `ReweightTail.py`, `Validate.py`, `AnimateTail.py`, then `Roundtrip.py`.
   Require the corresponding success marker/report; Blender can exit zero after a Python exception.
3. `SoftenFur.py` creates the optional tail-only derivative; `ValidateFur.py` checks both exports.
   `PreviewTail.py` renders the original-surface previews; rerun with `-- --soft-fur` for
   the fur derivative. Existing Python with Pillow runs `Package.py` to assemble ZIP/GIFs. No production/game animations are overwritten.

The source mesh uses a T pose, custom proportions and mannequin-style names. Keep a
new target skeleton/IK retargeter; do not assume assigning Epic's skeleton makes it compatible.
The existing 60 bones are retained. A root, seven tail bones and a backpack bone are added.
The backpack core is rigid, its attached cloth/straps use feathered weights. The tail has
no thigh weights. Modified weights are normalized and limited to four influences.

Tail FBXs are separate layers with body reference tracks. Import against the replacement
skeleton and configure additive reference-pose evaluation or branch-filter the tail chain.
Blend idle/gaits; use JumpStart, JumpAir loop, JumpLand according to actual movement state.
Jump timing, body retargeting and runtime layering are not implemented by these scripts.

Validation is confined to this asset: source geometry/UV identity, three posed deformation
checks, FBX/GLB round trips and loop/transition endpoints. The glTF importer creates a helper
bone-shape mesh; round-trip counts intentionally cover skinned meshes only.

The jump revision uncoils the tail downward and delays tip recovery for the landing rebound.
`ReweightTail.py` assigns weights along connected surface distance, fixing the tip fold
caused by nearest-segment ambiguity around the source hook. Rebuild all six clips after
changing the rest chain. The optional fur derivative adds 180 cards (1,440 triangles),
limits tail smoothing to 3 mm and preserves non-tail vertices: 76,623 triangles total.
It needs native Unreal masked-material setup; the original sculpted tufts remain visible.
