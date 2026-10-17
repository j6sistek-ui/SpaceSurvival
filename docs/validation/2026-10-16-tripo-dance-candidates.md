# Tripo dance motion candidates — October 16, 2026

Status: **PARTIAL, preview library only.** The owner supplied a Tripo animation export and requested useful chest-shimmy, backbend and inverted motions for Cyborg or Cyan before assembling a sequence. Four Cyborg candidates are now available in Blender and Unreal. Existing dancer routines, Cyan, the hero and station placement are unchanged.

## Open / Check / Still open

- Open `C:/Users/j6sis/SpaceSurvival/.agent/local/TripoDance_20261016/Review.html` for four normal-speed, 12 fps animated Unreal previews. The neutral material is temporary and intended only for motion review.
- In Unreal open `Content/SpaceSurvival/Licensed/TripoDancePreview_20261016`, double-click a candidate and press Play. Use the handstand with the `FloorFit` suffix.
- Check which portions are useful for a sequence. Foot planting, palm support, entrances/exits and joins remain lead work once the useful sections are selected. This preview does not establish completed choreography or performance acceptance.

| Native animation suffix after `A_Cyborg_` | Length | Adaptation and limitation |
| --- | --- | --- |
| `Dance_ShimmyTorso` | 4.958 s | Retains torso/leg motion; stabilizes noisy arms in their starting local pose. Foot planting and joins remain. |
| `Dance_Backbend` | 4.958 s | Fits wrists and reduces neck spikes. Review the deep bend and transitions before use. |
| `Dance_BackbendTorso` | 7.958 s | Source is mostly upright torso sway despite its name; stable local arm pose. Trim useful sections. |
| `Dance_HandstandHold_FloorFit` | 6.958 s | Smooth inverted hold; adds 171.6302 cm root height so it is above the floor. Palm support, entry and exit remain. It is a handstand, not a headstand. |

The unadjusted handstand is retained separately as source evidence, making five new native assets. The four chosen actions and originals are in `.agent/local/TripoDance_20261016/CyborgPreviewV2/Cyborg_Tripo_PreviewLibraryV2.blend`.

## Provenance and preservation

- Owner download: `Downloads/futuristic+armor+suit+3d+model.glb`, 20,633,072 bytes, SHA-256 `d59ecb872e16dcc1a5214b5e497031525d0020df2b3c9cc34b04f031bbd02bde`; Tripo GLB2, 61-bone skin, 12 actions at 24 fps. No new purchase, model generation or plugin installation.
- Accepted Cyborg source: `.agent/local/CyborgRepair_20261013/RiggedDelivery/Cyborg_CHEST_REVIEW.blend`, SHA-256 `ad585525e10a0d34e35af1a2a6790b586890f704f28fd1e3d38348bc2b2f79f0`. Original file, native mesh/skeleton and six accepted pole clips are preserved.
- Retarget uses 61 matching bones and verified parent-space local transforms. Source wrist jumps reach about 98–107 degrees/key; the backbend has neck spikes. Bounded wrist/neck filtering and separate stable-arm variants retain the useful body motion. Unchanged local tracks are checked against the imported actions.
- Native clips use `/Game/SpaceSurvival/Licensed/CyborgRefresh_20261014/Cyborg_Refreshed_Skeleton`. No existing animation is replaced and no sequence/actor assignment is changed.
- Local station remains `7431ed23`; editor module remains `d248d14e`. Fifty protected files, including the Cyborg library, station, module and present production saves, are unchanged. Five new preview assets are pinned in `NativePreview/ExitState.json`. Licensed/native files and raw captures stay local; this PR carries the guide and evidence only.

## Verification and limits

Blender pose verification on the corrected retarget has at most 0.0000022 world-unit position error and zero reported rotation error. All four native clips retain their exact key counts and 24 fps timing. The constant handstand height adjustment is checked across all 168 frames and 61 bones: position-delta error below 0.000056 cm, rotation error below 0.000023 degrees.

The final isolated Unreal Play preview records 300 frames (60/60/96/84) at normal-speed 12 fps sampling. Actual native head poses match evaluated animation poses within 0.009 cm and recorded times match requested times. Sampled front views were visually inspected. Fresh NullRHI reload verifies all five saved animations on the same skeleton and their durations; protected hashes and clean packages pass. No C++ changed, so no editor rebuild was needed. This is separate from natural gameplay, floor/prop acceptance, FPS or packaged validation.

The Blender library V2 also verifies the handstand offset in world space; a rejected local-axis trial is retained. Earlier retarget V1 parent-space drift, finger-only cleanup, black/occluded captures and frozen editor construction poses are retained as rejected private trials. Final captures use the separate Play world and verify actual poses. API-property errors were repaired; no failed capture is counted as evidence. Preview lighting and material changes were discarded. The engine basic material's transient skeletal-usage change was reloaded without saving it; both owned Unreal sessions exit after cleanup.

Private evidence is under `.agent/local/TripoDance_20261016`: `CyborgPreviewV2/Retarget.json`, `Stabilized.json`, `HandstandFloor.json`, `NativePreview/Import.json`, `FloorVerification.json`, `PlaybackPreviewV2.json`, `ExitState.json`, `NativeReload/Reload.json` and `ReviewValidation.json`. The HTML's paths and animated files pass static checks; browser visual/copy interaction is unverified because local-file automation is unavailable.
