# Known issues and limitations

Recorded 2026-09-13. Phase 1 remains **PARTIAL**. An implemented source path is not a validated player experience.

## Environment blockers

- Full Unreal Engine, UBT/UHT, Windows C++ compiler and Windows SDK are absent from the inspected locations. The `UE_5.8` name belonged to plugin/installation metadata directories. `Build.ps1 -Target Editor` stopped at missing `Build.bat`; no Unreal compiler ran.
- No generated Unreal map/assets or Windows executable exists in this delivery. Source authoring scripts are executable Python, but their Unreal APIs and engine-version compatibility remain unverified.
- Consequently real keyboard/mouse and controller input, flight feel, collisions, AI, complete ten-wave play, station visits, process-restart saves, music/audio mix, and frame-time performance cannot be claimed.

Docker's initial stale runtime-socket failure was superseded by a working daemon and successful portable domain builds/tests. It is no longer an active blocker for those checks.

## Implementation and quality gaps

These are actual open implementation/presentation items; they are not labelled impossible merely because the engine is absent.

1. **Commercial Hybrid presentation is not achieved.** The 26 authored source meshes are original provisional low-detail geometry, with simple PBR/emissive material authoring. There is no approved cinematic space treatment, detailed station dressing, high-detail hero spacecraft, Niagara production VFX, or verified polished HUD. The readable geometry/source previews are not gameplay screenshots.
2. **Character integration needs engine work.** The supplied textured, rigged model and walk animation are preserved, inspected in Blender and referenced by runtime code. Scale, front axis, collision fit, foot contact and walk/run blend are not verified. The cockpit currently places the skeletal mesh in its reference pose; there is no authored seated pilot pose, hand contact with controls, reactive animation, or exit/entry sequence. Docking changes possession into a walker without an exit animation.
3. **Station NPC/audio treatment is rudimentary.** Mica has a named diegetic vendor interaction and narrative text, but no distinct animated NPC actor/voice. The hub includes terminals, servicing-arm movement, ambience and a beacon interaction; it is not a convincing lived-in commercial station. Announcements and Acornaut lines are text; recorded dialogue is absent. Synthesized effects/music require a listening/mix pass.
4. **Content authoring remains partly code-owned.** `DA_Phase1` exposes core flight, damage, wave and economic values; actor/component fields are editable. Exact rosters, radius choices, reward offerings, station layout and menu layout still live in native code. Designer-authored encounter/weapon/hazard assets and Blueprint presentation subclasses are not fully wired through a content catalog.
5. **Flight/control verification is open.** Banking is derived from steering and lateral movement; independent manual roll is absent. Mouse aim follows the chase camera/ship steering. Controller bindings and pause-menu input are source-wired, not hardware-tested. Full remapping is absent. Input/action observation now completes tutorial hints, but timings, messaging and persistence need playtesting.
6. **Balance/fairness is unproven.** Domain station income permits about three initial upgrades plus a repair without active income, but actual pickup/kill/event availability and later tier priorities need full-run tuning. Spawn admission reserves clearance and reaction time; it is not proof against unavoidable states. Wave 10 must be played to verify the combined gravity/asteroid/enemy pressure remains readable.
7. **Save transaction durability needs process tests.** Payload round trips and malformed states are domain-tested; the UE SaveGame adapter has not run. Suspension is consumed before play, death writes the awarded run ID, corrupt account data blocks overwrite, and failed death writes block a new run. Crash/power-loss behavior of platform SaveGame writes is not verified. Corrupt-account recovery currently requires restoring a backup outside the game; no recovery UI or rolling backup scheme exists.
8. **Station 2 is an explicit slice boundary.** Further launch is unavailable; services and Save & Quit remain available. A labelled shell action can abandon the slice without death XP and return to a fresh hangar. This preserves the full game's no-final-wave concept but does not satisfy indefinite play or Station 2 relaunch. No owner approval of this boundary interpretation is implied.
9. **UI/accessibility requires layout checks.** A native Canvas HUD/menu supports mouse and controller navigation, scaling and text/shape cues, but wide text, small displays and maximum UI scale have not been rendered in Unreal. No verified resolution matrix, focus accessibility or text localization is delivered. A simple last-run summary is present; a multi-run history view/cosmetic presentation is not implemented.
10. **Performance is unmeasured.** Runtime uses native actor spawns and bounded actor iteration rather than a validated pooling strategy; synchronous asset loads may hitch on first use. CPU/GPU frame capture, packaged memory use, shader/cook behavior and 60/120 FPS results are open. See PERFORMANCE.md.

## Static review fixes already applied

Source review corrected double cannon/buff scaling, unused acceleration upgrades, unreconciled tuning values, repeated death-to-results on hangar entry, duplicate walkers on resume, pre-validation suspension consumption, unreadable-account overwrites, failed-death-save bypass, a blocked docking corridor/unit mismatch, paused-menu tick setup, unchecked offscreen marker coordinates, stale world-origin caches, station volume settings, and overlapping reward claims. These corrections still need Unreal verification.

No multiplayer, Steamworks, cloud saves, leaderboards, inventory, extra enemy/weapon/hazard/event/utility families, or authored post-Wave-10 progression was added.
