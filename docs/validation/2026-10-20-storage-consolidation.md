# October 20 storage consolidation

Owner scope: map the C project, M project and Codex storage; preserve unique inputs; keep active project dependencies inside the C project; use a new D folder only for cold archives. Existing D data must not be scanned. No character, scene, animation or gameplay redesign.

## Measured baseline

Logical file sizes, with reparse points excluded rather than counted again:

| Location | GiB | Interpretation |
| --- | ---: | --- |
| C project | 268.517 | Native content, source, unique art work, Git history and generated evidence |
| M project | 104.555 | Active linked content/artifacts/source plus downloaded vendor libraries |
| `.codex` | 65.339 | Separate worktrees31.415; sessions28.131; remaining database/plugins/attachments |
| Downloads | 5.453 | Mixed project originals and unrelated downloads; not blanket disposable |
| Documents/Codex | 31.778 | Mostly other project work; preserve unrelated checkouts |
| Local Temp | 26.333 | Mixed Blender/tool/archive/scratch data; ownership varies |
| Local UnrealEngine | 47.103 | Shared DDC32.123 and Zen14.686; normal shader caches retained |
| M Local AI/Projects | 17.276 | Editable character sources now copied into project SourceAssets |
| M Local AI/NPCTalk | 9.152 | Actual speech/dialogue binaries/models, now in LocalRuntime |

The initial inventory encountered seven long-path enumeration errors under the C project and locked/long-path files under Temp. Migration and the final C/M/Codex inventory use extended Windows paths; the final inventory has zero enumeration errors. This is not a complete scan of every disk. Only free-space metadata and newly created archive destinations were read on D.

Final snapshot at 18:47 UTC: C project311.118 GiB plus1.264 GiB of this audit's private receipts/rejected trials (excluded consistently from the inventory); `.codex`51.094 GiB; M project397,312 bytes in one locked Fab catalog database. The migrated M character-project and NPC-runtime roots have zero regular files remaining. C grows because the previously external data now physically lives there; this is not a new duplicate of the old M project.

Current C project composition: Content113.378 GiB, `.agent`82.087 GiB, Artifacts28.975 GiB, Git22.640 GiB, SourceAssets17.276 GiB and retained raw downloads16.476 GiB. These are logical lengths, excluding junction traversal, not allocated-cluster measurements. Codex still includes28.165 GiB of conversation sessions and17.133 GiB of separate worktrees; those contain user history and local work and were not discarded.

## Current storage layout

- `C:/Users/j6sis/SpaceSurvival/Content`: actual imported game and authoring assets. Eleven building roots formerly linked into an M worktree now physically live here. Their worktree aliases point back to C.
- `Artifacts/`: physical C directory, including current local package, prefab library, retained evidence and migrated historical worktrees. Git registrations were repaired; branches were not removed.
- `.agent/local/CharacterAssets`: preserved character work and source deliveries, now physical C.
- `SourceAssets/MigratedProjects`: preserved M character projects, with nine Blender scenes updated only for C texture paths/orphan-image retention as verified below.
- `User downloaded assets/SpaceSurvival`: retained raw/editable Fab sources and incomplete staging material on C.
- `LocalRuntime/NpcTalk`, `LuxTTS`, `HuggingFace` and `DirectorVoice`: offline dialogue, speech, voice environment/weights/cache. Base Python and Unreal are installed on C; these are machine-local dependencies, not a portable packaged redistributable.
- `D:/SpaceSurvival_StorageArchive_20261020`: newly created cold archive. Vendor native download copies, the unused Medieval library, rebuildable worktree PCH files and abandoned Git repack data belong here. No active game configuration points at D.

Historical receipts and embedded import-source metadata may retain original M filenames. They describe provenance and are not runtime dependencies; historical recipes should not be replayed wholesale. Raw licensed sources and models are ignored by Git. GitHub is not their backup.

## Spectrum Galaxy

`Content/Galaxy` has1,232 files totaling3,588,815,738 bytes. Every file matches the surviving Spectrum download by SHA256: zero missing/different files or hash errors. A fresh Unreal registry sees1,222 Galaxy packages and zero missing Galaxy dependencies. The Galaxy overview World loads successfully after relocation.

Galaxy remains an imported building library; no saved authored-game registry reference reaches it. This does not establish placement in the current station or visual acceptance, and is not a reason to delete it.

## Duplicates and unique sources

The asset-only hash audit found9,213 exact duplicate groups and41.173 GiB of additional identical payloads. This is a discovery total, not a safe-deletion total: separate worktrees and package paths can need identical bytes. Hardlink identities were excluded from duplicate accounting.

Most archived native download packs match their current imported counterparts. Gym has181 exact files plus one changed-size file; Futurist has258 exact files plus two changed-size files. Both vendor originals and current edited imports are retained. Medieval has9,691 native files absent from the current project; it is unique cold library material, not a duplicate.

