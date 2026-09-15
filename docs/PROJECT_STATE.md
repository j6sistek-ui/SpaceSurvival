# SpaceSurvival project state

**Phase 1: PARTIAL.** The visual pass is merged and itch **0.1.16-alpha.1 / build 1979965** is ready on windows-alpha (verified September 15 UTC / September 14 local). [PR #11](https://github.com/j6sistek-ui/SpaceSurvival/pull/11) and [PR #12](https://github.com/j6sistek-ui/SpaceSurvival/pull/12) are merged. The release-safety fix and distribution records are tracked in [PR #13](https://github.com/j6sistek-ui/SpaceSurvival/pull/13), merged at `ac08e0b`; its GitHub state is authoritative. It does not change the game binaries. [Open work and your next review](KNOWN_ISSUES.md) owns active priorities, owner checks and closure status. This page owns the source/build/release and storage explanation.

## Source, build and release

| Layer | Last verified state | What it means |
| --- | --- | --- |
| GitHub source | PRs #11–13 merged; main checkpoint `ac08e0b9dd37fa054ac691ca285162310271009e` | Documentation foundation and visual pass are in main. PR #13 carries the release publisher guard and release records; source merge and itch publication are verified independently. |
| Documentation foundation | PR #11 merged | Canonical state/open-work navigation and PR documentation review are present. Required status-check enforcement remains a separate open repository-setting task. |
| Current visual source | PR #12 merged; packaged source `cf6296f286dba9a89583649e19f988ed09af2f16` | C++ remains unchanged from Editor Build 12, 49 passing Unreal tests and the 30-file C++ format audit. The later star material was authored/cooked/captured separately. Release work changed distribution filtering/docs only; no Unreal rebuild was required. |
| Latest audited local game | Package 4/source `cf6296f`; `Artifacts/Windows/SpaceSurvival.exe` | Built successfully and passed actual IoStore dependency audit plus packaged Wave 1/four-image and Station 5/16-image captures. The star layer is dimmer with static directional variation. Furnished editable station, new starter, walkway fill and unlit labels remain included. Existing optional `Try New Ship.cmd` remains a separate trial. |
| Package identity | [Star-adjusted visual-pass receipt](validation/2026-09-14-visual-enhancement-stars.json); audit `ccc6491dd42e4219b36acabaa036cf91`; game SHA256 `65cc1f692bad328366cc7148e083631ab98414c6bef8c0d79a618c8ff906f5ca` | All 189 selected packages and all 1,380 indexed exports are described with zero unresolved imports; 63 archive files total 3,040,476,076 bytes. Both captures match the audited payload, including changed cooked material containers. The [Package 3 receipt](validation/2026-09-14-visual-enhancement.json) is preserved as an earlier checkpoint. |
| Published tester build | itch `0.1.16-alpha.1`, upload `19226459`, ready build `1979965` from `1978147`; [release record](ITCH_RELEASES.md#september-15-visual-release) | Same audited game executable and cooked containers as Package 4, with developer symbols/manifests and runtime Saved/log/save data excluded. Payload: 51 files / 2,664,557,549 bytes. Butler reports a 1.49 GiB patch; actual client update/save preservation remains unverified. Devlog copy is ready but browser sign-in/security verification blocks posting. |

To play locally, open `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`, keeping the complete directory. Do not open the Unreal project just to play. See [save-location differences](BUILD_RUN.md#local-saves) before changing launch arguments or moving an installation.

## Newly staged audio and input glyphs

September 15 evaluation found `IndieSounds-SciFi`, `cplomedia_SciFiSoundFX` and `EasyInputPrompts` inside `User downloaded assets/SpaceSurvival/Content`, with vault copies. These roots are absent from the working project Content and are not included in the current game/itch release. [The catalog evaluation](production/SOLUTION_CATALOG.md#new-local-audio-and-glyphs-evaluation-and-proposed-integration) owns resource fit and the proposed integration; ISS-05/08 own active follow-up. This was a read-only source/media inspection with private derived thumbnails/inventory and documentation updates.

## Local Station Workshop

[PR #14](https://github.com/j6sistek-ui/SpaceSurvival/pull/14) now carries the owner-authorized editor workshop, in addition to captured feedback. Its branch is `codex/owner-feedback-build-workflow`; it is not merged. The editor module is separate from packaged gameplay. Start it with `Open Station Workshop.cmd`; [Station editing](STATION_EDITING.md) owns controls, setup and limitations. [Workshop validation](validation/2026-09-15-station-workshop.json) records the successful Editor build, nine integration checks, ten material presets, 380 preserved placements and an actual panel capture showing the populated 677-asset catalog. Physical mouse/controller interaction and owner acceptance remain open.

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
| Existing vendor roots plus `Content/SpaceNebulaFantasy/`, `Spacecraft_Pack/`, `PyroVFX/`, `Sci_Fi_Weapons_VFX_AIO/`, `Robot_scout_R_21/`, `Defect/` | No | Locally licensed/free vendor content; excluded by `.gitignore`. Only selected runtime dependencies should enter the package. |
| `Content/StarterBundle/ModularSci_Comm/`, `ModularScifiProps/`, `ModularSciFiMats/`, `UE4_Assets/` | No | Four selected folders from Jonathon Frederick's Season 1 Starter Bundle: 1,153 files / 1,191,114,458 bytes, all SHA256-matched to the downloaded project. Furniture, terminals and their material dependencies support the editable station. The full Season 1/2 libraries are not blanket runtime selections; see [credits](../THIRD_PARTY.md). |
| `Content/SpaceSurvival/Licensed/` | No | Private atmosphere, combat effects, ship modules, provisional player derivatives, station exterior/dressing/screens, selected-asset cook label and `StationVisualPass/BP_StationVisualLayout.uasset`. Back up this saved Blueprint and its dependencies before manual editing; a clone will not restore them. |
| `Artifacts/Windows/`, `Artifacts/Releases/` | No | Local packaged game and prepared release payloads. An itch upload is a separate copy of a selected package. |
| `.agent/local/` | No | Logs plus unique paused art experiments and handoffs. It is not all disposable cache. |
| `Saved/` and game user profiles | No | Logs, validation and potentially personal saves/settings; preserve saves separately. |
| `Binaries/`, `Intermediate/`, `DerivedDataCache/`, `.vs/` | No | Usually reproducible build/editor cache; regeneration costs time. No cleanup is authorized by this page. |
| UE, Visual Studio, Blender and portable local helpers | No | Installed or local tooling, outside the source backup. |

**GitHub is not a complete backup of this working machine.** Licensed sources, private derivatives/manual tuning, unique art experiments and player saves need a separate backup plan (tracked in the open-work log). A fresh clone can validate source/export integrity and use fallback presentation; restoring licensed appearance needs the owned inputs and [content pipeline](CONTENT_PIPELINE.md). Follow [station editing](STATION_EDITING.md) to preserve manual Blueprint work. [Combined space look](production/COMBINED_SPACE_LOOK.md) retains an earlier atmosphere checkpoint.

Authoritative working folder: `C:/Users/j6sis/SpaceSurvival`. The earlier conversion copy `C:/Users/j6sis/SpaceSurvival 5.8` was absent at this audit. Additional Git worktrees are branch checkouts, not newer packaged games; use `git worktree list` when investigating them. No directories were deleted.

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
