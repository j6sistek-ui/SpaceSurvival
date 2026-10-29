# Inspected resources and evidence

Verified October28,2026, America/New_York. This is a resource snapshot, not a
task queue or permission to adopt any model/motion. Refresh paths/version/status
before applying it. Licensed source data stays private; the skill contains no models.

## Actual local findings

| Resource | Inspected contents | What the result proves / does not prove |
| --- | --- | --- |
| Motion2MixamoRig fork f05a718188026b06e7ee64b47bab077970444b19 | Package/Blender extension0.1.8; isolated Python3.11.9/CPU backend installed on M | One real72-frame/3-second run and native Blender import work. No validated GPU backend, fingers, target-character/pole contact or production zero-G trajectory |
| SMPL-X neutral NPZ |10,475vertices,55 weighted joints,486 pose bases,400 shape/expression bases; up to10 active influences | Numeric model fields read; weights normalized to about1.2e-7. This is not visual deformation acceptance |
| Legacy SMPL-X Blender ZIP dated20220623 | Three gender bodies; each10,475vertices/20,908triangles,56bones including root,55 vertex groups;797 keys: Base+300Shape+10Exp+486Pose | Body data loads in isolated Blender5.2.2. No actions. The older add-on code itself was not installed/tested |
| SMPL-X DLC dated20260505 | Three bodies with the same vertex/triangle/bone counts;887 keys: Base+300Shape+100Exp+486Pose | The extra90 keys are expressions, not extra dance clips. Data loads; compatible current add-on/export workflow still needs its own test |
| f_avg_noFlatHand.fbx / m_avg_noFlatHand.fbx | Each6,890vertices/13,776triangles,53bones including root,52 weighted groups;470keys: Basis+10Shape+459Pose; no actions | Already-rigged SMPL-H deformation references. Old f_avg_/m_avg_ bone names differ from the inspected Unreal plugin's canonical names; native compatibility not established |
| MANO_LEFT / RIGHT in mano_v1_2.zip | Each778vertices/16 weighted joints/135 pose bases; weights sum to one within about2.3e-16 | Pose/skin data exists. Legacy Chumpy shape fields were inspected as inert state, not executed or converted into a working hand estimator |
| SMPLH_female.pkl in that ZIP |6,890vertices/52 weighted joints/459 pose bases; weights normalized within about3.4e-16 | Matches the body/hand model family; old Python2 demos contain hard-coded author paths and are not a modern installation recipe |
| handpose.zip |38 lists,18,947 finite78-value samples | One sample decoded to156 full-pose values with the bundled default PCA profile. Source semantic convention/timing/FPS and animated visual quality remain unconfirmed |
| smplx_parts_segm.pkl |20,908 face labels and parent labels | Triangle segmentation for the SMPL-X topology, not generic target vertex groups |
| segm_per_v_overlap_SMPLH.pkl | Named overlapping vertex regions, including shoulders, hands/fingers and thighs | Different6,890-vertex topology; useful donor masks, not interchangeable with SMPL-X or Vexa indices |
| smplx_flip_correspondences.npz |10,475x3 face-vertex indices and matching barycentric coefficients | A surface correspondence, not a simple10,475-entry integer permutation; geometric mirror residual not yet measured |
| locked-head neutral NPZ | Same10,475vertices/55 joints/486 pose bases/400 shape-expression basis schema | Alternate model data. No proven anatomical-limit, neck-pose or joint-lock fix; exact intended shape differences not evaluated |
| smpl-unreal fork87cea30d6221c7a7a4a66749d1981a50fae88539 | C++ runtime node and model utility inspected | Fixed joint names and Pose### counts; local rotations mapped into SMPL coordinates and R-I curves. Not installed, built or tested in the game |
| UE5.8 installed FBIK source | Preferred angles, per-axis limits and bAllowStretch are present in PBIK headers | Native solver capabilities are available in engine source. No target rig/plugin runtime setup was validated in this study |

Numeric pickle inspection used a restricted reader, mapped legacy Chumpy classes
to inert metadata, and skipped NPZ object metadata. No bundled legacy demo ran.
Two temporary extracted body .blend files were read in isolated hidden CPU-only
Blender and removed afterward. Original archives, FBXs, native project/editor and
user preferences were preserved. No render, game import or model installation
was performed for the deeper resource study.

## Machine locations, verified at this snapshot

