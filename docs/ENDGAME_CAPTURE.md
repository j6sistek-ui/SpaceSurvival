# Rendered endgame capture fixture

**Editor build passed; first rendered endgame capture is pending.** This fixture adds targeted endgame measurement. It does not replace the natural ten-wave playtest or establish the representative 60 FPS gate.

The explicit Development-only `-SSWave10Soak` route creates a separate `ASSWave10Soak` actor after normal map/GameMode startup. Ordinary runs do not create the actor or bypass input. The fixture requires a fresh `Artifacts/EndgameSoak/<GUID>/User` profile, matching root argument and token marker, the exact generic save backend, unredirected paths, no existing save slots or capture outputs, and an enabled renderer. It calls no save API. Account writes are blocked in the fixture instance, and the wrapper compares both production save locations before and after the owned process exits.

The memory-only seed completes Wave 8 using the normal domain transition, then runs normal breathing, full Wave 9, normal breathing, the **40-second Wave 10 climax**, and five seconds of actual station approach. It retains Director budgets, the threat cap, enemy caps, spatial admission, telegraphs, damage and frame timing. It never forces actor admission, kills enemies directly, teleports objectives, accelerates world ticks or changes time dilation.

The seed is deliberately artificial: starter ship, Rapid Laser, all five Tier V upgrades, Overdrive Cooling, no active contract or optional events, and base hull/shield of 50,000. Scripted shallow strafing, boost/brake cycles, a dodge attempt every eight seconds, and firing for two seconds in each six-second interval exercise the existing controls and combat APIs. Enlarged durability permits a complete load sample; it is not evidence of natural survivability, economy or balance.

## Run after rebuilding

Use the repository root. The script neither builds nor installs anything:

```powershell
./Scripts/CaptureEndgame.ps1 -Editor
./Scripts/CaptureEndgame.ps1
```

The first command uses the installed editor with `-game`; the second uses the current packaged inner executable. They are separate captures. Default resolution is 2560Ã—1440; `-Width` and `-Height` change the explicit request. `-NoSound` is optional and recorded as a measurement limitation.

Activate the owned game window when it appears, then leave it in the foreground. The fixture waits for two focused seconds before starting CSV capture. It allows 60 seconds to obtain focus and 180 seconds for the run; the wrapper has a 240-second overall timeout and stops only the process it started. Foreground state is recorded on each fixture frame. Losing focus invalidates capture success; no global idle-throttle setting is changed. Natural keyboard/controller acceptance remains a separate hands-on test.

A successful run exits normally after the CSV write future completes. The GUID directory retains:

- `Endgame.csv` and `Rendered.log` with actual renderer/thread/frame metrics.
- `fixture.json` with actual PID, phase coverage, normal climax duration, concurrent compound actor-presence duration, peak threats, focus and empty test-save checks.
- `performance.json` with all-frame and phase timing distributions, simulation delta, per-kind counts, focus coverage and exact CSV/log hashes.
- `result.json`, `source-before.json` and production manifests binding exact executable/container/source/content bytes, before/after stability and owned process identity.

The packaged snapshot includes the project and global `.pak`, `.utoc` and `.ucas` files, with container additions/removals detected. An editor capture binds the editor executable and project DLL. Source snapshots include dirty files; a separate successful build/package record must bind those sources to the executable. A contemporaneous HEAD hash alone is not proof of compilation.

## Evidence limits

Compound coverage measures simultaneous gravity, asteroid and enemy actor presence, including telegraphs and offscreen actors. Completion requires at least 3.5 seconds of such presence, at least 39.5 sampled seconds of the normal 40-second climax, the intervening breathing phase, and five seconds of approach. These are fixture integrity checks, not newly prescribed game balance or visibility rules. Startup/CSV-drain frames are retained separately from fixture frames. CPU/GPU pipelines still require careful interpretation; count collection adds a capture-only actor scan.

The capture excludes natural early progression, Wave 5, physical input latency, station docking/disembark, listening/feel/retry appeal, clean-machine portability and final-art acceptance. It does not establish memory-leak behavior or worst-case load. A passed sample remains **RENDERED_ENDGAME_FIXTURE_NOT_NATURAL_GAMEPLAY**.

Source verification: six synthetic evidence-parser tests passed; parsing the existing package 4 18,000-frame CSV preserves the exact prior group/per-wave timing results and hash without inventing a fixture marker. Current source structural checks and PowerShell syntax checks passed. Synthetic rows are parser tests only. The combined editor build in `.agent/local/TailSoakEditorBuild.log` compiled `SSWave10Soak.cpp` and succeeded in 25.26 seconds. The separate 14-test suite passed; it does not run this rendered fixture. The real capture and measured results remain pending.
