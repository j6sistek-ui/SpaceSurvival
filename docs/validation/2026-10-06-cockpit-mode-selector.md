# Phoenix cockpit departure mode

Source preparation and native verification recorded 2026-10-07 UTC for the owner's October 6 request; updated 02:40Z. Build31 and four focused native tests pass cleanly. Its nine-image capture verifies card spacing, selected mode and sit/depart flow, but still exposes incorrect middle-cabin guidance and unfriendly typography/clutter. A new bounded prompt correction is prepared and unbuilt. Build30's separate framing failure and 15 Free Flight lifecycle Blueprint warnings remain historical evidence; the changed save-lifecycle expectation and physical input acceptance remain separate gates.

The owner requested Waves / Free Flight selection inside the Phoenix, with the selected mode clear before takeoff. The implementation adds a compact cockpit card at the existing supported pilot-chair interaction. R or D-pad Left changes the departure preference; E or Y retains the existing sit and departure action. The card displays both choices and marks the selected one. If a pilot subtitle is active, the card moves above its caption band.

The existing station launch service becomes **Flight Briefing**. It reports the selected departure and directs the pilot to the cockpit, without a competing mode switch. Explicit **Continue saved Survival** remains available when a checkpoint exists. An active Survival station stop keeps its current mode, ship and progress; the cockpit card reports that mode selection is locked.

## Implementation and state boundaries

- `ASSPlayerController::PlayerTick` passes keyboard/controller press edges to `ASSGameMode::HandleCockpitModeInput` only in its walking branch. A held button does not repeatedly cycle. Two devices pressed together cause one change. A mode press consumes that frame's interaction, so pressing mode and sit together cannot depart accidentally.
- The mode handler and card use the existing `IsWalkerAtPilotSeat` predicate: the possessed walker must be grounded at the supported chair in the owned parked ship. Menus, boarding, departure, flight and walking elsewhere cannot use the selector.
- Selection changes only `SelectedDepartureMode`. It does not start/restart a run, enter Free Flight, change possession, write a save or commit departure. Existing sitting, native pilot handoff, save-failure rollback, active-run continuation and Free Flight session isolation remain the departure transaction.
- No asset, ship geometry, map, service anchor or save schema is changed by this work. The full game uses `ASSGameMode` and the runtime Wayfarer station; the standalone owner preview remains an art preview and is not converted into the full boarding game by this source change.

## Verification

| Check | Scope and present evidence |
|---|---|
| Source structure | `python Scripts/CheckProject.py`: 40 checks passed after the source change. This is not an Unreal compilation result. |
| C++ formatting | Installed clang-format 22.1.3, `--dry-run --Werror`, passed on all seven changed selector/fixture files. |
| Patch hygiene | `git diff --check` passed. |
| Capture wrapper syntax | PowerShell parser accepted the new ignored `CaptureBoardingModes.ps1`; it was not launched by this agent. |
| Native Editor build | Build30: `Result: Succeeded`, 14.02 seconds. The log retains the non-preferred MSVC notice and engine-header C4996 deprecations; it is not a warning-free build. |
| `SpaceSurvival.Integration.PhoenixCockpitDeparture` | Native PASS, 7.636 seconds, zero errors/warnings. Injects raw R / D-pad Left through the actual player controller at the walked native chair. Covers held buttons, simultaneous devices, mode+use precedence, outside-chair context, menu guard, active Survival lock and entire run/account preservation; retains existing sit, handoff and rollback checks. |
| `SpaceSurvival.Flight.FreeFlightLifecycle` | Native assertions succeed in 10.505 seconds, zero errors, **15 warnings** from the existing apartment `BP_Blinds` construction script reading absent Frame/Rope/other material properties. Updated briefing, practice launch/return and rejection during flight pass, but this result fails the zero-warning gate. Its direct preference call is a lifecycle fixture, not independent raw-input proof. |
| Save lifecycle | Station 2 discard expectations now use an informational briefing followed by a direct preference call. Existing explicit checkpoint continuation/failure guards remain. Use the process-owning save lifecycle harness and scratch storage; native execution pending lead. |
| Boarding images | `PhoenixBoardingModes30`: PASS, native process exit 0, nine actual 1920×1080 images at UI scale 1.0. Records Waves at the reached chair, applies one contextual input edge, verifies unchanged account/run/possession, records selected Free Flight, then performs the existing sit/handoff/takeoff. Independent visual review found the two UI defects below; capture success is not final UI acceptance. |