- Motion tool: `M:/Local AI/Tools/Motion2MixamoRig`.
- Existing backend: `.venv/Scripts/python.exe`; Blender uses `pythonw.exe`.
- Outputs: `D:/Motion2MixamoRig/outputs`; model archive: `D:/Motion2MixamoRig/InputModels`.
- Extra source ZIPs/FBXs: `C:/Users/j6sis/Downloads` at this check. They can be
  archived separately; do not assume a later chat's path is still correct.
- Basic test: `D:/Motion2MixamoRig/outputs/Validation_20261028_01/Review.html`.
  One72-frame CPU run took214.94seconds including preflight. Sole grounding
  still shifted root by median2.81cm/max18.28cm despite `--no-foot-lock`.
- Detailed study: `D:/Motion2MixamoRig/ResourceStudy_20261028`:
  NumericDataProbe.json, BlenderAssetProbe.json, HandPoseSchemaProbe.json,
  DecodedHandPoseSample.npz, SmplUnrealTree.json and the native probe log.
  Probe scripts are in `D:/Motion2MixamoRig/SetupLogs`.
- Project evidence: `docs/validation/2026-10-28-motion2mixamo-evaluation.md`;
  canonical remaining work is RPT-20261021-01. This skill is not proof that
  current Vexa/Joy/Astra or other dancers received these corrections.

## Primary sources and version notes

All reviewed October28,2026. Model/code license boundaries remain separate;
evaluation proceeded at owner instruction, with commercial clearance unestablished.

- [Owner motion fork](https://github.com/j6sistek-ui/motion2mixamorig), pinned above;
  installed `motion2mixamorig/mixamo/animation.py` confirms grounding is independent
  of the foot-lock switch.
- [SMPL Unreal usage](https://github.com/j6sistek-ui/smpl-unreal/blob/87cea30d6221c7a7a4a66749d1981a50fae88539/docs/usage.md)
  documents body/animation import, threshold0.0,468/486 targets and runtime setup.
- [Node source](https://github.com/j6sistek-ui/smpl-unreal/blob/87cea30d6221c7a7a4a66749d1981a50fae88539/Plugins/SMPL/Source/SMPL/Private/AnimNode_SMPLPoseCorrectives.cpp)
  and [model utility](https://github.com/j6sistek-ui/smpl-unreal/blob/87cea30d6221c7a7a4a66749d1981a50fae88539/Plugins/SMPL/Source/SMPL/Private/SMPLPoseCorrectives.cpp)
  establish fixed bone lookup, supported morph counts and coordinate conversion.
- [Official SMPL-X code/documentation](https://github.com/vchoutas/smplx) covers
  body-model families, model conversion and their separate parameters.
- [Official MANO overview](https://mano.is.tue.mpg.de/) describes learned hand
  deformation and combined SMPL-H body/hand modeling; model code1.2 is dated2019.
- [SMPL-X Blender repository](https://gitlab.tuebingen.mpg.de/jtesch/smplx_blender_addon)
  is code-only; inspected downloaded README dated20220623 tested Blender3.1.
  Current exporter compatibility must be checked separately. Local DLC label is20260505.
- [Epic FBIK documentation, UE5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-full-body-ik-in-unreal-engine)
  describes effectors, preferred angles, target-specific axis limits and stretch.
  Installed cross-check: `Engine/Plugins/Experimental/FullBodyIK/Source/PBIK/Public/Core/PBIKBody.h`
  and PBIKSolver.h. Example mannequin angles are not universal anatomical limits.
- [Epic IK Retargeter documentation, UE5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine)
  distinguishes source/target chains and optional IK contact adjustment.
- [Epic Pose Driver documentation, UE5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/pose-driver-in-unreal-engine)
  describes bone-driven pose/curve targets; its documented experimental status
  is a reason to validate a shipping choice, not an instruction to install it.

## First useful experiments, selected by objective

1. **Current pole contact:** a short target-rig palm/contact window with root and
   elbow freedom, measured residual and no penetration. Keep the full routine.
2. **Body deformation:** one compatible donor and actual target in matched
   shoulder/hip bends; correctives off/on and export/native parity before transfer.
3. **Old SMPL-H plus plugin:** complete name map and bind-axis comparison, or a
   clean modern export; then one native node on/off test when authorized.
4. **Hand bank:** display a decoded donor sample, establish its pose convention
   and intended timing; only then select reference/retarget excerpts.
5. **New video motion:** a clear short source with free-flight/root preservation
   checked before extending to acrobatics or contact. Additional estimator models
   remain optional, not prerequisites for the preceding experiments.
