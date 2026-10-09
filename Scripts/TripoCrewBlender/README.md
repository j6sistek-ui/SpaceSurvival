# Tripo crew: Blender repair pass

Headless, CPU only (`blender -b`). Order per character:

1. `UnrealEditor-Cmd ... -RenderOffscreen` export the Tripo skeletal mesh to FBX (weights intact).
2. `check_weights.py <fbx>` - extremity test; any "bad" count well above 0 means re-skin in step 4.
3. `normalize_skeleton.py <fbx> <out> 1.78` - rebuilds the rest pose at unit bone scale, drops Tripo's
   x100 `Armature` bone, adds a floor `root`, scales to the given height in metres.
4. (scrambled weights only) `blender -b <out>.blend -P reskin_auto_weights.py -- <out>_auto`.
5. `blender -b <final>.blend -P export_for_unreal.py -- <Name>.fbx` - centimetre units, no scale left on
   any bone. Then `Scripts/ImportTripoCrew.py` and `Scripts/AuthorTripoCrew.py`.

Why each step exists is in the docstring of `Scripts/ImportTripoCrew.py`.

Per-character extras, run on the `.blend` before step 5 (each script's docstring has the measurements):

- `strip_root_weights.py` - **every mesh re-skinned with automatic weights needs this** (Amethyst, Cyan, Dread,
  Glyph, Olive, Tribal, Violet, Warden). Bone heat skinned the floor `root` bone, so feet and anything low stayed
  on the floor whenever the body left the root - spikes in zero-G floats, smeared feet when sitting, and Dread's
  dreadlocks stretched into what looked like a staff. `reskin_auto_weights.py` now excludes `root` up front.
- `cloak_to_pelvis.py` - Seer, Tendril: cloak tails and robe tatters were leg-weighted and fanned into spikes in
  any bent-knee clip (the seated terminal work, squats, bows). Free-hanging cloth now mostly follows the hips.
- `rig_lower_arms.py` - Ember's second pair of arms.
- `rig_tail.py` - Crest's tail (8 bones) and the thin cord beside it (5 bones); animated in Unreal by
  `Scripts/AuthorTripoCrewTail.py`.
- `fix_leg_frames.py` - the Elf: her tilted pelvis and exactly vertical thighs made EVERY Unreal import (the repair
  chat's native SK_Fantasy_Elf too) rotate the thigh reference frames 110-160 degrees, so the thighs collapsed into
  twisted ribbons in every clip. Rebuilds pelvis/thigh rest frames in the Cyborg's layout; mesh and weights untouched.
- `rig_hair.py` - Elf, Silver: hair chains (hair_<azimuth>_<n>, 7 bones) where long hair hangs, joints laid ON the
  hair (a lock draped over a shoulder otherwise put its chain inside the body), and hair lying on a shoulder rides
  that shoulder. Motion is a spring/collision simulation baked per clip by `Scripts/AuthorTripoCrewHair.py`.
- `tentacles/` - Kraken and Abyss. Humanoid clips on Kraken get her own tentacle lower body back from
  `Scripts/AuthorTripoCrewTentacleBlend.py`.

Olive was replaced on 2026-10-08 by the owner's newer Tripo export (72,735 faces; the Unreal import was an older
mesh with its textures landing on the wrong parts). Its eight `tripo_part_N` materials are renamed to the Unreal
materials that hold the same textures, matched pixel for pixel: Unreal `..._Mat_j` carries part `(j + 1) % 8`.

Check renders for any clip: `validate/export_clips.py` (Unreal, -RenderOffscreen) -> `validate/render_strip.py`
(Blender, CPU) -> `validate/sheets.py` (contact sheets). Adding animations: [docs/TRIPO_CREW_ANIMATION.md](../../docs/TRIPO_CREW_ANIMATION.md).

Checks after any repair: `check_weights.py` (extremities on the right bones) and no vertex on `root` - both must
read 0 before importing. On Kraken and Abyss the extremities are tentacle chains (counted as valid); their
deformation gate is `tentacles/check_stretch.py` and `tentacles/check_floor.py`.
