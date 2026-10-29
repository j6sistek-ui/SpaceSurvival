# Flight and station HUD spacing — October 29, 2026

RPT-20261029-02 continues PR102 after the owner annotated the wave-flight capture: move HUD elements outward to free the middle, and apply the same treatment to station HUD. The annotated reference remains local; no game artwork is regenerated.

## Implemented presentation

Keep wave/location information near the upper-left edge; use smaller upper-right radars. Move compact vitals and speed/boost information into the bottom corners, lower the weapon widget, and keep transient guidance and collision warnings above the central aiming area. Apply corresponding corner placement to station walking HUD and keep interaction prompts near the lower edge. Reticles, target labels, menu focus/hit behavior and conversation UI retain their existing roles.

## Verification

The canonical UE5.8.4 Editor rebuild passes in31.54s. Final module SHA256: `39180dfc06bb11975b0904c257c1a0eb4bd64f84b55a69f219744d0eb3069ebe`. Source structural checks50/50, digest tests13/13, scoped formatting and whitespace checks pass. The [wave receipt](2026-10-29-wave-flight.md) records24 passing native movement/integration cases on the preceding movement revision; gameplay code is unchanged by this HUD-only increment. Those tests are not claimed as rerun on the final HUD binary.

The existing capture harness, with the local300-second wall-clock allowance documented in the wave receipt, completes both final1920x1080 captures at UI scale1.0:

- Flight: `Artifacts/EndgameSoak/de0d5c2921bd4c6da256292dd1e9ce24/capture.json`,98seconds, all four Cruise/Turn/Boost/Brake images. Turn and Brake were visually inspected: compact corner vitals/drive, lower weapon panel, smaller upper-right radar and top-edge guidance leave the central flight area clear.
- Station/UI: `Artifacts/EndgameSoak/aebfdef0207d4b8ead984cc35c0fd020/capture.json`,76seconds, all six requested images. UIWalking and UIControlsAligned were visually inspected: the actual on-foot HUD uses peripheral title/currency/radar, and the controls menu remains readable without overlap. The fixture also validates menu hit bounds/focus and wardrobe scrolling.

Both receipts report success, unchanged production saves and binary artifacts, and no test save slots written. Captures use isolated profiles and hidden offscreen rendering; no owner's editor window or save is replaced. Existing engine/content/connectivity warnings remain recorded in the wave receipt. No packaged build or release is changed.

Collision warnings now use measured guidance height to remain above the aiming area; an active warning was not visible in the inspected final frames. Other resolutions/UI scales, natural play readability, physical-controller feel, performance and owner acceptance remain open under RPT-20261029-02 and RPT-20261029-01. Rendered captures verify this layout, not a complete player journey.
