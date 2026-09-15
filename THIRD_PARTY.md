# SpaceSurvival asset acknowledgements

## Milky Way sky

NASA/Goddard Space Flight Center Scientific Visualization Studio. Gaia DR2: ESA/Gaia/DPAC.

Source: [Deep Star Maps 2020](https://svs.gsfc.nasa.gov/4851/), released 2020-09-09 and updated 2022-08-12. The sky uses the native 8192 x 4096 Milky Way background, converted to display RGB8 without resampling or artistic edits. Bright Hipparcos/Tycho foreground stars are omitted in this background; faint Gaia points remain.

Reuse information: [NASA SVS policy](https://svs.gsfc.nasa.gov/help/), [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) and [Gaia DR2 credit instructions](https://gea.esac.esa.int/archive/documentation/GDR2/Miscellaneous/sec_credit_and_citation_instructions/). NASA SVS identifies its content as public domain unless otherwise noted. No endorsement by NASA or ESA is implied. No agency logos or constellation overlays are used.

The source project's `ContentSource/ThirdParty/NASA/MilkyWay2020` directory retains the exact source URL, hashes, conversion record and reuse notes. The original data source is not claimed as SpaceSurvival artwork.

## Rock Face material

Photography: Greg Zaal. Processing: Dario Barresi. Provider: Poly Haven.

[Rock Face source](https://polyhaven.com/a/rock_face), [CC0 license](https://polyhaven.com/license). Original 2K diffuse, ARM and DirectX normal maps are retained unchanged. The game applies its own material settings and mapping.

## Metal Plate material

Author: Rob Tuytel. Provider: Poly Haven.

[Metal Plate source](https://polyhaven.com/a/metal_plate), [CC0 license](https://polyhaven.com/license). Original 2K texture maps are retained unchanged. The game applies its own material settings to the station deck.

Source and reuse records were checked on 2026-09-13. These acknowledgements do not change the respective source terms.

## Owner-supplied Fab presentation

- Asteroid Library — Makemake: asteroid meshes and ambient cloud materials.
- Sci-Fi / Futuristic Corridor — Leartes Studios: station interior components.
- Space Station 4 — Gerardo Justel: exterior body derivative, preserving PBR maps; detached light-point geometry omitted and textures reduced to 2K.
- [Niagara Examples Pack — Epic Games](https://www.fab.com/listings/0e188eca-4e54-4fb2-a9ed-d8b8a565e600): engine ribbon trail evaluation/integration.

The September 14 visual pass additionally authors and imports derivatives from these locally supplied resources. Native receipts verify 36 ship/module assets, station/cargo imports and combat effects. The private regional sky and Package 4 were audited and captured; owner visual acceptance remains open. The September 15 audio/character follow-up has editor and automation evidence but no new package. Phase 1 remains PARTIAL:

- [Space Ship 02 Modular Pack — Havolk](https://www.fab.com/listings/8d658f0c-4d5e-4ba5-9470-d7c9d7823a10): source meshes and PBR materials for the existing Pursuer/Flanker pair and visual attachments representing the existing ship upgrade tracks and utilities. The original player hulls and supplied pilot retain their existing provenance and remain unchanged by this derivation.
- [NebulaFantasy — Marek Brzezinski](https://www.fab.com/listings/5a7278e8-70cc-4db9-a350-ce4e1d0c7277): selected regional sky and star cubemaps. The project supplies its own blend material and transition logic.
- [Sci-Fi Weapons VFX All In One — Pautinka](https://www.fab.com/listings/4dcaa163-a3d2-403b-baf6-30c78df942de): selected beam, muzzle, impact and anomaly Niagara sources; private derivatives use project allegiance colors, bounds and lifetime limits.
- [EXPLOSIONS — Sidearm Studios](https://www.fab.com/listings/ce3c49db-b637-469e-a507-cf712d194aa7): selected small enemy-explosion Niagara source. The project supplies bounded spawning/lifetime and instance-size control.
- [Space Station 3 — Gerardo Justel](https://www.fab.com/listings/192bc415-7e24-4515-993d-fc55dd8a4e53): distant ambient-structure derivative; detached light-point geometry removed and texture dimensions capped at 2K. Existing Station4 remains the serviced destination.
- [The Corner — Gerardo Justel](https://www.fab.com/listings/9bbf59e4-bd2e-4df3-8485-2925622ec046): static closed-pose service cargo; source studio floor omitted and texture dimensions capped at 2K. The source animation is not claimed as an implemented interaction.
- **Robot scout R21 — Dan4eZ:** selected mesh and matching idle clip supply two nonblocking station staff. No robot locomotion, example Blueprint, new AI or new interaction system is adopted.
- **ElectronicProps Vol1 — Defect-Ant:** six selected mesh assets supply seven static station props: two meters, two switches, two annunciators and one lamp. Existing services and physical layout remain authoritative.
- **Spaceship Sounds / `cplomedia_spaceship`:** ten selected local sounds supply provisional engine, weapon, impact, pickup, alarm, station and enemy/debris roles. Runtime lookup preserves the generated fallbacks. Exact seller/listing metadata was not established from local files; the owner should retain the Fab entitlement record.
- **Sci-Fi Space Character:** selected local skeletal mesh and matching walk/exit animations supply a temporary station hero, with the original Acornaut fallback when the pack is unavailable or incompatible.
- **Heavy Space Trooper:** selected local skeletal mesh and idle animation supply one nonblocking station staff member.
- **Customizable Drone Companion:** a selected local drone mesh and idle animation supply one nonblocking station staff member.
- **Cosmic Material:** local materials and example meshes are exposed to the owner workshop; applying or adopting a material remains an explicit scene choice.

For the later owner-editable station follow-up, **[Modular SciFi Season 1 Starter Bundle — Jonathon Frederick](https://www.fab.com/listings/86913335-3c75-42bf-8404-54fe9d9d7396)** supplies selected command-center/prop meshes and material dependencies. The September 14 source-preparation check verifies four staged folders under `Content/StarterBundle`: `ModularSci_Comm`, `ModularScifiProps`, `ModularSciFiMats` and `UE4_Assets`. All 1,153 staged files (1,191,114,458 bytes) match the owner's downloaded-project originals by SHA256. The local manifest identifies the bundle and UE4.18 build; the primary listing confirms the creator and notes included Unreal Engine example content. Staging does not establish the final selected layout, rendered appearance or package inclusion; those require the follow-up authoring and validation records. This credit covers the selected source subset, not wholesale adoption of the bundle's example levels.

The inspected [Sci Fi SPACE STATION Kitbash — Figur Assets](https://www.fab.com/listings/9af3878b-6c91-4e20-99e4-c5f1fd09baad) selected-object derivative remains a private, unadopted station candidate. **Wormhole Portal — Team Beaver**, installed engine plugin Version 1.0 for UE5.8/Win64, was evaluated but is not enabled or integrated in this project. It is separate from the Pautinka anomaly visual source; no Team Beaver portal-renderer/transit integration is claimed.

The robot and electronic-prop selection is integrated in station source and listed in an authored cook label; rendered acceptance and actual cook/archive verification remain open. The inspected [Sci-fi Container Game Free 04 — CGGame](https://www.fab.com/listings/977a1785-14ce-4aa3-becd-39957e429dbe) remains a source-only candidate. Downloaded files and the word "Free" in a title do not change source licensing or establish active-game integration.

These assets were supplied from the owner's local Fab library. Original packages and licensed derivatives remain outside public Git. Source roots include the ignored `User downloaded assets/VaultCache` and staged `Content/Spacecraft_Pack`, `Content/SpaceNebulaFantasy`, `Content/Sci_Fi_Weapons_VFX_AIO`, `Content/PyroVFX`, `Content/Robot_scout_R_21`, `Content/Defect`, `Content/SciFITrooper_Man_03`, `Content/Heavy_space_trooper`, `Content/CosmicMaterial` and the selected `Content/StarterBundle` folders above. New project derivatives, including selected audio, drone and cook labels, remain under ignored `Content/SpaceSurvival/Licensed`; private preparation files and source hash records stay in ignored `Artifacts` and `.agent/local`. These paths identify storage, not a license grant or a public download. Their respective licenses remain applicable; these credits do not grant redistribution rights to raw asset files. License tier, purchase price and entitlement records are not published here. RPG Environment VFX and Free Galaxy Shader were inspected but are not claimed as adopted runtime content.
