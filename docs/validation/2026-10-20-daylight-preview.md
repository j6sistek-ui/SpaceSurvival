# Station daylight editing preview — October20,2026

Owner scope: record remaining Unreal runtime reports and provide ordinary daylight for the owner's station redesign. This is an editor authoring aid, not a permanent art-direction change or runtime-performance repair. Active work remains in RPT-20261020-04 through -06 and -09 through -12, plus existing character/cloth entries.

## Delivered

`Content/Python/ss_daylight.py` registers two SS Prefabs commands at editor startup. Enable requires the current Wayfarer map with Play stopped. Four transient editor-only actors provide a30000-lux sun, specified daylight ambient cubemap, SkyAtmosphere and fixed exposure. Existing global lights/starfield are temporarily hidden only in the editor, with their exact prior visibility retained. Disable restores those flags and destroys only the preview rig. Repeated enable first removes the previous rig. No original light intensities, materials, map packages, user settings or saves are written. Reopening the map/session requires enabling the preview again.

The installed project uses legacy exposure luminance (`r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=0`), so min/max brightness use2048 rather than an EV value. An initial EV-style trial was visibly overexposed and rejected. The alternate extended-range code path uses14EV; that alternate project setting was not separately tested.

## Native verification and limits

Final isolated real-RHI editor profile `b872766ca7784afa9a3ec5f241c12847`:

- Menu registration, before/daylight captures, four preview actors and ordinary Play run verified.
- All9483 original actor references remain valid; their original temporary editor visibility is restored.
- No preview actors remain after disable, and zero preview actors appear in Play.
- Saved Wayfarer SHA256 remains unchanged; production save snapshot remains unchanged.
- Editor exits0. Earlier attempts included a menu-owner type error, overexposure and an invalid total-actor-count assertion because level instances loaded additional actors. A subsequent passing check had an access-violation exit after log shutdown; retained as failed evidence. Final harness releases its actor/capture references before exit and passes cleanly. No exact crash cause is claimed.
- Python compilation,50 source-structure checks, documentation gate and scoped Git whitespace checks pass. No C++ changed, so no new native build or package was needed or produced.

Private evidence is `.agent/local/DaylightPreview_20261020`: `Result.json`, `Exit.json`, `Before.png`, `Daylight.png`, retained rejected attempts and launch/profile logs. The final image is a useful outdoor authoring view, not a new station art-quality acceptance. Existing dark celestial backdrop/interior materials were not redesigned. Owner editing comfort and natural gameplay/performance remain untested.

The apartment's existing `BP_Blinds` missing Frame/Rope Material construction errors occur in both the earlier owner play log and this verification; recorded separately as RPT-20261020-12. The daylight test does not establish an error-free game.

## Runtime baseline retained in the open log

The earlier isolated TextureAudit4 used a1000MiB streaming pool with local dialogue AI disabled. Required streaming bytes correspond to Market1335.08MiB, Restaurant1327.63MiB, Lounge1819.82MiB and Apartment1399.06MiB. EX7's48 texture resources total886.6MiB resident across those views. These are different accounting categories; resident/non-streaming totals are not additional streaming-pool requirements. No new optimized benchmark is claimed. Cloth default/white retirement, bounded market removal, cloth physics, Silver and Lira remain open.

## Open / Check / Still open

- Open the canonical `Edit Current Station.cmd`; choose **SS Prefabs > Daylight editing preview**.
- Check whether the authoring view is comfortable; **Restore game lighting** returns the previous editor lighting. Save actual station edits normally before Play.
- Still open: owner comfort, existing runtime issues and all listed gameplay/cloth acceptance. This Python feature is local and source-reviewable; no package or merge.
