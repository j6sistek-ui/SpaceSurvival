# Performance findings

**Early flight and both rendered climax fixtures are measured; the representative Phase 1 performance gate remains OPEN.** Package 10 now includes the normal Wave 5 wormhole/climax/Station 1 transition and a separate full Wave 10 climax/approach sample. Neither capped, seeded scenario exceeded 16.667 ms per frame. Natural ten-wave play, physical response, Station 2 docking, full-run memory stability and lower-end scalability remain unmeasured. Later [combat-cue changes](COMBAT_CUES.md) are outside these Package 10 results.

## Package 10 rendered Station 5 and Wave 10 (2026-09-13)

Both independent receipts bind source `0fc4f7a7eb032f010cce1899e0ca279bd9e6ee80` and game SHA-256 `4dde20dc8776827419ee7e3fa58ebdca9cdd6aac203db0754ab57f8d51fd7498`. Package 10 built in 45.06 seconds, with all 88 project packages/Engine Cube and seven archive artifacts verified. See the [package receipt](validation/2026-09-13-windows-audio-economy-package.json), [Station 5 receipt](validation/2026-09-13-station-transition-performance.json) and [Wave 10 receipt](validation/2026-09-13-audio-rock-endgame-performance.json).

The Windows Development captures ran at 2560x1440, D3D12/SM6, all 11 quality groups2, VSync off and cap 120 on the i7-14700F/RTX 5080 PC (driver 616.92), with the owner's editor and desktop apps open. Audio was enabled and the renderer device initialized; nobody performed a listening assessment. Both fixtures seed a starter/Rapid Laser with five Tier V paths, Cooling and base hull/shield 50000, then use scripted existing control APIs. Normal world delta, budgets, caps, damage and transitions remain active; fixed timestep/frame rate/time dilation are rejected. These are not natural survival or controlled hardware-comparison benchmarks.

All captured frames are retained below, including one unmarked seed frame per run. Capture begins after the required two focused seconds; startup/focus wait and CSV drain are outside these samples. There is no additional warmup trimming or removal of slow frames. Every marked fixture frame was foreground. Nearest-rank percentiles and middle-pair median are used; CPU/GPU pipeline counters must not be added together.

| Scenario | Total / marked frames | Total frame-seconds | Mean ms | p99 ms | Maximum ms | Frames >16.667 /33.333 /50 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Station 5 | 16,872 / 16,871 | 140.648611 | 8.336215 | 8.4610 | 8.8284 | 0 / 0 / 0 |
| Wave 10 | 15,768 / 15,767 | 131.473918 | 8.338021 | 8.5187 | 8.8226 | 0 / 0 / 0 |

Marked-frame sums are140.640279 seconds for Station 5 and 131.465585 seconds for Wave 10; these differ from native callback wall durations and the all-frame sums above. Peak active threats were23 in each run. Counts include telegraphs/offscreen actors. Both owned processes exited0, wrote no save slots, and preserved production save hashes, all 131 source snapshot entries and all seven artifacts. Those stability checks belong to the capture interval; later source edits do not inherit them.

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

The fresh GUID profile used a seeded Tier V starter/Rapid Laser/Overdrive Cooling build with base hull/shield 50000 and scripted strafe, boost, brake, dodge and firing. It covered normal Wave 9, breathing, all **40.007 seconds of Wave 10 climax**, then **5.006 seconds of approach**. Gravity, asteroids and enemies existed together for **23.719 seconds**. Peak threats23, below cap24; kind counts include warning/offscreen actors.

All **15,770 frames** stayed foreground over **131.482 seconds** of recorded frame time. Mean **8.337 ms** (~119.94 FPS), median 8.334, p95 8.341, p99 **8.505**, maximum **8.818**; zero frames exceeded 16.667/33.333/50ms. GPU mean 2.765/p99 3.650/max 4.431ms; game thread mean 1.784/max 6.961ms. Simulation delta mean 8.337/max 8.807ms came from normal actor updates, with fixed step and time dilation rejected. This is a capped fixture measurement, not uncapped headroom or representative 60FPS acceptance.

The process exited0; source, all seven binary/container artifacts and production saves remained identical; no test save slots were written. Capture began after foreground warmup, so it does not measure startup loading. That historical run did not measure Wave 5 or station transitions; Package 10 later measured the Station 5 fixture above. Natural piloting, balance, Station 2 transition and full-run memory/leak tests remain open. See the [complete performance receipt](validation/2026-09-13-endgame-performance.json), [package binding](validation/2026-09-13-windows-visual-package.json) and [reproduction harness](ENDGAME_CAPTURE.md). Later source/content changes are excluded.

## Historical package 4 configuration and identity

- Windows 11 25H2 build 26200.9445; Intel Core i7-14700F; NVIDIA RTX 5080, driver 616.92. The environment audit recorded approximately 47.72 GiB RAM and 16 GiB VRAM.
- UE 5.8.2 Win64 Development, 2560×1440, DX12 / SM6, Lumen mesh distance fields, VSync off, effective 120 FPS cap.
- Source milestone `1464c1df365b89492f27bfe418400dd338b098d3`; package 4 game SHA-256 `35e01c0985fe450d259e6cc9d673b6d56b330cc9a5aa313b3566e779d7032984`.
- Fresh isolated profile `Artifacts/PackageSmoke/57579fdb25bd449ba907598454c4fed4`; neutral flight controls after native New Run selection. Other desktop applications and the owner's editor remained running. This is not a controlled clean-machine benchmark.
- All eleven scalability groups applied level **2** at frame 0 after engine initialization. The earlier package 3 capture rendered level 3 despite the menu's default 2; reapplying settings in GameInstance OnStart fixed that observed defect.

The complete capture contains 18,000 frames over 152.2925 seconds. Active-flight counters identify 15,131 gameplay frames over 126.126 seconds. Excluding frames starting within the first five seconds of active flight leaves **14,530 frames over 121.122 seconds**, spanning Waves 1–3 and up to **24 active threats**.

## Corrected-settings gameplay result

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

## Hitches, warnings and remaining measurement

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
