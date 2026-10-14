# Silver: live Unreal body springs

2026-10-13. RPT-20261013-01. Owner requested stronger lateral motion and Blueprint tuning, replacing the nearly static baked response. Shoulders, skin weights, hair, colors and other characters are outside this change.

## Implementation

`USSSoftTissueComponent` is an opt-in runtime C++ component, configured in the character Blueprint as **BodyDynamics**. It follows four skin-weighted anatomical anchors, including their world translation and rotation, and drives the existing paired body/garment XYZ morph targets. These explicit overrides replace twelve baked jiggle channels; the two arm-lift channels, skeletal animation and facial controls remain unchanged. No Chaos soft-body or new collision solver is claimed.

The spring exposes effective mass, stiffness, damping ratio, strength, per-axis response and displacement limits. Mass is a solver setting; changing visual material density does not control these morph springs. The derivative's source-weighted anchors match the imported reference skeleton to 0.000016 cm. XYZ sign conversion is `(1,-1,1)`, with one centimetre per authored morph unit.

| Region | Mass kg | Stiffness N/m | Damping ratio | Strength | XYZ response | Limit cm |
| --- | --- | --- | --- | --- | --- | --- |
| Chest, each side | 0.55 | 135 | 0.30 | 0.90 | 1.5, 0.8, 1.0 | 1.6 |
| Hip, each side | 0.90 | 300 | 0.36 | 0.85 | 1.4, 0.85, 1.0 | 1.2 |

Small integration steps, acceleration filtering, a smooth vector limit and hitch/teleport resets bound the response. Missing bones/morphs disable the component without replacing the original animation. No networking, vendor plugin or new host dependency was added.

## Verification

- Editor build succeeded through `Scripts/Build.ps1 -Target Editor` in57.19s; runtime module DLL SHA256 `f731b83f6d159371056a75524e79ce8f74305faa052d155cfc5595f78a3fab29`. Existing engine/header and unrelated deprecated-API warnings remain; no new component compile errors/warnings.
- Installed clang-format checks pass for both new C++ files. `CheckProject.py` passes44 structural checks; Python compilation and `ContentSource/ValidateSources.py` pass. Domain rules were untouched, so the portable domain suite was not rerun.
- Native PIE collected2,673 samples across dance, walk, turn, settling and a disable probe. Finite values, displacement limits and explicit morph override values pass. Dance peaks are15.47/15.51mm chest and10.36/9.72mm hips. Sideways chest excursion spans approximately-15.1 to+15.3mm; walking and turns also show nonzero lateral response. After3seconds stationary, offsets are below0.001mm.
- The disable probe's editor-property write reconstructed runtime state; restoring through the stale Python handle did not restore the live component. A first capture therefore had zero motion and was rejected. A fresh PIE capture explicitly requires enabled dynamics and nonzero recorded offsets. The final GIF is that second capture, not the rejected one. This is not evidence for live Details-panel edits without reconstruction.
- Final front/rear dance capture has419 frames with active groom simulation and recorded spring values. Capture used0.2 game-time dilation; GIF timings are reconstructed from animation time. Normal-speed motion was measured independently. Full-size extrema and a contact sheet were inspected; no new obvious garment separation appeared in those views. This is bounded visual evidence, not exhaustive mesh contact or performance validation.

## Delivery and tuning

Local root: `.agent/local/ViableEldFinish_20261013/`. `RuntimeDynamics` contains source-derived anchors, native settings, normal-speed samples, adoption/readback receipts and capture metadata. `Silver_Unreal_BodyDynamics.gif` is the review animation. Source master, current mesh, all13 clips and both hair assets remain unchanged.

Native candidate: `/Game/SpaceSurvival/Licensed/ViableEldReview_20261013/RuntimeDynamics_v1/BP_Silver_RuntimeDynamics`. **Adopted and reloaded:** `MotionFinish_v1/BP_Silver_Apartment`, SHA256 `a76aaa582377be18371846048024ca3b9f01989822c608e312209a22cd8ea903`. A visible owner editor initially held the target file and caused sharing violation32; the first addition was safely discarded with the previous saved Blueprint intact. After the owner saved and closed that editor, a fresh offscreen process applied the component, reloaded the saved package and verified all four settings on `HomeHub/Residents/Silver`. The9,408-actor station map remains byte-identical (`a36bffca`), as do the protected mesh, clips and hair assets. Both task editors exited cleanly; the readback reused the same private profile.

Final GIF:419 frames,28.49seconds,47,113,860bytes, SHA256 `12ed991d228107a3b5e24f72f9c91483f03ea22f866e4926c56e75cf016977ff`. Encoding was independently reopened and hashed.15 full-size key frames and all numerical samples remain;819 rejected/already-encoded raw frames were removed, reclaiming554,077,367bytes. No original source, native asset or profile folder was deleted.

For tuning after adoption, open the apartment Blueprint, select **BodyDynamics**, expand **Regions**, edit the Spring settings and save. Axis Response X controls sideways emphasis. Change both sides of a family together for symmetry. Binding/anchor edits require a new Play session; regenerate anchors if skin weights or mesh/morph units change. Existing source bake values remain a fallback when the component is absent; the new component leaves arm lift unchanged.

Owner motion acceptance, broader character/body contacts, live voice/lip-sync, representative performance and packaged inclusion remain open. No whole-station or release completion claim.
