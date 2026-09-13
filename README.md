# SpaceSurvival

The subsequent contract/electrical/Station2-discard milestone passes **17 Unreal tests**, **641 strict +641 sanitizer assertions**, formatting,21 structural checks and fresh persisted-content validation. A five-process regression verifies both real locked-write failures and durable highest-wave10 with zeroXP/history after discard. These source changes are newer than Package9 and are awaiting packaging. See [contract tuning](docs/validation/2026-09-13-contract-tuning.json), [electrical timing](docs/validation/2026-09-13-electrical-telegraph.json) and [Station2 discard](docs/validation/2026-09-13-station2-discard.json). **Phase1 remains PARTIAL.**

Unreal Engine 5 single-player space survival for Windows PC.

**Phase 1: PARTIAL.** Runtime/content milestone `4178ff443d34a7611a7353bac784091ec25ba0fa` is committed and Package 9 BuildCookRun succeeded in 74.18 seconds; all 78 committed project assets and Engine Cube were found in the cooked index; the full rendered endgame fixture passed. The final editor suite passes 14 Unreal tests with zero test warnings/failures, and portable domain checks pass 593 strict/593 ASan/UBSan assertions. Package 8 remains the historical source 442ff06 build with 62 project packages and Engine Cube; its prepared/assisted native evidence does not cover the current assets. Natural play, final art/audio, clean-PC startup and representative performance acceptance remain open.

**The owner rejected the current graphics as far below acceptable.** Generated spacecraft, station and secondary meshes are provisional implementation assets, not selected final art. A substantial art replacement pass is required. Preserve the supplied Acornaut asset. Primitive dressing is not a near-alpha presentation result.

Current source adds editable utility prices/effects in `DA_Phase1`, the separate Tail V2 derivative, a replacement starter ship, starless panorama v3 and a licensed CC0 station deck. Original hero assets are preserved. Actual Tail V2 CPU contact/handoff passes; natural docking/camera and continuous animation quality remain open. Real locked replacement, staging-denial and interrupted-write recovery tests pass, as does fresh-process corrupt-account protection. Disk-full/short-write, arbitrary binary corruption and hardware-loss cases remain open. Station 2 retains a live summary/save/discard boundary; discard and completion/retry acceptance remain open. See [KNOWN_ISSUES](docs/KNOWN_ISSUES.md).

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
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -StorageFaults
./Scripts/TestSaveLifecycle.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -CorruptAccount
./Scripts/Build.ps1 -EngineRoot 'C:/Program Files/EpicGames2/UE_5.8' -Target Package
```

The automated journey traverses all ten waves and both stations using 12-second waves, enlarged durability, forced objectives and fixture assistance. It is not a natural playthrough. Storage modes use separate guarded GUID profiles and real GameInstance/Windows file operations. The [eight-process fault receipt](docs/validation/2026-09-13-storage-faults.json) records staging access denial and an owned writer terminated before replacement; fresh recovery retains the old checkpoint and later awards 475 XP once. The [four-process corruption receipt](docs/validation/2026-09-13-corrupt-account.json) records protection of invalid account text inside a valid Unreal envelope, followed by manual restoration of exact fixture bytes and fresh reload. Production-save hashes remained unchanged; this is not a shipped backup feature. See [VALIDATION](docs/VALIDATION.md) for the wider coverage and limits.

The Package 9 Windows archive is at `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`; its launcher is `SpaceSurvival.exe`. Keep the entire folder. Package 9 binds source `4178ff443d34a7611a7353bac784091ec25ba0fa`; the inner game executable is 332,407,296 bytes, SHA-256 `af8431a544ccebcda1b6b46a15523abfe576f172c37514eac5029219370b3cd7`. All 78 project packages plus Engine Cube are verified; native Station 1 texture residency and the complete rendered Wave 10 fixture passed. The historical [BUILD_RUN](docs/BUILD_RUN.md) record binds package 8 to source `442ff06aa88e64569155f099b2fd38a56450d11e` and both executable hashes. Its guarded exit replay showed seated/airborne/landing/standing, suppressed prompts during exit, allowed service E and launched Wave 6. Prepared state, seeded kills and Slomo 0.1 limit that observation. Earlier package 7 exercised station save/vendor/resumed-death/account retention; these do not establish natural progression or physical-device feel. Package 8 bundles a compatible signed x64 runtime but has no clean-PC launch pass. Current utility/Tail V2/ship/sky/deck changes and later storage-fault evidence are outside that artifact. See the [Package 9 receipt](docs/validation/2026-09-13-windows-visual-package.json) for the exact audit and rendered checks.

The completed package 4 Waves 1–3 measurement held about 119.96 FPS at a 120 FPS cap, with p99 frame time 9.119 ms and no active-flight frame above 16.667 ms. Package 9 also completed a scripted rendered Wave 10 capture at about 119.94 FPS; Wave 5, station transitions and natural full-run performance remain unmeasured. See [PERFORMANCE](docs/PERFORMANCE.md) for configuration, startup hitches and limits.

For hands-on validation, follow the single sequential [playtest log](docs/PLAYTEST_TOMORROW.md): launch the recorded package, adjust mouse steering sensitivity, complete the keyboard/mouse route, then repeat with a physical controller. All 19 human checks remain untouched; resume at the first unchecked step. Steering sensitivity is an adjustable preference; **no owner touch/feel, listening or retry-motivation result has been received**.

Current source/content evidence is bound in the [visual/systems milestone receipt](docs/validation/2026-09-13-visual-systems-milestone.json). The earlier [uncooked visual preview](docs/validation/2026-09-13-visual-candidate.json) observed the ship/hangar/flight before Tail V2 and the floor residency correction; it does not approve the final candidates. Asset sources and license records are in [CONTENT_PIPELINE](docs/CONTENT_PIPELINE.md). The guarded [endgame capture harness](docs/ENDGAME_CAPTURE.md) is implemented; its 15,770-frame capture completed, including the full 40-second climax, with production saves unchanged.

Documentation: [build/run](docs/BUILD_RUN.md), [architecture](docs/ARCHITECTURE.md), [validation](docs/VALIDATION.md), [known issues](docs/KNOWN_ISSUES.md), [performance](docs/PERFORMANCE.md), [content pipeline](docs/CONTENT_PIPELINE.md), [Phase 2 integration](docs/PHASE2_INTEGRATION.md).
