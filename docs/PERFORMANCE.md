# Performance findings

Current source/build status is in [Project State](PROJECT_STATE.md); open acceptance is in [KNOWN_ISSUES](KNOWN_ISSUES.md). The visual enhancement pass is being validated. Dated records below are historical evidence for their exact builds; they do not identify the current executable after a rebuild. Screenshots and offscreen resource tests do not establish representative performance.

## Earlier build records

**2026-09-14 asset refresh ready for owner review:** [Refresh record](ASSET_REFRESH.md) supersedes earlier statements that no leg derivative was adopted. Licensed corridor/asteroid presentation, repaired walk/exit clips, depot and combat-feedback corrections are integrated. Latest Editor build and all 39 Unreal tests pass with zero test warnings. The offscreen Station 5 sequence reached docking, exit and Station 1 with 12 captures; this is visual/transition evidence, not FPS or natural gameplay acceptance. Optional Ludo ship packaged and exercised through the offscreen Station5 sequence. The final flight-fill/docking-light correction was compiled and verified in that package. Phase 1 remains PARTIAL.

**Historical measured package: 13; subsequent package at that checkpoint: 14. The representative Phase 1 performance gate remains OPEN.** Its normal-timing Wave 10 capture passed on the available i7-14700F/RTX 5080 at 2560x1440, DX12/SM6, quality 2, VSync off and cap 120. This is a seeded Tier V fixture with enlarged durability and scripted controls; it is not natural balance, physical response, clean-PC or lower-end acceptance.

Package 14 fixes station look and has no new performance measurement. The figures below belong to the preceding build.

## Package 13 Wave 10

Source `a628c7faa3d6c160ded22981bd3c230cb0cbf203` and game SHA256 `a07be4cf56e7c0c099d63953c566fe480a4a3bb144680f772b4a56f80eb73c21` are bound by the [package audit](validation/2026-09-13-windows-gameplay-fairness-package.json). Capture `755fd7116a074090bbfafb9c128128b4` / PID106548 exited 0 at 15:26:31 UTC, preserving source, all archive bytes and production saves. [Independent performance audit](validation/2026-09-13-gameplay-fairness-performance.json) retains exact sampling, timing and composition evidence.

All 15,619 CSV frames, including the initial unmarked seed frame, are retained below; startup/focus wait before CSV is not measured. No in-game screenshot readback, build, asset rendering or index workload overlapped. The owner editor and other desktop apps remained open. No sample was removed for being slow.

| Counter | Mean ms | p99 ms | Maximum ms |
| --- | ---: | ---: | ---: |
| FrameTime | 8.338382 | 8.5174 | 8.9063 |
| GPUTime | 2.720338 | 3.5521 | 4.6695 |
| GameThreadTime | 1.834523 | 2.7658 | 8.6768 |
| RenderThreadTime | 3.372188 | 4.4498 | 11.4776 |
| RHIThreadTime | 2.344024 | 3.2914 | 12.0072 |

Mean frame rate was 119.927 FPS; zero captured frames exceeded 16.667, 33.333 or 50 ms. All 15,618 marked fixture frames stayed foreground. The climax lasted 40.006196 seconds, including 38.280000 seconds of simultaneous gravity/asteroid/enemy presence, followed by 5.006182 seconds of approach. Peak threats were 23 against the cap of 24. This capped result does not measure uncapped headroom. CPU/GPU pipeline times must not be added together. Natural full-run RAM/VRAM, Station 2 docking, startup loading and representative hardware remain open.

## Package 12 preceding station and climax measurements

The [Package 12 audit](validation/2026-09-13-gameplay-quality-performance.json) retains source `3536bf9` and game `77501fdb` identity. The Station 5 sample has 16,869 marked frames: 119.943 FPS, p99/max 8.4871/8.7949 ms. Wave 10 has 15,616 marked frames: 119.921 FPS, p99/max 8.54/9.6356 ms. Both had zero marked frames above 16.667 ms and all marked frames foreground. Station 5 covered full wormhole/climax/approach/docking/exit/idle; it remains the latest measured Station 1 transition. These are historical Package 12 results, not Package 13 Station 1 measurements. The current 8K sky had already been included; it adds 40 MiB resident texture cost over the previous 2K panorama. HeroAlpha optimization remains paused/unadopted.

## Historical Package 11 station and endgame measurements

