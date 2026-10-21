# October21 roster and asset-quality correction

Scope: RPT-20261020-09 (Cloth default/white retirement), RPT-20261020-04
(texture pressure), and the owner's Epic-quality asset audit. Local development
changes only; no packaged build, release, merge or complete performance acceptance.

## Changed locally

- `DA_Phase1` now has eleven active hero rows, Cloth first; white EX7 is absent
  from selection. Stable identity values, other rows/tuning and production saves
  are preserved. Native DA SHA256
  `cbf52d35ffd80a7a4f60fb3e7d55883687843e49e9d035985852a5f594187597`.
- Source defaults/tests follow that order. A saved white preference falls back to
  Cloth without rewriting the account. White artwork remains available for repair.
- Twelve `KrakenRefresh_20261015/Textures/M{0..3}_{BaseColor,MetalRough,Normal}`
  textures now use their existing mip chains for streaming. Only `NeverStream`
  changes; source dimensions, compression, color handling and materials are retained.
- Exact original DA/texture packages are hash-verified in
  `D:/SpaceSurvival_AssetArchive/QualityPass_20261021`. These are recovery copies,
  not runtime dependencies. Native art stays on C and is not duplicated in the PR.

Tracked corrective scripts default to a plan, then require an explicit apply flag
and unchanged input hashes. Do not replay the old four-hero activation recipe.

## Measured texture demand

Same camera positions,1600x900, all ten scalability groups3, screen percentage100,
local dialogue AI disabled, private saves and20seconds warming per view. These
are real-RHI offscreen PIE captures, not a packaged/physical-input/FPS benchmark.

| View | White required pool MiB | Cloth before texture change | Cloth after texture change |
|---|---:|---:|---:|
| Market | 1335.3 | 593.4 | 525.2 |
| Restaurant | 1472.8 | 527.4 | 628.5 |
| Lounge | 1833.0 | 1021.1 | 1021.2 |
| Kraken | Not sampled | 520.2 | 520.5 |

Pool is1000MiB. Final Lounge remains21.2MiB over; final route transient peak is
1195.4MiB. Resident/non-streaming totals are different counters and cannot be
added to required pool demand. Changing views causes variation: the Kraken flag
change is not claimed to lower every view's streaming demand or fix all warnings.

The twelve Kraken textures previously forced139MiB resident; after correction
they use0.09MiB in the farther sampled route views. In a close frozen comparison,
normal streaming uses1.13MiB and a forced-residency reference uses104.27MiB of the
139MiB family maximum (the character does not use every texture). The displayed
body/face detail shows no visible regression between those captures. Gown textures
also rise from0.94 to53.44MiB under that reference; material appearance is unchanged.
This is a bounded visual comparison, not proof for every distance/lighting condition.

## Epic-quality audit

The bounded native inventory covers419textures and seven skeletal meshes from
the supplied heroes, workshop, XANDRA and Kraken families, plus earlier large
texture candidates. It is not the entire project.

- All419 have zero asset LOD bias.374 use group mip generation;42 use NoMipmaps,
  two SimpleAverage and one Blur5 (a vendor demo logo).
-138 have explicit maximum sizes;32 caps are below imported source dimensions.
  Most of those32 are demo mannequin content; six production mask/hair cases
  include1K hair opacity and1K/2K cosmetic masks. Some are sensible budgets and
  need close visual inspection before increasing memory use.
- All seven sampled skeletal meshes have oneLOD. Missing distance LODs are a
  performance follow-up, not evidence that their close mesh is low quality.
- NoMipmaps includes UI/VFX and large surface textures. The audit is not authority
  to change all42 indiscriminately. Static-mesh LOD queries returned unavailable
  in this commandlet and are recorded as unknown, not zero.

The game source default quality is High (`2`), not Low. Installed Epic texture
scalability uses a1000MiB pool. `r.MaterialQualityLevel=1` means the High material
permutation, not Low. Epic scalability cannot override asset source resolution,
explicit texture caps or missing LODs. Owner graphics settings were not saved or
globally changed by these private probes.

## Verification and limits

Editor build succeeds in88.9seconds. DLL SHA256:
`5e546820bf05840afad178a7c55af412bec33a2ee4d29d0f050d0a22e8f4bf78`.
Existing engine/plugin deprecation warnings remain. Two targeted native suites:
HeroRoster succeeds; PlayableHeroWardrobe succeeds with one existing
`SS_STATION_WARP_PLACEMENT_REFUSED reason=welcome footprint/support` warning.
No assertions fail, but the repository's strict no-warning gate is **not clean**.

Source structural50, Python compilation/content-source checks and changed-C++
format checks pass locally. Local formatter22 differs from CI14. The first view
probe failed because its transient camera did not enter PIE; retained failure,
corrected unsaved camera and subsequent successful profiles are separate receipts.
Each completed profile verifies production saves unchanged. Station/config hashes
and owner Git HEAD/index are guarded; later Kraken motion work has its own map
adoption receipt if applied.

Private evidence: `.agent/local/QualityPass_20261021/` contains
`RosterPlan.json`, `RosterApplied.json`, `KrakenStreamingPlan.json`,
`KrakenStreamingApplied.json`, `AssetQuality.json`, `Build.log`, `Tests/index.json`,
and `WhiteReference`, `ClothBaseline`, `ClothStreaming`, `KrakenClose` profiles.
Tables come from actual `ListTextures` logs; runtime budget samples are in each
`Result.json`. The fresh audit reports no load errors. No market dressing was
removed, no bulk texture cap/LOD edit was made and no owner station redesign was
reverted. PSO hitches, cold conversation latency, full AI-enabled performance,
Cloth/Kraken cloth, Silver, Lira and normal play acceptance remain lead-owned.
