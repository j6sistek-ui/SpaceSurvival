# SpaceSurvival

Unreal Engine 5 single-player space survival for Windows PC.

**Phase 1: PARTIAL.** Package 8 builds with all 62 project packages and the required Engine Cube. Source 442ff06 passes 13 Unreal tests without test warnings/failures and CI-verified 524 strict/524 sanitizer assertions. Native checks cover prepared-station save/vendor/death paths and a guarded slowed authored-exit/service/departure replay. Natural play, final art/audio, clean-PC startup and the representative performance gate remain open.

**The owner rejected the current graphics as far below acceptable.** Generated spacecraft, station and secondary meshes are provisional implementation assets, not selected final art. A substantial art replacement pass is required. Preserve the supplied Acornaut asset. Primitive dressing is not a near-alpha presentation result.

Remaining implementation includes substantial art replacement, vendor/audio presentation and broader content tuning outside native code. The authored exit has automated contact/handoff and guarded native smoke evidence; natural docking/camera and continuous animation quality remain open. Station 2 has a live summary/save/discard boundary; discard and completion/retry acceptance remain open. Locked-file save failures/retries passed; interruption, disk-full/short-write and corrupt-data coverage remain open. These are separate from owner touch/feel testing; see [KNOWN_ISSUES](docs/KNOWN_ISSUES.md).

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

The Windows archive is at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`; its launcher is `SpaceSurvival.exe`. Keep the entire folder. [BUILD_RUN](docs/BUILD_RUN.md) binds package 8 to source `442ff06aa88e64569155f099b2fd38a56450d11e` and both executable hashes. Its guarded exit replay showed seated/airborne/landing/standing, suppressed prompts during exit, allowed service E and launched Wave 6. Prepared state, seeded kills and Slomo 0.1 limit that observation. Earlier package 7 exercised station save/vendor/resumed-death/account retention; these do not establish natural progression or physical-device feel. Package 8 bundles a compatible signed x64 runtime but has no clean-PC launch pass. Later starless-sky/ship/storage work is outside that artifact.

The completed package 4 Waves 1–3 measurement held about 119.96 FPS at a 120 FPS cap, with p99 frame time 9.119 ms and no active-flight frame above 16.667 ms. Both climaxes, station transitions and full-run performance remain unmeasured. See [PERFORMANCE](docs/PERFORMANCE.md) for configuration, startup hitches and limits.

For hands-on validation, follow the single sequential [playtest log](docs/PLAYTEST_TOMORROW.md): launch the recorded package, adjust mouse steering sensitivity, complete the keyboard/mouse route, then repeat with a physical controller. Resume at the first unchecked step. Steering sensitivity is an adjustable preference; **no owner touch/feel, listening or retry-motivation result has been received**.

Documentation: [build/run](docs/BUILD_RUN.md), [architecture](docs/ARCHITECTURE.md), [validation](docs/VALIDATION.md), [known issues](docs/KNOWN_ISSUES.md), [performance](docs/PERFORMANCE.md), [content pipeline](docs/CONTENT_PIPELINE.md), [Phase 2 integration](docs/PHASE2_INTEGRATION.md).