Source `6912684223f4a93f4010cd12201aee7fb42395f3` and inner executable `10b9b664c9a9d7480d96412999dd9da0b33215bc423eaae77a395fde8c9ed32c` are bound by the [package audit](validation/2026-09-13-windows-integrated-presentation-package.json). The raw fixture records are under `Artifacts/EndgameSoak/ff25f69277224a3a85a07e37bb577ecf` (Station 5) and `9461b70d07454d738f22a1c87c91b793` (Wave 10).

| Captured workload | Marked frames | Mean ms | p99 ms | Maximum ms | Frames above 16.667 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Station 5 and arrival | 16,867 | 8.338488 | 8.5476 | 8.8939 | 0 |
| Wave 10 compound and approach | 15,618 | 8.337841 | 8.5134 | 9.9738 | 0 |

Station 5 used an 8.007362-second wormhole, 40.002631-second climax, 6.512440-second approach, 3.001230-second docking, 2.393800-second sampled exit stage and 15.007807-second hub idle. Wave 10 used a 40.003666-second climax, 38.278336 seconds of concurrent gravity/asteroid/enemy actor presence and 5.003929-second approach. Both peaked at 23 active threats against the cap of 24; all marked frames were foreground and the station contained no active threats.

These are scripted fixtures with Tier V stats and enlarged durability, normal simulation timers and audio enabled. No automated screenshot readback was used. CPU-only Blender rendering overlapped part of Wave 10 until 12:26:53 UTC; no Blender process remained during Station 5. The owner editor and desktop applications stayed open. The lead saw startup and Station 5 combat, not the full transition or live Wave 10 climax. Source, archive and production saves remained unchanged. The [independent combined receipt](validation/2026-09-13-integrated-presentation-performance.json) binds these results. This is not a clean-machine, natural-balance or minimum-spec acceptance result.

## Current visual runs are not performance measurements

Source 691 integration has 24 clean Unreal tests and new editor-game visual captures. `CaptureEndgame.ps1 -CaptureVisuals` records the normal viewport/HUD, pose request metadata and ListTextures, but screenshot readbacks perturb frame time. The [Station 5 visual receipt](validation/2026-09-13-integrated-station-visuals.json) binds 12 images on the pre-camera DLL 12b8; only the first exit image samples inside the 0.18-second live-pose blend. Its CSV and generated performance.json must not support FPS, hitch or smooth-transition claims. The [newer Wave 10 visual audit](validation/2026-09-13-integrated-endgame-visuals.json) verified a normal process close and four images on fd6c66. Its Compound residency snapshot reports hero 1K versus 2K maximum, rocks 2K and sky 2048x1024. The subsequent component-only hero residency correction compiled in 8.54 seconds and was subsequently confirmed at full 2K in the separate Package 11 readback. Neither visual capture establishes performance.

The +2-degree camera/manual-aim correction passed source/actor tests on DLL fd6c66; later warning wording and hero-residency source are separate from that run. Those synthetic tests do not measure physical input latency, gameplay rendering or uncapped headroom. The Package 11 scenarios above are historical source-bound benchmarks. Earlier Package 10 measurements below remain historical.

## Historical Package 10 rendered Station 5 and Wave 10 (2026-09-13)

Both independent receipts bind source `0fc4f7a7eb032f010cce1899e0ca279bd9e6ee80` and game SHA-256 `4dde20dc8776827419ee7e3fa58ebdca9cdd6aac203db0754ab57f8d51fd7498`. Package 10 built in 45.06 seconds, with all 88 project packages/Engine Cube and seven archive artifacts verified. See the [package receipt](validation/2026-09-13-windows-audio-economy-package.json), [Station 5 receipt](validation/2026-09-13-station-transition-performance.json) and [Wave 10 receipt](validation/2026-09-13-audio-rock-endgame-performance.json).

The Windows Development captures ran at 2560x1440, D3D12/SM6, all 11 quality groups 2, VSync off and cap 120 on the i7-14700F/RTX 5080 PC (driver 616.92), with the owner's editor and desktop apps open. Audio was enabled and the renderer device initialized; nobody performed a listening assessment. Both fixtures seed a starter/Rapid Laser with five Tier V paths, Cooling and base hull/shield 50000, then use scripted existing control APIs. Normal world delta, budgets, caps, damage and transitions remain active; fixed timestep/frame rate/time dilation are rejected. These are not natural survival or controlled hardware-comparison benchmarks.

