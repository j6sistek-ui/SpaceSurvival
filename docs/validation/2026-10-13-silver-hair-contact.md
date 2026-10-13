# Silver hair contact review — 2026-10-13

Related issue: RPT-20261013-01. **Unresolved hair defect; approved assets restored.**

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

After three assessment cycles, tuning stopped under the repository's [CLAUDE.md](../../CLAUDE.md) rule: “screenshot assessment is capped at three cycles, then stop and report”. The owned offscreen editor29336 exited cleanly. The original groom was restored from its hash-checked backup while no editor was running. All70 pre-existing character assets match their pre-task SHA256 hashes, including:

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

