# Contributor and other-chat onboarding

This is a navigation and working-method guide, not another backlog. Verified against the local checkout on September 16, 2026. Read current owner instructions and refresh Git state before relying on a dated snapshot. A chat opened in another project does not automatically inherit this repository's instructions or local assets.

## Start here

1. Use **`C:/Users/j6sis/SpaceSurvival`**, remote **`https://github.com/j6sistek-ui/SpaceSurvival.git`**. The surrounding Codex task may default to `C:/Users/j6sis/acornaut`; that is a different project. Set an explicit working directory before every project command.
2. Read [AGENTS.md](../AGENTS.md), [.agent/CONTINUITY.md](../.agent/CONTINUITY.md), [GAME_SCOPE](GAME_SCOPE.md), [IMPLEMENT](../IMPLEMENT.md), then the current instruction and relevant action in [KNOWN_ISSUES](KNOWN_ISSUES.md). GAME_SCOPE/IMPLEMENT remain authoritative unless the owner explicitly supersedes a requirement.
3. Check `git status --short`, `git branch --show-current`, `git worktree list`, the PR head and any running Unreal process. Preserve uncommitted/manual work. Do not switch/reset a shared checkout or stop another chat's editor.
4. Read [PROJECT_STATE](PROJECT_STATE.md) for source versus local development build versus packaged/itch state. Select one authorized ACT item and the relevant catalog IDs. Do not start a second audit or priority list.
5. Load one or two relevant skills, inspect the actual implementation and asset dependencies, then reproduce the issue or capture a baseline before editing.

At this handoff, PR17 is the draft `codex/flight-combat-space-slice` branch. **The owner has paused ACT-03 environment iteration; the target remains NOT MET.** Current improvements are retained. ACT-01 is next in the existing production order, not a blanket authorization for every later issue. Consult the log for subsequent direction. Do not infer approval to merge, package, publish, install tools or delete caches.

## Files, tools and storage

Paths below are local unless explicitly identified as GitHub. Relative paths elsewhere in this guide are relative to `C:/Users/j6sis/SpaceSurvival`.

| Location | Purpose and boundary |
| --- | --- |
| `SpaceSurvival.uproject` | Working UE5.8 project. Owner-installed engine is `C:/Program Files/EpicGames2/UE_5.8` (5.8.2 at verification). Do not use the incomplete similarly named `Epic Games/UE_5.8` location or convert/downgrade the project casually. |
| `Source/SpaceSurvival` | Runtime C++; `Domain/SurvivalCore.*` owns simulation/session rules. `Source/SpaceSurvivalEditor` owns the editor Workshop. |
| `Scripts`, `Config`, `ContentSource` | Tracked build/authoring/capture scripts, runtime configuration and generated fallback sources. Script reruns can overwrite tuned private outputs; inspect and back up first. |
| `Content` | Unreal assets actually available to this project. Vendor roots and `Content/SpaceSurvival/Licensed` include ignored private content. Use `git check-ignore`/`git ls-files` to establish storage status; do not assume every asset is tracked. |
| `User downloaded assets/SpaceSurvival/Content` | Separate downloaded-assets staging content. Includes audio/input sources and additional art not necessarily integrated into the game. This is not the authoritative game project. |
| `User downloaded assets/VaultCache` | Earlier local vendor downloads; `FabLibrary` contains raw GLB/Blender sources such as Figur station kit and station exteriors. |
| `C:/Users/j6sis/Downloads/VaultCache` | Additional recent downloads. Alien source: `Untitled00569c949a0dV1/data/Content/Megastructure_Scifi_World`. A cache download is not runtime integration. |
| `.agent/local` | Ignored preparation data, asset inventories, previews and manual-work backups. Preserve `StationWorkshop` backups/layout exports. Not a GitHub backup. |
| `Artifacts/EndgameSoak/<id>` | Actual game captures, fixture/capture receipts and logs. `Artifacts/EnvironmentRefresh/<label>.json` points to runs. Read receipt identities, not just a convenient filename. |
| `docs/validation` | Tracked, sanitized historical evidence and hashes; no raw licensed assets. [Area/gallery receipt](validation/2026-09-16-space-areas-gallery.json) records final candidate/reviewer findings. |
| `Play Development Build.cmd` | Launches the current Editor game using a separate persistent review profile under `Artifacts/DevelopmentReviewUser`. Does not compile or package. |
| `Open Station Workshop.cmd` | Opens the authoring Workshop. Saved source: `Content/SpaceSurvival/Licensed/StationWorkshop/L_StationWorkshop.umap`; Save + Apply derives the private station Blueprint. |
| `Artifacts/Windows/SpaceSurvival.exe` | Existing packaged game; keep its whole folder. It does not receive source/asset edits automatically. Current package and itch identity belong only in PROJECT_STATE/ITCH_RELEASES. |
| `Saved/SaveGames` and `%LOCALAPPDATA%/SpaceSurvival/Saved/SaveGames` | Potential player save locations depending on launch mode. Preserve them. Use isolated profiles for destructive lifecycle tests. |

