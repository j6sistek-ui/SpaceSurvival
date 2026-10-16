# Kraken blue fit and eye previews — 2026-10-16

## Result and boundaries

Owner approved blue and requested modestly shorter sleeve loops, closer upper cuffs, less transparency in the front rectangle and a softer back. Saved local V10 uses azure `#4C8DD8`, front fabric opacity0.9, breast0.75 and back0.65. These scalars apply through the original atlas fabric mask; gold and neutral details retain their existing opacity. Sleeve sheers retain their original alpha. Darker head gain0.32 remains.

This supersedes V7's opaque-back/front0.5 appearance. Kraken stays on her current atrium route. Final role/zone is deferred. The owner selected Purple Mandala eyes; combined V11 is saved as a separate source/native candidate but is not assigned to the saved station actor. Appearance acceptance remains RPT-20261015-03, and lead owns resulting repairs. The owner requested VRAM back, so Unreal remains closed and GPU work is held.

## Exact local artifacts

All paths below are relative to `C:/Users/j6sis/SpaceSurvival/.agent/local/KrakenOutfit_20261015/` and remain private/ignored:

- `BackSheer_20261016/Kraken_Outfit_Fit_V10.blend`, SHA256 `fb7a1fc8d6e31d70a9f6437f7ac0b740984dbf87db8202c60afa1fbb43260cbf`.
- `BackSheer_20261016/Kraken_Body_Gown_V10.fbx`, SHA256 `41e4c46e16aba1d98bffe3b632e7cc4fb29a242af340709baab3efad0e564383`.
- `BackSheer_20261016/{FitV10Verified,V10FreshReloadVerified,NativeV10Imported,Adopted,FreshReload}.json` distinguish Blender, import, save and fresh native checks.
- `BackSheer_20261016/Review.html` is the outfit review; `EyeFit_20261016/Review.html` compares eyes.
- `MandalaFinal_20261016/Kraken_Outfit_Mandala_V11.blend`, SHA256 `7bd7344b08a51443480c52cd0e083302066141c8129090f3e7f1aedecdc24905`.
- `MandalaFinal_20261016/Kraken_Body_Gown_Mandala_V11.fbx`, SHA256 `453d30a144a207f6cbb563ec58be0f0163f7e475a48b448bce7f8ca75b5805fc`.
- `MandalaFinal_20261016/{FitV11Verified,V11FreshReloadVerified,NativeV11Imported,CandidatePreview,OwnerVramRelease}.json` distinguish Blender verification, native import/preview and the GPU hold. There is no V11 station-adoption or fresh native reload receipt.
- Native mesh `/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/SK_Kraken_Gown_V10`; eight material slots.
- Saved Wayfarer map SHA256 `fee0cfa0e879f7f23dd4aa2a47596840d02087bd71c1c5a2aac4690e3367534b`.
- Existing canonical module SHA256 `35b7379d28476dcf5a0e75a64171231b6122253fec19fb2369800c4ee81e38c6` (Joy cache Build15). No C++ change/rebuild in this amendment; no cook/package/release/publication.

## Fit and preservation

V8 shortened the loose sleeve-loop region18% while retaining its roots and full-length recovery, tightened the cuffs/waist and removed125 concealed central/lower underwear triangles that overlapped the original metal pelvis. Gown now has7,285 vertices/12,532 triangles. Breast geometry was restored to V7 after a tightening trial clipped.

V9 repaired a right-cuff/body weight mismatch:405 cuff vertices and96 neighboring sleeve-root vertices now interpolate the underlying body influences. Geometry/UVs/material assignments remain identical to V8. Native two-view motion inspection passes for the requested correction, but shallow rear/join face contact remains; this is not an intersection-free or all-animation claim.

V10 changes only the material assignment of source component2:1,380 triangles (face IDs5326–6705) now use `XiuxianWearOutfit_BackSheer`. Native `MI_Gown_BlueBack_V10` is a separate instance; front, breast, gold, cuffs and underwear are not faded by this change. Fresh Blender reload verifies original body/metal, prior shader nodes, geometry, UVs, weights,243bones and34actions. Original17 clips and adapted copies remain; no new animation repair.

