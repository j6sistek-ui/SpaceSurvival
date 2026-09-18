# 0.1.19-alpha — the squirrel takes the deck

The hero is no longer a borrowed trooper standing in. The astronaut squirrel is in the game, lit so you can see him, with animation of his own.

## What changed

- **New hero.** Our own squirrel model was cleaned, re-rigged and rebuilt for the game: 199,000 triangles with three levels of detail beneath it, down from 1.96 million, on a 46-bone skeleton with a real five-bone tail. The rebuild closed holes you could have seen through at the hips when he sat, and fixed weighting that would have sheared the tail against his legs as he walked.
- **His own walk.** Authored for this game rather than borrowed: upright, heel-to-toe roll through the boots, arms in opposition, and the tail carrying its own follow-through. The stride is tuned so his boots exactly cancel the walking speed — no skating.
- **He stands still properly.** Standing used to be one frozen frame of the walk. He now has a real idle, and every twelve seconds or so he shifts his weight or glances around and settles back.
- **He jogs and runs.** Two more gaits, each picked by how fast you are actually moving, so the animation plays at close to its natural speed instead of the walk being sped up until his legs blur.
- **Footsteps.** There were none before; you walked the station in silence. Boots on deck plate now, with a little variation so it does not tick like a metronome.
- **He is lit.** His suit is genuinely near-black — about half as reflective as fresh asphalt — and every lamp in the hangar hangs above head height, so he was a silhouette on a bright floor. He now carries a warm key and a cool rim light of his own, confined to him. The share of him crushed to unreadable black went from 65% to 7%. They light *him* and nothing else: he is not meant to glow on the deck like a lantern, and no longer does.
- **He sits in the seat.** He had been floating 44 cm above the cockpit seat — a third of his own height — because he inherited the previous hero's seat position. It is measured against the cockpit itself now.
- **Arrival fix.** The hero was being put on the station facing due north regardless of the heading you flew in on. He now faces the station.
- **Leaving the ship** is the docking motion, then being outside it. The old climb-out lifted the character 125 cm over his own hull, and with no door on the ship there is nothing an animation can do about that yet. It is logged as a known gap rather than papered over.

## Known issues

- The tail hangs straight down the middle of his back while he stands still, so from directly behind — the camera you play from — it reads more like a fur cape than a squirrel tail. It reads correctly while he walks, and the idle fidgets break it up.
- No climb-out animation when you leave the ship; he simply appears outside it.
- No turn-in-place: he pivots instantly with the camera.
- His head does not turn and his wrists do not move while walking, so the hands read as mitts.
- During an idle fidget his foot can drift about 4 cm across five seconds.
- Carried over from 0.1.17: the station ALIEN WORLD doorway can intermittently ignore the interact key until the game is relaunched.

## Everything else

Unchanged from 0.1.18-alpha. The station, the flight model, combat, the paint bay and the asset library are as they were.

## Updating and feedback

Close the game and update through the itch app on the **windows-alpha** channel. Your saves carry over.

Most useful feedback this time: whether the hero reads at a glance while you walk around the station, whether the footsteps sit at the right volume, and whether he looks the right size next to the consoles and the ship.
