# Wayfarer tester release — October1

Owner authorizes the current station and furnished apartment in the game, preservation of the separate build area, and an itch update for testers with known unfinished behavior. This is not owner acceptance or Phase1 completion. The later owner instruction explicitly authorizes merging completed work and carrying outstanding tests into one new PR; this supersedes the initial no-merge boundary.

## Integration

The existing repaired checkout combines station PR64 with harder-director PR66 and wormhole PR67. Runtime station composition is derived from the saved outpost; original outpost, apartment and flat BuildingSandbox hashes are unchanged. [Map receipt](2026-10-01-wayfarer-runtime-map.json) identifies the runtime asset and 7,782 stable actor tags. The original outpost/ULAT authoring checkout and second building sandbox remain available. Actual player ship, paint, home loadout, survival services and Free Flight use the existing game systems. Supplemental service anchors cover the prior preview-only gaps. No progression, survival cadence or difficulty reduction.

## Focused checks

- Native Editor builds pass. Final fixture build8: 5.24seconds; prior substantive build4:23.39seconds. Existing engine C4996 warnings remain.
- Changed C++ formatting, runtime Python syntax,39 source checks and documentation navigation gate pass. No full panel or whole gameplay suite run.
- Runtime map preparation passes source hash preservation. Raw UWorld duplication first crashed because a vendor particle component retained the transient duplicate; normal level Save As avoids that path. A second Save As to the existing target was refused; final saved-level tagging uses the current-level save API. The failed logs remain private.
- First integration fixture had an incorrect mobile-depot mooring assertion for a parked station ship; repaired to verify disabled flight tick and exact pad position. Second fixture passes four real service openings and all27 apartment floor/clearance probes, and renders pad/services/apartment. It stopped on the harness's incorrect assertion that the temporary practice account's last-run identity must remain unchanged. Corrected to require unchanged state during service calls and exact account/run restoration after Free Flight.
- The final package and stable packaged fixture now pass as recorded below, superseding the earlier pending package/smoke status. Publication remains pending; no itch delivery is established by this local receipt.

## Explicit limits

Synthetic pawn approaches and route probes are not a natural keyboard/controller walkthrough. The fixture skips moving door leaves during geometric clearance sampling. Departure uses public StartFreeFlight, return uses public EndFreeFlight; this does not establish natural approach/landing or physical boarding/cockpit seating. The Wave5 station portion seeds an isolated in-memory state rather than playing five waves. No purchase/save action is selected; existing production saves are protected by capture snapshots. Screenshots and blocking streaming checks are not representative 60FPS/VRAM or visual acceptance. Existing apartment blind-material warnings and editor-only agent-tool Python startup errors are retained as known issues; neither is presented as a clean all-log run.

## Packaging follow-up

The first full cook found two source IK rigs in HeroReplacement (root and Final/RTG_Body_Source) referencing deliberately never-cooked MocapSource/SK_Mannequin. The existing exact-package authoring exclusion now includes those two helpers without recursion. ReplacementHero/Retarget.py identifies them as source retarget inputs; meshes, skeletons and baked runtime clips remain selected. Original source assets are not modified. The initial packaging attempt under Windows PowerShell5.1 also rejected Tee-Object -Encoding; the installed pwsh7 runs the existing packaging script correctly.

The final editor fixture d349effd403d41c0bde9d25a1755ec18 passes all six runtime stages, eight service openings,27 probes and exact Free Flight state restoration. Its outer wrapper correctly fails because HEAD changed while the identical built sources were being committed. It remains limited runtime evidence; the stable packaged fixture below supplies the separate end-to-end artifact validation.

The first exclusion exposed duplicate short-name PrimaryAssetIDs between the root and Final folders and the parent RTG_Body retargeters. Final rules use two distinct primary asset types, each excluding its RTG_Body and RTG_Body_Source packages without recursion (four packages total). The duplicate-ID warning and missing-reference cook failure are retained; source files remain untouched.

## Verified Windows package and packaged smoke

At source `e6c2a87ca3971749b7a19ace848faa10d4f237fd`, `Artifacts/WayfarerPackage4.log` records successful Win64 Development build/cook/stage/archive, AutomationTool exit 0, and cook **0 errors / 31 warnings**. The native targets were already up to date (zero compile actions in this invocation). The package is `Artifacts/Windows`; runtime game executable SHA256 is `03354F2C397B0A9177DC1300FED4ACF3F94253B1303C79CE49BDAC800FA0A405`. This is local package evidence, not publication or clean-PC launch evidence.