P1toP5_Bundle is41.688 GiB and has1,183 packages reachable from the authored game graph. Do not remove it as unused bulk. Clouds_Tunnel_Loop is12.635 GiB with31 packages and no saved authored reachability in this audit; retained as a possible later cold-storage candidate. Dynamic references and owner library plans still matter.

## Verification

- Native before/after registry:25,372 package identities and identical sorted hard/soft dependency sets; no new missing game reference.
- All25,372 native package files physically resolve inside the C project; all eight configured NPC runtime paths exist on C.
- Fourteen native loads pass: current Wayfarer station, tuning asset, one StaticMesh from each of the eleven relocated roots, and Spectrum overview. The final fresh NullRHI commandlet repeats this after retiring the old M live-source files, exit0; no new missing dependency.
- The first verification assertion incorrectly compared unordered dependency lists; package names and actual dependency sets were unchanged. That failed receipt is preserved. Corrected order-independent comparison passes in a fresh editor, exit0.
- Fresh CPU-only helper health/inference uses private ports18701/18702/18703 and the relocated C paths. Whisper ready1.532s, LuxTTS46.180s, station llama4.539s. Astra/Joy audio both transcribe exactly; dialogue returns a nonempty normal-stop reply. Owned helpers exit; source/config/reference guards remain unchanged.
- Source structural checks50 pass; Python compilation and content-source validation pass; six voice-cache tests pass.
- Git connectivity check passes before and after moving the abandoned temporary pack. Real Git packs and branches remain.
- Ninety migrated Blender scenes were inspected for external dependencies. Thirteen scenes with old path/provenance entries have exact originals archived on D; nine needed live/packed image path updates. A first save trial dropped an unused image and was rejected; originals were restored before the corrected save explicitly retained orphan images. Fresh reload verifies unchanged geometry/UVs, object/material inventories, armatures and animation ranges. An independent comparison of all13 scenes/123 image entries verifies identical external/packed image payload hashes. No live M/D library or image path remains in those inspected scenes; old weak appended-data provenance remains historical.
- No C++ change or rebuild, package/release change, microphone/listening validation, physical input acceptance or visual/performance claim.

## Cleanup receipts and limits

243 isolated-test CachedAssetRegistry files were removed:49.680 GiB reclaimed. Six rebuildable worktree compiler-cache files were moved to D with before/after SHA256 verification:14.282 GiB released on C, retained on D. The abandoned Git temporary repack was moved and verified:9.693 GiB released on C. The Medieval vendor DDC cache4.344 GiB was also archived. Normal shader caches, player saves, unique art and Codex conversations remain. Disposable isolated editor runs now document `-NoAssetRegistryCacheWrite` to avoid rebuilding those repeated test registries.

All22 cold vendor jobs are hash-verified:27.230 GiB. Together with the compiler/vendor caches, abandoned Git repack and original Blender scenes, the new D archive contains60,846,617,267 bytes (56.668 GiB) across14,436 indexed payload files. Its own `ArchiveIndex.json` and `ARCHIVE_README.txt` preserve recovery mapping and hashes without relying on C. Deleting this archive would not break the checked current game, but would discard recovery copies and the unique unused Medieval library.

Retirement followed fresh source/retained-copy hashes and exact-file size/mtime guards:54,950 files/136,000,857,168 bytes retired from M, plus996 files/1,670,679,943 bytes from C. This is source-volume space released, not additional net savings when the replacement copy was newly created. No recursive delete followed a junction. Sixty-five obsolete original M junction objects were removed without touching their C targets.

One388 KiB `FabLibrary/listings_v1.db` remains on M, locked by the background Epic Launcher. A scoped change to its on-disk vault setting was subsequently overwritten by the running launcher. Owner must fully exit the launcher before lead reapplies the C setting and retires the last verified DB copy; the game does not depend on this catalog. This is the only remaining regular file under the audited M project.

Automatic approval review rejected compiler/vendor-cache deletion and removal of14 parked obsolete junctions without a specific reason. The caches were safely archived instead; the14 junction objects remain isolated in the audit recovery folder and are not used by the game. No blanket Content, worktree, Temp or Codex-history deletion occurred.

Private evidence: `.agent/local/StorageAudit_20261020/` contains `StorageReport.html`, original/final inventories and CSV maps, duplicate hashes, per-file copy/retirement manifests, cutover records, protected-file hashes, rejected comparator/save-trial evidence, `AfterFinal/NativeVerification.json`, `BlenderPayloadVerification2.json`, `CloseoutMetrics.json` and `HelperHealth/Run/Result.json`. No licensed source payloads, local model weights or private conversation contents enter the PR. Pending owner check: open the usual C project and try a station conversation; prior gameplay/character acceptance remains separate.
