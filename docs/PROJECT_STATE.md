# SpaceSurvival project state

Updated 2026-09-13 UTC. **Phase 1: PARTIAL. Not near-alpha, not packaged, not gameplay-validated.**

## Delivered implementation

The formerly document-only repository now contains a UE5 C++ project/module/targets/configuration; portable survival rules; flight/input/camera and weapons; world hazards, two enemy archetypes, pickups and a pressure-budget Director; Wave 5 wormhole and Wave 10 compound routing; physical station/hangar source actors and diegetic interactions; upgrades/utilities/contracts/economy; account XP and sidegrade unlocks; station-suspension/account/settings save domains; a PC shell/HUD; content authoring and build scripts; automated tests and CI.

The source GLB is preserved. The content pipeline supplies 26 original provisional OBJ assets, 10 original PCM WAVs, material/map/data-asset authoring, source manifests, format checks and clearly labelled source previews. It has not generated actual Unreal assets because the editor is absent.

## Verified

- GCC 14 C++17 strict build of the portable domain and 266 assertions passed.
- ASan/UBSan build and the same 266 assertions passed without diagnostics.
- 19 source-project structural checks and Python syntax checks passed.
- 26 OBJ and 10 WAV source-format checks passed; content regeneration was byte-identical across 39 source/manifest files.
- Supplied GLB hash remains `c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91`. Its mesh/texture/walk source was inspected in Blender. This is not Unreal character verification.
- Independent scope and integration reviews identified and corrected source defects; the validation record maps every IMPLEMENT gate to its status.

## Not verified / not delivered

No Unreal open/UHT/C++ compile, engine asset import, Windows cook/package, input playtest, integrated ten-wave experience, save-close-relaunch test, listening test or frame-time result is available. There is **no Windows executable/package location to deliver**. `Artifacts/Windows` is the configured future output path only.

The engine directories inspected on this machine contain plugins/installation metadata, with no editor or build scripts. MSVC and the Windows SDK were also absent. The build command was attempted and failed at the missing `Build.bat` preflight; compilation did not start. Docker became available during execution and enabled the portable tests.

Presentation, character seating/entry/exit, distinct station NPCs/recorded announcements, deeper designer-authored content, UI layout verification and balance remain real implementation/quality work. They are not excused as completed by the environment blocker. See KNOWN_ISSUES.md.

## Design decisions needing continued review

- Station 2 is the ten-wave slice boundary, with services and suspension. It does not fabricate death or a full-game final-wave victory. Further launch is unavailable; explicit abandonment can return to a fresh hangar without death XP. Indefinite continuation/Station 2 relaunch remains open.
- One utility slot and one active contract keep the intended deliberate choice without an inventory system.
- Ordinary shell/settings pause flight; depot/reward choices preserve moving flight.
- Only actual action observations clear tutorial hints; tutorial comfort and flow remain untested.
- No Phase 2 feature implementation was added.

## Next execution gate

Provision the full Unreal/Windows C++ development toolchain under owner authorization. Build the editor target, execute content authoring and inspect its report, then fix UHT/compiler/import failures. Validate the real keyboard/mouse and controller flight slice before tuning later encounters. Execute the full manual protocol in VALIDATION.md, address the quality gaps, package Windows and repeat the critical tests in the package. Keep the implementation PR open and unmerged until the owner reviews the evidence.

Documentation entry points: BUILD_RUN.md, ARCHITECTURE.md, CONTENT_PIPELINE.md, VALIDATION.md, KNOWN_ISSUES.md, PERFORMANCE.md and PHASE2_INTEGRATION.md. The canonical working brief is ../.agent/CONTINUITY.md.
