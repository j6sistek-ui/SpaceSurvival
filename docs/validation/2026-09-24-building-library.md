# Building library authoring receipt — 2026-09-24

**State: IMPLEMENTED LOCALLY; owner usability/visual acceptance remains open.** Native library authoring, fresh prefab loading/movement, ULAT palette persistence and complete Cargo Level Instance loading/movement passed. No frame-rate, owner-acceptance, packaged-build or release claim is made.

Workspace: `C:/Users/j6sis/SpaceSurvival/Artifacts/Worktrees/asteroid-outpost`. Private assets and raw receipts remain local. This checkpoint does not replace the canonical issue log or project state.

## Verified authoring results

| Item | Result and evidence |
| --- | --- |
| Static assemblies | 41 generated Blueprints: 30 windows, 7 screens, 3 workstations and 1 chair. Native component count, mesh presence, bottom pivot and moving all layers together passed. `Artifacts/BuildingLibrary/prefab-author.json` reports PASS with no errors. |
| Cargo wrapper | Saved `/Game/BuildingLibrary/Assembled/Ships/BP_CargoShip_Complete`, referencing private `/Game/BuildingLibrary/Ships/L_CargoShip_Complete`. Authoring PASS, 2,078 retained actors; fresh instance loading and a 321cm translation pass. |
| Cargo contents | Interior, local lighting, ropes and gate Blueprints retained. Removed 58 global-environment/camera/sequence/group actors, including the giant sky sphere. Source hull bounds give approximately 29.8 × 65.1 × 12.8 m. |
| Local assembly collection | `Saved/Collections/SS_01_Assembled___Drag_These.collection` contains 42 entries, including Cargo; 42 corresponding `.uasset` files exist. |
| ULAT palette | Applied successfully: 1,146 new mesh rows, all 4 prior rows preserved, 1,150 verified total. Six useful type labels added. Existing collection names retained; no apply errors. |
| ULAT backups | Both engine-plugin data packages were backed up and checksum-verified before mutation under `Artifacts/PrefabLibrary/ULATBackups/20260924T234018Z-5b024254/`. Palette remains engine-global. |
| Portal/Solar isolation | Earlier native relocation receipts report 13 Portal and 55 Solar assets, no remaining dependencies on the temporary `/Game/Rocket` roots, and no leftover source redirectors. |
| Source/map preservation | Both authoring receipts report the owner outpost map unchanged. Cargo receipt also reports the vendor showcase unchanged. |

ULAT application receipt: `Artifacts/PrefabLibrary/ULAT-20260924T234018Z-5b024254.json`. Assembly receipt: `Artifacts/BuildingLibrary/prefab-author.json`. Cargo receipt: `Artifacts/BuildingLibrary/cargo-prefab.json`. Relocation receipts: `Artifacts/BuildingLibrary/relocate-portal.json` and `relocate-solar.json`.

## Asset identities

| Asset | SHA-256 |
| --- | --- |
| Owner outpost map, before and after | `a57659ae6d9d8585cc8964c0d956ff39b7c9f69d6267d356211d22caf659eff7` |
| Vendor Cargo showcase, preserved | `18854441be398118a889dfdc258260bf99d2228e4373bd42dfd9ec8e8e264c62` |
| Private Cargo level | `d2601cf5d7881481ba2be26d09af64b3776cefee75c1a1e54b49af6c74dab588` |
| Cargo Level Instance Blueprint | `2ebc5b2949a6f16fed538989513ec6038220ba6bf382a09757da965f5eb04af0` |

## Verification limits and retained history

An earlier ULAT attempt passed a `SoftObjectPath` to this engine's legacy registry binding, which expects a `Name`. Per-entry errors were incorrectly treated as ordinary skips. The helper now passes `Name`, records unexpected entry errors and blocks successful dry-run/application status when any occur. The final native application receipt above supersedes that unsuccessful palette attempt; it does not erase it.

The relocation helper now requires an exact per-file match to the selected family's staging receipt, matching registry packages, an empty destination and no dirty packages. Small local fixture checks verified rejection of extra, changed and missing source files. This additional guard was reviewed without rerunning asset relocation.

The native `BuildingCargoInspect.log` records an 8,860,553-triangle Hibernation Pod source build. This is source complexity, not rendered triangle cost or a performance measurement. The complete ship retains its detailed interior and is not an optimized gameplay vehicle.

Physical editing, collision/walking, retained gate behavior, representative performance and owner acceptance remain unverified. Download imports and library generation did not authorize placing content into the owner's map, packaging, publication or merge.

## Final focused checks and corrections