Guarded native save preserves all9,473 actor fingerprints and44 prior non-map packages. Fresh offscreen Editor38 confirms eight assigned materials, exact opacity readbacks, original skeleton/walk, head-attached groom and clean packages.9,469 initial world transforms are identical; four existing socket attachments have recorded initialization differences below0.3cm/0.05degrees, with negligible scale roundoff. Actor identities, labels and tags remain unchanged. No relocation or unrelated authored actor changes.

`BackSheer_20261016/FinalWalking.json` verifies normal Survival startup with crew trim1 and the saved V10 mesh used directly:259 samples over55.656seconds/3861.811cm, advancing walk and a valid head-groom link throughout. Six ordinary1600x900 views cover front, quarter, waist, back and both cuffs. No temporary mesh/material override is used for this saved-state capture. Sharp pale patches near the lower rear hem and shallow cuff rear/join contact remain unresolved; this is a bounded walking check, not outfit completion.

## Eye comparison

Owned Meshy sources `a6543166` (PurpleMandala) and `c707be10` (GalaxyVortex) were fitted as paired almond-shaped surface caps over Kraken's continuous face, preserving circular iris art and the existing lower waterline. The original face is untouched. Each pair has897 triangles; fitted weights follow the original face. Seventeen sampled Blender walking frames retain positive surface clearance; all244 FBX rig/bone transform records match the body export.

Native four-view comparison uses the same frozen pose and unchanged station lighting after29 moving samples; head-follow error is0cm. The first comparison was rejected when an older diagnostic session expired and reduced the viewport midway. The repeated comparison explicitly owns/restores its viewport session and produces four ordinary1600×900 images. Preview actors are removed and the original actor mesh restored afterward. `EyeFit_20261016/NativePreview.json` says `adopted:false`;47 source packages, including Astra eye materials, remain unchanged.

The owner's subsequent Purple Mandala selection supersedes the pending-choice state. V11 adds only the two fitted eye caps to the combined export, preserving V10 body/gown geometry, UVs, weights, materials,243bones and34actions. All244 exported bone/root transforms and hierarchy match V10. Native `SK_Kraken_Gown_Mandala_V11` has nine materials, assigned by slot name, and reuses the unchanged `MI_Eye_PurpleMandala`. Import preserves64 protected packages. `CandidatePreview.json` and `MandalaFace.png` record an actual native candidate preview; the station still references V10. Blender's `V11FreshReloadVerified.json` is not native station-reload evidence.

## Checks, failures and remaining work

Material authoring initially stopped on the UE5.8 Clamp pin name and a parameter setter returning false for an already-correct default. Installed API inspection plus parameter readback corrected these; original assets were unchanged. An unsaved scratch-material deletion produced an ensure in Editor36; that editor exited and fresh Editor37 authored the candidates. V10's first import guard incorrectly treated a combined topology/material fingerprint as topology-only; it stopped before writes and was replaced with explicit unchanged topology/UV/weight and exact1380-face assignment checks. Failed receipts are retained.

Single-sided and masked temporal-dither back-material trials did not remove the lower-hem patches and were not adopted. Editor38 exited after a GPU crash at2026-10-16T03:06:13Z during this diagnostic; causation is unconfirmed. The owner requested VRAM release and CPU work. Both owned editor sessions are absent, and the saved V10 map hash was rechecked unchanged. `OwnerVramRelease.json` records3991/16303MiB used at that time; it is a point-in-time reading, not a continuing reservation. Do not relaunch GPU work until the owner releases the hold. Owner Blender/workflows were not closed.

No texture residency, global exposure or lighting override is used. Existing BP_Blinds null-material errors and room rendering warnings remain outside this asset correction. Independent cloth simulation, broader animation clearance, physical-input play, representative performance and cooked-game verification remain open. No sound/mix evidence is claimed from offscreen NoSound sessions.

Documentation consistency and whitespace checks pass for this amendment. Earlier visibility-source builds/tests remain recorded in the October15 gown receipt; this asset/documentation checkpoint changes no C++ source and requires no additional build. PR75 remains draft/unmerged. Open the saved outfit review; check rear transparency and cuff fit. The eye choice is settled. Lead next: after the GPU hold is released, save/reload the selected V11 eyes and resolve the lower-hem artifacts using a supported new hypothesis, then inspect motion. Broader bar requests remain open in PR74; hero and squirrel changes remain deferred.
