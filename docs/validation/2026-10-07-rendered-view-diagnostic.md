# Rendered view diagnostic — isolated Operations capture

2026-10-07T06:37Z [TOOL] **PARTIAL; aggregate capture FAIL, native exit0.** This opt-in editor-only observation measures actual rendered view rectangles and AA flags. It does not change production quality defaults, owner settings/saves, assets, ship physics or the held cabin source. The saved preview is not accepted T9, packaged or published by this result.

## Compiled scope and retained build failures

This section describes the first observer run's frozen Build38. Build39's separately gated viewport diagnostic is recorded below; it does not rewrite the first run's failure.

The first private `SSRenderedViewDiagnostic.cpp/.h`, primary module startup/shutdown hooks and editor-only Renderer/RenderCore/RHI dependencies register observation commands only when both `-SSRenderedViewDiagnostic1` and `-renderoffscreen` are present. Ordinary launches retain their previous behavior. The extension observes the actual PIE player camera on the game thread, passes immutable family data to the render thread, and queues numeric samples back to a bounded game-thread log. This first version never changes a view, quality CVar or render pass. Limits are512 total samples,60 steady samples and90seconds; world/module cleanup stops recording, flushes outstanding render commands and drains the queue.

- Build36 failed on the missing `Misc/LexFromString.h` include. The installed declaration is supplied through `Containers/UnrealString.h`; failed source and log remain preserved. Log SHA `349bb5234c2ddf46556c69bfe91396d4e857386253e3c6afce55fcd383a66004`.
- Build37 failed C4458 because the local `World` name hid `FWorldSceneViewExtension::World`. The sole repair renamed that local to `ActualWorld`; no warning suppression. Log SHA `a405d200f967ec2af863db06b05b4eba6db55bd000fa8296f4db8b14b0016ca9`.
- Build38 succeeded, root-collected native exit0; UBT4.23seconds. The retained Visual Studio toolchain advisory is not a project compile failure. Log SHA `d05bca8884a50dd47de726baa40635a1314b9e21f9d64ac8b43cff4bb159e370`, linked DLL SHA `c8895bb93614d95714a7e4145e49d1e3fa5b113d4fe7e14053add40ff7552cb5`.
- Final CPP SHA `850eb53869c2f8209f855415a18e5efa1470542a6bed2031e6531ce45b4eb226`; private header SHA `5db4901eb9cbbc04dcc6cff2a1bb3eb7c18c80cef3dd30c1d56d2ae48bf1d6d0`. Full four-file clang-format check and CheckProject40 checks passed before compilation; peer source review found no confirmed lifetime/threading defect. Header preflight alone was not treated as build proof.

Actual raw rectangles come from the installed public `UE::FXRenderingUtils::GetRawViewRectUnsafe`, only in the render callback after checking that the view is the renderer's actual game `FViewInfo`. This avoids inferring effective resolution from `r.ScreenPercentage` or unsafe casts to a private renderer type.

## Executed attempt and actual pixels

The frozen wrapper is `.agent/local/StationRefinement/capture_rendered_view_diagnostic1.py`, SHA `29cec8943e932f9fd8e8a78aa1049f6fc44e4630398c7a0d22a577307a0073c5`. The receipt `.agent/local/StationRefinement/RenderedViewDiagnosticCapture1/manifest.json` SHA is `6cd9b0bd72a0e0c1e8db6cb597d53cd36f4be54bbb09212efe3a24b87c78ac04`. Root's `NativeExitReceipts-20261007T0632.json` records the collected process exit0; a receipt cannot establish its own native exit.

Both images are **unsaved camera tests of the current saved preview**, map SHA `211c812516fd81a71be64c6ddd3a372b3a2a94187f56790c03bc60719a077f34`. The temporary camera at(8180,−700,185), FOV80 remains the actual PC view target through ordinary/high-resolution warmup and shots. Natural Phoenix animation is not paused, so hero orientation is not a fixed comparison. No image is owner-approved or a published build.

| Capture | Actual viewport / image | Actual scene raw rectangle | Scene output rectangle | Raw/output scale |
|---|---|---|---|---|
| Ordinary Shot |1014×344|[0,0,612,344]|[201,0,813,344]|1×1|
| HighResShot |current viewport1014×344; image/render target1600×900|[0,0,1600,900]|[0,0,1600,900]|1×1|

The ordinary camera is rendered into a612×344 letterboxed area, not a1014×344 full-width scene. The high-resolution image uses1600×900 actual scene pixels. A full-size ordinary PIE capture remains required before comparing their visual quality as equivalent render paths.

All65 recorded samples have actual AA method4(TSR), AA show flag1, temporal-AA show flag1, screen-percentage flag1, primary method1, secondary fraction1, a non-null view state, camera-cut0 and nonzero temporal jitter. All65 retain the expected/current view-owner identity170673, the same camera origin/rotation/FOV, and measured raw/output fraction1. The explicit end reports65 logged/0 invalid;20 steady samples exist for each of stages0,1,3, plus requested-shot samples. These observations **do not support an AA-disabled diagnosis**. They do not establish temporal-history validity/convergence or isolate Lumen/reflection/material noise.

