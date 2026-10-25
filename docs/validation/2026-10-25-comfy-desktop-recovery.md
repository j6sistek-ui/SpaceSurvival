# Comfy Desktop recovery — October 25, 2026

Scope: RPT-20261020-07. The owner requested one working ComfyUI, preservation of workflows/models, and deletion of old temporary/generated work; existing D backups suffice. No Unreal or Blender launched.

## Diagnosis and repair

- `C:/Users/j6sis/AppData/Local/Comfy-Desktop` already correctly resolves to `M:/Local AI/AppData/Comfy-Desktop-Migrated`. The separate non-Migrated M folder was incomplete staging, not the active installation.
- Desktop selected ComfyUI0.39.2, whose standalone environment lacked torch and several support packages required by its source. The October20 migration manifest already lacked torch for that selected environment; prior health evidence exercised ComfyUI(1) instead. Copy equality did not establish Desktop health.
- Restored4059 missing torch-family files from the matching local environment using NTFS hardlinks, preserving data blocks without duplicating2.85GB. Installed nine support packages selected by the existing0.39.2 requirements after a pip dry-run. Restored eight already-present optional dependencies from the retained internal environment for UltraTex/custom nodes without extra payload copies. No global/system Python changed.
- Removed incomplete staging, ComfyUI(1), installer download cache, and old input/output/temp/log/snapshot files. Physical M free space rose from321,968,312,320 to332,144,246,784 bytes during the measured interval, approximately9.48GiB; logical hardlink sizes must not be treated as reclaimed capacity.
- The single local launcher entry now points directly to `M:/Local AI/AppData/Comfy-Desktop-Migrated/ComfyUI-Installs/ComfyUI`. Blender's texture-server launcher and comfy-cli now use that install. Comfy Cloud is a remote service entry, not a second installed runtime. The C compatibility junction remains intact.
- Automatic approval review rejected a combined cosmetic root-rename/junction-replacement operation without a specific reason. It was not retried; retaining the working root/link fulfilled consolidation safely.

## Preservation and verification

23 existing workflow graphs and their index stayed unchanged;44 additional distinct graphs were extracted from old image metadata before cleanup. The workflow API lists67 graphs. All105 original/recovered protected file hashes pass. UltraTex's99MB decoder remains inside the active model folder; global `M:/Local AI` model folders were untouched. No bulk D backup was made; two tiny pre-change launcher configuration receipts remain there.

Missing-torch reproduction, the initial `comfy_aimdo.storage` failure, package dry-run/apply receipts and final checks are retained privately in `.agent/local/ComfyDesktopRepair_20261025`. Final CPU-only startup with Manager and installed custom nodes returns HTTP200, reports ComfyUI0.39.2/PyTorch2.12.1+cu130/device CPU, registers GGUF plus nine UltraTex nodes, and lists67 workflows. `pip check`: no broken requirements. All owned probe processes stopped; no model inference was queued.

## Open / Check / Still open

**Open:** Comfy Desktop, the single local ComfyUI entry. **Check:** Start opens the workspace; saved/recovered workflows and models are visible; when VRAM is available, one known workflow generates correctly. Previous image input paths may require selecting new inputs because old work files were explicitly deleted.

**Still open:** normal Desktop backend Start, GPU generation, each workflow's dependencies and Blender texture generation after repointing are not validated by CPU startup. The optional Qwen GGUF PromptEnhancer lacks `llama_cpp`; Matrix sharing lacks `matrix-nio`; neither prevents the server from starting. These are not silently accepted or repaired by adding unrelated packages. Game/runtime/package identity and existing character-texture rejection are unchanged.

After the owner reopened the app at15:03UTC, `app.log` reports Comfy Desktop1.1.8 (previously1.1.7). Readback still contains one local instance with the same ID and M path; physical directory checks find no new installation. The visible install was the Desktop application update. This does not validate a subsequent GPU generation.
