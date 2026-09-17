# 0.1.18-alpha — a station you fly into, a paint bay, and a field that fights back

This tester update rebuilds the station, adds a ship painter, and repairs a defect that had been quietly thinning the asteroid field. Phase 1 remains in development.

## What changed

- **The station is one body now.** It was a box parked in front of a larger hulk. It is now a single structure, a disc and tower with a dock module under the rim, and the hangar mouth you see is exactly the opening you can fly through. What looks solid is solid, and nothing solid reaches into the hangar or the approach lane.
- **The hangar has a floor plan.** Mezzanines, stairs, banners, cargo stacks, a gantry hung from the ceiling and warm working light. The flight lane through it is kept empty by rule.
- **Paint bay.** A ninth station service. Your ship's hull is split into four sections and each takes one of ten finishes, or the factory scheme. It is saved with your account and applies to the ship you fly and the ship parked in the bay.
- **Flight feel.** A layered thruster plume, a camera and screen effects that respond to thrust, and shots that vary slightly in pitch so sustained fire stops sounding like one looped sample.
- **The field.** Hazards now move fast enough to matter and lead your path instead of drifting past it, and scenery meshes you could fly through are solid.
- **Button prompts** follow the device you are using.

## The repair you will notice most

Hazards are placed ahead of you at a distance that grows with your speed, and removed once they are too far away. After hazard speed was raised, those two distances overlapped: part of what the game placed was removed again a frame later, and the faster you flew, the more went missing. At Wave 10 the gravity well that the climax is built around never appeared at all, and accepting the salvage signal during a boost could make its third cache vanish so the objective could not be finished.

That is fixed. Nothing is removed for being where it was placed, the Wave 10 gravity well is brought back if you lose it by turning away, and fields no longer outrun you when they appear during a boost. **The field is denser and more dangerous than in 0.1.17, most of all while boosting.** If it is now too much, say so: it was tuned against the thinned version.

## Known issues

- The station walker is still the temporary trooper. The squirrel hero is planned, not built.
- The service arm beside the parked ship is a placeholder, and the station's hull plating and amber mouth frame are provisional.
- The ALIEN WORLD doorway defect from 0.1.17 (ignoring the interact key until a relaunch) has logging added but is not confirmed fixed. If it happens, please report whether it was the home hangar or a mid-run station.
- Shooting audio, thruster shape and hazard tuning are still waiting on owner choices.
- Natural docking, controller comfort, five- and ten-wave balance, audio mix, representative performance, clean-PC installation and an update that preserves saves all remain unverified by hands-on play.

## Updating and feedback

Close the game and update through the itch desktop app on the existing **windows-alpha** channel. Browser downloads do not provide the app's managed update. Unreal Editor and Visual Studio are not required. If Windows reports a missing Visual C++ runtime, use the bundled Microsoft runtime installer action. Your account save moves to a new version on first launch; older saves still load.

Checked before release, by script rather than by play: 54 automated Unreal tests, a packaged Wave 10 run (the gravity well, asteroids and enemies were present together for 39 of the climax's 40 seconds; in the broken build it was 0), a packaged Station 5 run through wormhole, docking and the walk out, and a dependency audit of the cooked content. These do not establish game feel or frame rate.

Please report version **0.1.18-alpha**, controller or keyboard and mouse, GPU, the wave or station, what you expected and what happened, and a short clip if you can. Most useful this time: how the field feels at cruise and while boosting, whether flying into the station reads as the way in, and the paint bay.
