# SpaceSurvival

Unreal Engine 5 single-player space survival for Windows PC.

**Phase 1 status: PARTIAL — source implementation and portable tests, not a validated or packaged game.**

The authoritative design is [GAME_SCOPE](docs/GAME_SCOPE.md); the execution and acceptance contract is [IMPLEMENT](IMPLEMENT.md). Both are preserved. See [project state](docs/PROJECT_STATE.md) for exact open gates.

The source contains C++ gameplay rules and Unreal adapters for flight, combat, hazards, a pressure-budget Director, two station visits, upgrades, contracts, events, account progression and consumable station suspensions. Original provisional mesh/audio sources and a real Unreal authoring script are supplied; the original rigged Acornaut GLB remains unchanged.

Portable validation uses containers:

```powershell
./Scripts/TestCore.ps1
python Scripts/CheckProject.py
```

With a complete Unreal 5.8 installation and compatible Windows C++ toolchain:

```powershell
./Scripts/Build.ps1 -EngineRoot 'C:\Program Files\Epic Games\UE_5.8' -Target Editor
./Scripts/Build.ps1 -EngineRoot 'C:\Program Files\Epic Games\UE_5.8' -Target Content
./Scripts/Build.ps1 -EngineRoot 'C:\Program Files\Epic Games\UE_5.8' -Target Test
./Scripts/Build.ps1 -EngineRoot 'C:\Program Files\Epic Games\UE_5.8' -Target Package
```

The inspected machine has only UE plugin directories, so these Unreal steps have not succeeded. There is no packaged Windows executable yet. Generated Unreal content must be imported and validated before opening the default map successfully.

Documentation: [build/run](docs/BUILD_RUN.md), [architecture](docs/ARCHITECTURE.md), [validation](docs/VALIDATION.md), [known issues](docs/KNOWN_ISSUES.md), [performance](docs/PERFORMANCE.md), [content pipeline](docs/CONTENT_PIPELINE.md), [Phase 2 integration](docs/PHASE2_INTEGRATION.md).
