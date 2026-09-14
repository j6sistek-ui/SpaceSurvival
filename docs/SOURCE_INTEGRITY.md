# Source integrity across Git checkouts

**Project status: PARTIAL.** This document explains source serialization and retains the September 13 checkpoint below. The September 14 consolidation passed `source` and `core` CI on each merged PR head; the earlier pending-candidate wording is historical. Full Unreal authoring from a fresh checkout remains unverified, and public Git excludes licensed local inputs. See [PROJECT_STATE.md](PROJECT_STATE.md) for source/build/storage identity and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for active verification work.

The original mesh and candidate receipts recorded Windows CRLF bytes. Git stores these text files with LF, so the old exact-byte guard rejected unchanged source on checkout. The reproduced failure was the first `SM_AcornShip.obj` manifest check from commit `2e4ad847ec4424ca11f50f7e60d96776921e4793`.

`Scripts/SourceDigests.py` now accepts exact raw bytes or the complete alternate LF/CRLF representation for valid UTF-8 OBJ, MTL and JSON files. Mixed newlines, bare CR, invalid UTF-8 and NUL-containing data remain raw-only. It does not rewrite files, parse or reorder JSON, trim whitespace, add a final newline, remove a BOM, or relax geometry/material values. Binary assets, Python and HLSL remain exact.

| Pipeline area | Repair |
| --- | --- |
| Base source manifest | Portable source validation and `AuthorContent.read_sources` compare approved text representations; mesh geometry/index/normal/UV checks remain. |
| Starter and Swift hulls | Source report and existing material/mesh metadata guards accept the reviewed OBJ representation without relabeling old execution hashes. |
| Enemy candidates | Shared source checks replace the earlier two-file LF exception; reviewed palette and geometry identities remain. |
| Tail repair | The two recorded ray-selection JSON files accept complete newline conversion; GLBs remain exact. |
| Adopted asteroid materials | The three protected original asteroid OBJ references use the shared comparison; image bytes and built geometry stay guarded. |
| Field candidates | Protected OBJ/JSON references and source outputs use the helper. Composite material keys retain their verified reviewed OBJ digest. V3 is the current pipeline; V1/V2 remain candidate history. |
| Grip fit | Protected source and mesh metadata guards use the helper; Pilot/Exit binary animation identity remains exact. |

`ContentSource/ValidateSources.py` is read-only when called with no output path. Its command-line receipt defaults to `Saved/Validation/SourceFormats.json`; historical `ContentSource/source_validation.json` is not overwritten.

Run these from the repository root using an existing Python runtime:

```powershell
python Tests/TestSourceDigests.py
python Scripts/TestFreshCheckout.py --output Saved/Validation/FreshCheckout.json
python ContentSource/ValidateSources.py --check-only
```

`TestFreshCheckout.py` resolves an immutable Git commit and exports its actual `ContentSource`, `Content` and original hero bytes into a new temporary directory. It rejects links and path escapes, validates source references without regenerating content, and checks every exported byte before and after. Its receipt identifies the exported commit independently of the validator/helper implementation. Swift and Field V3 reports are mandatory when their author hooks exist in that same commit. Historical commits without those hooks may omit them. The two test commands are also in the source CI job.

At the September 13 checkpoint, the local run passed 13 focused tests and validated 507 files exported from `2e4ad847`: 26 meshes, 16 WAVs and 33 reviewed source references, with all 507 files unchanged. That exported commit lacked the then-pending Swift/V3 candidates. The worktree at that checkpoint passed 83 reference checks. The lead's repeated Content pass preserved all 110 Content files exactly; fresh rendering-enabled persisted validation passed on 2026-09-13 at 11:48 UTC. The first persisted validation failed the V3 shader-stat guard under NullRHI and was repeated with real RHI; no missing-stat skip was added.

The [focused receipt](validation/2026-09-13-source-line-endings.json) retains the original failure, final source hashes, full fresh-export result, raw log identities and the engine execution boundary. The final committed-candidate export and remote CI result were pending at that checkpoint; they are not current pending-CI claims. The later merge checks described above do not retroactively change the receipt's source or establish fresh Unreal authoring.

Historical standalone candidate generators and source-check scripts keep their recorded identities. In particular, old Field V1 runtime-source pins can require their original checkout; they are not the current main authoring pipeline. Source checks do not establish native visual quality, gameplay acceptance or the full Phase 1 Definition of Done.
