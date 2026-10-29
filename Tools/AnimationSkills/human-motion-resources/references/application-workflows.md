# Targeted application workflows

## A. Video or existing mocap to a character

Inspect the actual source first. Prefer a useful existing clip over recovering
the same motion again from rendered video. For video, verify person visibility,
camera movement, occlusions, AI-generated discontinuities, FPS and the source interval.

For Motion2MixamoRig, use its current `run --help`; `--rig` expects a Mixamo FBX.
Start with the verified CPU backend or an explicitly available tested GPU backend.
This machine's known short-test command shape is:

```powershell
& 'M:/Local AI/Tools/Motion2MixamoRig/.venv/Scripts/python.exe' -m motion2mixamorig run `
  --video 'D:/path/short-reference.mp4' --rig 'M:/path/mixamo-reference.fbx' `
  --device cpu --no-foot-lock --output-dir 'D:/path/new-run'
```

The placeholder paths must be chosen for the task; do not overwrite the earlier
validated run. Do not run install/setup again when the existing environment works.
Reuse `--skeleton <previous/skeleton_motion.npz>` for another compatible target only
when source/extraction identity is unchanged. Archive a run receipt with source hashes,
trim/FPS, target identity, model/tool versions, settings and output locations.

The inspected0.1.8 implementation calls `plant_soles` when contact data exists,
independently of the `foot_lock` option. There is no verified `--no-ground` option.
For zero-G, first isolate/bypass grounding in a derived tested backend path or use
the raw extracted trajectory in a separate conversion. Verify it against a control;
do not silently delete the Y/Z track or invent a nonexistent CLI flag. Retargeted
root motion and generated previews alone do not prove source world travel.

For Unreal target transfer, establish source/target chains, rest poses, root/pelvis,
axes and scale on copies. An IK Retargeter transfers skeletal motion; weights,
corrective shapes, material appearance and prop-contact logic remain separate.
Test a gesture and one contact transition before retargeting the full library.

## B. Use learned correctives without replacing the target character

The donor provides a reference, not a universal skin patch. Compare matched poses:
rest, intermediate and high flexion, overhead/forward reach, twist, and mirrored
cases relevant to the observed defect. Keep motion identical while comparing
weights, corrective activation and their combination. Preserve body proportions
and neutral neck/torso silhouette; a smoother but inflated body is not a successful fix.

SMPL pose corrections use local rotation-matrix residuals `R - I`, with nine
coefficients per contributing joint. They are signed coefficients, not nine
ordinary 0–1 sliders or nine clinical joint-limit rules. Their vertex deltas are
defined on their own bind mesh. A non-SMPL character needs a validated surface/bone
mapping or target-authored corrective shapes and drivers; test one joint first.
Sharing a skeleton or nearly the same vertex count is insufficient compatibility.

Preserve the influence budget deliberately. The inspected donor weights use up
to10 active influences for SMPL-X,8 for SMPL-H and6 for MANO. A four-influence
preview/export may alter them. Measure dropped weight and compare deformed
surfaces after import rather than silently pruning or assuming native parity;
do not change project-wide rendering settings merely because a donor uses more.

The SMPL Unreal plugin already supplies the compatible body's runtime driver.
Reuse it rather than rebuilding that driver. At the inspected source, it detects
486/468 SMPL-X or459 SMPL-H `Pose###` targets and resolves fixed canonical bone names.
It also converts the expected Unreal bind convention to SMPL coordinates.
An older FBX can match the morph count while still failing bone lookup or rotating
correctives incorrectly. Prefer a compatible current export or a derived adapter
whose naming **and** bind-axis behavior are tested on rest and single-axis poses.

For the documented UE5.8 export/import route: enable morph import and set Morph
Threshold Position to0.0; the two eyes'18 zero-offset targets may be omitted,
giving468 rather than486. Import body once and animation-only clips onto that
skeleton. Avoid conflicting baked corrective curves when the runtime node drives
the same curves. Do not apply these settings blindly to unrelated imports.

In an authorized native test, inspect resolved bones, morph targets, active
curves and node on/off deformation after the final pose-changing operation.
Later IK changing the pose after corrective evaluation can make weights stale.
Blender Corrective Smooth/Preserve Volume, bendy bones and drivers do not all
transfer through FBX as an equivalent Unreal runtime operation; explicitly bake
or implement the required deformation and compare after reload.

## C. Palm/pole, prop and leg support

Establish contact phases from the actual routine: reach → catch → supported
motion → release. Keep source motion outside the intended correction window.
Transform both the apparatus and the palm helper into the same space. A wrist
bone origin is not the palm surface. For a cylinder, account for its finite
axis, radius and palm offset, rather than targeting the pole's centerline.

Use the native limb IK/FBIK tools when suitable. Configure target-specific bend
directions, rotation limits and root behavior; disable stretch when preserving
proportions. Seek a feasible body/contact configuration. If it cannot reach,
adjust an authorized root/contact plan or release the contact rather than force
an elbow backward, twist a wrist or stretch a limb. Continuous switches need
matched transforms; avoid a full blend toward a fixed hand orientation.

Measure palm/contact residual, skin penetration and limb length through the
window, then inspect opposing views and full-rate motion. An approximation
based on body-part vertices can miss a pole cutting through adjoining regions.
Contact may slide deliberately along the pole; distinguish intentional sliding
from missed contact. The owner may accept a palm contact before detailed finger
grip; do not spend the first pass on fingers while support remains visibly absent.

For free flight, explain course/rotation changes by the authored impulse or
contact. Preserve deliberate limb counter-motion and purposeful root travel;
do not pull the performer back like a tractor beam or freeze the body between poses.

## D. Hands, pose banks and secondary motion

MANO is the hand model; an estimator is a separate stage. Low-resolution/hidden
fingers cannot become reliable capture merely because MANO is installed. For
an authored grip, a target hand pose plus contact constraints can be a smaller
and more useful first test than another heavy inference setup.

The local hand bank has78 numbers per sample. The bundled old wrapper's default
layout is66 body axis-angle values, then6 left and6 right PCA coefficients.
Each hand expands with its matching first six `hands_components` rows and
`hands_mean`; expanded full pose has156 values. The relaxed/flat mean choice
matters. Do not treat the final12 values as four joint rotations. The sample
lists supply no verified FPS or root-translation channel; reconstruct and
visually identify one sample before creating a timed sequence.

For flesh/chain/cloth/hair, start after the primary rig/contact works and keep
the accepted appearance. Validate finite bounded response, contact, settling,
fresh reload and native parity. Zero gravity alone does not define damping,
air drag or the desired artistic response; tune from evidence, not copied
universal values. These simulations are not a replacement for static corrective
volume or a physics-based anatomical guarantee on baked animation.
