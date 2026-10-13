# Silver: retained sources and reusable rigging lessons

Updated 2026-10-13. This guide identifies recovery sources after the owner-requested cleanup; it does not declare every animation or collision accepted.

## Start here

- Current editable master: `.agent/local/ViableEldFinish_20261013/Blender/Silver_Platinum_Finish.blend`. Seven image datablocks are packed, no linked libraries or Alembic cache dependencies; 17 actions are embedded. Keep its adjacent `blendcache_Silver_Platinum_Finish` directory: the current dance has 856 baked hair frames. The core NPC library is a separate retained source below.
- Untouched originals: the four GLBs in `C:/Users/j6sis/Downloads/Viable Eld`. Vendor hair/outfit/animation packs remain in their existing locations, outside cleanup scope.
- Current Unreal assets: `/Game/SpaceSurvival/Licensed/ViableEldReview_20261013`. Preserve the entire namespace, including earlier import skeleton/material dependencies. The current apartment actor uses `MotionFinish_v1/BP_Silver_Apartment`; its live `BodyDynamics` component overrides the small baked XYZ channels while preserving pose/lift curves. The owner accepted this visible body motion. Hair collision remains unresolved; previous assets were restored, not approved. `HairContact_v1/PA_Silver_BodyContact` is unassigned diagnostic work, not the current collision asset. Later research confirmed collision response but did not produce a saved repair; preserve the interpolation-import failure evidence before further authoring. See the [contact receipt](../validation/2026-10-13-silver-hair-contact.md).
- Native import source: `.agent/local/ViableEldFinish_20261013/BodyDynamics/Garment_ST_cm_5769183e/Sentinel_ST_Derivative.blend` and adjacent FBX. Keep `Ready_ST_Morph_Curves.json`, export/import helpers and their readback receipts.
- Final GIF and apartment view remain in the task folder. The dated [motion receipt](../validation/2026-10-13-silver-motion-finish.md) and [voice receipt](../validation/2026-10-13-silver-persona-voice.md) distinguish implemented work from owner/live-audio acceptance.


- Current native scalp overlay: `.agent/local/ViableEldFinish_20261013/HairCoverage/Silver_ScalpFoundation.blend` and `G_Silver_ScalpFoundationFull.abc`; Unreal `HairCoverage_v3/G_Silver_ScalpFoundation`, binding and `PA_Silver_HeadCollision`. The original full master/cache remain unchanged; use this overlay alongside them for the current native appearance. `PlatinumHair` and `PlatinumScalpCoverage` share `M_Platinum_Strands`; editing that material changes both, while a component-only material override must be assigned to both. See the [hair repair receipt](../validation/2026-10-13-silver-hair-coverage.md).

## Retained recovery models

Paths below are relative to `M:/Local AI/Projects/ViableEld_20261012/work/`.

| File | Why retained |
| --- | --- |
| `InnerCup_Weight_Trial.blend` | Exact 9dc6 body/weight baseline used to assemble the current master. The historical filename is not a signal to adopt a newer trial. |
| `Dance_Finger_Pose_Candidate.blend` | Corrected finger action donor used by the current master. |
| `NPC_Core_Basics_Library_v2.blend` | Compact core action library. |
| `CoreBasics_Barefoot_Paired_Library_v1.blend` | Paired core-body controls and the native core export source. |
| `Sentinel_Optimized_Unrigged.blend`, `Sentinel_Optimized_Rigged.blend` | Early optimized body before later outfit/deformation assembly. |
| `Blonde_Groom_Derivative.blend` | Editable extracted groom source. |
| `Variety_Outfit_OriginalDesign_Refined.blend` | Original outfit cutouts retained after rejecting the added opaque panel. |
| `Mouth_Speech_Relaxed_v2.blend` | Accepted relaxed speech pose/metallic teeth source. |
| `Hair_FinalRepair_Candidate_v2.blend` | Earlier groom setup for recovery/comparison. |
| `ShakingHip_Action.blend`, `VarietyDance_Hinge90_Action.blend` | Compact animation donors. |
| `Upper_Attachment_ARAP_c365960d/Shoulder450_Trial.blend` | Manual frame-450 shoulder study, **not adopted or safe to generalize**. Its disposition, target arrays and matched images are retained. |