**GitHub is not a complete backup of this machine.** A clone lacks much licensed content, private derivatives and owner edits. Missing-asset fallbacks can make a clone launch successfully while showing the wrong presentation. Never remove these files on the assumption that Git can restore them. Preserve originals, licenses and private revisions outside the public/source handoff.

## Canonical documentation contract

| Document | What every contributing chat must maintain |
| --- | --- |
| [KNOWN_ISSUES](KNOWN_ISSUES.md) | Sole active priority, ACT/ISS/RPT/PT and follow-up log. Reuse IDs; record observed versus reported behavior, owner, next operation and closure evidence. Keep paused, failed and partial work open. |
| [SOLUTION_CATALOG](production/SOLUTION_CATALOG.md) | Resource fit, acquisition, source paths, candidate comparison and evidence. Distinguish **owned, local, imported, referenced, rendered/auditioned, accepted**. Names/thumbnails are not evaluations. No competing task priorities here. |
| [PROJECT_STATE](PROJECT_STATE.md) | Current source/build/release identity and local-versus-GitHub storage. Merge, rebuilt DLL, cooked EXE and published itch are different states. |
| [.agent/CONTINUITY.md](../.agent/CONTINUITY.md) | Brief dated provenance-tagged handoff: authority, current ACT, exact branch/head, evidence, blocker and next concrete operation. Compress history; do not paste transcripts. |
| [BUILD_RUN](BUILD_RUN.md), [STATION_EDITING](STATION_EDITING.md), [ARCHITECTURE](ARCHITECTURE.md), [CONTENT_PIPELINE](CONTENT_PIPELINE.md), [VALIDATION](VALIDATION.md), [PERFORMANCE](PERFORMANCE.md) | Update impacted commands, authoring behavior, ownership, content references, tests and cost limits. Review unaffected documents without cosmetic edits. |

Before every PR handoff, complete all six groups in [.github/pull_request_template.md](../.github/pull_request_template.md) with **Updated** or **Reviewed unchanged** and a reason. Give **Open / Check / Still open**, with an exact build or artifact and at most three owner checks. Review README/navigation and catalog freshness. Run `python Scripts/CheckPrDocumentation.py --repo .`; its pass checks consistency, not factual truth. Always use a PR; never auto-merge. An existing authorized review PR can receive the current work.

## Skills and efficient execution

Skills are local files under `.agents/skills`, not evidence of an MCP connection. Start with [skill selection](../.agents/skills/README.md) and [PROJECT_ADAPTER](../.agents/skills/PROJECT_ADAPTER.md). If automatic discovery fails in another chat, read the relevant `SKILL.md` directly.

| Work | Skill to read before implementation |
| --- | --- |
| Player-path acceptance, visual/gameplay review | `spacesurvival-gameplay-review/SKILL.md` |
| Reproduce a defect, diagnose failed build/capture | `ue5-debug-validation/SKILL.md` |
| Flight, combat, presentation component or tuning schema | `ue5-cpp-gameplay/SKILL.md`; `ue5-architecture/SKILL.md` if ownership/lifetime changes |
| Blueprint/content composition and owner-editable settings | `ue5-blueprint-workflow/SKILL.md` |
| Station service, collision/interaction eligibility | `ue5-world-interaction/SKILL.md` |
| Input prompts and HUD focus | `ue5-ui-umg-slate/SKILL.md` |
| Persistence or gallery return/session preservation | `ue5-save-load-replication/SKILL.md` (single-player scope only) |
| Measured performance/cook/package | `ue5-performance-packaging/SKILL.md` |

The [work-area guide](../.agents/skills/spacesurvival-gameplay-review/references/skills-by-work-area.md) routes VFX, materials, lighting, animation, audio and collision work to additional references. Read selected references when needed; verify APIs against installed UE5.8 source. Do not load every skill or install a tool based on its name. Check callable tools before asserting Blender/Unreal MCP access.

