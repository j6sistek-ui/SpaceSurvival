# Wave route flight — October 29, 2026

Owner-directed continuation of the bumper/camera repair in PR102, tracked under RPT-20261029-01. The [earlier control receipt](2026-10-29-flight-controls-camera.md) remains evidence for the first repair only; its editor hash and six-test result do not prove the later wave changes.

## Behavior

- Flight/Breathing/Climax use a prescribed forward route with an invisible 120m-wide by 80m-high ship-center travel area. These dimensions are `USSPhase1Data` defaults, not authored tunnel geometry.
- Ordinary automatic cruise is 85% of the run's upgraded cruise speed; RT/W/S raises it to full cruise, braking targets 45%, and boost retains the existing multiplier/resource rules.
- Left stick/mouse plus A/D/R/F drift across the route. Outward resistance begins at 60% of each half-extent and increases smoothly; releasing input damps lateral movement, and inward commands retain full response. Bumpers remain signed dash/roll controls.
- The camera permits visible lateral ship movement, follows gently at screen edges, and retains route orientation during roll. Wave framing has room for that movement; boost does not add camera zoom or shake in waves.
- Hazards use stable route axes and check for escape space inside the play area. Ordinary debris favors its sides; offers remain reachable. Persistent scenery reserves the route when admitted, without moving existing visible instances.
- Free Flight and station approach retain unrestricted nose steering, coasting and free-look. The wormhole retains its existing transit controller. Route coordinates survive world rebasing; saves, progression and five-wave station cadence are unchanged.

## Existing resources and design reference

The supplied D-drive archive is cold recovery storage. Its indexed files contain no newer flight-controller source or last-run log. The installed ShipCore spline/path actor is an authoring option, but its autopilot also writes thruster/gyro inputs and is not enabled alongside the existing native driver. The existing bounded wormhole movement is reused as the architectural pattern. `Clouds_Tunnel_Loop` is a visual asset and is not used: the owner explicitly requested an invisible gameplay boundary.

Dead/soft camera zones are an established composition pattern: the target moves within the dead zone, then the camera follows with damping in the soft zone. Reference inspected October29: [official Cinemachine Position Composer documentation](https://docs.unity.cn/Packages/com.unity.cinemachine%406.6/manual/CinemachinePositionComposer.html). This is a design reference, not a Unity dependency or a claim of identical implementation.

## Verification

The canonical UE5.8.4 Editor rebuild passes in22.82s after an initial181.02s compilation identified a camera-local name hiding an inherited member and a test's `TObjectPtr` deduction error; both are corrected. All10 focused native cases pass with0failures,0skips and0warnings: the six original controller cases, wave movement, route lifecycle, Director admission and persistent scenery reservation.

Measured wave movement spans38.8% of normalized screen-coordinate space while the camera and nose turn0.000degrees. The projected visible-mesh bounds retain8.20% minimum view margin against4% required during movement, edge dodges and both rolls. Maximum transient boundary overshoot is30.69cm before the next swept correction. Tests also verify progressive outward slowdown, responsive inward reversal, release damping, automatic cruise/brake, mouse/keyboard/gamepad axis agreement, breathing/wormhole/approach transitions and world rebasing. Director tests cover fixed-axis placement, immediate-boost reaction time, escape rejection and reachable offers. Scenery tests cover whole-group rejection, stable surviving transforms, phase changes, cell return and rebasing.

Editor module SHA256: `f0170c201e567fcb446045a4935efa369d30fa7fb938b682024020b3d15e4f6d`. Source structural checks50/50, digest tests13/13, documentation consistency and scoped formatting/whitespace pass. Local Docker is unavailable; portable container verification belongs to CI. Existing engine deprecations, nonpreferred compiler and HairStrands dependency warning remain outside this change.

This is the movement-test binary identity. The later presentation-only HUD adjustment has a new rebuilt binary and fresh flight/station captures, recorded in the [HUD spacing receipt](2026-10-29-hud-spacing.md); it supersedes this hash as the installed Editor build without changing the movement implementation.

Fourteen affected existing integration cases also pass:12clean and2with warnings. They cover FreeFlight lifecycle, Director pressure/trajectory/readability/volley/admission/arrival, hazard lifetime and scenery stability. Warnings arise from an HTTP connectivity timeout, refused station-warp placement and missing material references in the existing apartment blinds; no test assertion fails. The startup GameFeatureData scan-configuration errors also occur in the earlier pre-wave flight log and are outside this change. These are recorded rather than suppressed.

Tests use isolated profiles, real controller/ShipCore/Chaos and NullRHI with the same unused-plugin exclusions recorded in the earlier receipt. Original files and scoped canonical integration hashes are kept locally under `work/wave-backup`. Two offscreen Wave1 captures timed out at120seconds amid shader/PSO/texture preparation; partial images and failed receipts are retained, not counted as completed captures. A local copy of the existing harness increases only the wall-clock allowance to300seconds and pins the same canonical project path; its hash/change record is `work/wave-capture-harness.json`. The gameplay sequence, image requirements, save checks and production script remain unchanged.

The extended capture completes successfully in107seconds with all four1920x1080 frames (Cruise/Turn/Boost/Brake), unchanged binary identity, unchanged production saves and no test save slots written. Local receipt: `C:/Users/j6sis/SpaceSurvival/Artifacts/EndgameSoak/078092d69adc4b9b86c3ce6816698c20/capture.json`. All four images were inspected: the Phoenix moves visibly to the right during drift, remains fully framed, and the scene retains open space and side debris without walls/route markers. Normal collision/damage and brake-overheat behavior remain live. The scripted29-second sequence is visual evidence only, not a natural playthrough or FPS measurement.

Physical-controller feel, rendered natural play, representative performance and packaged behavior are not yet accepted. This is a synthetic regression/capture record; no complete player journey or owner acceptance is claimed. Packaged/itch builds are unchanged.
