# SpaceSurvival

**Current local project:** use `C:/Users/j6sis/SpaceSurvival` for both the game and authoring. Open [Edit Current Station.cmd](Edit%20Current%20Station.cmd) to edit the Wayfarer station used by the game, or [Play Development Build.cmd](Play%20Development%20Build.cmd) to play. The normal editor opens Wayfarer; Play routes through the Survival game map. [Launch paths and package distinction](docs/BUILD_RUN.md).

**Tester update:** [itch0.1.22-alpha](https://j6sistek-ui.itch.io/space-survival) is published (build2048604), with the October1 Wayfarer Exchange, apartment and gameplay baseline. The October6 survival-quality repairs are newer local work in [PR69](https://github.com/j6sistek-ui/SpaceSurvival/pull/69), not that published download. [Current build identity](docs/PROJECT_STATE.md) and [remaining testing and Phase1 gaps](docs/KNOWN_ISSUES.md#october1-consolidated-phase1-follow-up) separate implementation from release and acceptance.

Unreal Engine 5 single-player space survival for Windows PC. **Phase 1 remains PARTIAL.**

**[Open work and your next review](docs/KNOWN_ISSUES.md)** is the single active task and priority log. Start there; it contains the owner review queue, all hands-on acceptance checks, unresolved problems and closure evidence.

- [Project state and where files live](docs/PROJECT_STATE.md): GitHub source, local assets/builds and the separately published itch version.
- [Contributor and other-chat onboarding](docs/CONTRIBUTOR_ONBOARDING.md): repository paths, skills, high-value owned assets, documentation duties and mistakes to avoid.
- [Build and run](docs/BUILD_RUN.md): launch the packaged game or develop with the installed UE 5.8.3.
- [Edit the station](docs/STATION_EDITING.md): arrange the current Wayfarer map and apartment while preserving gameplay boundaries.
- [Solution catalog](docs/production/SOLUTION_CATALOG.md): owned assets and possible solutions across Phase 1; catalog value is not the work schedule.
- [Game scope](docs/GAME_SCOPE.md) and [implementation contract](IMPLEMENT.md): authoritative design and completion requirements.

The canonical checkout includes the October1 Wayfarer integration, furnished apartment, replacement hero, harder survival and wormhole improvements. The former `flight-loop-reset` and outpost worktrees are retained development history, not the default project. [Project State](docs/PROJECT_STATE.md#source-build-and-release) identifies the current native build, separately stored Windows package and itch version; source changes do not update a package automatically.

Keep each packaged game's entire folder and preserve existing save profiles. A local Editor rebuild does not republish the game.

The game has the ten-wave system foundation, two weapons/enemies, four hazard families, stations, progression and local saves. Automated and scripted checks exist; natural play, controller comfort, near-alpha presentation/audio and representative performance still need acceptance. Current art is provisional.

**Station authoring:** [Edit Current Station.cmd](Edit%20Current%20Station.cmd) opens `/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime`, the station used by home and survival visits. Save changes with Play stopped. `Open Station Workshop.cmd` edits the preserved legacy `BP_StationVisualLayout`; its Save + Apply does not update Wayfarer. [Station editing](docs/STATION_EDITING.md) explains the current workflow and shared apartment level.

**Preserved outpost sandbox:** [Play Outpost Sandbox.cmd](Play%20Outpost%20Sandbox.cmd) and [Edit Outpost Sandbox.cmd](Edit%20Outpost%20Sandbox.cmd) still open the separate `/Game/OutpostSandbox/L_AsteroidOutpost` experiment. Its preview consoles remain distinct from the current station's game services. Editing it does not automatically replace the current station. The [outpost guide](docs/OUTPOST_SANDBOX.md) records its design history; the [building library guide](docs/BUILDING_LIBRARY.md) explains complete assemblies, ULAT and native collections in the canonical project.

**Try the building examples:** the [Building sandbox workflow](docs/BUILDING_SANDBOX.md) covers the separate Genesis/companion-scene workbench, walking launcher, Blender placement round trip and laptop handoff.

## Development

From the repository root, use existing tooling; no host package installation is implied:

```powershell
./Scripts/TestCore.ps1
./Scripts/Format.ps1 -Check
python Scripts/CheckProject.py
```

Portable checks use the repository containers. Unreal compilation, authoring, testing and Windows packaging use the owner's installed Windows toolchain; see [build/run](docs/BUILD_RUN.md). Licensed assets are local and are not reproduced by a Git clone alone.

## Contributing and documentation

Every PR must complete the [documentation review checklist](.github/pull_request_template.md), identify what the owner should open/check, and update affected documents or explain why they remain correct. The [documentation check](.github/workflows/documentation.yml) checks that handoff is present; reviewers still verify its truth. See [operating rules](AGENTS.md#documentation-and-open-work).

Technical references: [architecture](docs/ARCHITECTURE.md), [content pipeline](docs/CONTENT_PIPELINE.md), [source integrity](docs/SOURCE_INTEGRITY.md), [validation](docs/VALIDATION.md), [performance](docs/PERFORMANCE.md), [Phase 2 integration](docs/PHASE2_INTEGRATION.md), [release workflow](docs/ITCH_RELEASES.md). These explain systems and evidence; active priorities live only in the open-work log.
