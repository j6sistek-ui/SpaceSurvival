# Performance findings

> Reboot checkpoint, 2026-09-13 04:35 UTC: the editor C++ build **succeeded** using MSVC14.51.36257 and Windows SDK10.0.26100.0; earlier missing-toolchain statements below are historical and superseded. Current portable tests pass372 assertions in each strict/sanitizer build. Gameplay content creation, Unreal save-test execution, package and player validation remain pending. See [PROJECT_STATE](PROJECT_STATE.md) for resume order.

## Measured boundary

**No gameplay CPU, GPU or frame-time measurement is available. No 60 FPS or 120 FPS claim is made.** The portable rule tests validate logic; their duration is not a game-performance benchmark. A real Unreal5.8.2 editor workbench can now import/render assets, but the missing Windows C++ toolchain prevents representative game execution.

The inspected machine is Windows 11 Home build 26200, Intel Core i7-14700F (20 cores/28 logical processors), approximately 47.72 GiB RAM, NVIDIA RTX 5080 with approximately 16 GiB VRAM and driver 616.92. The observed display was 2560x1440. Initial free C: space was about 175 GiB. These are environment facts, not measured game results.

## Source measures

- Flight integrates bounded 120 Hz movement substeps, with exponential response, acceleration limits and swept movement. Low-frame-rate handling still needs cross-rate gameplay comparisons, especially for external forces and collision sweeps.
- Director limits active threats (default 24), tracks a spending budget, constrains overlaps and considers closing speed for reaction distance. Fragment/event spawns check capacity.
- Native world actors expire, old encounters are cleared at stations/death, and world-origin rebasing limits accumulated coordinates. Ordinary wave transitions retain existing bodies.
- Generated secondary geometry is deliberately small; the geometry manifest contains exact triangle counts. This does not account for hero skinning, real engine materials, lighting, shadows, overdraw or audio processing.
- Graphics quality selects Unreal scalability; frame caps offer 60/120/144. Shake and motion blur can be disabled. These are configuration paths, not verified scalability gains.

## Likely bottlenecks to measure

1. Synchronous `LoadObject` calls during actor creation and sound playback; move validated assets into a loaded content catalog/preload phase if captures show first-use hitches.
2. Actor iteration for targeting, danger detection, field influence, enemy hazard avoidance and HUD radar. The cap bounds common work, but combined projectiles/fragments/events need profiling before choosing spatial indexing or pooling.
3. Spawn/destroy bursts for wormhole rings, station meshes/components, transitions and destruction fragments.
4. Supplied character skinning/material cost, shader compilation, translucent/emissive overdraw and shadow settings.
5. Canvas text/layout and camera/input handling at unusual resolutions and refresh rates.

## Required capture protocol

Use a Development Windows package at 2560x1440 first, recording engine/build/driver/quality and commit SHA. Capture baseline flight, maximum boost/dodge, electrical storm, gravity plus debris, Wave 5 wormhole/combat, both docking transitions, station UI and the Wave 10 compound climax. Use Unreal Insights plus `stat unit`, `stat gpu`, `stat game` and CSV profiler as supported by the installed version.

Record average, p95 and p99 frame times, CPU game/render time, GPU time, hitches and memory; show worst gameplay intervals rather than only an empty scene average. The baseline target is 16.67 ms/frame for 60 FPS. Compare a lower quality preset and 120 FPS-capable settings (8.33 ms budget) without removing simulation, response or essential warning cues. Compare input/flight behavior at 30, 60, 120 and 144 FPS. Include the packaged build and hardware identifiers with every capture.

Performance gate remains open until those measurements exist and any major bottlenecks are addressed or explicitly accepted.