- Native `BuildingLibraryReview5` establishes all 41 building prefabs reload with their expected mesh components and move together. The complete Level Instance loads its hull and moves it exactly321cm with its parent. Palette reload reads1,150rows. Process exits0; all three protected map hashes match. Reviews6/7 repeat only this narrow validation while correcting the unsaved preview environment.
- Six advert variants now apply the selected material to both native pane slots. Independent audit reconstructs all247 transformed native bounds, with maximum extent difference0.00000223cm, and all36 pane bounds fit their frames. The first slot-repair attempt stopped at a duplicate component-template handle check before writing; unique template-path selection fixed it.
- Six private Cargo glass components opt out of Nanite because their native translucent materials are unsupported by Nanite. Vendor meshes/materials are untouched. The private map and wrapper identities above supersede their first-save hashes.
- Earlier Cargo validation queried editable editor actors before streaming finished. Fully loaded Level Instance children are excluded from that query, producing a false missing/movement failure. The corrected check queries all actors in the loaded world after the loading barrier. Earlier reports and logs are retained, including the premature move failure and timeout.
- Reviews2/3 encountered background library-refresh/export interference and were terminated only after verifying the owned process/log identity. Review4 removed that callback in its own process and exited0 after its query timeout. Owner editor processes were not closed. Review5's screenshots were overexposed because zero brightness was used while extended exposure units were disabled; those images and receipt are preserved under `Preview5Overexposed`. Review6 was underlit and showed windows edge-on; preserved under `Preview6Underlit`. Review7 corrects the camera direction, adds a native daylight reflection cubemap and uses finite exposure in the unsaved test scene. No saved scene lighting or materials changed for these previews.
- Python compilation,38 source structural checks, canonical documentation check and Git whitespace check pass. No runtime C++ changed, so no C++ rebuild or full gameplay regression/package was run.

The palette addition skips91 meshes whose short names collide with existing or earlier entries; all remain imported and browsable in native folders/collections. ULAT cannot safely distinguish those short names. Original four rows are preserved.

## Reproduction and storage

The reviewed helpers are `Scripts/StageBuildingDownloads.py`, `RelocateBuildingMaterials.py`, `BuildingPrefabRecipes.py`, `ConfigureUlatLibrary.py`, `AuthorBuildingLibrary.py`, `AuthorCargoPrefab.py`, and `ValidateBuildingLibrary.py`. The private source manifest is `Artifacts/BuildingLibrary/download_manifest.json`.

For a fresh clone with licensed inputs, stage Solar/Cargo/Nova Content first, relocate the exact Solar receipt natively, stage Portal and relocate it, then stage Rocket props. Never combine the conflicting Rocket helper sets. Staging defaults to dry-run and refuses overwriting different bytes. Existing project assets cannot satisfy the relocation guard: it requires the exact original staging file set. Do not rerun relocation on this completed library.

Authoring runs in a dedicated Entry-map native editor with `-NullRHI -unattended`, disabling UAssetBrowser/NwiroIntegrationKit only in that process. `AuthorBuildingLibrary.py` with `-SSApplyUlat` dry-runs the palette first and then applies with backup. `AuthorCargoPrefab.py` preserves edited/unknown existing assets by receipt hash. `ValidateBuildingLibrary.py` uses `-RenderOffscreen -SSCaptureBuildingLibrary` for three unsaved previews, or `-NullRHI` for structural checks. All new vendor/generated Content roots are ignored. Source-only clones need the private assets, Saved/Collections and installed plugin to reproduce the local result.

## Final saved-copy verification — 2026-09-25 00:01 UTC

`BuildingLibraryReview8` passes fresh41-prefab checks,1150-row palette reload, complete Cargo loading and321cm parent/child translation, and all three protected map hashes; process exits0. Raw1440x900 previews are `Artifacts/BuildingLibrary/Windows.png`, `Workstation.png` and `CargoShip.png`. Lead visually inspected them: matched frame/pane placement, complete Goliath components and coherent ship exterior are visible. Native worn/translucent/glitch materials remain unchanged; these neutral test views are not acceptance of the final station composition or all downloaded materials.

Review7 exposed four immense vendor planets/sun shells remaining alongside the hull. Source survey confirms kilometre-scale bounds and remote positions. The final private copy removes these four backdrops, retains2078 ship/local actors, and now asserts no `SM_Planet` actors accompany the instance. Source showcase and station remain unchanged. This supersedes the initial2082-actor wrapper and first saved-copy hashes. Review7 logged normal closure but its shell returned1; that disagreement is retained, with no fabricated clean exit claim for that attempt. Review8 is the clean final run.

The complete vendor ship still emits a VSM overlapping-local-lights warning. Its dense interior, retained gate logic, natural walking/collision and representative GPU performance require evaluation before gameplay integration. This batch does not disable the vendor's lighting or reduce its meshes to conceal that limitation. Screen panes remain intentionally nonblocking visual components.