The shared `FlightCockpitTests30/index.json` reports three clean successes, one success with warnings, one failure and zero not-run tests, in 20.228 seconds. Besides the cockpit test, `ControllerTestingPreset` and `ControllerChaseRollIsolation` pass without warnings. The camera regression records 929.19 degrees of body roll with 0.000 degrees of nose/view rotation, 35.02 cm of bounded eye displacement and a largest 2.000-degree camera step through the pitch loop. `ChaseFraming` fails at 30 Hz, scenario 3, frame 52: hull-corner projection `(0.561, 0.960)`, depth 2713.8. Camera framing is handled separately; these mixed results do not establish overall flight acceptance.

Read directly for this update:

- `.agent/local/SurvivalQuality/Build30.log`, SHA-256 `6e242b54252a664fc600e782724b867759421709eb2863283fd0f24486a2efbb`.
- `.agent/local/SurvivalQuality/FlightCockpitTests30/index.json`, SHA-256 `08d22ef2ee47242f73ac459c9aa1275aaf5888195fa213d39a6d50c86f20bf05`.

The existing ignored `CaptureBoarding.ps1` is preserved for its historical eight-frame fixture. Its new sibling, `.agent/local/SurvivalQuality/PhoenixCockpit/CaptureBoardingModes.ps1`, checks the nine-frame sequence and the two pre-departure card states. Its SHA-256 at preparation is `a3f9db32554506e937c7f06040d4adc32abba95a2a79e5e76c67b4cffec2bbb4`.

## Actual boarding pixels and bounded correction

The Build30 capture spans 2026-10-07T01:53:28Z–01:55:00Z. Receipt root: `Artifacts/EndgameSoak/3a24658431444f28b41cf3db881b2b0d`, reached through `Artifacts/EnvironmentRefresh/PhoenixBoardingModes30.json`. Its project DLL SHA-256 is `c2c74f44b77af2827736c51cc9862ae6912804ffdf7904a277416d434d9dce9f`. Production saves and build artifacts remain unchanged, with no test save slots written. The route travels 2343.923 cm with zero recovery teleports, a largest 14.595 cm frame step and a 0.05973 cm seated-to-pilot handoff difference; fixture guards restore.

All nine PNGs were independently viewed. The card is absent along the ramp/cabin/stairs, appears at the actual chair showing Waves, changes to Free Flight before boarding starts, and disappears during the sit. The final image shows actual Free Flight takeoff. The selected highlight and sit/depart mode agree. The interior and character remain dark in the existing ship presentation; this capture does not accept their lighting or animation quality.

Two concrete presentation defects prevent final UI acceptance of Build30:

1. `SELECTED` touches the mode-name lettering. The source correction uses measured text heights, a minimum 53-pixel choice row and 134-pixel card, growing upward while preserving the bottom interaction prompt.
2. The cabin/stairs still display `Move closer to FREE FLIGHT`. `IsWalkerInsideShip` previously recognized only the legacy rear-entry region, X −940..−650. The source correction additionally recognizes the walker's actual `ParkedInterior` floor support attached to this ship root, so passage/stair guidance points to the cockpit. Runtime Launch service labels become `FLIGHT BRIEFING`. `IsWalkerAtPilotSeat` and departure eligibility remain unchanged; the expanded predicate's production caller is HUD guidance only. A reached-chair guidance assertion was added to the existing native regression.

These corrections pass source structure, formatting and patch checks, but require the next native build/regression and fresh card images. Build30's evidence is retained unchanged.

Capture receipt hashes:

- `capture.json`: `c3ec0b392c79a0b1eccc837f67536450e2b70c9b616136d5ebc1e5f592d64b2c`.
- `boarding.json`: `03e5050993e88c2b4bf8eee155b73daefaed5d8808ee27741335122a49e2c368`.
- `boarding-capture.json`: `2b1590e356f4860e6ec958ba751942bfc9afdaa958e15f182a9e1de59cd1a923`.

