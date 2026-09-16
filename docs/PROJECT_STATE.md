# SpaceSurvival project state

**Phase 1: PARTIAL.** The visual pass is merged and itch **0.1.16-alpha.1 / build 1979965** is ready on windows-alpha (verified September 15 UTC / September 14 local). [PRs #11–16](https://github.com/j6sistek-ui/SpaceSurvival/pulls?q=is%3Apr+is%3Amerged+11..16) are merged; PR #14's Station Workshop merge is `e44decdd`, and PR #15's owned audio/character/staff merge is `4aa4656`. These source changes do not alter the published game binaries. [Open work and your next review](KNOWN_ISSUES.md) owns active priorities, systematic action IDs, owner checks and closure status. This page owns the source/build/release and storage explanation.

## September 16 continuation is unfinished

PR17 also carries orbital-wreck composition work based on the owner's accepted concept. The editor lock cleared, the Editor build succeeded, and three private derivatives were imported. Twelve authored major masses, flight-only directional lighting and a private directional sky grade were rendered through successive comparisons. The first independent review rejected target completion; ACT-03 remains open and PR17 remains draft. The latest valid capture includes four 1080p views and 84 timestamped samples, with screenshot timing limitations. [Iteration receipt](validation/2026-09-16-orbital-wreck-review.json) binds source/content/capture identities and validation; [preparation receipt](validation/2026-09-16-orbital-wreck-preparation.json) retains the earlier blocked state as history. EXE and itch unchanged.

## Source, build and release

| Layer | Last verified state | What it means |
| --- | --- | --- |
| GitHub source | PRs #11–16 merged; main `f2fae331bd32b8c3a76242f0ce74deb7f0a4951d` verified September 15 | Documentation foundation, visual pass, release guard, Station Workshop and the owned audio/character/staff integration are in main. The systematic-gap action log from PR16 is now in main. PR17 remains unmerged. Source merge and itch publication remain separate. |
| Current unmerged slice | PR17 on `codex/flight-combat-space-slice`; latest implementation `16007ab` (earlier slice `b6c58b8`) | Flight/combat/space source and editor evidence only. Editor build, 49/49 headless tests, 1/1 rendering-enabled Niagara lifecycle test, container formatting and fixed captures pass within their recorded limits. The [slice receipt](validation/2026-09-15-flight-combat-space-slice.json) lists selected/rejected owned candidates and open acceptance. Package 4, the local EXE and itch remain unchanged. |
| Documentation foundation | PR #11 merged | Canonical state/open-work navigation and PR documentation review are present. Required status-check enforcement remains a separate open repository-setting task. |
| Current visual source | PR #12 merged; packaged source `cf6296f286dba9a89583649e19f988ed09af2f16` | C++ remains unchanged from Editor Build 12, 49 passing Unreal tests and the 30-file C++ format audit. The later star material was authored/cooked/captured separately. Release work changed distribution filtering/docs only; no Unreal rebuild was required. |
| Latest audited local game | Package 4/source `cf6296f`; `Artifacts/Windows/SpaceSurvival.exe` | Built successfully and passed actual IoStore dependency audit plus packaged Wave 1/four-image and Station 5/16-image captures. The star layer is dimmer with static directional variation. Furnished editable station, new starter, walkway fill and unlit labels remain included. Existing optional `Try New Ship.cmd` remains a separate trial. |
| Package identity | [Star-adjusted visual-pass receipt](validation/2026-09-14-visual-enhancement-stars.json); audit `ccc6491dd42e4219b36acabaa036cf91`; game SHA256 `65cc1f692bad328366cc7148e083631ab98414c6bef8c0d79a618c8ff906f5ca` | All 189 selected packages and all 1,380 indexed exports are described with zero unresolved imports; 63 archive files total 3,040,476,076 bytes. Both captures match the audited payload, including changed cooked material containers. The [Package 3 receipt](validation/2026-09-14-visual-enhancement.json) is preserved as an earlier checkpoint. |
| Published tester build | itch `0.1.16-alpha.1`, upload `19226459`, ready build `1979965` from `1978147`; [release record](ITCH_RELEASES.md#september-15-visual-release) | Same audited game executable and cooked containers as Package 4, with developer symbols/manifests and runtime Saved/log/save data excluded. Payload: 51 files / 2,664,557,549 bytes. Butler reports a 1.49 GiB patch; actual client update/save preservation remains unverified. Devlog copy is ready but browser sign-in/security verification blocks posting. |

To play locally, open `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`, keeping the complete directory. Do not open the Unreal project just to play. See [save-location differences](BUILD_RUN.md#local-saves) before changing launch arguments or moving an installation.

## Asteroid follow-up: source/editor only

Source `16007ab` uses 15 owned rock/debris meshes, native Blueprint layout samples, sustained shell parallax and quieter dust. Three private skies use 2048-face BC6H compression after fixed 2K/4K comparisons. Four final 1920x1080 editor-game frames are under `Artifacts/EndgameSoak/b6f44246abb2439da60423c6b0cf087f`. [The receipt](validation/2026-09-15-asteroid-depth.json) binds source hashes, editor DLL, native auditions and tests. Licensed changes and backups remain local/private; Git alone cannot reproduce this look.

Editor build and 49/49 automation pass. Visual depth/motion and representative performance remain unaccepted. Thrusters still have cubic cores; ACT-01 is unfinished. No change to Package 4, the playable EXE or published itch build.

## Flight, combat and space source checkpoint

The unmerged slice implements the first ACT-00–ACT-03 source pass: state-driven drive presentation, distinct native rapid/cannon/hostile bolts, bounded combat light cues, broader enemy movement, Nerves electrical fields, an owned Asteroid Library Blueprint comparison and explicit background/material selection. The first Free Galaxy comparison and overbright engine-light treatment were rejected; corrected editor captures retain NebulaFantasy regions and reduced drive lighting. Cosmic Materials remain available for alien surfaces and the Workshop rather than being forced into the background.

ACT-04 has an installed-plugin inventory only. The 309-asset Wormhole Portal plugin is not enabled in the project, and the fixed Station 5 capture still shows the existing custom ring tunnel. Natural play, synchronized sound, boost/brake readability in motion, dynamic-combat feel, the plugin pilot, representative performance, package/cook and owner acceptance remain open. Ship Core Pro is recorded as owned but blocked by its UE5.7 installer against this UE5.8.2 project. See [validation](VALIDATION.md#september-15-flight-combat-and-space-slice) for evidence and limits, and [KNOWN_ISSUES](KNOWN_ISSUES.md) for the only active queue.

## Owned audio, characters and input glyphs

September 15 evaluation found `IndieSounds-SciFi`, `cplomedia_SciFiSoundFX` and `EasyInputPrompts` in the downloaded asset project. This follow-up selectively imports ten `cplomedia_spaceship` roles into ignored `Content/SpaceSurvival/Licensed/Audio` and routes engine, weapons, impact, pickup, alarm, station ambience and enemy/debris cues through private-first generated-fallback lookup. It also adds the local Sci-Fi Space Character as a temporary station hero, plus Heavy Space Trooper and drone presentation staff, while keeping missing-asset fallbacks. Cosmic Material assets are available to the workshop. The other audio pack and input glyphs remain evaluated staging inputs, not runtime integrations.

[The catalog record](production/SOLUTION_CATALOG.md#new-local-audio-and-glyphs-evaluation-and-selective-integration) owns resource fit and selection. The [owned-asset receipt](validation/2026-09-15-owned-audio-station-assets.json) records the successful Editor build, 49/49 automation result and exact catalog counts. Listening, rendered/package review and glyph integration remain open under ISS-02/03/05/08/09. None of this is included in the current packaged executable or itch release.

## Local Station Workshop

[PR #14](https://github.com/j6sistek-ui/SpaceSurvival/pull/14) merged the owner-authorized editor workshop at `e44decdd`. The editor module is separate from packaged gameplay. Start it with `Open Station Workshop.cmd`; [Station editing](STATION_EDITING.md) owns controls, setup and limitations. [Workshop validation](validation/2026-09-15-station-workshop.json) records the successful Editor build, nine integration checks, ten material presets, 380 preserved placements and the initial populated 677-asset catalog. PR #15 expands the exact filtered catalog to **708** placeables while preserving the ten presets. Physical mouse/controller interaction and owner acceptance remain open.

The saved `Content/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop.umap` is the authoring source; Save + Apply derives `BP_StationVisualLayout`. Ten original preset instances live under `StationWorkshop/Materials`. Both remain local/private, as do timestamped layout JSON exports and previous map/Blueprint backups under `.agent/local/StationWorkshop`. Preserve this folder and the referenced private Content assets when backing up. Source-only Git does not reproduce this furnished workshop without those assets.

Applying a layout affects the next editor gameplay session and future packages; it does not update the existing packaged EXE or itch installation. The published build above is unchanged. Collision/services remain native and reported bugs remain paused in the sole [issues log](KNOWN_ISSUES.md).

## Verified foundation and limits

C++/Unreal integration covers flight, damage, manual weapons, the Director, four hazards, two enemies/weapons/events/utilities/contracts, one depot, five I-V upgrade paths, both station visits, hangar, settings, account unlocks and station suspensions. This is implemented scope, not an accepted near-alpha experience.

The [Package 3 receipt](validation/2026-09-14-visual-enhancement.json) records the passing 49-test integration and 20 packaged screenshots at `4dc45ac`. The lead inspected Cruise, StationIdle, StationServices and StationOverview: the new hull is framed, the walking pilot is visible, service labels are clearly lit and the station is furnished. The saved `BP_StationVisualLayout` contains 380 editable components; an ordinary author-script rerun preserved its exact saved bytes. The Havolk starter and 26 matching module/utility meshes have verified import bounds, materials and collision settings. See [station editing](STATION_EDITING.md) for the owner workflow. This closed-cockpit kit starter remains a provisional interpretation pending owner art review; the regular artist retains long-term hero/iconic-starter ownership.

The owner subsequently found stars overpowering forward flight and station views. Source `cf6296f` changes only the space authoring script: star brightness falls from 0.55 to 0.30, contrast increases to 1.45, and fixed directional variation gives points different brightness without animation. Nebula brightness and object lighting are unchanged. Authoring, Package 4's archive audit and both new packaged captures pass. The lead inspected Cruise, Approach and StationOverview: stars are quieter, object contrast is improved, and station lights/labels remain visible. The [star-adjusted receipt](validation/2026-09-14-visual-enhancement-stars.json) binds this new payload; [validation](VALIDATION.md#september-14-star-brightness-follow-up) records exact evidence and parameters. Owner acceptance remains open.

Earlier combined-look, assisted ten-wave, station, storage and performance receipts remain valid only for their recorded revisions. Package 4's packaged fixtures verify their recorded payload and transitions; natural play, continuous animation, visible combat-effect quality, audio and representative performance remain open. Neither the fixtures nor screenshots close hands-on acceptance.

Current quality gaps and the exact owner checks are maintained only in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). The lead still owns implementation, regression checks, packaging and evidence; the owner supplies experience/feel decisions. Do not treat all remaining work as owner testing.

## Where files live

Verified against tracked paths and ignore rules at the September 14 handoff. GitHub contains committed and pushed files, not every file under the project folder.

| Files/folders | On GitHub? | Purpose and preservation |
| --- | --- | --- |
| `Source/`, `Config/`, `Scripts/`, `Tests/`, `SpaceSurvival.uproject`, documentation | Yes, committed versions | Durable code, configuration, authoring tools, checks and project instructions. Uncommitted edits are local until committed/pushed. |
| `Content/` outside the ignored vendor/private folders | Yes, selected project assets | Original Unreal project assets and fallback presentation. Not every Content asset is tracked. |
| `ContentSource/`, `model-rigged.glb`, `art/` | Yes, committed sources | Editable sources, preserved original hero and reference media. |
| Lowercase `artifacts/` reference files | Yes: briefing PDF and reference images | Windows treats `artifacts` and `Artifacts` as the same folder. Tracked references coexist with ignored build outputs: do not treat the entire physical folder as disposable. |
| `User downloaded assets/` | No | Fab downloads/raw imports; preserve originals or an exact reacquisition record. |
| Existing vendor roots plus `Content/SpaceNebulaFantasy/`, `Spacecraft_Pack/`, `PyroVFX/`, `Sci_Fi_Weapons_VFX_AIO/`, `Robot_scout_R_21/`, `Defect/`, `SciFITrooper_Man_03/`, `Heavy_space_trooper/`, `CosmicMaterial/` | No | Locally licensed/free vendor content; excluded by `.gitignore`. The last three supply the temporary hero, supplemental staff and workshop materials in this local pass. Only selected runtime dependencies should enter the package. |
| `Content/StarterBundle/ModularSci_Comm/`, `ModularScifiProps/`, `ModularSciFiMats/`, `UE4_Assets/` | No | Four selected folders from Jonathon Frederick's Season 1 Starter Bundle: 1,153 files / 1,191,114,458 bytes, all SHA256-matched to the downloaded project. Furniture, terminals and their material dependencies support the editable station. The full Season 1/2 libraries are not blanket runtime selections; see [credits](../THIRD_PARTY.md). |
| `Content/SpaceSurvival/Licensed/` | No | Private atmosphere, combat effects, ship modules, provisional player derivatives, station exterior/dressing/screens, selected audio, drone, cook labels and `StationVisualPass/BP_StationVisualLayout.uasset`. Back up this saved Blueprint and its dependencies before manual editing; a clone will not restore them. |
| `Artifacts/Windows/`, `Artifacts/Releases/` | No | Local packaged game and prepared release payloads. An itch upload is a separate copy of a selected package. |
| `.agent/local/` | No | Logs plus unique paused art experiments and handoffs. It is not all disposable cache. |
| `Saved/` and game user profiles | No | Logs, validation and potentially personal saves/settings; preserve saves separately. |
| `Binaries/`, `Intermediate/`, `DerivedDataCache/`, `.vs/` | No | Usually reproducible build/editor cache; regeneration costs time. No cleanup is authorized by this page. |
| UE, Visual Studio, Blender and portable local helpers | No | Installed or local tooling, outside the source backup. |

**GitHub is not a complete backup of this working machine.** Licensed sources, private derivatives/manual tuning, unique art experiments and player saves need a separate backup plan (tracked in the open-work log). A fresh clone can validate source/export integrity and use fallback presentation; restoring licensed appearance needs the owned inputs and [content pipeline](CONTENT_PIPELINE.md). Follow [station editing](STATION_EDITING.md) to preserve manual Blueprint work. [Combined space look](production/COMBINED_SPACE_LOOK.md) retains an earlier atmosphere checkpoint.

Authoritative working folder: `C:/Users/j6sis/SpaceSurvival`. The earlier conversion copy `C:/Users/j6sis/SpaceSurvival 5.8` was absent at this audit. Additional Git worktrees are branch checkouts, not newer packaged games; use `git worktree list` when investigating them. No directories were deleted.

## Storage cleanup snapshot

No files were deleted. The measured September 15 cleanup candidates are `Intermediate` at about 4.84 GiB and the rebuildable parts of `Saved/StagedBuilds`, `Saved/Cooked` and `Saved/Shaders` at about 3.29 GiB; preserve `Saved/SaveGames`. Older release directories total about 4.32 GiB and can be removed after retaining the current audited 0.1.16-alpha.1 payload or confirming itch/redownload is sufficient. Downloaded audio staging/cache occupies about 5.14 GiB; deleting it gives up convenient re-audition/reimport and may require a Fab redownload, while the selected private derivatives still need their own backup. Fourteen working/staging art roots total about 8.76 GiB and are ignored by Git, so do not delete them until their license/reacquisition record and an off-machine backup are verified. These are cleanup choices, not current authorization to remove data.

## Asset collaborator handoff (proposal, not configured)

The owner confirmed the regular contributor supplies model/texture/animation files only. For that role, the recommended starting point is one private shared Drive handoff folder, separate from the live Unreal project. Keep revisions such as `Hero/v003/` together: editable source (for example Blender), agreed export, textures, preview and a short change note tied to ISS/WBS ID. Upload a new revision rather than overwriting an accepted delivery. The owner chooses access; no folder, collaborator invitation or sync automation has been created.

The modeler uploads; the lead retrieves/syncs the handoff, checks geometry/materials/rig/scale, imports into a controlled branch, records the adopted revision in the catalog/content provenance, exercises it in-game and packages a review build. This lets the owner focus on feedback without personally shuttling each file. A shared folder is transport/storage; the selected source revision, integration changes and build still need an explicit record. Keep the receipt and authorized project assets in Git; preserve private source/derivatives in the agreed private storage.

For a regular contributor editing inside Unreal, evaluate versioned large-asset collaboration separately. Git LFS stores pointers in Git and the large file content separately; it is not configured by this PR. See [GitHub's LFS documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage), checked September 14, 2026. Do not migrate history or publish vendor source as part of a casual handoff.

Unreal can [monitor source folders and automatically reimport](https://dev.epicgames.com/documentation/unreal-engine/reimporting-assets-automatically-in-unreal-engine?lang=en-US) (Epic docs checked September 14, 2026). That does not validate a changed rig/material, preserve every custom authoring choice, or update an already packaged tester game. For this project's guarded imports and private derivatives, start with deliberate import/review; enable watched imports only for a proven isolated workflow. ISS-14 owns the setup decision and follow-up.

## How this stays current

- README and root PROJECT_STATE are entry points, not parallel status logs.
- KNOWN_ISSUES owns active work, priority and closure; PLAYTEST_TOMORROW redirects there.
- The solution catalog owns candidate/acquisition/evaluation facts, not task priority or purchase authorization.
- Work packages and the quality plan are scope/dependency references, not a live sprint board.
- Build/run owns commands; this page owns the latest source/package/release pointer.
- Validation receipts retain immutable history; old package numbers do not identify a shared path after it is rebuilt.
- Every PR reconciles these boundaries and gives the owner an explicit open/check/still-open handoff.
