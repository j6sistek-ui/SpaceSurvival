# SpaceSurvival

Unreal Engine 5 single-player space survival for Windows PC. **Phase 1 remains PARTIAL.**

**[Open work and your next review](docs/KNOWN_ISSUES.md)** is the single active task and priority log. Start there; it contains the owner review queue, all hands-on acceptance checks, unresolved problems and closure evidence.

- [Project state and where files live](docs/PROJECT_STATE.md): GitHub source, local assets/builds and the separately published itch version.
- [Build and run](docs/BUILD_RUN.md): launch the packaged game or develop with UE 5.8.2.
- [Solution catalog](docs/production/SOLUTION_CATALOG.md): owned assets and possible solutions across Phase 1; catalog value is not the work schedule.
- [Game scope](docs/GAME_SCOPE.md) and [implementation contract](IMPLEMENT.md): authoritative design and completion requirements.

The latest recorded local review build is the September 14 combined space look at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`. Keep its entire folder. The [project state](docs/PROJECT_STATE.md#source-build-and-release) identifies its evidence and the older itch release. A source merge does not rebuild the executable or publish an update.

The game has the ten-wave system foundation, two weapons/enemies, four hazard families, stations, progression and local saves. Automated and scripted checks exist; natural play, controller comfort, near-alpha presentation/audio and representative performance still need acceptance. Current art is provisional.

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