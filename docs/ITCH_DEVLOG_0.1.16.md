# 0.1.16-alpha.1 — new starter ship, furnished station and deeper space scenery

This tester update refreshes the ship, station and surrounding space using the newly supplied asset packs. Phase 1 remains in development; this release is a visual review milestone.

## What changed

- The default starter now uses a provisional closed-cockpit ship, with fitted visual hardware for its existing upgrades and utilities. Our regular artist will develop the final iconic starter and hero.
- Space includes three blended regional nebula backgrounds, more varied decorative asteroids, smaller dust particles, thin atmospheric volumes and distant structures. Decorative scenery does not increase the early-wave collision hazard count.
- Stars are dimmer and vary more in brightness, helping the ship, asteroids and station remain the focus.
- The station has furnished workbenches, storage, terminals, two idle robot staff and additional lighting. Service labels face the camera and remain readable in shadow.
- Station decoration is saved in an editable Blueprint so the layout can be adjusted without regenerating it on every authoring pass.
- Weapon and impact effects have been integrated, and a short-range projectile cleanup defect was corrected. Combat readability still needs playtesting.
- The wormhole entrance stays ahead of the travelling ship during the transition. Its final arrival impact and sense of entering somewhere unfamiliar remain unfinished.
- Release packaging now excludes local saves, settings and logs. The game continues to use the existing itch launch option that stores player saves outside the installation.

## Known issues

- Shots, hits and deaths may still be difficult to distinguish. Explosion activation is verified, but the packaged capture has not yet established a visible fire/smoke plume.
- Ship identity, exhaust placement, hero animation and station composition remain provisional.
- Controller comfort, keyboard/mouse parity, event and depot clarity, natural five- and ten-wave balance, audio and replay appeal still need hands-on review.
- Representative performance, lower-end hardware, clean-PC installation and an actual itch update with preserved saves remain unverified.

All 19 hands-on acceptance cases remain open in the [single issues and playtest log](https://github.com/j6sistek-ui/SpaceSurvival/blob/main/docs/KNOWN_ISSUES.md). A completed build or screenshot does not close those checks.

## Updating and feedback

Close the game and update through the itch desktop app on the existing **windows-alpha** channel. Browser downloads do not provide the app's managed update process. Unreal Editor and Visual Studio are not required to play. If Windows reports a missing Visual C++ runtime, use the bundled Microsoft runtime installer action.

The C++ changes passed 49 Unreal tests. The later star-material adjustment was separately authored, cooked and captured; the resulting package passed its dependency audit and 20 scripted visual captures. These checks do not establish game feel or representative frame rate.

Start by setting your preferred sensitivity and pitch direction, then check the ship view during ordinary turns, boost and brake. Please report version **0.1.16-alpha.1**, controller or keyboard/mouse, GPU, wave or station, expected versus actual behavior, and one short reproduction or clip.