`01_Ordinary.png` SHA `6af7f4a4eed184b3170df56472aa9035d3a2f174bd1deec9a73a700c3020ec04`; `02_HighRes.png` SHA `dc882472b4c169337459468eed43d8c3966b0b97b9d26171542a26e969a26aaf`. Both remain in the ignored receipt folder.

## Exact scene check — retained failure

The receipt reports renderer-complete true, files/saves/quality/ships unchanged true, PIE stopped true and errors empty. It also reports **editor_scene_unchanged false**, so success remains false. No tolerance, exclusion or retrospective pass was applied.

Selective parsing of all997 exact editor deltas found:

- 973 quaternion component-rotation records. Exactly 130 are sign-negated quaternions representing the same rotation. The other 843 have actual numeric differences; maximum difference after aligning quaternion signs is `7.746804726316281e-7`. The maximum unaligned difference is 2.0. These numeric changes remain reported, not waived.
- 8 light-color string records have exactly identical `{b,g,r,a}` payloads and differing temporary native addresses in the `Color` representation. This is an address-dependent serialization defect in the raw guard, not measured changed channel values. The original failure stays intact.
- 8 removed and 8 added hidden, non-colliding `BillboardComponent` keys on two SmartTray and four FlyingDroid actors. The eight corresponding components have equal hidden/visible/collision flags and scale. Two matched SmartTray locations differ by `1.4210854715202004e-14` cm; four FlyingDroid matched quaternion differences reach the same `7.746804726316281e-7`. Reconstructed names and numeric drift remain explicit evidence.

All997 records belong to the existing Mech Blueprint families: Ant774, FlyingDroid96, FlyingInsect67, RoboticArm40, SmartTray16 and Box4. No separate actor-location, material, mesh or numeric-light-property delta category is recorded. This bounded classification is not a general gameplay/state-preservation claim; added/removed billboard payloads include their own transforms.

## Remaining verification

2026-10-07T07:04Z [TOOL] Build39 adds a separate `-SSRenderedViewViewport2` opt-in alongside `-RenderOffscreen`. Root collected successful compilation in 4.24 seconds, native exit0, log SHA `3205a90129f2692acb9c54f928b203a1373bb4984315bab556aa6a9a6439806a`, DLL SHA `582d1fb955480af2d399d19bd393de0340d87657f02f7dafa1f0c658e7472390`. The sole CPP revision is `a711ed749b8e8b25bd8c02d7a65949190b0be47fe1086344956476172c388778`; header/module/Build.cs retain Build38 identities. Frozen38 source, log, wrapper and receipt remain preserved.

The new commands resize only the exact session-owned typed PIE viewport to1600×900, record its original dimensions/fixed state, and restore those exact values before ending the session. They reject another world, client or viewport. Native restoration is also attempted on explicit stop/world cleanup/module shutdown. No global quality CVar, configuration, runtime default or native window changes occur. Installed zero-size unfix behavior remains a native gate rather than an assumed guarantee.

Prepared ordinary2 wrapper `13fc6bb4e35d6f93fda332e6b4811cdc9fe5eb27416ac8378ed312cf7e158361` has independent bounded review and Python AST/compile passes. It accepts only exact saved Main1 or successful Remainder4 evidence, warms the same possessed camera for at least90 frames/six seconds per stage, takes one ordinary screenshot, and requires actual viewport/raw/output1600×900 plus native original-size/fixed-state restoration. Typed RGBA replaces address strings; all quaternion/component membership/numeric differences remain exact and fail preservation. This new native capture is **UNRUN** at this entry; compilation and source review do not prove resize, restoration or visual quality.

2026-10-07T07:13Z [TOOL] Supersedes the preceding ordinary2 unrun state: root collected native exit **1**, receipt `d2b66d7c2e8587df65b62699952de659d96e6b7e99d39f7b07d1b69630f927fa`, **PARTIAL**. The actual ordinary image `b7b1086beca9c8ba8f78717de923b38dcce5a1563527a1cd1d998e987ecf4278` is 1600×900. All 41 native rows measure viewport/target/raw/output 1600×900, fraction1, AA4, temporal flag1, view state present, camera-cut0 and nonzero jitter. The image was taken after 466 frames/six seconds in its ordinary warm stage. It supplies actual native-size scene evidence; an AA-disabled diagnosis remains unsupported.

Native restoration ultimately verifies original1014×344, fixed-state0 and actual1014×344/fixed-state0. `viewport_restored` is true. The Python wrapper attempted to verify the restore log synchronously before its row reached disk, then stopped on that failure. Stage3 has zero steady samples; `renderer_complete` is false. This is a deferred log-read race, not evidence of a native viewport restoration defect. No observer CPP repair or additional build is indicated by this receipt.

Files, saves, quality, ships and stopped PIE checks pass. The strict editor comparison still fails with 989 deltas, retained independently from the log race. No tolerance or excluded field was applied. The actual image independently rates approximately6.5–7/10: floor and graphite podium are coherent, while bright noisy chrome desks and thin service silhouettes remain material presentation gaps. This is a lead/specialist visual assessment, not owner approval or T9 closure. No production resolution, AA, lighting or material tuning is authorized by the diagnostic alone.

Representative owner-size streaming pressure, runtime FPS, temporal-history validity, actual owner input/comfort, T9 quality, final cabin route, packaging and publication remain unverified. Existing failed captures and native shutdown crashes are retained separately; this clean exit does not turn them into passes.
