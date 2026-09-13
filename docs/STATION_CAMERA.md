# Station camera repair — 2026-09-13

Owner report: Station 1 was impossible to navigate because look did not turn the camera and backward movement made Acornaut face the viewer. The requested behavior is a fixed third-person position behind the character, with usable mouse/right-stick turning. The owner also requested vertical mouse inversion; Settings → Controls → Invert pitch already reverses vertical look for both mouse and controller. Its existing saved preference is preserved.

## Cause and change

`ASSPlayerController::PlayerTick` polls look after `Super::PlayerTick`. The old walker queued `AddControllerYawInput`/`AddControllerPitchInput` after the engine's rotation update; `APlayerController::TickActor` then cleared the queue before another rotation update. The fix applies the station control rotation immediately. The same yaw drives the upright character and movement, so backward movement and strafing no longer rotate the body toward the viewer. Pitch is bounded to -55/+35 degrees; the collision-tested spring arm and fixed 350 cm distance remain. Hangar and station entry initialize a modest -12 degree downward view. Authored disembark remains input-locked. The on-foot HUD now identifies mouse/right-stick turning.

Flight controls, sensitivity/inversion settings, saves, station services, animation assets and ship camera are unchanged. Direction-dependent locomotion animations remain provisional; this change does not claim animation or physical comfort acceptance.

## Verification

Source milestone: `f4bfec8bb955a9dab23300c55b1ca81c53442504`.

- Editor build passed in 5.12 seconds after correcting two test-only float/double overload errors in the initial build. Existing engine Character.h deprecation and nonpreferred compiler warnings remain.
- 38/38 Unreal tests passed at 2026-09-13 16:40:33 UTC, duration 2.694498 seconds, zero warnings/failures/not-run.
- New `SpaceSurvival.Integration.StationChaseCamera` uses actual arrival/disembark, then verifies both look directions at 30/60/144 Hz, immediate yaw, upright body alignment, backward/strafe direction, run speed, the actual camera behind the body, enabled boom collision and pitch bounds. This is scripted actor testing, not a physical controller test.
- Container formatting check, 23 source checks and whitespace check passed.

Package 14 succeeded (UAT 0h 2m 8s) and its [receipt](validation/2026-09-13-station-camera.json) binds archive hashes and test evidence. The visible native hangar showed a rear chase view, then a changed position/yaw still behind the body after user input. The attempted automation drag was rejected due to concurrent user input; no controlled injected mouse test is claimed. The user retained control of this isolated profile. Previous Package 13 performance measurements do not measure this revision.

## Duplicate Unreal project

The owner identified `C:/Users/j6sis/SpaceSurvival 5.8`, created separately from the authoritative `C:/Users/j6sis/SpaceSurvival`. It contains copied Git history, artifacts, intermediate files and local experiments. Tracked source/content match the prior revision; only the four new camera source edits differ. Its project descriptor has a local engine GUID and generated solution files. No unique `.agent/local` work was found.

Two differing account/suspension saves were copied byte-exact to `Artifacts/RecoveredSaves/20260913-164011-UE58Copy`, without replacing live saves. The duplicate was not deleted by the agent. Close its Unreal window before removing that exact duplicate folder. The copy's saves have not been adopted as live saves. Use the original packaged launcher for playtesting; opening a `.uproject` is an editor workflow and can offer conversion/copy dialogs.
