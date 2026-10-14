# Cyborg arm and finger repair checkpoint

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
