# SpaceSurvival

**Current local game:** use **Play SpaceSurvival - Current** or **Unreal Engine** on the desktop; both now point to the repaired game checkout. The latter opens UE5.8 directly into the game. [Launch paths and package distinction](docs/BUILD_RUN.md); [replacement hero review](docs/validation/2026-09-24-replacement-hero.md).

**Tester update:** [itch0.1.22-alpha](https://j6sistek-ui.itch.io/space-survival) is published (build2048604), with Wayfarer Exchange, its apartment and current gameplay. Completed PRs are merged; [remaining testing and Phase1 gaps](docs/KNOWN_ISSUES.md#october1-consolidated-phase1-follow-up) stay open.

Unreal Engine 5 single-player space survival for Windows PC. **Phase 1 remains PARTIAL.**

**[Open work and your next review](docs/KNOWN_ISSUES.md)** is the single active task and priority log. Start there; it contains the owner review queue, all hands-on acceptance checks, unresolved problems and closure evidence.

- [Project state and where files live](docs/PROJECT_STATE.md): GitHub source, local assets/builds and the separately published itch version.
- [Contributor and other-chat onboarding](docs/CONTRIBUTOR_ONBOARDING.md): repository paths, skills, high-value owned assets, documentation duties and mistakes to avoid.
- [Build and run](docs/BUILD_RUN.md): launch the packaged game or develop with UE 5.8.2.
- [Edit the station](docs/STATION_EDITING.md): add and arrange owned props in the saved station Blueprint while preserving gameplay boundaries.
- [Solution catalog](docs/production/SOLUTION_CATALOG.md): owned assets and possible solutions across Phase 1; catalog value is not the work schedule.
- [Game scope](docs/GAME_SCOPE.md) and [implementation contract](IMPLEMENT.md): authoritative design and completion requirements.

The current playable checkout is `C:/Users/j6sis/.codex/worktrees/flight-loop-reset/SpaceSurvival`. Its October1 integration adds Wayfarer Exchange and the furnished apartment to the existing game, alongside the replacement hero, harder survival and wormhole improvements. Use **Play SpaceSurvival - Current** for the development game or **Play Packaged Review.cmd** in that checkout for its separately built Windows archive. [Project State](docs/PROJECT_STATE.md#source-build-and-release) identifies the exact package and itch version; source changes do not update either automatically.

The original `C:/Users/j6sis/SpaceSurvival` remains an authoring checkout. Keep each packaged game's entire folder and preserve existing save profiles.

The game has the ten-wave system foundation, two weapons/enemies, four hazard families, stations, progression and local saves. Automated and scripted checks exist; natural play, controller comfort, near-alpha presentation/audio and representative performance still need acceptance. Current art is provisional.

**Station authoring:** the current game consumes a derived copy of the editable Wayfarer scene; see [Station editing](docs/STATION_EDITING.md). `Open Station Workshop.cmd` and the [Station Workshop guide](docs/STATION_EDITING.md) still edit the preserved legacy layout, and have not been migrated to the reset. Existing packages update only after a later build.

**Explore the new asteroid outpost:** use [Play Outpost Sandbox.cmd](Play%20Outpost%20Sandbox.cmd) to walk through Wayfarer Exchange or [Edit Outpost Sandbox.cmd](Edit%20Outpost%20Sandbox.cmd) to open its separate editable map. The [outpost guide](docs/OUTPOST_SANDBOX.md) and [assembled building library guide](docs/BUILDING_LIBRARY.md) explain rooms, controls and authoring boundaries. The original sandbox retains preview consoles, while the separate runtime copy routes to real game services. Editing the original does not automatically regenerate or publish the runtime copy.

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
