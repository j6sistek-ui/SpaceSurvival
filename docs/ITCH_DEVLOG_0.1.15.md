# 0.1.15-alpha — environment refresh, camera fixes and known issues

This is an early-development tester update. Phase 1 remains partial; the game is not yet at the intended near-alpha visual or gameplay quality.

## Changes in this update

- Revised rear flight camera to keep more of the ship visible during normal flight, boost, braking and turns.
- Added clustered background asteroids and fine local dust for depth and speed cues. Decorative rocks do not add collisions or increase early-wave hazard counts.
- Integrated purchased asteroid and station interior assets, plus an industrial station exterior.
- Added provisional Niagara engine wakes.
- Updated depot interaction toward optional magnetic mooring and aboard-ship services, with clearer event/contract and threat feedback.
- Included repairs to the hero animation assets and an optional new ship trial. Use Try New Ship.cmd in the installation folder; the normal launch retains the visible-pilot starter.
- Retained Controls settings for sensitivity and pitch inversion, and the corrected rear third-person station camera.

## Known issues and unfinished work

- Atmospheric cloud banks are disabled by default because the packaged check exposed opaque rectangular artifacts. The desired layered nebula/dust-volume look is unfinished. Local dust and background rocks remain enabled.
- Engine wakes use temporary warm ribbon effects. Final exhaust color, placement and tuning remain work in progress.
- The station exterior has a conservative solid collision boundary. Gaps in that exterior model are not fly-through passages.
- Character motion, ship/pilot fit and the optional enclosed ship still need continuous-motion and player review. The optional ship hides the pilot.
- A source review found differences between controller and keyboard capabilities while live reward panels are open. Tutorial progress also uses synchronous account writes; any noticeable hitching still needs reproduction and measurement.
- Enemy death feedback, target allegiance, event/contract clarity, wormhole arrival impact and combat difficulty need further player evaluation and polish.
- Natural ten-wave balance, controller comfort, audio quality and replay appeal are not accepted as complete.
- Current representative 60 FPS performance, lower-end hardware, clean-PC installation and update/save preservation need broader testing. Older scripted high-end benchmarks do not establish performance for this asset refresh.

## Validation and updating

The current Unreal regression suite passed 42 tests with no test warnings or failures. These are technical checks, not proof of game feel or a natural complete run. Package/render verification is recorded separately in the release receipt.

Close the game, then update through the itch desktop app on the existing windows-alpha channel. Browser downloads require replacing the installed files manually. The itch launch keeps saves outside the installation. A clean-PC prerequisite and A-to-B save-preservation pilot remains unverified.

If Windows reports a missing Visual C++ runtime, use the bundled Microsoft runtime installer action. Unreal Editor and Visual Studio are not needed to play.

Please include version 0.1.15-alpha, your controller/GPU, wave or station, expected versus actual behavior, and a short reproduction or clip with feedback. Start by checking whether the whole ship stays comfortably visible during a turn, boost and brake.