The rendered route remains a disclosed scripted fixture: one placement at the ramp, ordinary CharacterMovement afterward, contextual mode edge at the chair, and temporary pose holds for sit photography. It is not uninterrupted human play, physical-controller acceptance or performance evidence. Native build and cockpit input regression pass at Build30; unresolved suite findings, the prepared UI correction, saved-run process testing and rendered/owner acceptance must not be collapsed into those passes.

## Build31 superseding focused check and current prompt follow-up

Build31 succeeds in56.42s; its four-test native batch reports4 successes,
0 succeeded-with-warnings,0 failed and0 not-run. `PhoenixCockpitDeparture`
passes in9.458s; ChaseFraming, ControllerChaseRollIsolation and
ControllerTestingPreset also pass. The lead observes native exit0. Build31
retains the known engine/toolchain notices; a clean test report is not a claim
of a warning-free compilation or physical-controller comfort.

`PhoenixBoardingModes31` completes nine actual1920×1080 UI-scale1.0 images,
native exit0 and source/build/save preservation. Root is
`Artifacts/EndgameSoak/b95331e9d24b41499ed3521d17d2fc2c`; the pointer remains
`Artifacts/EnvironmentRefresh/PhoenixBoardingModes31.json`. Independent review of
Cabin, Stairs, Chair and ModeSelected confirms the selected caption no longer
touches the mode name. The title-case/readable-font correction described below
is absent from these Build31 images. Stairs correctly point toward the cockpit;
the middle cabin still wrongly says Move closer to Flight Briefing. Interior and
hero visibility also remain dark and unaccepted.

| Build31 evidence | SHA256 |
| --- | --- |
| `.agent/local/SurvivalQuality/Build31.log` | `47d2ce9e5f483edb2421395b0d50d6180cbde1af9f1473a89f8b34a62ae283ae` |
| `.agent/local/SurvivalQuality/FlightCockpitTests31/index.json` | `1da04347cf3dad0771546a12a2530efd6983a3e6ab6561cea11ccfed657a91e3` |
| Modes31 `capture.json` | `866a1f78346bbd38e85643fdb9b45cca2102e1f166b2722aec62e52b38e957dd` |
| Modes31 `boarding.json` | `46d0d09a8e579294f066230110bed29a3878070182789b6852ee09c3bd3dd768` |
| Modes31 `boarding-capture.json` | `1051c962ed9f48593319e5aad2a1a11ca21626167fe0daa1e1069ee5f8144f9d` |

The measured cabin sample is localX−637.857/Y−10/Z313.442, grounded on the
owned Phoenix Hull. It lies beyond the legacy rear-only X≤−650 entry gate and
does not stand on the added ParkedInterior support. `IsWalkerInsideShip` now
additionally recognizes actual non-null Hull floor support inside the measured
inner cabin envelope: X−940..940, capsule entirely inside Y±180, feetZ210..405.
The existing possessed-walker, grounded, parked ship, rear entry and attached
ParkedInterior checks remain. This predicate is guidance only; no pilot-chair
eligibility, departure authority or collision is broadened. The native cockpit
walk regression now requires observing supported middle-cabin traversal and
continuous cabin guidance, rather than testing only a reached-chair sample.

The station/cockpit prompt uses the existing engine readable font, plain action
labels and one centered nearby action card. It removes the persistent distance/
use-radius/complete-controls strip. Waves/Free Flight selection, press-edge
semantics, sit/depart inputs and selected preference stay unchanged. The cockpit
card says Choose your next flight / Change mode / Selected; cabin guidance says
Walk forward to the cockpit chair. Information-only fallback prompts reflect
actual access. The design-preview HUD similarly describes Read overview actions
honestly and presents one nearby E/X card; the full game's existing E/Y use
binding remains. Flight HUD and menus keep their current presentation.

The five saved source edits are unbuilt and native-unverified at this checkpoint.
Source structure40, scoped formatting and patch checks pass. Exact pre-change
Build31 sources and hashes remain in ignored
`.agent/local/StationRefinement/Prompt31Before`. Lead must build the frozen source,
run the cockpit departure regression and review new Cabin/Stairs/Chair images;
code presence does not establish guidance or readability acceptance. A separate
specialist owns the requested cabin lights and restrained mounted gear/display
scene. Saved maps and published package remain separate from this source work.
