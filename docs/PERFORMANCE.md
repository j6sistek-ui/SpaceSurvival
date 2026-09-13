# Performance findings

**Measured early flight; representative Phase 1 performance gate remains OPEN.** The corrected-settings Windows Development build held approximately 119.96 FPS during a capped Waves 1–3 sample on the available PC. No recorded gameplay frame exceeded the 16.667 ms / 60 FPS budget. This does not establish either climax, station transitions, full-run stability or physical input responsiveness.

## Measured configuration and identity

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

Neither capture covers Wave 5/10, docking/stations, world-origin rebasing, sustained boost/dodge or a fully upgraded build. The subsequent encounter-label readability patch is outside this measured executable's identity; see [BUILD_RUN.md](BUILD_RUN.md) for the delivered archive.

## Reproduce and close the gate

Start the Development package using an isolated profile and `-windowed -ResX=2560 -ResY=1440 -csvCaptureFrames=18000 -csvGpuStats`. Wait for the completed CSV footer before analyzing:

```powershell
python Scripts/AnalyzePerformance.py 'path/to/completed.csv' --log 'path/to/game.log' --output 'Artifacts/performance.json'
```

The analyzer uses Python's standard library, accommodates Unreal's growing header and large event field, excludes metadata rows, separates actual run phases and records exact hashes/settings. The [corrected-settings receipt](validation/2026-09-13-final-performance.json) contains per-wave timings, CPU/GPU measurements, worst frames, configuration chronology and method limits.

Next capture ordinary active piloting, electrical/gravity/debris overlap, Wave 5, both station transitions and Wave 10. Record process RAM/VRAM, frame-time spikes and an Insights trace; compare quality levels and 60/120/144 caps using a controlled route. Prioritize responsive input, simulation correctness and hazard readability before visual fidelity. No representative 60 FPS or 120+ FPS acceptance is claimed yet.