The packaged `OutpostReview` capture `bf48cdc01570484fb59278620460a277` succeeds with process exit 0 on October 1, 20:39:55–20:41:04 UTC. Its `Artifacts/EndgameSoak/<token>/capture.json` records the same source HEAD before/after, stable executable/container hashes, unchanged monitored production-save locations and no test save slots written. The only recorded untracked file is local `.mcp.json`, which is not a gameplay source change. A release manifest must separately bind the package to its source; recording HEAD alone is not that binding.

- The actual runtime map loads 7,783 actors, 13 service anchors and 17 authored terminals. The real Phoenix is parked at the station. Six 1920×1080 frames cover pad, home services, furnished apartment, Free Flight departure, home return and seeded Wave5 pit stop; the pad/apartment images were visually inspected.
- Four home panels (Wardrobe, Paint, Launch, Weapon) and four active-run panels (Upgrades, Repair, Contracts, Save) open through real `Interact` calls. Merely opening them leaves account/run state unchanged; no purchase/save action is executed.
- All 27 sampled apartment-route floor/upper-capsule-clearance checks pass. Public `StartFreeFlight` performs takeoff and powered movement; public `EndFreeFlight` restores the exact account/run state. The separately seeded Wave5 station has a supported possessed walker and functioning service panel openings.
- The fixture is offscreen and muted. It does not establish actual apartment/door/cockpit traversal, natural landing, five-wave progression, physical-controller behavior, audio, representative FPS/VRAM, or owner visual acceptance.

Known material limitations remain: the cook reports unset Frame Material / Material / Rope Material reads on apartment `BP_Blinds` actors `HorisontalBlind2_5`, `HorisontalBlind3` and `HorisontalBlind_2`. Packaged `Rendered.log:1067` reports missing `InstancedStaticMeshes` usage on `/Game/SpaceSurvival/Licensed/OrbitalWreck/KitBeam/M_Figur_0`, so affected instances use the default material. The inspected run has no fatal/runtime error, but is not warning-free. No texture-pool/VRAM-overflow warning appeared in this particular run; that absence is not a performance qualification.

**Later server verification confirms publication:0.1.22-alpha / build2048604 READY.** [Project State](../PROJECT_STATE.md) owns the eventual release version, itch build identity and publication receipt. These results satisfy the focused tester-build smoke, not Phase1 completion.

Native executable provenance: `WayfarerPackage2.log` records compilation of the changed SpaceSurvival modules and linking SpaceSurvival.exe (116.89seconds, build succeeded) before its later cook failure. From integration commit a69b559 to packaged commit e6c2a87, only Config/DefaultGame.ini and this receipt changed; gameplay C++ is identical. Package4 therefore correctly reused those up-to-date native binaries, then recooked/staged/archived with the repaired cook exclusions. The [package receipt](2026-10-01-itch-0.1.22-alpha-package.json) binds every archived file and the stable packaged capture to e6c2a87.

CI follow-up: source workflow36924199375 failed only because TestCookCoverage still asserted10 exact authoring exclusions. The test now expects14, explicitly verifies the four root/Final retargeter packages and confirms the final hero mesh/eight animation clips stay covered. All8 cook-coverage tests pass and CheckCookCoverage reports143string-loaded paths with0uncovered. This is test/documentation-only after packaging; game source, configuration and payload bytes are unchanged.

## Owner-authorized consolidation and tester upload

On October1 the owner explicitly accepted completion of the initial task and requested all completed PRs merged, with testing/revisions in one new PR. PR68 merged at e4489d5; PR64/66 were marked merged through their included ancestry. PR67 then merged into its original stacked parent; its full head was already in main. All four are confirmed merged and no older PR remains open. A fresh comparison of Source, Config, Content and the project file between packaged e6c2a87 and origin/main e4489d5 is empty. The new codex/phase1-test-and-audio-followup branch starts at that main. This source consolidation changes no package bytes and establishes no new natural-play acceptance.

Butler validation, dry-run and upload succeed: 51files/8772436373bytes, 3.43GiB patch, 58.02percent savings, 55.55percent old-data reuse. Fresh server status verifies itch build2048604 READY, version0.1.22-alpha, replacing2003058 on upload19226459. [Immutable published receipt](2026-10-01-itch-0.1.22-alpha-published.json).
