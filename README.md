# SpaceSurvival

Unreal Engine 5 single-player space survival for Windows PC.

**Phase 1: PARTIAL.** The Unreal module and Windows Development package build successfully. Twelve Unreal tests pass without test warnings/failures, 404 strict and 404 sanitizer assertions pass, and an isolated fresh-process GameInstance save lifecycle passes. Natural play, final art/audio and the representative performance gate remain open. A packaged launch, neutral-controls death/results and fresh-run restart have been observed.

**The owner rejected the current graphics as far below acceptable.** Generated spacecraft, station and secondary meshes are provisional implementation assets, not selected final art. A substantial art replacement pass is required. Preserve the supplied Acornaut asset. Primitive dressing is not a near-alpha presentation result.

Remaining implementation work includes the Station 2 completion/restart boundary, authored exit/vendor/audio presentation and broader content tuning outside native code. Storage failure handling still needs fault-injection verification. These are separate from owner touch/feel testing; see [KNOWN_ISSUES](docs/KNOWN_ISSUES.md).

The authoritative design is [GAME_SCOPE](docs/GAME_SCOPE.md); the execution and acceptance contract is [IMPLEMENT](IMPLEMENT.md). See [project state](docs/PROJECT_STATE.md) for current evidence and open gates.

The source contains C++ gameplay rules and Unreal adapters for flight, combat, hazards, a pressure-budget Director, two station visits, upgrades, contracts, events, account progression and consumable station suspensions. Original generated mesh/audio sources and Unreal authoring scripts are supplied; the original rigged Acornaut GLB remains unchanged.

Portable validation uses containers:

```powershell
./Scripts/TestCore.ps1
./Scripts/Format.ps1 -Check
python Scripts/CheckProject.py
```

Use the complete owner-installed UE 5.8.2 engine and Windows C++/SDK toolchain:

```powershell
./Scripts/Build.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -Target Editor
./Scripts/Build.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -Target Content
./Scripts/Build.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -Target Validate
./Scripts/Build.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -Target Test
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8'
./Scripts/Build.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -Target Package
```

The automated journey traverses all ten waves and both stations using 12-second waves, enlarged durability, forced objectives and fixture assistance. It is not a natural playthrough. The separate storage harness verifies real GameInstance suspension, resumed death and fresh-start persistence across isolated processes; owner save hashes are unchanged. See [VALIDATION](docs/VALIDATION.md) for exact coverage and limits.

The Windows archive is at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`; its launcher is `SpaceSurvival.exe`. [BUILD_RUN](docs/BUILD_RUN.md) records both executable hashes. Package 5 builds and renders New Run. Its Wave 2 Salvage Cache label wraps legibly over dark backing, and pressing E accepted the event while flight continued. Package 4 separately verified startup graphics settings. Earlier package 3 smoke reached a neutral-controls Wave 4 death, restarted into a fresh run and retained the account after relaunch. These are limited packaged checks, not event completion, active piloting or natural ten-wave acceptance.

The completed package 4 Waves 1–3 measurement held about 119.96 FPS at a 120 FPS cap, with p99 frame time 9.119 ms and no active-flight frame above 16.667 ms. Both climaxes, station transitions and full-run performance remain unmeasured. See [PERFORMANCE](docs/PERFORMANCE.md) for configuration, startup hitches and limits.

For hands-on validation, follow the single sequential [playtest log](docs/PLAYTEST_TOMORROW.md): launch the recorded package, adjust mouse steering sensitivity, complete the keyboard/mouse route, then repeat with a physical controller. Resume at the first unchecked step. Steering sensitivity is an adjustable preference; **no owner touch/feel, listening or retry-motivation result has been received**.

Documentation: [build/run](docs/BUILD_RUN.md), [architecture](docs/ARCHITECTURE.md), [validation](docs/VALIDATION.md), [known issues](docs/KNOWN_ISSUES.md), [performance](docs/PERFORMANCE.md), [content pipeline](docs/CONTENT_PIPELINE.md), [Phase 2 integration](docs/PHASE2_INTEGRATION.md).
