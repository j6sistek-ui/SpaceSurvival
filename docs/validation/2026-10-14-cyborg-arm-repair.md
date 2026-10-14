# Cyborg deformation repair checkpoint

## Latest checkpoint: October 14, 05:14 UTC

**PARTIAL / chest accepted, arms unresolved; no station adoption.** The owner accepted
the latest chest appearance, then rejected the worsening shoulder/neck trials. The
owner permits dropping an animation if the issue occurs in only one clip. A fresh
native capture on the unchanged chest candidate covers 36 closeups from 12 clips;
pinching recurs in PoleIdle, StripDance3 and Sensual2_Dance4/7. The single-clip
condition is not met, and no animation was removed. New deformation trials are
rejected, isolated and unadopted. Silver remains untouched until Cyborg passes Unreal.

The 118,998-triangle surface, materials and fitted skeleton remain intact. The latest
private candidate changes only six breast displacement morphs: their influence was
centered at Z=1.302 m, below the breast volume; the new center is Z=1.371 m with a
continuous attachment falloff. Matched upward/downward Blender tests retain a rounder
shape. Rest vertices, skin weights and skeleton are exactly unchanged by this step.
The two existing downward shoulder correctives remain; raised-arm corrections are
not adopted. Native chest capture completed: 163 frames / 1,088 samples, with finite breast
offsets peaking at 1.5622 cm left and 1.4330 cm right (1.6 cm limit). The owner
accepts the chest; this does not accept the remaining rig defects.

The new opt-in `SSJointCorrectiveComponent` reads arm direction relative to the chest
and writes bounded morph weights after mesh evaluation. It never changes bones or
creates physics regions. It rejects missing or duplicate morphs, missing bones and
invalid thresholds. Only the private Blueprint uses the two downward correctives.
An experimental quaternion pose driver was removed from the deliverable after its
associated surface trials failed visual review.

The retargeting helper now validates the imported mesh reference skeleton and updates
the private Skeleton reference pose from it. This fixes stale finger translations
after reimport. Explicit FBX import preserves all eight morphs; the earlier JSON
reimport dropped morphs and is not the current recipe.

Subsequent private pole derivatives fit palm contact and body clearance, so the earlier
claim that all body/arm tracks remain unchanged applies only to the finger-only stage.
BodyWave/BackSlide use one gripping hand and move the body clear of the pole; Spin's
minimum orbit radius is 32 cm. A suffix filter temporarily reset left-leg tracks in
two derivatives; that defect was identified and the original leg keys restored.
Sampled vertex clearances are positive, but these measurements are not visual acceptance
or a complete collision test. Original six clips remain unchanged.

Rejected local trials include broad surface averaging (worsened breast folds), narrower
shoulder weights (sharper joint creases), joint relocation and raised volume correctives
(residual distortions). None was imported. Clay and physics-off tests separate mesh/
skinning defects from spring behavior. Official Epic Pose Driver and Blender Corrective
Smooth guidance was consulted; diagnostic success is not a claim those methods fixed it.

Native Editor rebuild after removing the rejected optional driver: **PASS, 5 actions /
13.67 seconds**, runtime module SHA256
`db71721d12c3bcda371b060bb1857945707a51d2a25a6de54cd970d413a9252b`.
This is the canonical authoring checkout build, not a packaged game or isolated
worktree build. Existing toolchain/plugin dependency warnings remain.

Current source: `.agent/local/CyborgRepair_20261013/RiggedDelivery/Cyborg_CHEST_REVIEW.blend`.
`Cyborg_FINISH.blend` preserves the previous source; `Cyborg_MARKED_REPAIR.blend` is
rejected. Recipes and receipts live under the same private task directory, particularly
`build_chest_candidate.py`, `export_rigged_delivery.py --chest`,
`import_finish_commandlet.py`, `Finish/Chest`, `Finish/Isolation` and `Finish/Import.json`.
The owner-folder GIF and Blender file listed below are historical until replaced.

New twist-helper, alternative shoulder weights, clavicle-lift and smoothing trials
failed visual review and are marked REJECTED under Finish/{ArmTwist,ArmHeat,ArmSwing,
ArmSleeve,ClavicleLift,AnatomicWeights}. Automatic bone heat also failed to produce
weights; no failed result was saved as a candidate. None changed native assets.
The native audit is Finish/ArmScope/Capture.json and Decision.json. PIE ended and the
temporary studio map was discarded without saving; original production hashes match.

**Next, lead-owned:** preserve the accepted chest and do not adopt the rejected
trials. The shoulder repair remains unresolved; removing one animation cannot close
it. A later validated repair or an explicitly agreed reduction of the animation set
must precede station adoption and Silver work.

## Earlier checkpoint (historical evidence, superseded where noted above)

2026-10-14 UTC. **PARTIAL / review candidate only**, associated with RPT-20261014-01.
The current in-game Cyborg and original animations are not replaced.

## Change and diagnosis

The owner marked a folded gripping hand and a sharp shoulder crease. The replacement
surface was still bound to the original character's proportions: finger joints lay
outside the visible fingers, while shoulder vertices retained neck/torso influence.
The pole authoring recipe also curled every finger about local X, although the
original finger rolls differ substantially. Fitting the joints alone therefore did
not correct the sideways curling.

