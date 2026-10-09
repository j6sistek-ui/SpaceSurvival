# Squirrel hero at 178 cm: rig and animation

The other chat delivered a 178 cm squirrel (`.agent/local/CharacterAssets/HeroSquirrel_20261008/Delivery`, see its
`HANDOFF.txt`). These scripts give it the live squirrel's eight clips. They do NOT switch the game to it: that is the
Squirrel row in `DA_Phase1` on the `codex/unified-editor-library` branch, and it is the owner's call.

Runs in an isolated content-only project, `.agent/local/CharacterAssets/Squirrel178_Sandbox/Squirrel178Sandbox.uproject`,
holding copies of the delivery's 9 packages and the live `Licensed/HeroReplacement/Final` folder. Its `/Game` paths are
the game project's, so the result migrates by copying `Content/SpaceSurvival/Licensed/HeroReplacement178/` across
(git-ignored; nothing tracked changes). The main checkout is another chat's working copy - no runs there without the
owner's OK.

1. Copy the CURRENT delivery's `UnrealContent/Diagnostic` (today `Delivery_RedStreaks`) to the sandbox's
   `Content/Diagnostic` (the packages reference that path) and check the hashes against its `MANIFEST.json`.
2. `Stage178.py` (-NullRHI, `SS_SQ_OUT=<folder>` receives the JSON receipts; required by both scripts) - moves
   them to `/Game/SpaceSurvival/Licensed/HeroReplacement178` through Unreal, and
   compares skeletons. Measured: same 69 bones, rest rotations within 0.001 deg, a uniform K = 1.991773, and one
   constant -42.42 cm shift (the delivery centred the pelvis over the origin; the live one sits 21.3 cm forward).
3. `Derive178.py` (-NullRHI) - rebases the 8 clips: rotation and scale per key unchanged, translation
   `rest_new + K * (key - rest_old)`. Proof in the same run: every bone, every third frame, the new clip equals K x
   the old one plus the shift, within 0.0001 cm. It also measures the row values the switch-over would need.
4. Check renders: `../TripoCrewBlender/validate/export_clips.py` with `SS_AF_PATHS` (-RenderOffscreen), then
   `render_strip.py` and `sheets.py`.

The current delivery is the colour fix, `Delivery_RedStreaks` (named in `HeroSquirrel_20261008/CURRENT_HANDOFF.txt`);
the scripts default to its package names (`SS_SQ_PKG`, `SS_SQ_MESH` select another). Same geometry, bones and weights
as the first 178 cm delivery, but its packages are renamed and bring a FRESH skeleton, so clips bound to the earlier
one cannot play on it - a colour revision delivered that way needs steps 1-3 again (clear `HeroReplacement178` in the
sandbox first). Done 2026-10-08: identical numbers, and clay renders pixel-identical to the first run.
`SS_SQ_REDO=1` re-derives clips that already exist.

Bone set: the 61 deforming bones of the UE4 mannequin with the same names, plus `backpack` and `tail_01`..`tail_07`
(the mannequin's 7 IK helper bones are absent and carry no skin). Any mannequin-named clip retargets onto it.
