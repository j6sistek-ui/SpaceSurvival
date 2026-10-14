# Phoenix chase-camera comfort repair — October 6, 2026

## Scope and cause

Owner reported camera spinning around the Phoenix while turning or holding bumpers, causing dizziness. The current owner play log identifies the active 2484 cm Stellar Phoenix on UE5.8.3. This repair changes camera follow/framing only; ship input, forces, angular rates, roll/evade behavior and collision remain unchanged.

The old pitched spring arm composed its relative pitch with the rolling physics parent before discarding the resulting Euler roll. A roll therefore changed chase yaw/pitch despite `bInheritRoll=false`; its elevated local anchor also revolved with the hull. Reconstructing zero-roll Euler angles alone would introduce discontinuities at vertical pitch.

`USSChaseCameraArm` instead transports a continuous frame from changes in parent forward direction after physics, then applies authored pitch and deliberate free-look. The authored anchor is captured once and follows this frame. Completed docking resets orientation without recapturing the already-compensated anchor. Only the physics Phoenix opts in; the classic path delegates to the original spring-arm behavior.

## Native evidence and retained failure

All receipts below are ignored local files under `.agent/local/SurvivalQuality/`. Root observed the stated process exits. These are isolated synthetic actor/component tests, not physical-controller or visual-comfort acceptance.

- **Build29:** native build PASS, exit 0, 168.15 s. This predates the completed-docking reset/classic opt-in follow-up.
- **Build30:** native build PASS, exit 0, 14.02 s. It includes reset/anchor preservation and classic isolation; retained engine/API C4996 warnings are not presented as new camera failures.
- **FlightCockpitTests30:** process exit 0, but automation report has one actual failure and must not be summarized as a full pass. `ControllerChaseRollIsolation` passes with no warnings: 929.19 degrees of ordinary held-bumper body rotation, 0.000-degree nose/view change and 35.02 cm maximum relative-eye displacement. The full pitch loop with simultaneous body bank measures a maximum 2.000-degree view step, including both vertical poles. Explicit free-look, release, non-coplanar flight → docking → next-takeoff framing assertions also pass.
- **ChaseFraming failure:** with the new stable frame and the former +5-degree local camera tilt, the 30 Hz steer/strafe scenario reaches projected Y=0.960 at frame 52, violating the unchanged 4% hull margin. `ChaseSurvey30` records only 0.003 minimum margin at 30 Hz and an actual screen-edge breach at 60 Hz. This exposed a real silhouette-framing limitation; the acceptance margin was not widened.
- **ChasePitchCandidate30:** the same Build30 binary with the existing `-SSChasePitch=-3` override passes `SpaceSurvival.Flight.ChaseFraming` cleanly, with root-observed exit 0. Worst hull margins across five scenarios are 0.155 / 0.152 / 0.151 at 30 / 60 / 144 Hz. Maximum measured arm shortfall is 231.0 cm (0.0608 of the arm), below the existing hull allowance. Arm length and flight dynamics are unchanged.

The source now adopts the measured -3-degree camera-local pitch, preserving the -18-degree arm and 3800 cm base distance. The raw-bumper regression additionally projects all eight corners of the actual visible skeletal hull after every ordinary physics tick throughout both held rolls. It reports the complete minimum and requires the existing hull margin rather than stopping at the first threshold breach.

**Build31 / FlightCockpitTests31:** build PASS, exit 0, 56.42 s; root also confirmed automation-process exit 0. All four tests pass with zero warnings/errors: `ChaseFraming`, `ControllerChaseRollIsolation`, `ControllerTestingPreset` and `PhoenixCockpitDeparture`. The adopted default retains the 929.19-degree physical roll with 0.000-degree nose/view change and 35.02 cm maximum relative-eye displacement. Full held-roll hull margin is **0.0442**, above the unchanged 0.0400 requirement; maximum pole-crossing view step remains 2.000 degrees. This closes the native framing failure above while retaining its original failed receipts.

| Local automation report | SHA-256 |
| --- | --- |
| `FlightCockpitTests30/index.json` | `08d22ef2ee47242f73ac459c9aa1275aaf5888195fa213d39a6d50c86f20bf05` |
| `ChaseSurvey30/index.json` | `e04f7a4b93b5d2472befea33d8928d45b9e01b0c2f48b4c2ed4398657991cf13` |
| `ChasePitchCandidate30/index.json` | `4916971dbac8d49f900eb98307d6b0c430c067bfe1caf31a3d1836d7ff6ea2ae` |
| `FlightCockpitTests31/index.json` | `1da04347cf3dad0771546a12a2530efd6983a3e6ab6561cea11ccfed657a91e3` |

## Verification boundary

Native clang-format, `CheckProject.py` (40 checks) and scoped `git diff --check` pass. Independent source review found no remaining blocker in the orientation-only docking reset, independent anchor latch or classic fallback. No source/vendor material, station map, save schema, packaged build or release is changed by this camera work.

Pending: actual rendered turn/roll inspection and owner comfort retest. Existing `CaptureSpaceLook.ps1 -Sequence` commands real turn/boost/brake input but does not command bumper rolls, so those images alone cannot validate the reported roll problem. Phase 1, controller feel, performance and packaged acceptance remain separate.