Use containers for portable project tooling when available (`Scripts/TestCore.ps1`, `Scripts/Format.ps1 -Check`). Native Unreal compilation, authoring and Windows packaging use installed UE/Visual Studio through `Scripts/Build.ps1`. Docker was unavailable during the latest pass; existing native tools were used, without installs. Recheck availability instead of assuming it remains unavailable. A Docker pass is not an Unreal gameplay pass.

One lead owns the editor. Serialize builds/authoring/captures, batch independent source reads, and delegate only bounded authorized tasks with file ownership. Never launch competing engine processes. Reuse existing receipts and deterministic captures; rerun expensive gates when relevant code/content changes, a failure or an unresolved concern warrants it.

## High-value owned assets and where to start

This is a locator and role assessment, not another full catalog or purchase list. These project roots were verified on disk September 16. Catalog IDs retain detailed provenance and acceptance limits. Look at native example scenes/Blueprint behavior and real gameplay scale before selecting pieces.

| Owned resource | Location | High-value use and remaining limit |
| --- | --- | --- |
| **C23 Havolk Space Ship 02 Modular Pack** | `Content/Spacecraft_Pack`; selected derivatives in `Content/SpaceSurvival/Licensed/PlayerShipVisualPass` and `ShipVisualPass` | Current provisional player hull, module silhouettes and enemy variation. Verify actual selected ship/mounts in gameplay. Regular artist owns long-term hero/iconic starter; do not replace that commitment. |
| **A07 Niagara Examples** | `Content/NiagaraExamples`; current private trail `Content/SpaceSurvival/Licensed/Atmosphere/NS_DeepSpaceExhaust` and `M_DeepSpaceExhaust` | Reusable ribbon/exhaust foundation. Runtime cubic cores, size, emission and lighting still live in `SSAmbientPresentation.cpp`; trail edits alone do not remove the cubes. Expose meaningful tuning rather than promise editor controls that do not exist. |
| **C32 Sci-Fi Weapons VFX; C08 Pyro explosions** | `Content/Sci_Fi_Weapons_VFX_AIO`, `Content/PyroVFX`; selected private assets `Content/SpaceSurvival/Licensed/Combat` | Full muzzle/travel/impact/shield/hull/destruction chains for both weapons. A visible effect is not a complete readable chain or synchronized sound. Check allegiance, scale, lifetime and screen coverage in combat. |
| **A23 Nerves** | `Content/NERVES/FX`; private field derivatives under `Licensed/Combat` | Electrical arcs/field feedback. Preserve endpoint ownership/cleanup; audition appearance and performance. Filename spelling in the pack may be unusual; use actual asset paths. |
| **A01 Asteroid Library** | `Content/Asteroid_Library`; samples/recipes in `Content/SpaceSurvival/Licensed/Atmosphere/DA_DeepSpaceLook` | Native Arch/Globular/Linear examples, 15 selected rock/debris forms and layered fields. Dense counts alone failed the target; use scale hierarchy, overlap and depth attenuation. ACT-03 currently held. |
| **A24 Alien megastructure** | `Content/Megastructure_Scifi_World/Meshes` and `Level`; private assembled forms `Content/SpaceSurvival/Licensed/SpatialAssemblies` | Full architecture and thick broken assemblies. Both `L_Showcase_level` and `L_assets` are accessible through ALIEN WORLD. Some panels have zero thickness. Complete rendered gallery exists; flight composition remains unaccepted. Exact storefront identity is still unpinned. |
| **A02 Corridor; C17 Modular SciFi; A19 Electronics** | `Content/SciFiCorridor`, `Content/StarterBundle`, `Content/Defect`; private station layout under `Licensed/StationVisualPass` | Structural room composition, connected entrances, service consoles and lived-in props. Design layout/camera/clearance before dressing. Workshop visual placement does not automatically establish collision, NPC navigation or services. |
| **A16 Station3; C16 Figur kitbash** | Selected derivatives `Licensed/StationVisualPass`, `Licensed/OrbitalWreck`; raw Figur source under `User downloaded assets/VaultCache/FabLibrary/Sci_Fi_SPACE_STATION_Kitbash___3D_Kitbash_Asset_Pack___Blender-9af3878b/blender/space_station_kit.blend` | Distant landmarks, broken arcs/beams, ambient structures and modular exterior exploration. A complete exterior is not a walkable station. Preserve private baked materials. |
| **B03 NebulaFantasy; A08 Galaxy; C05 Cosmic Material** | `Content/SpaceNebulaFantasy`, `Content/Vefects`, `Content/CosmicMaterial`; selected sky/material derivatives under `Licensed/Atmosphere` | Sky variety and selected anomaly/surface materials. Current skies are cubemaps, not a fly-through procedural volume. Two galaxy sky trials were rejected; retain other roles without forcing every pack into the sky. |
| **A18 Robot Scout; temporary hero/heavy trooper/drone** | `Content/Robot_scout_R_21`, `SciFITrooper_Man_03`, `Heavy_space_trooper`; `Licensed/OwnedCharacters`, `Licensed/StationAssets/Drone` | Compatible locomotion/idle/work roles and station life. Existing staff are provisional; verify mesh/skeleton, placement, collision and motion. Do not infer patrol/AI from a mesh or idle animation. |
| **Audio and B23 input glyphs** | Staging `User downloaded assets/SpaceSurvival/Content/{cplomedia_spaceship,cplomedia_SciFiSoundFX,IndieSounds-SciFi,EasyInputPrompts}`; selected audio `Content/SpaceSurvival/Licensed/Audio` | Audition engine loops, weapons, impacts, station cues and device prompts. The ten selected roles come from `cplomedia_spaceship`; do not conflate it with the separately inventoried SciFiSoundFX pack. Glyphs remain unintegrated. Names/header parsing are not listening tests. |

