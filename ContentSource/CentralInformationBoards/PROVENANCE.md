# Central information boards

Two original, deterministic visitor guides prepared on 2026-10-07. These are information boards, not advertisements. The owner's central limit of one or two ads does not limit useful information boards; two boards are the starting design.

`Generate.py` produces the SVG typography sources and matching 1960 x 1000 PNGs with Pillow and the owner's installed Segoe UI regular/bold fonts. Font bytes are recorded in `manifest.json`; fonts are not distributed or installed. The preserved sources match the original reviewed drafts. No generated illustration, external artwork, font binary or Unreal package is included.

## Copy evidence

| Copy | Implemented source |
|---|---|
| Operations, Crew Archive, Social Lounge, arrival concourse and lower passage | `Scripts/RefineStationOperationsAtrium.py` room/direction tuples |
| Ships/weapons at home; upgrades/contracts at Survival stops; pilot record | `Source/SpaceSurvival/Private/SSStationOutpost.cpp`, terminal-to-service panel mapping |
| Character choice at Crew Wardrobe | `Source/SpaceSurvival/Private/SSGameMode.cpp`, Crew Wardrobe handling |
| Home Waves/Free Flight and Survival-stop continuation through the cockpit chair; conditional Continue saved Survival | `Source/SpaceSurvival/Private/SSGameMode.cpp`, departure and saved-run handling |
| Landing-pad readiness; Free Flight protects Survival progress | `Source/SpaceSurvival/Private/SSGameMode.cpp` docking handling; `SSGameInstance.cpp` session/save handling |

There is no powerup purchase, online leaderboard, universal wall arrow or new interaction claim. Preview information terminals do not themselves grant the services described.

## Native recipe

`Scripts/RefineStationCentralInformation.py` adopts or places two complete, normally oriented SciFiCorridor monitors on the existing NE/SW solid diagonal wall stacks. It preserves the original `MI_Assets` housing material and all other direction panels/reception consoles. The original insert's measured UV0 rectangle is normalized by the existing private master; an additional 0.15 cm in source-local Y avoids its coincident housing surface. Uniform scale is 3. Artwork fits the native chamfered aperture without stretching or cropping.

The recipe reuses exactly two private textures, two private instances and one private master under `/Game/OutpostSandbox/StationRefinement/CentralInformationBoards20261007`. Those local Unreal assets must be staged separately; this folder contains no `.uasset` copies. Read-only `check_adoption` precedes adopt/replay; stable actor tags reject partial/duplicate assemblies and preserve exact rollback. The recipe neither imports assets nor loads/saves a map. Brightness 8 matches the root-accepted, unsaved three-view trial; fresh saved replay and owner acceptance remain separate. The root resolves the held T display trial and backs up the actual shared map before saving. Source presence is not pixel acceptance.

At the 2026-10-07 handoff, root saved those five private assets separately. The four board actors remain in the unsaved editor trial; the shared Main map has not been saved by this pass. Source adoption/replay validation is still separate from that asset save.
