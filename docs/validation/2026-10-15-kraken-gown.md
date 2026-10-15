# Kraken gown fit and normal-startup correction

Owner request, October15: fit the owned blue/white/gold Immortal Cultivation
MetaHuman gown over Kraken's tentacles, alongside the separate Astra work.
Issue: `RPT-20261015-03`. This does not reopen Cyborg/Silver or the deferred
seventeen-animation repair.

## Provenance and preservation

The owned source is `oa_xiuxianwearoutfit_v11.mhpkg` in the M: Fab library's
`Immortal_Cultivation_Oriental_style_women_s_clothing_fully_adapted_to_body_shape-a261e551/metahuman/UE_5.7`
directory. Archive SHA256 is
`a27420c5f42bcd6add87f112f02a027b7328774311b1d74d6eccc176bd414155`.
No purchase, download or host installation was required.

The source contains 13,373 garment triangles and three original 4096 maps.
The fitted garment retains 12,657 triangles. Shoes and the forehead ornament
are omitted from the candidate only; the complete source remains preserved.
Sleeves fit the lower arm-tentacle branches. The body, armor, UVs, weights,
243-bone rest rig and all 34 original/adapted action blocks are unchanged.
Armor remains in the editable blend but is excluded from the gown export.
The native mesh uses the existing Kraken skeleton and walking clip.

Private preparation, recovery and images are under the canonical checkout's
`.agent/local/KrakenOutfit_20261015`. The original Desktop
`MODELANDRIGKRAKEN_FITTED.blend` remains SHA256 `e3b0092e` as recorded in
`Sources.json`. The original 17-clip library is unchanged.

## Defects caught during verification

- Normal Survival startup hid Kraken, disabled its tick and stopped its walk
  because `TrimCrew` did not include the restored actor. The source change
  retains exactly `Crew/Kraken visitor`; other population rules are unchanged.
  Empty screenshots are retained as `RejectedHidden_*` and are not a pass.
- Worktree build1 failed because that isolated checkout lacked the existing
  private ShipCore plugin. A local Plugins junction to the canonical installed
  plugins enabled build2; no plugin was installed or source dependency removed.
- The first material graph attempt asserted during compilation. The failed
  editor did not save a material or station map. The corrected graph compiled
  after establishing skeletal usage and texture properties before compilation.
- Initial three-second captures showed blurred textures. Forced-residency
  diagnostics restored detail without UV changes. A subsequent ten-second
  per-view check loaded the pattern normally without forced residency; resident
  maps were 1024 at the full-body camera distance, from the original 4096 sources.
  No global texture pool, lighting or graphics settings were changed.
- The vendor shader is masked, two-sided, default-lit with dithered opacity.
  Its sheer panels remain visibly noisy in these moving views. Making the whole
  gown translucent caused rear surfaces to sort over the front and was rejected.
  The adopted V4 uses 6,459 masked solid/cutout triangles and 6,198 separately
  shaded sheer triangles. Dense source-alpha sampling keeps mixed borders on
  the masked section. No geometry, weights or UVs changed. The three final
  native views preserve the opaque front and substantially reduce the broad
  screen-door pattern; masked cutout edges still have temporal rendering limits.

## Verified source and runtime checkpoint

The isolated editor build passes in71.04s; canonical integrated build passes
in 27.13s. Existing engine/API deprecation and toolchain-preference warnings
remain outside this one-line behavior change. Scoped installed clang-format
check and 45 structural source checks pass. CI uses its prescribed formatter.

Fresh canonical Editor28, runtime module SHA256
`b07543eb70a385356ca11c2098e75f17c9709403a5bbf1ccf9a7feb3d918873f`, starts normal
`Survival` with `SSGameMode` and `ss.StationCrewTrim=1`. Kraken is visible with
actor/component ticks enabled, without a visibility override. A29-sample
walking preview travels693.98cm and advances the existing clip; hair stays
attached to the head throughout. This supersedes relying on the older integration
receipt as proof of current normal-startup visibility.

## Saved result and fresh verification

The current station now uses `SK_Kraken_Gown_V4`. Map SHA256 is
`79e384032c916929e97135b193ffe5fc3193f65424fdf4938f068b4220d49655`.
Before and after adoption, all 9,473 actor identities, numeric transforms and
actor tags match. A first guard incorrectly compared pointer-bearing Transform
strings; it stopped before saving. Repeating with numeric values passed.
The 22 original Kraken assets, five vendor material/texture packages and original
Desktop fitted blend retain their hashes. `StationBeforeGown.umap` is the exact
pre-adoption backup; never restore it over later owner work.

Fresh Editor30 reload confirms the five material slots, original skeleton,
head-attached groom, all 9,473 numeric actor fingerprints and clean packages.
Normal Survival startup then verifies 93 continuous samples over 31.859s,
2,116.01cm travel, advancing walk phase and head attachment at every sample.
The saved mesh is used directly, with crew trim 1 and no visibility override,
forced texture residency or material swap. Front, quarter and back ordinary
1600x900 screenshots were visually reviewed. The final editor exited cleanly.

Garment motion is skinned to the existing walk; this does not add independent
Chaos cloth simulation. Physical-input play, other animation collisions,
representative performance, cooked-game behavior and owner appearance acceptance
remain open. Existing room `BP_Blinds` material warnings remain visible in logs.

Editable gown file: `.agent/local/KrakenOutfit_20261015/Kraken_Outfit_Fit_V4.blend`,
SHA256 `93e02c64f5fd5573a51ab9e1691818f1999196c26d660a247bb7a8c228cc5d9a`.
The combined FBX is `Kraken_Body_Gown_V4.fbx`, SHA256
`099bffea83c2eb50b17278742fd6a84b91c5fbfd5ae67a0d8c51a4a147d9f84a`.
`Review.html` opens the three fresh native views. Key local receipts are
`MaterialSplitV4Verified.json`, `NativeV4Imported.json`, `GownAdopted.json`,
`GownSavedReload.json`, `FinalNativeWalking.json` and `Verified.json`.

## Storage and review

Licensed models, maps, grooms, vendor packages and Blender files remain local;
the source PR is not their backup. The five original material/texture packages
were copied with matching hashes and original package paths under
`Content/Outfits/XiuxianWearOutfit`. Candidate meshes/materials are under
`Content/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015`.
The prior Kraken packages remain unchanged. Do not replay the original NPC
placement recipe on an already populated station. No package, publication or
merge is implied by these checks.
