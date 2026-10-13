# Silver hair contact review — 2026-10-13

Related issue: RPT-20261013-01. **Unresolved hair defect; previous assets restored. Hair was not approved.**

The owner accepted the visible body dynamics and remaining appearance, and reported hair passing through the arms in the rear and raised-arm views. This pass was restricted to hair collision. Shoulders, skin weights, colors, clothing and body dynamics were not retuned.

## Findings and bounded trials

The apartment Blueprint uses `HairCoverage_v3/PA_Silver_HeadCollision` for the moving groom. Both lower-arm bodies contain no shapes. Its upper-arm capsules have4.5cm radii and do not fit the current reference skeleton. Measurements of the retained import source show proximal upper-arm skin extending approximately6.9–7.0cm from the bone axis; forearm radii are approximately3.6cm. The source coordinates were checked against the native reference bones within0.001cm before fitting.

Three normal-speed28.5-second dance trials each captured29 native frames with active Niagara and enabled live body springs:

1. A separate PhysicsAsset candidate fitted the upper arms and added forearm capsules. Rear shoulder penetration remained visible.
2. Eight substeps/twelve iterations, reduced bend stiffness and disabled post-solve bend projection allowed greater movement, but changed the approved rear-flowing style and left contact defects. Rejected.
3. Restored the original bend/projection settings, retained eight/twelve solver steps, increased collision radius to0.8cm and added0.8cm arm-envelope clearance. The raised-arm view improved, but rear shoulder/upper-arm penetration remained visible around25seconds. Not adopted.

