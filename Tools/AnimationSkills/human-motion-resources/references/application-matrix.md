# Resource and application matrix

Use a row for the actual problem, not every resource because it exists.
Read [verified-resources.md](verified-resources.md) for dated local evidence and
[application-workflows.md](application-workflows.md) for the selected procedure.

## What to apply, why, and the next test

| Need | Resource | Why it helps | Adaptation / boundary | Small next test and evidence |
| --- | --- | --- | --- | --- |
| Recover a movement from video | Motion2MixamoRig / GVHMR | Produces estimated body motion and a skinned Mixamo preview instead of inventing every key | Single clear person; monocular depth/occlusion uncertainty; no automatic pole contact; installed CPU path still grounds soles | Recover a short visible gesture; compare source, estimated joints and target continuously; log root changes before extending it |
| Build a routine from known good clips | Existing dance, sensual, flips, social or other mocap library | Preserves captured coordination and supplies transition material | Check actual skeleton, root motion, source speed, trimmed interval and joins; labels alone do not establish fit | Retarget one chosen excerpt onto the target; retain useful leg/body motion and inspect its entry/exit |
| Study shoulders, hips, knees or wrists under motion | SMPL-X / SMPL-H reference meshes and pose-correction bases | Supplies explicit joint placement, skin weights and learned deformation deltas | Reference topology and training distribution differ from the target; normalized weights do not guarantee good deformation | Pose a donor and target alike; compare skin with correctives off/on; identify whether bind placement, weights or corrective shapes cause the difference |
| Drive existing SMPL correctives in Unreal | smpl-unreal | Computes pose-dependent morph weights every frame from the final animated local joint rotations | Requires matching body, exact bone names, rest-axis convention and correct Pose### targets; older FBXs need conversion/adapter checks | Import a derived compatible body; verify morph names/counts and resolved bones; compare one joint with node off/on before a full routine |
| Reuse the old SMPL-H FBXs with that plugin | Clean export or derived compatibility adapter | Existing FBXs already contain 459 pose targets; the driver need not be reinvented | Current old f_avg_/m_avg_ names differ from plugin expectations; renaming alone does not prove bind-axis equivalence | Produce a complete name map, then test rest plus a single-axis bend against a donor control; use a current exporter when that is simpler |
| Improve deformation on a non-SMPL character | Target-authored weights/helpers/corrective morphs; Unreal Pose Driver or equivalent | Corrects the target's actual shoulder/hip volume without replacing its appearance | Donor deltas and drivers are not directly portable across unrelated vertex order/rest axes; animation retargeting does not transfer them | Diagnose one reproducible target pose, create a local correction, test activation and nearby/mirrored poses, then export/reload |
| Reconstruct detailed fingers from visible video | MANO model + a compatible hand estimator such as optional HaMeR | Models articulated hands and pose-dependent deformation | MANO files alone are not an estimator; extra dependencies/weights and sufficient finger visibility are required | Use a clear close hand excerpt; compare handedness/thumb direction and one opening/closing action before full-body capture |
| Obtain hand/body pose references without another capture | handpose.zip + SMPL-H/MANO PCA mapping | Local bank contains many body/hand parameter samples and can supply pose exemplars | Older 78-value format is not 26 ordinary axis-angle joints; FPS, root travel and capture semantics are not supplied by the lists | Decode one sample with the matching PCA basis/mean, display on a donor, confirm semantics and timing before selecting an excerpt |
| Make a palm actually contact a pole / prop | Target Control Rig / limb IK or FBIK, plus phase-aware contact targets | Solves explicit geometric reach after retargeting; does not require learning contact from examples | Correct space/units, palm-surface offset, elbow guide and feasible root needed; contact collision is not automatically enforced | Solve one target palm during a short contact interval, move the torso through it and measure residual plus penetration in opposing views |
| Prevent wrong-way elbow/knee/ankle solutions | Target-local preferred bend directions and joint limits | Guides IK toward intended bend plane and rejects implausible alternatives | Limits apply only where the solver uses them; axes and rest pose are character-specific | Flex a copied joint through useful motion; verify preferred direction, twist, both sides and nearby poses before applying to a clip |
| Focus a weight/morph/contact diagnostic region | SMPL-X face segmentation or SMPL-H overlapping vertex groups | Gives repeatable masks for local inspection and regional measurements | Vertex/triangle indices belong to their exact source topology; overlapping groups are intentional | Check counts/index bounds against the donor, visualize a shoulder/hand mask, then create a separately validated target mapping |
| Compare or mirror left/right deformations | SMPL-X flip correspondences | Provides face vertices plus barycentric weights for a reflected surface mapping | It is not a target's vertex permutation or a rule for swapping quaternion signs | Validate reflection axis, barycentric sums and surface residual on the donor before using correspondence on a copied correction |
| Use the newer Blender body package | Compatible current SMPL-X extension + its model DLC | Provides inspectable body meshes, many shape/expression channels and pose targets | DLC is data, not a second complete add-on; body data loading does not prove the old add-on code works on the current Blender | Check manifest/exporter version; load one body, update joint positions after shape changes, test a driven pose and export/reload |
| Evaluate the locked-head model | Alternate SMPL-X NPZ | Retains the same body-model schema as an alternate reference source | Filename is not a neck constraint; no demonstrated solution for an ugly neck or animation twist | Compare intended shape differences using identical parameters; do not replace a verified model merely because of the name |
| Add flesh/chain/cloth/hair follow-through | Existing spring, AnimDynamics, cloth or hair system | Adds velocity-dependent secondary motion after the primary motion works | Does not restore static pose volume, create contact or fix a broken retarget | One controlled motion/settle/contact test with a preserved no-simulation control; keep hair behind the owner's current priorities |

## Symptom routing

| Observation | First comparison | Likely work layer |
| --- | --- | --- |
| Source hand reaches; retargeted hand misses | Rest pose, chain lengths, root and wrist/palm frames | Retarget/contact; not a skin-weight problem |
| Bones are acceptable but axilla/glute collapses | Same target pose with original/repaired weights and correctives | Deformation |
| One shoulder is worse | Mirrored rest geometry, axes, weights and drivers in matched poses | Establish asymmetry before adding offsets |
| Limb flips when an effector is locked | Preferred bend plane, twist continuity, reach feasibility and space switching | IK/contact |
| Character moves toward the pole before catching it | Root velocity and contact-event timing | Choreography/root causality |
| Motion becomes a rigid orbit | Compare coordinated source limbs and transition timing | Motion content; do not simplify it to hide a rig fault |
| Blender looks good, Unreal does not | Actual imported influences, morphs/curves, bone motion and materials | Native import/evaluation parity |
| Grip pose looks closed but pole enters skin | Palm-surface target and finite pole radius; then finger contacts | Contact geometry, then grip detail |
| Still images look good but loops snap | Full-rate motion, angular velocity, phase boundaries and loop joins | Temporal validation |

## Recommended order when planning a first application

Choose the owner's current objective. For the existing SpaceSurvival routine,
use available choreography, verify target/root transfer, then establish visible
support and release before isolated finger detail. For a deformation study, a
single joint with correctives off/on is a better first experiment than another
full dance. For hand capture, require visible fingers before adding a large
estimator. These are choices of test, not authorization to resume implementation.
