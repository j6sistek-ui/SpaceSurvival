# Silver development cleanup — 2026-10-13

The owner requested removal of obsolete character iterations while preserving originals, current editable assets and transferable repair knowledge. Cleanup was limited to this thread's ViableEld work folders. No new asset optimization or gameplay change was made.

## Result

- Deleted22,467 explicitly inventoried files:51,207,807,541 bytes (51.21 GB /47.69 GiB).
- M: ViableEld work folder:40,138,038,907 bytes removed.
- C: current task scratch:1,494,073,519 bytes removed; earlier archived scratch:9,575,695,115 bytes removed.
- Removed obsolete Blender experiments/backups, caches belonging to discarded experiments, private offscreen editor cache files and raw native GIF frames after retaining the encoded GIF/contact sheet/timings.
- Preserved four original Downloads GLBs,15 selected editable models,856 current hair-cache frames, all scripts/reports/numerical data/import-export sources and useful diagnostic images, final GIF, apartment view, current station map and every asset in the native ViableEld namespace.
- All4,437 retained-file SHA-256 checks pass; no planned deletion target remains. Current Blender dependency inspection confirms packed images and no linked library or Alembic dependency. No editor was launched for gameplay, no current game asset was deleted and an unrelated running editor was left alone.

## Recovery and audit

Use [the retained source and rigging guide](../production/SILVER_CHARACTER_PIPELINE.md) for the current master, key donors and lessons. The manual shoulder study remains explicitly unadopted.

Exact local inventory, reasons, sizes, retained hashes, deletion receipt and post-delete verification are under `.agent/local/ViableEldFinish_20261013/Cleanup/`. Deletion-plan SHA-256: `7b77e933215d8a87ca9c3ac66bf14f9222ce494542327f79a4a61f7c4ecab214`.

Old diagnostic receipts retain references to intentionally discarded scratch copies; they are historical evidence, not guaranteed rerunnable commands. The guide identifies the retained reconstruction inputs. Native assets and local licensed sources remain private, not backed up by GitHub.

The byte total comes from successfully removed manifest entries, not the change in whole-drive free space, which can also reflect other work. Documentation checks apply to this docs-only repository update; no C++ build, package, release or merge occurred. Earlier motion/dialogue/owner acceptance limits remain open.
