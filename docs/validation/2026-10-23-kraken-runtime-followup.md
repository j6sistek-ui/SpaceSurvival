# Kraken runtime and NVIDIA owner follow-up — 2026-10-23

Status: **PARTIAL investigation; owner motion and appearance reports remain open.**
Issues: RPT-20261015-03 and RPT-20261022-01 in [the canonical log](../KNOWN_ISSUES.md).

## Owner evidence and current constraint

James reported Kraken travelling as a rigid body, questioned her texture appearance, and reported that DLAA worked while a DLSS option warned about PIE. His exact tested map/build/date and the precise NVIDIA option are UNCONFIRMED. On October23 he requested light VRAM use. The hidden review finished and exited; no new GPU tests are authorized by this receipt. Continue with saved evidence until GPU clearance.

## Bounded current-build check

The unchanged canonical project used Unreal5.8.4, Editor DLL SHA256 `70234269350d35c2533a0ea14ee1c5d3a6f9452bcce5eaef7e8b658f934d9c57`, Survival map and its streamed Wayfarer station. Station SHA256 `56c18f661f6975ef35998e6a424c82c97791f172f5a3f3f9d3866cadbde838a7`; crawl clip SHA256 `2e67d68971a9c13136684db045563dd21fd412bcf09526ba3e26bfd31877c812`.

A private offscreen profile cloned production saves without writing them. After the native game-review transition, the observer waited 12 game seconds for actor replacement/streaming to settle. It did not alter Kraken's route, animation, playback rate, mesh or materials.

- The single `Crew/Kraken visitor` used `SK_Kraken_Gown_Mandala_V12` and the expected KrakenRefresh skeleton. Actual playback, idle and walk all referenced `A_Kraken_IndependentCrawl_24s`.
- 97 samples over 48.00 game seconds all reported playing; playback wrapped twice. Component-space tips changed independently of actor translation: 20 lower chains spanned 3.33–13.96 cm, four arm chains 6.09–8.54 cm, two antennae 0.83–0.85 cm. Summed route travel was 3319.82 cm.
- Animation tick was enabled, pause/no-skeleton-update were false, rate1, and AlwaysTickPoseAndRefreshBones was selected. The tracked actor remained valid after settling.
- Six front/rear captures were readable and inspected. The face appears gray against browner limbs; hair and sheer fabric have grainy edges. All nine effective material slots resolve, including Purple Mandala and blue gown materials. Assigned materials do not prove full mip residency or correct shading.
- At 36.02 seconds the private session requested Epic scalability and 100% screen percentage. Rear captures afterward remain noisy. This is not a matched before/after diagnosis: character location/lighting changed, effective resolution was not captured, and the log explicitly warns that the editor screen-percentage override ignores DLSS quality scaling. Temporal/high-resolution screenshot behavior remains a possible contributor, not an established cause.
- Exit 0; no observer errors; all 11 protected files and production saves unchanged. No map/mesh/material/config or game binary was saved or rebuilt.

This check did not reproduce a fully frozen pose. It does not invalidate the owner report or establish natural-play quality. It was unattended, which bypasses normal crew trimming, and did not reproduce the owner's exact presentation/session. Mesh deformation/contact and garment physics remain unaccepted.

## Earlier unsuccessful evidence

The initial attempt produced a readable first image but zero-filled later captures and numeric receipts; those artifacts cannot substantiate motion. Cause is UNCONFIRMED. Trial2 sampled a transient streamed actor that was replaced; the invalid final sample and resulting null-instance error are excluded from all metrics. Trial3 added the streaming wait and validity checks. Failed attempts remain private; no success is inferred from them.

## NVIDIA and packaging distinction

Installed NVIDIA plugin source `StreamlineDLSSG/Source/StreamlineDLSSGBlueprint/Private/StreamlineLibraryDLSSG.cpp` emits “PIE mode is not supported for Streamline DLSS-FG” when frame generation is requested in unsupported PIE presentation. This matches the reported wording, but the owner's exact option remains unconfirmed. DLSS Super Resolution and DLAA support PIE; `DLSSSettings.h` enables that by default. `DLSSUpscaler.cpp` warns when `r.Editor.Viewport.OverridePIEScreenPercentage` overrides scaling. The current review log contains that warning.

Game capability queries do not alone establish frame generation availability in the current viewport. AI follow-up is presentation-aware availability/message verification and ordinary Standalone/packaged testing. A successful API mode-state test is not a generated-frame, latency or image-quality pass.

Packaging removes editor-specific overhead and can improve performance, but gains require matched resolution/settings and representative measurements. It does not establish a cure for texture pressure, shader/PSO stalls or scene cost. [AMD's Unreal performance guide](https://gpuopen.com/learn/unreal-engine-performance-guide/) advises profiling outside the editor; [NVIDIA's June21,2023 integration article](https://developer.nvidia.com/blog/now-available-nvidia-dlss-3-for-unreal-engine-5/) describes compatible presentation modes. Installed8.9.0 source, rather than the older article, grounds this project's plugin behavior.

## Evidence and next work

Private evidence: `.agent/local/KrakenRegression_20261023/Trial3/{Launch,Review,MotionSummary,Exit}.json`, `Kraken_00.png` through `Kraken_05.png`; log in `.agent/local/StationReview/2d2f54d2bb8d489f8698ed173ec6d31a/Editor.log`. Native assets and captures remain local. Repository change is documentation only, with no new package or release.

AI retains normal-session freeze reproduction and controlled skin/material/texture-residency/temporal-rendering diagnosis after GPU clearance. Preserve blue styling, Purple Mandala and original route. James's failed motion result and appearance concern remain open in existing ClickUp tasks; no new immediate owner retest is requested. Cloth/contact, normal frame generation, restart and comparative performance remain open.

