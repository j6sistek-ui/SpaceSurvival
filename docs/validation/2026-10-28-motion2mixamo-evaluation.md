# Motion2MixamoRig installation and first evaluation

Owner authorizes installation from their fork, isolated evaluation and D-drive outputs.
The reusable skill is conditional on useful motion; none was created. This record supports
RPT-20261021-01 and does not close dancer/contact or owner-quality acceptance.

## Installed and verified

- Fork: https://github.com/j6sistek-ui/motion2mixamorig at
  `f05a718188026b06e7ee64b47bab077970444b19`, package/extension0.1.8.
- Runtime: `M:/Local AI/Tools/Motion2MixamoRig/.venv`, Python3.11.9,
  CPU PyTorch2.15.0, existing Windows compiler; no global Python/system packages.
  Docker service was stopped. Native Windows integration was tested in its isolated
  venv; no container installation or CUDA backend was validated.
- Blender5.2.2 extension is enabled as `bl_ext.user_default.motion2mixamorig`.
  Prior user preferences are backed up under `D:/Motion2MixamoRig/SetupLogs/OriginalPreferences`.
  Fresh hidden Blender reload verifies the extension, configured external pythonw
  and project paths, and preservation of all previously enabled add-ons.
- All generation outputs route to `D:/Motion2MixamoRig/outputs`; the clone's outputs
  directory is a verified junction there. Runtime weights and isolated caches use M.
- `pip check` passes. FFmpeg7.1 resolves from the venv without a system installation.
  The required SMPL-X neutral NPZ loads; SHA256 starts `376021446ddc86e9`.
  The original870,108,517-byte model ZIP was moved from Downloads to
  `D:/Motion2MixamoRig/InputModels/models_smplx_v1_1.zip` only after complete
  SHA256 verification (`cb593838a5d60239...`).

Initial sandbox smoke crashed because the test held a Blender RNA preference wrapper
across add-on unregister/register. Reacquiring the wrapper after registration fixes
the test; the corrected sandbox and actual-preference install/reload both exit0.
This was not an owner-scene crash. Its original diagnostic is retained on D.

## First actual video-to-animation run

Input: first3seconds of the owner's supplied floating-dancer reference,72frames at24fps.
Original full-video SHA256: `9594dec51713135204af57cacf008f14386c9d779a1d175145ec73dbbb2d324e`.
Target: owner-downloaded Female Dance Pose Mixamo FBX, copied/hash-verified as
`assets/mixamo/UserMixamoCalibration.fbx`; original remains unchanged.

CLI settings: `--device cpu --no-foot-lock`, hand detection off, explicit D output.
Runner exit0 in214.94seconds including preflight; pipeline reports206.2seconds.
First-use weights downloaded to M. No Unreal instance was launched or modified.

Run: `D:/Motion2MixamoRig/outputs/Validation_20261028_01`.

- Four MP4s decode all72frames at24fps: source comparison, human skeleton,
  Mixamo skeleton and skinned target.
- Animated GLB:1,144,320bytes; native Blender imports one65-bone armature,
  two meshes/14,309vertices and the animation, with finite motion across all72frames.
  Saved editable `Motion2Mixamo_Validation.blend` is in that run folder.
- Retarget NPZ has22 controlled bones; rotations/translations are finite.
  Largest adjacent-frame joint rotation16.34degrees,99th percentile4.04degrees;
  these metrics are not anatomical or artistic acceptance.
- Tool self-intersection report has zero detected penetrations deeper than1cm.
  Its approximate test excludes adjoining body parts and does not test pole/floor
  contact, joint limits, or all deformation defects.

Visual comparison shows a recognizable approximate body pose/gesture transfer.
It does not establish an exact reconstruction, clean acrobatics or production quality.
The source itself is AI-generated and has depth/occlusion ambiguity. Missing focal
metadata triggers the tool's heuristic; no extra system package was installed for it.

