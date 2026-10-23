# Saved station benchmark diagnosis — October 23, 2026

## Result

The installed LevelBenchmark2.0 plugin has usable saved **log evidence**, but these
runs do not establish steady station performance or a unique expensive asset.
No graphics settings, plugin source, station assets or production saves were
changed by this diagnosis. No performance improvement is claimed.

Evidence is in `Saved/Logs/SpaceSurvival-backup-2026.10.23-06.20.33.log`;
the compact extraction is `.agent/local/Observatory_20261023/SavedBenchmarks.json`.
The plugin's default `Saved/BenchmarkExports` contains no saved CSV for these
runs. The local installed source, including `BenchmarkOrchestrator.cpp`,
`BenchmarkPIEPass.cpp` and `BenchmarkOrchestrator.h`, was reviewed directly.

| Saved run, UTC | Observed result | Interpretation |
| --- | --- | --- |
| 06:08:16 | 13,522 mesh components;531 lights;225.29ms frame average;0ms GPU | GPU timing unavailable, not free rendering |
| 06:13:41 | Same static counts;77.02ms frame average;18.64ms reported GPU;1000MiB texture pool with0MiB over budget | Editor-loop timing and a summed GPU-stat estimate, not a matched standalone CPU/GPU frame |
| 06:16–06:20 | Per-light sequence stopped at light24 of231 | Incomplete; several negative light costs show measurement noise, not a useful ranked removal list |

The plugin waits1.5seconds, then samples the core ticker for1second. The second
run starts in Wayfarer at06:13:21, loads Survival at06:13:25 (line3820), and
captures complexity/overdraw before completion. Static editor counts and sampled
runtime worlds therefore differ. Its GPU number sums inclusive `IncAve` stats
from the latest stats snapshot; parent/child passes and overlapping queues may
overlap. It is not an independent whole-GPU frame measurement and should not be
converted into a reliable GPU FPS ceiling or subtracted from the frame average.

## What the evidence supports

- **Pipeline creation is a demonstrated stall source.** The ordinary session
  reaches450 cumulative PSO hitches by06:10:39,500 by06:12:58 and750 during
  the second benchmark capture. Logs contain100–200ms waits at06:12:42 and
  06:12:59, before that benchmark, and further waits during capture. None of
  those logged hitches were precached. Benchmark debug view captures themselves
  can create more PSOs; do not attribute the entire750 to normal gameplay.
- **Streaming/registration adds startup work.** The cargo level instance has
  repeated component-registration slices around20–24ms at06:09:07–09. These
  are observed startup slices, not proof of recurring warm rotation stalls.
- **Texture pool pressure was not present at the sampled instant.** The second
  run reports1000MiB with0MiB over budget at06:13:40. This neither disproves
  the owner's earlier over-budget warning nor measures total process VRAM.
- **The station is dense.** Static inventory reports13,522 mesh components and
  531lights. Counts alone do not identify visible draw calls, shadow casters,
  loaded texture residency or which assets can safely be removed.
- **Lighting/post processing warrant controlled comparison.** Reported passes
  include Postprocessing3.654ms, TSR2.382ms, ShadowDepths2.041ms and Lumen
  ScreenProbeGather2.017ms. These are overlapping/inclusive statistics; do not
  add them. Both TSR and DLSS appear in this editor capture, which does not
  prove the game is applying both upscalers to the same view.
- Shader complexity reports10.3% very-high pixels and7.9% of pixels with4x+
  overdraw. The `PlayerStart` hotspot name identifies a sampled viewpoint,
  not an expensive PlayerStart actor.

## Next discriminating check

RPT-20261020-04 remains lead-owned. Capture the same busy-station camera route
after map/texture/shader settling, then repeat it warm in the same process.
Use independent game/render/GPU timing and p95/p99 frame times, PSO hitch deltas,
streaming pool/residency and active NPC/helper state. Compare against an editor
view of the same route without gameplay to separate editor and gameplay costs.
Only then test one reversible change at a time: PSO coverage, room streaming/
visibility, and measured shadow-light/material offenders. Preserve Epic visual
settings for the baseline. The incomplete per-light run does not authorize
bulk removal of531lights or another full231-PIE-session sweep.

The separate new observatory is not a performance substitute for the busy station.
No package,60-FPS acceptance, owner feel acceptance or unique root cause follows
from this saved benchmark review.
