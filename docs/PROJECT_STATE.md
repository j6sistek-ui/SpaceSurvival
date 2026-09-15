# SpaceSurvival project state

**Phase 1: PARTIAL.** State reconciled September 14, 2026. [Open work and your next review](KNOWN_ISSUES.md) owns active priorities, owner checks and closure status. This page owns the source/build/release and storage explanation.

## Source, build and release

| Layer | Last verified state | What it means |
| --- | --- | --- |
| GitHub source | PRs #3, #6, #9 and #10 merged; main synchronized locally at `425e3b2` before this documentation-only PR | Foundation, refresh, catalog and merge handoff are in main. This is a dated checkpoint, not an automatically updating branch indicator. |
| This documentation change | Branch `codex/documentation-review`, based on that main checkpoint | Consolidates work/status navigation and requires PR documentation review. No gameplay, imported asset, save or package change. Review [PR #11](https://github.com/j6sistek-ui/SpaceSurvival/pull/11); its live GitHub state is authoritative. |
| Latest recorded local game | September 14 combined space look; `Artifacts/Windows/SpaceSurvival.exe` | Owned cool sky, thin nebular volumes, ambient light, layered asteroids and blue-white exhaust. Existing optional `Try New Ship.cmd` remains a separate trial. |
| Package identity | [Combined-look receipt](validation/2026-09-14-combined-space-look.json); inner game SHA-256 `89b5dd59f63cd77be56018869b03df79f91a08bf32f0e3e061404554abb2d815` | The six executable/container hashes and eight recorded source hashes were independently matched before the merge handoff. This is not an exhaustive fresh-clone reproduction claim. |
| Published tester build | Last verified itch `0.1.15-alpha`, build `1978147`, source `602be07`; [release record](ITCH_RELEASES.md#september-14-update) | Older than the local combined-look game; experimental clouds disabled in that release. Later source merges did not upload it. Devlog publication remains open. |

To play locally, open `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`, keeping the complete directory. Do not open the Unreal project just to play. See [save-location differences](BUILD_RUN.md#local-saves) before changing launch arguments or moving an installation.

## Verified foundation and limits

C++/Unreal integration covers flight, damage, manual weapons, the Director, four hazards, two enemies/weapons/events/utilities/contracts, one depot, five I-V upgrade paths, both station visits, hangar, settings, account unlocks and station suspensions. This is implemented scope, not an accepted near-alpha experience.

The latest combined-look record reports 44 Unreal tests with zero test warnings/failures/not-run, 27 structural source checks, successful Editor compilation and Windows packaging, and a 29-second scripted offscreen Wave 1 capture at 1080p. Earlier assisted ten-wave, station, storage and performance receipts remain valid only for their recorded revisions. Neither those fixtures nor screenshots close hands-on acceptance.

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
| `Content/Asteroid_Library/`, `SciFiCorridor/`, `NiagaraExamples/`, `RPGEnvironmentVFX/`, `Vefects/` | No | Locally licensed vendor content; excluded by `.gitignore`. |
| `Content/SpaceSurvival/Licensed/` | No | Private atmosphere, exhaust, station exterior and other derivatives. Back up manual tuning/authoring; a clone will not restore it. |
| `Artifacts/Windows/`, `Artifacts/Releases/` | No | Local packaged game and prepared release payloads. An itch upload is a separate copy of a selected package. |
| `.agent/local/` | No | Logs plus unique paused art experiments and handoffs. It is not all disposable cache. |
| `Saved/` and game user profiles | No | Logs, validation and potentially personal saves/settings; preserve saves separately. |
| `Binaries/`, `Intermediate/`, `DerivedDataCache/`, `.vs/` | No | Usually reproducible build/editor cache; regeneration costs time. No cleanup is authorized by this page. |
| UE, Visual Studio, Blender and portable local helpers | No | Installed or local tooling, outside the source backup. |

**GitHub is not a complete backup of this working machine.** Licensed sources, private derivatives/manual tuning, unique art experiments and player saves need a separate backup plan (tracked in the open-work log). A fresh clone can validate source/export integrity and use fallback presentation; restoring the current licensed appearance needs the owned inputs and authoring steps in [CONTENT_PIPELINE.md](CONTENT_PIPELINE.md) and [COMBINED_SPACE_LOOK.md](production/COMBINED_SPACE_LOOK.md).

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