All task scripts, JSON reports, numerical arrays, raw import/export sources and diagnostic images outside the encoded native GIF sequence remain available. Deleted experiments referenced in old reports are historical; do not blindly rerun those scripts. Reconstruct from the named sources above and use a new output/cache path.

## Lessons to transfer to another character

1. **Retarget local anatomical axes, not names alone.** Rest-relative head/hand frames, forearm roll sharing and finger bend axes matter. A clip can have matching bone names yet twist wrists or splay fingers. Review both sides through idle, sitting, conversation, wave and extreme dance poses. Start with `core_animation_retarget.py`, `repair_core_hand_basis.py`, `repair_core_head_basis.py`, `repair_dance_finger_splay.py` and the hand-axis audit reports in the retained M: scripts/work folders.
2. **Separate skinning, pose correction and secondary motion.** Diagnose with dynamics off, then on, and check the actual textured surface. Smooth normalized weight transitions are foundational. Rebuild control anchors after changing weights, pair curves to the exact action and retest clothing. The historical Blender bake measured about 2.25 mm breast/1.02 mm hip, with 3 mm arm-raise lift. The current Unreal Blueprint overrides its twelve XYZ channels with live springs (16 mm chest/12 mm hip limits), while retaining the lift curves; see the [runtime settings and evidence](../validation/2026-10-13-silver-runtime-springs.md). These are character-specific, not universal values. Use `soft_tissue_runtime.py`, `adopt_body_weights_rebake.py` and the C: assembly/control receipts.
3. **Preserve the garment design.** Raw triangle overlap in transparent cutouts is different from visible clothing penetration. Test opacity alongside body/garment contact. Do not add coverage to conceal a weight problem. Keep matched body and garment morph deltas; preserve neutral geometry, UVs, skin weights and rest bones across export.
4. **Keep unit conversion explicit.** The export derivative uses metres internally and explicit centimetres for Unreal FBX. Round-trip before integration. Copy animations to the intended skeleton and read back all motion-curve keys/interpolation values. Use the retained `BodyDynamics` export, verify, merge and native-import scripts as concrete examples.
5. **Hair must have a coherent cache and collision setup.** A Blender action/collider/body change invalidates the old bake. Bake in one process; use a distinct filename/cache for previews. In Unreal, fit head/neck/torso proxies and verify Niagara activity. Temporary hair over the face is natural if it clears; coverage alone is not penetration or sticking. Unreal array structs must be assigned back by index for edits to persist.
6. **Treat groom initialization separately from tuning.** A missing `DataFlags_HasData` interpolation assertion is a resource/binding problem, not proof of bad stiffness. A fresh saved-asset/binding load recovered this test; it is not a proven general engine fix. Preserve the failed receipt and verify playback after recovery.
7. **Inspect captures before changing assets.** In the apartment, the lace initially looked opaque because texture mips had not streamed for the remote capture. A local view/prestream request restored detail without altering the material. Camera-only evidence can mislead about materials and collision.
8. **Do not generalize a one-pose repair.** The shoulder ARAP study was left unadopted. Equal-arm tests substantially reduced apparent left/right lift asymmetry, showing that choreography contributed to the screenshot difference. Stop when the owner sets the quality/cost boundary; do not trade a tolerable local crease for a broad speculative repair.

9. **Retain scalp coverage independently of loose lengths.** A tip-only strand mask deleted entire right-side/root sections. Restoring all long locks caused instability, so this repair uses short bound prefixes beneath the existing moving groom. Head collision must follow the head bone and cover the measured face envelope, not an undersized neck-owned approximation. Test at normal speed as well as capture-friendly time steps; neither proves all future motions. Copy reflected nested structs before editing them, since direct wrappers can dirty their source objects.

## Cleanup audit

The local `Cleanup/DeletionPlan.json`, deletion receipt and verification record list exact files, reasons, bytes and retained-file hashes. Cleanup removes redundant experimental `.blend` files/backups, their unused physics caches, isolated editor caches and raw frames already encoded into the retained GIF. It does not remove original downloads, current source/cache, native assets, station maps, saves, shared tooling, or unrelated character work. The [dated cleanup receipt](../validation/2026-10-13-silver-cleanup.md) records the verified51.21 GB reclaimed.
