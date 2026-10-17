# October17 floating repair contact preview

RPT-20261016-14 remains partial. A separate local map adds a fitted blue-and-steel ratchet and repair target to the owned Space Crew floating wrench Start / Loop / Loop / End clips. It is a staged contact example on Manny, not new station AI or a changed crew role.

## Native content

Folder: `/Game/SpaceSurvival/Licensed/StationAssets/MaintenancePreview_20261017`.

- Map: `L_MaintenanceContact`; current SHA-256 `b3072efb7ad281c13342cc90d1572483c1e1ed5da9be2f8ecc427514a08ab392`.
- Use `LS_FloatingRepairContactV2` at30fps,315frames/about10.5seconds. The original failed `LS_FloatingRepairContact` is retained only as evidence; the placed player uses V2.
- `SM_MaintenanceRatchet` is original locally authored geometry,3884triangles, with three materials. Its saved attachment follows `hand_r`. No purchase, generation service or host installation.
- A keyed actor-position correction of at most1.8695cm reduces the authored tool-end drift. Original animation bone tracks, rig and pack files are unchanged. The tool head stays on the bolt while the character floats. The left hand retains the authored bracing pose; this does not prove collision-safe support on arbitrary surfaces.
- Neutral preview materials and lighting make pose/contact inspection legible. These are not a proposed replacement for station lighting or finished environment art.

## Verification and retained failures

Initial native live playback records2723samples, two wraps and pause/resume. The working end stays within0.169cm of its target during the repair loop; the tool follows the wrist with zero sampled separation.

The first fresh reload exposed a real failure: all three sequence bindings resolved to zero objects because they were authored while the map still had a temporary name. Sequence time advanced while the saved pose stayed frozen. The106-frame capture and its insufficient contact-only check are rejected and retained under `Reload/FramesRejected.json`; they are not motion evidence. V2 was authored against the permanent saved-world actors. The fresh verification now requires all three bindings to resolve, and frame verification requires substantial hand travel plus agreement with the expected poses.

Fresh V2 reload finds12assets, three resolved bindings, the `hand_r` attachment and clean packages. The106native frames include Start, both repair blocks and End. Hand-height range is67.349cm; maximum expected tool-tip error across the whole sequence is0.21718cm, with repair-loop error0.16451cm and zero sampled tool-follow separation. Overview frames were visually reviewed; final natural movement and production-character contacts remain separate checks.

The initial pose export used an unavailable direct skeleton property, corrected to `get_editor_property`. A save attempted during Play was refused and then performed after ending Play. Early dark/cropped inspection views are retained. The isolated empty-sky capture supplied no useful ambient reflection; the preview uses a specified engine cubemap and a matte inspection panel. This follows Epic's [Sky Lights documentation](https://dev.epicgames.com/documentation/unreal-engine/sky-lights-in-unreal-engine), checked October17 against installed5.8 `SkyLightComponent.h`. No station lighting change.

All16guarded files retain their hashes: canonical module, station map, original teaching map/sequence and both original/previously retargeted wrench sets. Current module remains6566a257 and station7431ed23. No C++ changed, so no new build or gameplay regression suite was needed. Documentation/whitespace checks accompany publication. No cook, package, merge, station placement, save-schema change or hero/squirrel change.

## Open and next

Local review: `C:/Users/j6sis/SpaceSurvival/.agent/local/MaintenanceContact_20261017/Review.html`; native frames are in `M:/SpaceSurvival/Artifacts/MaintenanceContact_20261017/FramesV2`. The HTML uses these unedited native frames at10fps and has static path checks; browser interaction remains unverified because the earlier browser tool blocked local-file navigation.

Native/private assets and the ratchet `.blend`/FBX remain local; this PR publishes the guide and evidence. The `.agent/local/MaintenanceContact_20261017` receipts preserve source poses, pivot fit, first failed reload, repaired bindings, captures and guarded hashes.

Lead next: fit a production maintenance character, choose a bounded station location, verify approach/exit and tool contacts, interruption/resume and clear player paths. Owner appearance/behavior feedback remains pending without stopping independent work. No full maintenance-crew or Phase1 completion claim.