**Important zero-G limitation:** `--no-foot-lock` does not disable sole grounding.
This run still shifts the hips vertically by median2.81cm, maximum18.28cm.
Its world trajectory is therefore not faithful free-flight data. Fingers were not
recovered. A project-character retarget, hand/contact constraints, routine integration,
Unreal playback, CUDA timing and owner acceptance remain untested. Do not create a
production skill or replace accepted motion on the strength of this smoke test.

## How to open and use

Blender5.2: 3D Viewport > N sidebar > Motion2MixamoRig. External Python is already
configured to `M:/Local AI/Tools/Motion2MixamoRig/.venv/Scripts/pythonw.exe`;
project directory is `M:/Local AI/Tools/Motion2MixamoRig`.
Choose a single-person video and a Mixamo-rigged FBX. CPU is the verified backend.
The Python backend remains outside Blender. Existing extraction can be reused with
`--skeleton` to avoid paying inference time again for another compatible target.

Evidence: `D:/Motion2MixamoRig/SetupLogs` contains install/native-reload receipts,
InputReceipt.json, ShortValidationReceipt.json, OutputValidation.json,
NativeOutputValidation.json, full logs and the reference/comparison contact sheets.
These private models, videos, packages and environments are not uploaded to GitHub.

## Additional owner downloads, inspected October28

| Download | Value and boundary |
| --- | --- |
| `mano_v1_2.zip` | Contains MANO_LEFT/RIGHT and SMPLH female/male models. MANO_RIGHT is the optional hand-detector model for this tool; no finger dependencies or extra weights installed yet. Useful separately for hand-pose/deformation research. |
| `handpose.zip` |38 serialized pose-data files,48.1MB expanded; not ready-made FBX/Unreal clips. Requires format-specific import/retargeting before useful animation evaluation. |
| `f_avg_noFlatHand.fbx`, `m_avg_noFlatHand.fbx` | Body/hand FBX candidates for inspecting an alternate rig and deformation; not imported or validated in this pass. |
| `smplx_blender_addon_300_20220623.zip` | Legacy Blender add-on with body model, shapes and sample textures; README tested Blender3.1. Not the installed Motion2MixamoRig extension and not validated on Blender5.2. |
| `smplx_blender_addon_dlc_smplx1.1-1.0.0-20260505.zip` | Five body-data files, including a344,984,132-byte .blend and shape-to-joint maps. Data DLC, not a standalone second add-on. Retain for a compatible current SMPL-X extension. |
| `smplx_lockedhead_20230207.zip` | Three alternate body-model NPZs; not required by the current test. Retain as optional reference rather than replacing the verified model. |
| Segmentation/flip files | Body-region labels and mirrored-vertex correspondences; useful for region masks/symmetry tooling, not motion clips or joint-limit rules. |

These further Downloads were inspected without importing their models or deleting/moving
them. They are optional reference/archive candidates for D; the current runtime does
not depend on their Downloads paths. Mathematical body models are useful deformation
references, not universal anatomical/contact solvers for unrelated character topology.

The owner's [smpl-unreal fork](https://github.com/j6sistek-ui/smpl-unreal) computes
runtime corrective-morph weights for matching SMPL-X/SMPL+H meshes. Its
[usage requirements](https://github.com/j6sistek-ui/smpl-unreal/blob/main/docs/usage.md)
require the corresponding imported morph targets; it does not generate them for Vexa.
Reviewed only; not installed, built, or integrated. The official
[MANO overview](https://mano.is.tue.mpg.de/) describes learned hand deformation and
SMPL+H's body/hand combination. Sources reviewed October28,2026.

Code, model, training-data and output permissions are separate. Installation proceeds
at the owner's instruction; commercial clearance remains unestablished. No research
body data or derived motion was adopted into the commercial game in this evaluation.

Open: comparison MP4 and editable blend in the D run folder. Check: whether recovered
gesture/limb timing is useful enough for a second targeted test. Still open: AI
free-flight preservation and target-character/contact evaluation before any reusable
production workflow; James motion acceptance. The broader backlog remains held.