All captured frames are retained below, including one unmarked seed frame per run. Capture begins after the required two focused seconds; startup/focus wait and CSV drain are outside these samples. There is no additional warmup trimming or removal of slow frames. Every marked fixture frame was foreground. Nearest-rank percentiles and middle-pair median are used; CPU/GPU pipeline counters must not be added together.

| Scenario | Total / marked frames | Total frame-seconds | Mean ms | p99 ms | Maximum ms | Frames >16.667 /33.333 /50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Station 5 | 16,872 / 16,871 | 140.648611 | 8.336215 | 8.4610 | 8.8284 | 0 / 0 / 0 |
| Wave 10 | 15,768 / 15,767 | 131.473918 | 8.338021 | 8.5187 | 8.8226 | 0 / 0 / 0 |

Marked-frame sums are 140.640279 seconds for Station 5 and 131.465585 seconds for Wave 10; these differ from native callback wall durations and the all-frame sums above. Peak active threats were 23 in each run. Counts include telegraphs/offscreen actors. Both owned processes exited 0, wrote no save slots, and preserved production save hashes, all 131 source snapshot entries and all seven artifacts. Those stability checks belong to the capture interval; later source edits do not inherit them.

| Scenario / counter | Mean ms | Median ms | p95 ms | p99 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Station 5 / FrameTime | 8.3362 | 8.3334 | 8.3378 | 8.4610 | 8.8284 |
| Station 5 / GPUTime | 2.9834 | 2.7851 | 4.4415 | 4.8751 | 5.8013 |
| Station 5 / GameThreadTime | 1.7295 | 1.6823 | 2.1706 | 2.5601 | 6.3624 |
| Station 5 / RenderThreadTime | 3.2379 | 3.1698 | 3.8092 | 4.2185 | 7.4780 |
| Station 5 / RHIThreadTime | 2.2145 | 2.1736 | 2.7710 | 3.1313 | 4.4955 |
| Wave 10 / FrameTime | 8.3380 | 8.3335 | 8.3437 | 8.5187 | 8.8226 |
| Wave 10 / GPUTime | 2.7723 | 2.6532 | 3.4341 | 3.6472 | 4.1336 |
| Wave 10 / GameThreadTime | 1.8040 | 1.7525 | 2.2649 | 2.7179 | 7.1126 |
| Wave 10 / RenderThreadTime | 3.2763 | 3.2045 | 3.8791 | 4.3154 | 8.0821 |
| Wave 10 / RHIThreadTime | 2.2415 | 2.1894 | 2.8572 | 3.2308 | 4.5622 |

Station 5 followed full Wave 5 into the ordinary wormhole/climax/approach/docking path, then the authored exit and 15 seconds of stationary hub. The fixture steered toward the actual port; it did not teleport or force docking. Post-update scenario stages provide these distributions:

| Stage | Frames | Simulation seconds | Frame mean ms | Frame p99 ms | Frame max ms | GPU mean ms | GPU p99 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Flight | 7,189 | 59.924632 | 8.3356 | 8.4347 | 8.7068 | 2.7446 | 3.6140 |
| Breathing | 695 | 5.793288 | 8.3357 | 8.4222 | 8.5770 | 2.6545 | 3.5115 |
| Wormhole | 960 | 8.006323 | 8.3399 | 8.5213 | 8.7139 | 2.9400 | 3.8065 |
| Climax | 4,799 | 40.005359 | 8.3362 | 8.4540 | 8.8284 | 2.7136 | 3.5706 |
| Approach | 781 | 6.511785 | 8.3378 | 8.5127 | 8.7297 | 3.1202 | 5.0070 |
| Docking | 360 | 3.000141 | 8.3337 | 8.3575 | 8.3641 | 4.4076 | 5.4305 |
| AuthoredExit | 287 | 2.392316 | 8.3356 | 8.5003 | 8.7502 | 4.1804 | 5.0298 |
| StationIdle | 1,800 | 15.006435 | 8.3369 | 8.5396 | 8.8083 | 4.2713 | 5.1220 |

One GameMode phase sample differs from the post-update fixture phase when approach engages docking. It is retained and reported, not relabeled or discarded. The 2.392316-second exit stage counts updates still reporting disembark; the terminal update becomes idle. It does not shorten the authored 2.4-second clip. Normal simulation delta was mean 8.336215/p99 8.435/max 8.8075 ms for Station 5.

