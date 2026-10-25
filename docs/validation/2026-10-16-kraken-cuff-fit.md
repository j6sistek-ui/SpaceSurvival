# Kraken cuff fit — October 16, 2026

## Result and scope

The saved V12 mesh improves the cuff bands that cut through Kraken's upper arms during her walk. The left cuff now uses body-derived weights, matching the earlier right-cuff repair. Local subdivision lets the seam follow the curved arm instead of a few long triangles cutting across it. Native front/back comparisons show more continuous bands. This is an improvement with remaining seam contact, not a claim of complete cloth clearance.

The original V11 source and native mesh remain intact. Body, armor, selected Purple Mandala eyes, all 243 bones, 34 actions, original garment vertex positions and original UV corners are preserved. The 11,132 non-cuff garment faces are unchanged. The derivative changes 405 left-cuff and 94 nearby sleeve-root weights; local cuff subdivision adds 164 vertices and 320 triangles, giving 7,449 garment vertices and 12,852 triangles. New seam points follow the body surface and receive body-derived weights. FBX skeleton properties/hierarchy and all nine material slots match V11.

## Local identities and preservation

- Saved map SHA256 `113492edbd77ff3dab8cf418728ad289111fddeb0e9332a101d3567eb60d5fac` supersedes `6669965d5190170d9cfe589a9876dbd7fb66ef3ad953e107a0fa2bbf02e8ccb5` only for the placed Kraken mesh assignment. All 9,483 actor transforms, labels and tags remain unchanged.
- Mesh: `/Game/SpaceSurvival/Licensed/StationAssets/KrakenOutfit_20261015/SK_Kraken_Gown_Mandala_V12`. All nine effective materials remain unchanged, including the separate rear-hem override. Blue colors, front/chest transparency, selected eyes, walk, hair attachment and current route are preserved.
- Combined editor module `b9a9d71ebba7a27f7988a24348e308df29d4ba1ae0a9481ce31b611f65885f2e` is unchanged. No C++ edit/build, cook, packaged release or remote merge belongs to this asset/documentation amendment.
- Private root: `C:/Users/j6sis/SpaceSurvival/.agent/local/KrakenOutfit_20261015/CuffClearance_20261016/`. `Kraken_Outfit_Mandala_V12.blend` SHA256 `78fb82be19dd7100ccc0cef81aa36827b810c622b0a9f60080761d20e0545b72`; `Kraken_Body_Gown_Mandala_V12.fbx` SHA256 `0136180db7fea0e5589df181ebc6bf2c9bea7858708841e8d9fbf59f81b5b596`.
- `StationBeforeCuffs.umap` retains the immediate pre-change station. `ExportV12.json`, `Adopted.json`, `Reload.json`, `GuardAfter.json` and `FinalPreservation.json` are the receipts. All 224 prior non-map files, including owner saves and original licensed assets, pass unchanged; final guard covers 226 files. V11 Blender SHA256 remains `7bd7344b08a51443480c52cd0e083302066141c8129090f3e7f1aedecdc24905`.
- Licensed meshes, private Blender/FBX sources, screenshots and native map remain local. The PR carries provenance and validation, not those paid assets.

## Verification and retained limits

CPU inspection covers rest plus 17 walking frames using evaluated body/cuff triangle intersections. Baseline left cuff rises from 16 rest crossings to 75 in motion. Weight-only Trial1 reduces it to 16 throughout. Trial2 moves existing seam points outward but retains 11–14 crossings and is not adopted. Trial3 preserves original vertex positions and subdivides 32 crossing faces; it retains four left and 9–11 right crossings. Native views support the visible improvement, but those remaining intersections are recorded rather than described as solved. The new seam projection is at most 2.30 cm; original points are not inflated.

The exact unchanged UV corners, non-cuff faces, body/eyes/rig/actions/materials and exported skeleton were checked before import. Opaque CPU diagnostics isolate the cuff; native review uses the real outfit materials and station lighting. Twelve before/candidate views cover 351 samples. Saved-map unload/reload verifies 9,483 actor fingerprints, all nine materials and head-groom attachment. Saved ordinary Play uses V12 directly without mesh/material substitution: 176 samples over 37.641 seconds, 2,602.972 cm cumulative travel and six 1600×900 views. Hair attachment and materials remain valid throughout. Packages are clean and the owned offscreen editor exited.

The first private weight report failed JSON serialization after saving its candidate; a fresh read verified it without recreating the file. The first CPU render helper cached an invalid evaluated mesh; it was corrected and rerendered. The first native adoption helper used an unavailable direct AnimSequence.skeleton attribute and stopped before any mutation; the reflected editor property completed the same guard. These helper failures and their logs remain private. The original owner Blender session/preferences were not changed.

NoSound captures provide no audio evidence. Independent cloth, all-animation clearance, natural player interaction, physical inputs, representative performance, cooked-game and owner appearance remain unverified. Remaining cuff seam contact and Astra/bar repairs stay with the lead. Hero/squirrel work and PR73 remain held.

## Owner review

Open `CuffClearance_20261016/Review.html`. Check cuff fit from the front and rear on her normal route; the eye choice remains settled. Feedback is pending under RPT-20261015-03 and does not pause independent work. [Prior hem evidence](2026-10-16-kraken-hem-opacity.md) and [V11 source/eye provenance](2026-10-16-kraken-blue-fit-eyes.md) remain historical receipts.
