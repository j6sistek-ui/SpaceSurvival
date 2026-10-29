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

## Deeper resource study and reusable skill

Later October28 the owner explicitly requests a deeper resource/use-case study,
a skill and an application matrix. This supersedes the earlier skill deferral
for a resource-selection workflow; it does not accept the recovered animation.

Installed: `C:/Users/j6sis/.codex/skills/human-motion-resources`. Versioned source:
[skill](../../Tools/AnimationSkills/human-motion-resources/SKILL.md),
[application matrix](../../Tools/AnimationSkills/human-motion-resources/references/application-matrix.md),
[application procedures](../../Tools/AnimationSkills/human-motion-resources/references/application-workflows.md)
and [verified findings/sources](../../Tools/AnimationSkills/human-motion-resources/references/verified-resources.md).
The entrypoint routes between motion, retargeting, contact, deformation and secondary
motion; it preserves current owner scope and requires target-specific evidence.

New actual inspections, with no Unreal launch or game changes:

- Both legacy SMPL-H FBXs load in isolated hidden Blender5.2.2:6,890vertices,
  53bones including root,459 pose correctives and no animation actions. The old
  SMPL-X bodies have486 pose correctives and10 expressions; the newer DLC has
  the same486 pose correctives and100 expressions. DLC is data, not a second add-on.
- MANO numeric fields contain778vertices/16 joints/135 pose bases. The SMPL-H
  model has52 weighted joints/459 pose bases; SMPL-X has55/486. Some donor
  weights use more than four influences; pruning can change native deformation.
  Legacy Chumpy objects were treated as inert metadata, not executed.
- All38 hand-pose lists contain18,947 finite78-value samples. One sample expands
  to156 values under the bundled wrapper's66-body-plus12-hand-PCA default.
  Semantic profile, FPS, world travel and animated quality are still unverified.
- Source review of smpl-unreal87cea30d confirms fixed canonical bone names,
  Pose### morph counts and coordinate conversion. The old FBX bone names differ;
  a compatible export or derived name/bind-axis adapter can reuse this existing
  driver, subject to a one-joint parity test. No plugin installation/build occurred.
- Native PBIK headers confirm preferred angles, per-axis limits and stretch settings.
  These guide a configured solver; they are not automatically applied anatomical
  guarantees on every animation. No target rig was changed.

Private receipts are under `D:/Motion2MixamoRig/ResourceStudy_20261028`.
Two temporary extracted .blend files were removed after inspection; original
downloads/models/preferences remain. The brief D disconnection interrupted only
ZIP creation; the drive returned and the final15,411-byte skill archive was written.
The five-file30,905-byte installed/repository copies match, all relative reference
links resolve, and the skill-creator validator passes. This validates the skill's
structure and inspected facts, not an end-to-end game repair or an independent
behavioral acceptance test. No global dependencies, model downloads or GPU work.

Portable archive: `D:/Motion2MixamoRig/ResourceStudy_20261028/human-motion-resources-20261028.zip`.
Invoke `$human-motion-resources` in a subsequent chat. The matrix recommends a
small experiment appropriate to the objective; those recommendations do not
authorize changing another chat's work or automatically resume the held backlog.

## CUDA and hand detection ready

Later October28 local time (2026-10-29T01:32Z), the owner reports liking the sample
and explicitly requests optimization plus a fully working hand setup. The following
supersedes the historical CPU-only, missing-finger and untested-CUDA status above;
acceptance of the sample is not acceptance of a game-character animation.

The existing isolated M venv was upgraded in place to torch2.14.1+cu130 and
torchvision0.29.1+cu130. `pip check` passes and an actual CUDA kernel succeeds
on RTX5080, compute capability12.0/sm120, driver621.01. CPU fallback remains
available in the same environment; no second venv, global Python package or CUDA
toolkit was installed. Cache/temp paths, including CUDA/TRITON caches, remain on M.

The hand estimator is vendored in the tool; the absence of a top-level `hamer`
import does not indicate missing code. MANO_RIGHT.pkl from the owner's original
ZIP was converted with the bundled converter and installed in the expected
`assets/body_models/mano` directory. The original archive is unchanged.

The original Texas weight URL failed certificate/connection checks. Securely
downloaded individual files from the author's [official HaMeR Space](https://huggingface.co/spaces/geopavlakos/HaMeR/tree/aabc78ee4fd1f1ccf1a55fdd4225bf84df0e680a)
match its published LFS SHA256 values; TLS verification was never disabled:

- hamer.ckpt:2,689,536,166bytes,
  `e5cc06f294d88a92dee24e603480aab04de532b49f0e08200804ee7d90e16f53`.
- mano_mean_params.npz:1,178bytes,
  `efc0ec58e4a5cef78f3abfb4e8f91623b8950be9eff8b8e0dbb0d036ebc63988`.

No duplicate6GB model archive was downloaded. The heavier body/hand stages use
CUDA; the short2D ONNX pose stage uses CPU and is not a CUDA failure.

A fresh run repeats the preserved3-second/72-frame video and Mixamo target,
with `--device cuda --detect-hands --hand-smooth 0.08 --no-foot-lock` and explicit
D output. It exits0 in61.39seconds overall; the pipeline reports39.4seconds.
The initial CPU run included first-use downloads, so these are not a matched
speedup benchmark. Both hands are processed on72/72frames; all30 finger tracks
move, rotation matrices are finite/orthonormal, and four MP4s decode72frames
at24fps. Hidden native Blender5.2.2 evaluates the exported GLB and confirms all
30 moving finger bones. The task process exits and releases its GPU allocation.
The owner's open scene/preferences and all Unreal editors remain untouched.

Open `D:/Motion2MixamoRig/outputs/Validation_CudaHands_20261028_01/Review.html`
or the adjacent `Ready_To_Try_CUDA_Hands.blend`. The blend contains the actual
animation and populated source/rig fields, CUDA, Detect Hands,0.08 smoothing and
previews enabled. For another input, change the source video and use a Mixamo-rigged
FBX; the MANO/weight locations are already configured. Outputs remain on D.

Receipts: `D:/Motion2MixamoRig/SetupLogs/GpuHands_20261028`, especially
CudaInstallReceipt.json, AuthorHandWeightsReceipt.json, CudaHandsValidationReceipt.json,
CudaHandsOutputValidation.json and NativeCudaHandsValidation.json.
The installed skill, tracked mirror and new16,454-byte portable archive match:
`D:/Motion2MixamoRig/ResourceStudy_20261028/human-motion-resources-20261028-cuda-hands.zip`.
The original skill archive is preserved. Standalone matrix companion links on D
now resolve to the updated procedures/findings.

Still open under RPT-20261021-01: exact finger accuracy on new/occluded footage,
unrelated target compatibility, pole contacts and native game adoption. Sole
grounding still alters zero-G root travel; this setup does not fix that behavior.
No production animation, native game plugin, character or release was changed.
