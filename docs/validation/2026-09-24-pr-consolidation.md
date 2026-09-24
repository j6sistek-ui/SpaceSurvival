# PR consolidation and Blender refresh - 2026-09-24

Owner authorized merging all open PRs and refreshing the stale sandbox before the next task.
PR62 merged into main at56ebedb, PR60 into docs/station-authoring-process at6ae5ae0,
and PR63 into codex/flight-loop-reset atbcb28b5. PR58 carries the combined source to main.
Conflicts were confined to documentation; both histories and remaining acceptance gaps are retained.

The integrated Source, Config, ContentSource, SpaceSurvival.uproject, DA_Phase1.uasset and
Survival.umap match the built replacement-hero commit3d2ff3c byte-for-byte in Git.
No new gameplay code was authored, so the prior native build and two focused hero tests apply;
no additional Unreal build or full-game test sweep was run. Source structural and documentation
checks pass; GitHub source/core/documentation checks must pass before the final merge.
No package, itch upload, save changes, vendor-asset mutation or gameplay acceptance is claimed.

Background Blender5.2.2 regenerated the sandbox from the saved5522-placement scene.json,
then reopened it and checked every placement ID, asset path, target map and matrix.
Maximum matrix-element error is0.00001257658; all5522 IDs/assets match.
The source and output hashes are recorded in the companion JSON. The existing7431-placement
BuildingSandbox.blend was copied and checksum-verified as
BuildingSandbox-before-refresh-20260924.blend before promoting the new file to the usual name.
The refreshed duplicate is also retained as BuildingSandbox-Refreshed-20260924.blend.
No Unreal session or scene mutation was needed. The1325-entry library is unchanged.

Still open: actual cockpit boarding/fit, owner hero/input feel, station replacement, sandbox
brightness/doors/reflection/VSM checks and later packaging. Merge does not close those reports.
