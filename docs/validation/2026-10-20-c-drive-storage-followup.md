# C-drive storage and Blender texture-tool follow-up

Date:2026-10-20. Owner-authorized local maintenance; no game build, native content change, package or merge.

## Storage measurement

The full C scan observed2,016,434 files and789 excluded reparse points. Allocation was deduplicated by file identity: a naive sum overcounts34.54GiB of hardlinks. Capacity is930.52GiB (999.14 decimal GB). Before cleanup, free space was16.72GiB; after selected cleanup it is approximately120GiB, a net increase of about103GiB. Background applications can change free space while measurements run.

| Before cleanup, distinct categories | Approximate allocated GiB |
| --- | ---: |
| SpaceSurvival including audit files |313.1|
| AppData, including AI, caches, Docker and temp |213.7|
| Program Files |123.2|
| Paging, hibernation and swap |57.6|
| Codex app data/history |51.1|
| Documents |32.0|
| ProgramData |23.8|
| Windows, hardlinks counted once |21.7|
| Program Files (x86) |17.6|
| Other measured directories |32.2|
| Protected/system/filesystem or otherwise unmeasured remainder |27.9|

These are rounded audit categories, not a claim that protected data was enumerated. The scan recorded367 access/enumeration errors and four allocation-query errors. Full private summaries retain those limits.

The initial narrow project inventory was311.336GiB: Content113.492, .agent82.137, Artifacts28.977, .git22.654, migrated editable sources17.276, downloaded assets16.476, game LocalRuntime11.715, Intermediate5.09 and DDC4.143GiB, plus smaller folders. The post-cleanup project is approximately278GiB excluding both storage-audit roots. Source and runtime content were not indiscriminately classified as cache.

## Actions and preservation

- M:37.536GiB unique standalone Comfy Desktop, OmniVoice cache and VoiceStudio runtime data copied with retained hardlinks and SHA verification; fresh two-copy verification preceded retirement of235,041 C files. Original app paths are compatibility junctions. Comfy health/model discovery and VoiceStudio Python/torch imports pass; complete standalone app workflows remain untested. The game's independent11.715GiB LocalRuntime stays physically on C.
- D:21 raw Fab download folders,5,560 files/10.840GiB, hash-archived under `D:/SpaceSurvival_StorageArchive_20261020/SourceDownloads/FabLibrary`. Exact old files retired; small C notes identify archive paths. No D runtime junctions created. The remaining mixed nested project and editable sources were retained.
- White hero:136 superseded `.blend`/`.blend1` files totaling18.199GiB retired only in three explicitly inventoried experiment roots. Latest `D:/Game Archive-User/SpaceSurvival_AssetArchive/EX7_Appearance_20261017/Rigged_20261019/Hero_EX7_Rigged_8K.blend` reloads with packed image payloads and no external libraries;45 associated native/export/texture files match their latest copies. Original `ApprovedFit_Source.blend` remains verified. Native Unreal hero assets and other characters were untouched; other D iterations were not blanket-pruned.
- Unreal:36.275GiB ordinary Common/project DerivedDataCache removed after no editor/compiler/Zen process was running and native/save/reparse guards passed. Zen/Data was retained. First use may rebuild caches; disk cleanup does not itself fix texture-pool over-budget warnings.
- Audit:four metadata databases totaling1.289GiB archived with hash verification to `D:/SpaceSurvival_StorageArchive_20261020/AuditDatabases`; compact manifests/reports retained on C.
- Automatic approval review rejected deletion of the failed first M staging copy, `M:/Local AI/AppData/Comfy-Desktop`. It remains unused and was not retried through another tool. The successful application destination is `Comfy-Desktop-Migrated`.

25,372 registered native package files and all eight configured NPC runtime paths still resolve inside C. Current-preflight native sizes/timestamps match after cleanup. The older migration hash guard failed for the rebuilt DLL and two owner-play saves; those files predate this cleanup and match its22:13 preflight metadata. The station map and suspend save still match their earlier hashes. The failed old comparison is retained; no rollback or claim of a new full native hash/gameplay pass is made.

Private evidence: `.agent/local/DownloadArchive_20261020/StorageReview.html`, `AfterSummary.json`, `PostCleanupValidation.json`, `WhiteRetired.json`, `UnrealCacheCleared.json`, `AI/Retired.json`, `SourceArchive/Retired.json` and `AuditDatabaseArchive.json`. Large scan databases and private machine paths are not published.

## Texture tools

Owner reported no Easy Textures model selector, a StableGen error and missing FLUX.2 Klein models. Easy Textures deliberately uses RealVisXL automatically; it is a simplified StableGen interface, not a separate engine. Local1.0.2 now identifies the automatic model and adds retrying Start/Refresh discovery. Fresh5.1.2/5.2.2 processes recover from empty/offline state to Ready in three probe polls.

The owner's exact `bpy_prop_collection[key]: key "Color2" not found` error was reproduced in Blender5.2.2 on an ordinary image-to-Principled material during Refine/Restyle. StableGen's emission-map exporter assumed a MixRGB input. The local installed5.1/5.2 repair accepts linked color outputs and constant base colors, handles every material slot, uses temporary object-linked copies and restores original slots even when output creation fails. Native image/constant/modern-Mix renders, shared-mesh preservation and injected-failure cleanup pass in both versions. No owner scene or preferences were saved. The Blender MCP live read was unavailable with429; the owner session was not controlled.

Klein9B, `qwen_3_8b_fp8mixed.safetensors` and `flux2-vae.safetensors` already existed on M. The texture server config omitted diffusion_models, text_encoders and vae. Adding those categories and restarting only the idle owned8190 server makes all three discoverable from StableGen. No models or dependencies were downloaded. This is discovery evidence, not a successful Klein inference claim.

Private repair backups and regression outputs: `M:/Local AI/Tools/BlenderTextureSetup_20261015/Repair_20261020`; setup instructions updated. Existing Blender sessions need save/restart to load the patched Python module. Owner's full-character generation/review remains pending in RPT-20261020-08. TRELLIS.2 was an unrelated optional-module warning, not the cause of Color2.

## Open / Check / Still open

- Open: the local StorageReview.html above and the installed Blender Easy Textures/StableGen panels; no new game build is delivered.
- Check: save/restart Blender, then retry the same Refine/Restyle operation; refresh the model list after choosing FLUX.2 Klein if evaluating it.
- Still open: full generation and owner appearance acceptance; remaining mixed Downloads/source classification; ordinary cache regrowth; Cloth default/white roster removal, market-stand removal, performance and real cloth physics. These are lead-owned work, not completed by storage maintenance.
