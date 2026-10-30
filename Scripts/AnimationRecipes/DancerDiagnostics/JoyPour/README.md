# Joy archived pour: source-bound Candidate04

This small CPU-only recipe reproduces an **isolated, unapproved** six-track correction from two owner-private pose exports. It fixes demonstrated contact-solver roll discontinuity and restores the original cup-hand travel to the complete bottle/cup assembly. It neither changes native assets nor launches Unreal/Blender. Python and NumPy must already exist; no dependency installation is included.

## Minimum source files for PR96

- `JoyPourFrameRepair.py`: deterministic patch and numerical metrics generation.
- `JoyPourFrameValidate.py`: independent sparse-patch readback, full-frame contact/direction/endpoint guards, using math helpers from the adjacent repair script.
- This README. These three files form the source-only recipe under `Scripts/AnimationRecipes/DancerDiagnostics/JoyPour/`; see the [validation receipt](../../../../docs/validation/2026-10-26-dancer-source-followup-and-service-audit.md). Do not publish `prepare_reproduction.py`, previous trial scripts, raw exports, generated pose patches, native content, FBX/blend files, screenshots or private rig metadata.

## Required private inputs

1. `.agent/local/Waitress_20261015/Handoff_20261016/PourReview/Inputs.json`, SHA256 `6a44e5863000034a40d805431c0b94654c816aaa5f90a1d2cc30a730e590bec7`. Contains the historical actual Joy action export at `joy.poses.Pour`, 101 CC_Base bones, 381 frames at 30 Hz, component-space centimetres, local transforms as `[translation, quaternion_xyzw, scale]` with parent names.
2. `.agent/local/Waitress_20261015/ContactPoses.json`, SHA256 `652b12c9c9f9033a18478b9b0691c1f307a36b18302f87fa937306fc526c49cc`. Contains `A_Joy_Bar_PourAndServe` and `A_Joy_PourStanding`, the original native-source motion before the contact correction.

Both hashes are enforced. A different source or skeleton requires new diagnosis and identity; removing the guards is not adaptation. This is not a generic IK tool and does not use Vexa morphs.

```powershell
python Scripts/AnimationRecipes/DancerDiagnostics/JoyPour/JoyPourFrameRepair.py --native-poses '<private Inputs.json>' --original-poses '<private ContactPoses.json>' --output-dir '<new private output directory>'
python Scripts/AnimationRecipes/DancerDiagnostics/JoyPour/JoyPourFrameValidate.py --native-poses '<private Inputs.json>' --original-poses '<private ContactPoses.json>' --patch '<new private output directory>/RigFrameCandidate04Patch.json' --report '<new private output directory>/Readback.json'
```

Run from the repository root with the existing Python/NumPy runtime. The repair
refuses an existing output directory, and the validator refuses an existing report
with an exclusive write. Choose fresh paths for each run; do not delete or overwrite
earlier evidence to rerun it. All generated data belongs in ignored private output,
not `Content` or the source recipe folder.

The generated sparse patch must hash to `be9e2d6a88c28d84b6865f64defd34ee81e5d468e8d5a34b1c59895898e32eb4`. Numerical metrics and source hashes are emitted separately. Only `CC_Base_[L/R]_[Upperarm/Forearm/Hand]` rotations change. All local translations/scales, 95 protected tracks and exact endpoint frames remain unchanged. Shared hand travel preserves bottle/cup relative position and their world orientations. Calibration is the original safely bent frame 60; signed roll unwrapping and the original contact envelope address the known branch/return failures without broad smoothing.

## Evidence and limitations

All 381 frames were regenerated and independently read back. The largest right-wrist local frame step changes from 57.45 to 16.22 degrees; right forearm from 51.79 to 11.51. At 3.833 seconds these become 10.56 and 4.07 degrees. Hand-pair relative error is below 1e-12 cm and world hand orientation error below 0.000003 degrees. These are continuity/contact checks, not visual or anatomical acceptance.

The actual current mesh source was separately identified through SK_Joy.uasset import metadata: `SourceAssets/MigratedProjects/JoyBartender_20261014/outfit_v25/SK_Joy.fbx`, MD5 `6dbfec92efed06b5684b892d8bc86fc1`, SHA256 `465b6f5f20b648a38619772d9e48fc124bfbac1fba32ce9f848e68f8ff5ab91d`. A metadata-only Blender import matches all 101 native rest names/parents, bone origins within 0.00006114 cm, and segment lengths within 0.00002945 cm. World position conversion is Blender metres `(x,-y,z) * 100`; replay must account for per-bone FBX/native orientation bases. The older `soft_tissue_v2` mesh is not the current outfit.

The private `JoyAssessment_20261026/VisualProof_Candidate04` comparison now has18 paired event views on that matching mesh and a381-frame30Hz video, SHA256 `884eb3813fd292ae4c085ff36c26534a52b486723a7ac0560d362a3b860b5108`. Nine rest-basis replay samples agree within0.00248mm at bone origins. Inspected stills/adjacent frames show no gross missing arm or branch inversion; the right pouring wrist remains strongly flexed. Existing neutral-display garment artifacts also occur in the rest control, and actual props/counter are absent. These are limited source observations, not continuous-motion, skin or native clearance acceptance.

Before adoption, the lead must verify current scene assignments, review the supplied actual-speed playback and inspect skin/twist/helper response with actual held props in the native scene. The separate CounterCandidateV8 delivery is unpatched; hunch, jacket/body/counter contact, other actions and live gameplay remain open. No source or numerical result grants owner acceptance.