The installed UE5.8 headers distinguish post-solve bend projection, collision projection and guide collision radius. [Epic's groom physics guide](https://dev.epicgames.com/documentation/unreal-engine/enabling-physics-simulation-on-grooms-in-unreal-engine), checked October13,2026, documents these controls. Setting values and an active Niagara component are insufficient evidence that interpolated visible strands stay outside the skin.

The remaining cause is **UNCONFIRMED**. Next useful investigation is guide versus rendered-strand motion/contact at the failing rear pose, including the separate nonsimulated scalp layer. Do not claim the missing forearm shapes explain every visible penetration. Stop repeating stiffness changes without that evidence.

## Recovery and preservation

After three assessment cycles, tuning stopped under the then-current repository rule. The owner subsequently replaced that rule with online research followed by a supported new test; [CLAUDE.md](../../CLAUDE.md) now reflects that direction. The owned offscreen editor29336 exited cleanly. The original groom was restored from its hash-checked backup while no editor was running. All70 pre-existing character assets matched their pre-task SHA256 hashes, including:

- Apartment Blueprint `a76aaa582377be18371846048024ca3b9f01989822c608e312209a22cd8ea903`.
- Moving groom `ac17faf275172ab3b5bb1021360452a481d1b41199a24288ac2ebab123510517`.
- Body mesh, thirteen clips, bindings, materials, scalp overlay and original collision assets.

The existing station map remains `a36bffcae35be2b37b0291b0dd9894291dde2ba38a28f34ee5b511ba61688e6a`. The approved body-spring settings, original419-frame GIF, Editor module `f731b83f`, source code and packaged release are unchanged. There is no new fixed-hair GIF or collision-complete claim.

The small `/Game/SpaceSurvival/Licensed/ViableEldReview_20261013/HairContact_v1/PA_Silver_BodyContact` asset is retained as an **unassigned diagnostic candidate**. It is not used by the saved apartment character.

## Evidence and checks

Private evidence root: `.agent/local/ViableEldFinish_20261013/HairContact`.

- `Before.json`, `ArmMeasurements.json`, `FitDryRun.json`, `Fit.json`, `Solver.json`, `Refine.json`: original settings and exact trial recipes.
- `Trial`, `Trial2`, `Trial3`: timestamped capture receipts, contact sheets and retained diagnostic frames. These are unsuccessful candidate views, not accepted output.
- `Rollback.json`, `Close.json`, `Editor.log`:70 matching protected asset hashes, no candidate adoption and clean process exit.

Python syntax and repository documentation checks apply. No new C++ build, portable domain suite or package is needed for this reverted asset experiment. Owner acceptance of the body's visible motion does not establish voice, performance, arbitrary-animation contact or packaged integration.

## Research follow-up requested by the owner

On October13,2026 the owner requested internet research after three unsuccessful repairs, followed by a test of a supported hypothesis. This replaces the earlier stopping rule. Hair settings were **previous settings**, not owner-approved collision behavior.

The supplied sources were checked against Epic's UE5.8 documentation and installed headers:

| Suggestion | What was verified or tested | Result |
| --- | --- | --- |
| Enable groom simulation, assign the character PhysicsAsset, fit capsules | Already configured/tried in the earlier pass. Asset simulation, solve collision and project collision are enabled. | Necessary setup, not a demonstrated repair. |
| Enable collision on the bodies/shapes | All19 body instances and all existing primitive shapes in both current and candidate assets already use QueryAndPhysics. | No disabled body/shape switch found. This does not read back the separate rigid-body pair-disable table. |
| Register a collision component explicitly | Called GroomComponent.AddCollisionComponent on Silver's skeletal component in the isolated rear25s pose. | Did not remove the visible shoulder intersection. The cited method concerns additional skeletal components; Silver's own mesh is already the parent. |
| Component simulation override | Installed log explicitly says SetEnableSimulation requires OverrideSettings. With overrides off, the saved component's false override field is not evidence that asset simulation is disabled. | Corrected the diagnostic interpretation; not a collision fix. A later override test inherited some defaults despite requested assignments, so it is not a matched-settings comparison. |
| Guides, scalp layer, local space and projection | Rendered the guides; isolated the long groom from the short scalp layer; tested local/world space and post-solve projection switches at25s. | Intersection is visible with the long groom alone. No tested variant cleared it. Guides were visualized, not numerically proven clear of skin. |
| Collision refresh | Compared fitted and deliberately oversized18cm arm radii, then repeated with the Niagara system reinitialized. | Reinitialized oversized capsules visibly deflect the hair. This confirms collision response is possible; the oversized shape is unsuitable as a final fix. Earlier live shape edits without reinitialization are inconclusive. |
| One guide per visible strand | Prepared a fresh import with Use Unique Guide, preserving the original source and character. | Not evaluated: saving the newly imported simulated groom hit the UE5.8 interpolation-data assertion below. No candidate was saved or adopted. |

[Epic's simulation settings](https://dev.epicgames.com/documentation/unreal-engine/enabling-physics-simulation-on-grooms-in-unreal-engine) describe solve/project constraints and component overrides. They do not establish that reducing damping or solver iterations universally repairs jitter. [Epic's physics overview](https://dev.epicgames.com/documentation/unreal-engine/hair-physics-in-unreal-engine---overview) explains that simulated guides drive visible strands; its [interpolation guide](https://dev.epicgames.com/documentation/unreal-engine/groom-interpolation-in-unreal-engine) documents single-guide interpolation. Those support the diagnostic direction, not a claim that it fixes this character.

The [2020–2021 Enable All forum thread](https://forums.unrealengine.com/t/4-26-groom-collisions/475967) ends with the original reporter saying the suggestion did not help. The [July2023 collision-component report](https://forums.unrealengine.com/t/can-groom-interact-with-collision-objects/784586) describes adding other skeletal meshes. The [2020–2022 packaged-only failure](https://forums.unrealengine.com/t/4-26-hair-no-collision-in-compiled-game/475605) does not match this defect, which is already visible in PIE; its startup workaround was not added. All sources accessed October13,2026.

### Import failure and preserved result

The first import attempt found the Alembic translator disabled in the temporary session. A subsequent offscreen launch enabled the already-installed AlembicHairImporter for that process only, without changing the project file. Import then reached SavePackages and failed at GroomResources.cpp:1922: `FHairStrandsInterpolationBulkData::DataFlags_HasData`. This is missing interpolation resource data, not proof of bad collision stiffness. A previous saved-asset reload recovery does not validate this unsaved candidate. A safe derived-data/binding rebuild remains required before this hypothesis can be evaluated; no engine fix was attempted.

Private evidence: `.agent/local/ViableEldFinish_20261013/HairResearch`. `Baseline.json`, completed `Isolation2/Isolation.json`, the two `CollisionProbe*/Probe.json` files, native images and `Importer/Editor.log` preserve the findings and failures. The first isolation script invalidated component references during an editor-property reconstruction; its incomplete later captures are excluded. The corrected isolation used runtime property assignment and completed all seven captures.

`Preservation.json` verifies **71 character assets plus3 protected project/map/layout files unchanged**, zero remaining Unreal editors and zero saved new native assets. The existing apartment Blueprint, body springs, colors, source models and original GIF remain intact. Research evidence occupies approximately13.2MB; no new model copies were retained. Hair collision is **still unresolved**. Next lead work is a safe interpolation-data/binding rebuild and an actual animated comparison, not another assumption that enabled checkboxes prove success.