The private candidate fits arm/finger translations while preserving all 61 bone names,
parents, reference orientations and scales. Local shoulder/hand weight gradients were
revised; the 104,000-triangle body/head surface, UVs, materials and six breast morphs
remain unchanged. The mapped, owner-fitted collar adds 14,998 triangles: 118,998 total.

`USSCharacterAuthoringLibrary::ConfigureCyborgArmRetargeting` validates the exact private
mesh and original skeleton paths, hierarchy, rotations/scales and non-arm translations
before applying Skeleton translation retargeting to the 40 arm descendants. It never
modifies the source skeleton or saves packages. Dry-run is the default.

Six private pole-clip copies re-express finger rotation deltas around the fitted palm
bend axes. The source clips, body/arm/wrist tracks, duration and key count are preserved.
`Scripts/CyborgRefresh/CorrectPoleFingers.py` derives keys from the original on each run,
so interrupted-run recovery does not stack a second correction. Its private correction
data is generated from the fitted Blender rig, not a general replacement for arbitrary
animation data.

The candidate Blueprint has exactly two `SSSoftTissueComponent` regions, Breast_L and
Breast_R. Mass .55 kg, stiffness 135, damping ratio .3, strength .9, response (1.5,.8,1),
maximum displacement 1.6 cm. There are no rear/hip morphs or dynamic regions. The collar
retains its atlas and SilverTint, PanelTint and AccentTint material parameters.

## Verification and rejected steps

- Native Editor build succeeded: 15 actions / 87.33 seconds. Runtime module SHA256
  `6059ebcdc5c3ed297150b6e26ffd300001ffb8d0a3ac543ced5145f4a0b9c91b`.
  The build used the canonical authoring checkout; this PR isolates the new helper
  from unrelated local changes. Existing engine deprecation warnings remain; no
  new package or game build was made.
- Preflight correctly rejected an initial export that rotated connected clavicles by
  8.535 degrees. Disconnecting edit-bone connections before translating joint centers
  preserved axes and passed the same preflight. No orientation tolerance was widened.
- First import used the wrong native FBX enum spelling and created static meshes;
  it was rejected. Correct native `FBXIT_SkeletalMesh` import/reimport exited zero.
- The final private mesh evaluates 675 sampled poses across all 135 original clips,
  with finite transforms and the expected hierarchy. This is compatibility evidence,
  not a complete visual pass of every clip.
- Native PIE recorded all six corrected pole clips at normal speed: 173 frames and
  380 dynamics samples. Both regions remained finite and bounded; peak displacements
  were 1.5954 and 1.5953 cm. Before/after closeups show the finger fold corrected and
  the shoulder crease reduced. A residual shoulder crease remains visible.
- Original six clip hashes, original skeletal mesh and original skeleton remain
  unchanged. The CharacterStudio map was staged only in memory, not saved.
- Isolated PR worktree checks pass: 41 structural checks, Python compileall, source
  validation (26 meshes / 17 WAVs / unchanged GLB), clang-format and the repository
  documentation gate. The canonical authoring checkout's prior44-check result is a
  different source snapshot. No broad portable gameplay suite was needed for this
  editor authoring helper.
- Offscreen Editor11108 exited after discarding its temporary studio stage. Final
  studio map SHA256 remains `aa1b081a14ad1fd9295f6e29da8caeb85dde3183df510b87eeb5ac2431712ca5`.

API basis: Epic's [AnimationDataController documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AnimationDataController?application_version=5.7)
was checked against installed UE5.8 `IAnimationDataController.h` and existing project
authoring recipes on October14. Bone-track writes use the supported controller API.

## Local artifacts and repeatability

Private source/work: `.agent/local/CyborgRepair_20261013/RiggedDelivery` in the canonical
`C:/Users/j6sis/SpaceSurvival` checkout. Native candidate:
`/Game/SpaceSurvival/Licensed/CyborgRefresh_20261014/BP_Cyborg_Refresh`.
Licensed/generated character binaries and renders are local, not in this source PR.

Owner review folder: `M:/Local AI/Projects/Cyborg_Claude/refresh_20261013`:

- `Cyborg_RIGGED_REVIEW.blend`: latest editable candidate, packed materials.
- `Cyborg_ARM_REVIEW.gif`: native six-clip playback, not a Blender animation.
- `Cyborg_Arm_Before.png`, `Cyborg_Arm_After.png`: matched Blender closeups.
- `Cyborg_Arm_Unreal.png`: actual native closeup.

Retained recipes: `repair_arm_weights.py --fit`, `repair_marked_arm.py`,
`export_rigged_delivery.py --hands`, `import_with_commandlet.py --hands`,
`configure_native_candidate.py`, and `correct_native_pole_fingers.py` in the private
work folder. Each native write has a dry-run/preflight. Import requires no running
Editor; current source and original assets must be preserved before rerunning.
Receipts include `HandShoulderRepair.json`, `FingerAxes.json`, `CommandletImport2.json`,
`PoleFingerRepair.json`, `NativeReview/Capture.json` and `ArmDelivery.json`.

## Still open — lead owns the next work

The shorter fitted arms move hand endpoints. The existing pole contact must be refit
before replacing the in-game mesh/animation mapping; sampled grip-hand displacement
is about 4 cm in PoleIdle. The largest sampled hand displacement across pole poses is
12.74 cm, including free hands. The review capture does not claim pole contact.
Residual shoulder pinching, broader non-pole visual checks, collar contact during
extreme poses and owner acceptance remain open. No station adoption, packaging or
representative performance claim follows from this checkpoint.