Wave 10 covered normal breathing, full Wave 9 and all 40.001767 seconds of the Wave 10 climax, then 5.003874 seconds of approach. Gravity, asteroids and enemies existed concurrently for 23.727849 seconds. Simulation delta was mean 8.338022/p99 8.4955/max 8.7977 ms. This scenario stops before docking; it does not measure Station 2 arrival/disembark/services.

The lead visually observed Flight only in Station 5, and Wave 9 plus the Wave 10 compound scene in the separate endgame run. The independent audits read files/source/CSV and make no visual or listening assertion. Natural controls, station walking/purchases/save/relaunch, balance, memory leaks, clean-PC startup and final art remain open. The historical startup hitch below is not retested by a capture that begins after loading. Rendered logs retain the known MotionVectorSimulation warning and explicit motion-blur setting precedence; no warning-free or hitch-free startup claim is made. The two scenarios and earlier packages differ in route/composition/assets, so they do not establish an optimization A/B result or uncapped headroom.

## Historical Package 9 rendered endgame (2026-09-13)

Source `4178ff443d34a7611a7353bac784091ec25ba0fa`, package 9, game SHA `af8431a544ccebcda1b6b46a15523abfe576f172c37514eac5029219370b3cd7`. The guarded fixture ran normal engine frames with audio enabled at 2560x1440, DX12/SM6, all quality groups 2, VSync off and cap 120 on the same i7-14700F/RTX 5080 machine. Owner editor and desktop apps stayed open.

The fresh GUID profile used a seeded Tier V starter/Rapid Laser/Overdrive Cooling build with base hull/shield 50000 and scripted strafe, boost, brake, dodge and firing. It covered normal Wave 9, breathing, all **40.007 seconds of Wave 10 climax**, then **5.006 seconds of approach**. Gravity, asteroids and enemies existed together for **23.719 seconds**. Peak threats 23, below cap 24; kind counts include warning/offscreen actors.

All **15,770 frames** stayed foreground over **131.482 seconds** of recorded frame time. Mean **8.337 ms** (~119.94 FPS), median 8.334, p95 8.341, p99 **8.505**, maximum **8.818**; zero frames exceeded 16.667/33.333/50 ms. GPU mean 2.765/p99 3.650/max 4.431 ms; game thread mean 1.784/max 6.961 ms. Simulation delta mean 8.337/max 8.807 ms came from normal actor updates, with fixed step and time dilation rejected. This is a capped fixture measurement, not uncapped headroom or representative 60 FPS acceptance.

The process exited 0; source, all seven binary/container artifacts and production saves remained identical; no test save slots were written. Capture began after foreground warmup, so it does not measure startup loading. That historical run did not measure Wave 5 or station transitions; Package 10 later measured the Station 5 fixture above. Natural piloting, balance, Station 2 transition and full-run memory/leak tests remain open. See the [complete performance receipt](validation/2026-09-13-endgame-performance.json), [package binding](validation/2026-09-13-windows-visual-package.json) and [reproduction harness](ENDGAME_CAPTURE.md). Later source/content changes are excluded.

## Historical package 4 configuration and identity

- Windows 11 25H2 build 26200.9445; Intel Core i7-14700F; NVIDIA RTX 5080, driver 616.92. The environment audit recorded approximately 47.72 GiB RAM and 16 GiB VRAM.
- UE 5.8.2 Win64 Development, 2560×1440, DX12 / SM6, Lumen mesh distance fields, VSync off, effective 120 FPS cap.
- Source milestone `1464c1df365b89492f27bfe418400dd338b098d3`; package 4 game SHA-256 `35e01c0985fe450d259e6cc9d673b6d56b330cc9a5aa313b3566e779d7032984`.
- Fresh isolated profile `Artifacts/PackageSmoke/57579fdb25bd449ba907598454c4fed4`; neutral flight controls after native New Run selection. Other desktop applications and the owner's editor remained running. This is not a controlled clean-machine benchmark.
- All eleven scalability groups applied level **2** at frame 0 after engine initialization. The earlier package 3 capture rendered level 3 despite the menu's default 2; reapplying settings in GameInstance OnStart fixed that observed defect.

The complete capture contains 18,000 frames over 152.2925 seconds. Active-flight counters identify 15,131 gameplay frames over 126.126 seconds. Excluding frames starting within the first five seconds of active flight leaves **14,530 frames over 121.122 seconds**, spanning Waves 1–3 and up to **24 active threats**.