**Tools already available:** UAsset Browser is installed at `C:/Program Files/EpicGames2/UE_5.8/Engine/Plugins/Marketplace/UAssetBr561f579a4fe2V15` (project enablement/UI not independently exercised). It indexes external content and imports dependencies; it does not integrate gameplay. Wormhole Portal lives beside it under `Wormhole8c083dd18940V1`; the recorded project pilot is unperformed. Ship Core Pro is owner-reported owned but compatibility-blocked at the last check; do not downgrade the engine. The existing Station Workshop is the owner composition entry point. No additional purchase is needed just to continue evaluation.

## Failures to avoid repeating

- **Stopped contrary to the owner's directive.** The lead stopped after documenting NOT MET despite instructions to keep iterating until independent target agreement. Accurate partial reporting did not satisfy that completion requirement. Continue authorized work until its acceptance criterion, a concrete blocker, or a later owner change. The current owner hold is such a later change; it does not retroactively validate the stop.
- **Confused implementation with quality.** Builds, asset counts, imports and successful capture receipts did not establish the requested look. Use the supplied reference at the actual player-camera scale. Lead and independent reviewer must agree before claiming visual acceptance when that gate is requested.
- **One good angle hid weak environments.** Turns exposed sparse backgrounds, flat alien slabs and masses behind the aim point. A second seed changed local rocks but largely retained main framing. Review multiple areas, angles, travel distances and materially different arrangements; do not close long-zone variety from one composition.
- **Added density without enough composition.** More isolated rocks did not produce receding volume. Audition whole native examples, assemble coherent structures and vary overlap/contrast/haze with depth. Increasing counts is not the acceptance target and needs a measured performance budget.
- **Owned packs were underused or only inventoried.** Select candidates by concrete role, inspect their actual modules/materials/Blueprints, compare rejected and selected examples, and record why. Do not describe names or listing thumbnails as a deep evaluation; do not buy around unfinished integration.
- **Visual geometry and physical behavior diverged.** Station walk-through/label-blocking/NPC overlap are owner reports still requiring proper reproduction. New reachable region structures explicitly use NoCollision. Never call them physical cover or collision-ready obstacles; do not silently add damage mechanics to disguise the mismatch.
- **Owner-editable controls were incomplete.** Cube thruster core geometry and state tuning are hardcoded; changing a Niagara ribbon cannot fix them. Separate runtime-generated behavior from saved assets. Changes made to transient Play actors can disappear when Play stops.
- **Failed trials were not acceptance.** The first gallery asset camera showed only floor; corrected framing passed the bounded round trip. Excessive fog washed out the ship and was reverted. Preserve rejected evidence and the exact correction instead of showing only the preferred image.
- **Source/build/release and evidence scope were easy to confuse.** PR17 is not the installed EXE/itch. The current 51/51 automated result does not prove physical input, listening, smooth motion, representative FPS or packaged behavior. Keep these claims separate and tied to exact hashes.
- **Authoring can erase manual work.** Preserve owner edits, private originals, layout exports and backups before regenerating a Data Asset/material/map. Do not use missing local content as a reason to rebuild or delete a vendor library blindly.

## Leave a usable handoff

Update the existing ACT row and continuity with: objective; owner authority/hold; branch and exact head; affected source/private assets; skill used; baseline and final evidence; failures still open; next concrete operation. Include the exact launch/review path and one to three owner checks. Keep responsibility for unfinished implementation with the lead. Another chat should be able to continue one bounded action without reading this entire conversation or recreating the library audit.
