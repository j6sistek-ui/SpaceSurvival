# Canonical Unreal project and complete building library

Owner issue: `RPT-20261006-01`. This repair consolidates implemented work into
`C:/Users/j6sis/SpaceSurvival`; it does not close the broader Phase 1 acceptance queue.

## First divergence and repair

The owner's normal editor opened canonical source `684db34` with a September20
Editor module. The newer game was built in the separate flight-loop-reset checkout.
The root now starts from `731e9316`, which includes merged main `e4489d5`. Ninety-six
modified/conflicting files were preserved in `.agent/local/consolidation-20261006`,
with a scoped Git stash for prior tracked edits. Shared private maps/content were
preserved. No owner scene regeneration or vendor-asset renaming was performed.

The editor startup map is the editable current
`/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime`. Pressing Play there
travels to Survival and its real game mode. The original outpost and flat asset
sandbox remain separate maps. `Edit Current Station.cmd` and the desktop shortcuts
target the canonical project; normal editing keeps Nwiro enabled.

ULAT's existing installation was moved from the engine's top-level Plugins folder
into `Plugins/Marketplace/UltimateLevelArtTool`. The first build's missing-module
rules failure is retained; the second native Editor build passed in 35.74 seconds.
No host packages were installed. Known vendor/engine deprecation warnings remain.

## Native verification

Offscreen normal-editor run `.agent/local/CurrentStationVerification5` passed all
12 checks with an isolated user/save profile. It verified:

- Complete apartment loading: 745 child actors, 924 apartment mesh placements.
- Full snapshot: 12,315 placements, 423 distinct mesh assets, 7,172 editable direct
  placements and 5,143 locked component/instance/skeletal reference placements.
- One real placement moved 10 cm and was restored on the same native actor;
  a stale repeat was rejected. The original full-precision transform was restored.
- Normal Play reached `Survival` / `/Script/SpaceSurvival.SSGameMode`, with one
  station, 7,775 tagged outpost actors in one streamed station level, and 744
  apartment actors in the game world. PIE then stopped normally.
- Current station, original outpost, apartment source and flat sandbox map files
  retained their exact pre-test SHA256 hashes. No test placement was saved.

Snapshot identity: `7021c48bc2a34cf1ae3c8ab2029f67fe`, under
`Artifacts/WayfarerBlender/Snapshots`. Hidden collision/sky geometry remains hidden
in Blender. Blueprint behavior, lighting, complex material graphs and animation
remain authoritative in Unreal; their mesh representations are locked context.

Earlier native failures are retained as Verification1–4: the Guid wrapper lacks
component fields, EditorActorSubsystem excludes uneditable LevelInstance children,
and streaming properties are not readable through Python. The final bridge uses
Guid's public string conversion, actor enumeration that includes streamed children,
and public streaming-object iteration/methods. It refuses incomplete snapshots.

## Asset coverage

`Artifacts/BuildingLibrary/Refresh/20261006T030726Z-5a317fed/refresh.json` records an
additive verified refresh of 16,051 assets across 70 collections. Existing collection
members were preserved. ULAT has 2,617 rows, up from 2,156. Its short-name importer
skips 204 collisions and four unsupported Tripo names; all 208 remain available in
native collections, Content Browser and the full-path Blender mesh library.

The catalog contains 2,825 real mesh proxies with zero failed exports. All 2,825
have previews: 2,814 native thumbnails plus 11 clay fallbacks for thin/glass meshes.
The native Blender asset cache has 2,825 entries and zero unavailable meshes.
The builder now releases only its per-asset temporary datablocks after writing,
preserving existing scene data while preventing whole-library memory accumulation.

Blender 5.2.2's focused library workflow passed registration, surface isolation,
duplicate handling, native assets, incremental rebuilding, offline relocation and
unsafe-archive rejection. The Wayfarer safety suite passes 19 cases and the snapshot
cache suite passes three. The focused library workflow was repeated successfully
after the final skeletal importer repair.

## Blender scene, geometry and portable delivery

The native geometry regression passed 10/10 cases, covering the nine skeletal
exports and a transformed-parent mesh join. Bone-display icospheres were previously
being mistaken for character geometry; the importer now excludes those widgets,
bakes evaluated skeletal geometry and its complete world transform before removing
armatures, and checks join completion. Each result matches the evaluated source
vertex/polygon counts and bounds, with zero measured bounds error. Phoenix is
31,634 vertices and approximately 12.44 by 24.84 by 7.05 metres. Mech detail is
supplied by 1,151 separately exported Nanite static-component placements alongside
71 skeletal instances. Earlier failed geometry checks are retained locally.

The final background scene was rebuilt after this repair, then appended into the
owner's open Blender 5.2.2. Live receipt `.agent/local/LiveWayfarerFinal.json` verifies
12,315 objects, 7,172 editable placements, 5,143 locked references, 301 hidden
collision/sky objects, 2,825 catalog entries and 2,825 native library assets. The
previous three-object scene is preserved, with an additional pre-import backup.
Installed importer/cache/Wayfarer source hashes match the repository. Library
auto-refresh is restored; Live synchronization is off. One separate Asset Browser
is open with the SpaceSurvival catalog and 128-pixel thumbnails.

- Working file: `Artifacts/WayfarerBlender/Wayfarer-Working-20261006.blend`.
- Source build: `Artifacts/WayfarerBlender/Wayfarer-Current-20261006-Final.blend`.
- Inspected viewport: `Artifacts/WayfarerBlender/Wayfarer-Blender-Overview.png`.
- Final laptop ZIP:
  `Artifacts/BuildingSandbox/SpaceSurvival-Library-0.5.0-20261006-final.zip`.
  It includes 2,825 assets and 8,508 files with no missing previews (4,249,452,608
  bytes). Full archive CRC verification passes and key addon hashes match the
  installed/current source. The working
  station `.blend` is separate from this reusable parts library.

The large live append exceeded the bridge's response timeout but completed and was
verified through a separate read; it was not repeated. The browser initially
reported an operator-context error after opening its window; the existing window
was configured and verified without opening another. The viewport confirms station,
ships, rock, skyline and apartment geometry. It is a placement view with simplified
materials, not an Unreal lighting or gameplay render.

The native Editor build, changed C++ formatting, 39 structural checks, Python
compilation, documentation gate and whitespace checks pass. An independent final
review found no actionable blockers in startup/Play routing, transfer guards,
artifact launchers or the corrected geometry importer. Checks were scoped to the
changed paths; the ten-wave gameplay suite was not rerun.

## Local package and release distinction

Canonical `Artifacts/Windows` now contains the latest previously published game.
The old directory is preserved as `M:/SpaceSurvival/Artifacts/Windows-before-unified-20261006`.
All 53 original copied files were hash-verified. The three release metadata files
were then added and all 51 published payload entries match the `0.1.22-alpha`
release manifest. Additional local debug files are not part of that published payload.
Production saves were not reset.

Itch remains build2048604, `0.1.22-alpha`, published source `e6c2a87`; no new cook,
upload or merge is part of this repair. Source consolidation, scripted checks and
publication do not establish natural gameplay, physical input, performance or owner
acceptance. Those remain in `docs/KNOWN_ISSUES.md`.