## Historical Package 4 corrected-settings gameplay result

All values below are milliseconds. Percentiles use nearest rank; the median averages the middle pair. Raw startup and gameplay remain in the receipt; warmup exclusion is explicit.

| Counter | Mean | Median | p95 | p99 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| FrameTime | 8.336 | 8.334 | 8.819 | 9.119 | 10.898 |
| GPUTime | 2.659 | 2.464 | 3.382 | 3.524 | 4.063 |
| GameThreadTime | 1.684 | 1.635 | 2.136 | 2.527 | 5.008 |
| RenderThreadTime | 3.164 | 3.094 | 3.701 | 4.203 | 6.038 |
| RHIThreadTime | 2.037 | 1.989 | 2.628 | 2.956 | 4.067 |

Raw and warmup-trimmed gameplay each had **zero frames above 16.667, 33.333 or 50 ms**. The 120 FPS cap is confirmed by the 8.3333 ms target-budget counter; the CSV's earlier `targetframerate=320` metadata is not the effective runtime cap. CPU and GPU counters are pipelined and must not be added together.

The separate [baseline receipt](validation/2026-09-13-packaged-performance.json) records level 3, 12,001 trimmed frames, mean 8.335 ms, p99 9.035 ms and maximum 11.353 ms, with up to 21 threats. Its GPU mean was 2.802 ms versus 2.659 ms in the corrected level-2 capture. These different compositions and durations are not a controlled A/B optimization result.

## Historical startup hitches and remaining measurement

The corrected capture includes a **2,174.921 ms startup frame** and two startup frames over 50 ms. The earlier capture's maximum startup frame was 2,336.641 ms. These were before active flight; they are retained separately rather than hidden inside a steady-state average. Asset loading, shader/PSO initialization and startup UI warrant an Insights trace before assigning a cause or claiming a hitch fix.

The packaged log reports an engine `r.MotionVectorSimulation` render-thread warning. It also reports the intended motion-blur game setting taking precedence over scalability. No project runtime error was observed in this smoke. These messages are not evidence of a clean full run.

This CSV exposes system free memory and selected renderer allocator counters, **not a complete process RAM/VRAM or leak measurement**. Process memory over a full run remains open. No simulation-delta counter exists in the capture. Separate Unreal flight tests compare actual pawn trajectories at 30/60/120/144 Hz; CSV wall frame time does not establish input or simulation correctness.

Neither historical package 3/4 capture covers Wave 5/10, docking/stations, world-origin rebasing, sustained boost/dodge or a fully upgraded build. The subsequent encounter-label readability patch is outside this measured executable's identity; see [BUILD_RUN.md](BUILD_RUN.md) for the delivered archive.

## Reproduce and close the gate

Start the Development package using an isolated profile and `-windowed -ResX=2560 -ResY=1440 -csvCaptureFrames=18000 -csvGpuStats`. Wait for the completed CSV footer before analyzing:

```powershell
python Scripts/AnalyzePerformance.py 'path/to/completed.csv' --log 'path/to/game.log' --output 'Artifacts/performance.json'
```

The analyzer uses Python's standard library, accommodates Unreal's growing header and large event field, excludes metadata rows, separates actual run phases and records exact hashes/settings. The [corrected-settings receipt](validation/2026-09-13-final-performance.json) contains per-wave timings, CPU/GPU measurements, worst frames, configuration chronology and method limits.

Next capture ordinary active piloting, natural arrivals at both stations, the unmeasured Station 2 transition and a natural ten-wave run. Package 10's scripted Station 5 measurement does not close those human-play checks. Record process RAM/VRAM, frame-time spikes and an Insights trace; compare quality levels and 60/120/144 caps using a controlled route. Prioritize responsive input, simulation correctness and hazard readability before visual fidelity. No representative 60 FPS or 120+ FPS acceptance is claimed yet.

## 2026-09-14 camera/environment follow-up

See [ENVIRONMENT_REFRESH.md](ENVIRONMENT_REFRESH.md) and its validation receipt for the camera, bounded background asteroids, dust/volume layer, Niagara wake and licensed station exterior. This supersedes older presentation descriptions only. Phase 1 remains PARTIAL; scripted captures do not establish natural gameplay, controller feel or near-alpha acceptance. No itch publication or merge is included.
