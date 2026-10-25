# Entertainment observatory

Private, editable three-floor layout at
`/Game/SpaceSurvival/Licensed/EntertainmentObservatory/L_EntertainmentObservatory`.
The original station and two-floor workshop remain unchanged.

## Open the delivered level

In the canonical C-drive project, open that map in the Content Browser.
It uses the installed First Person template GameMode for a separate walking
review. It is not the normal game's startup map. The original crew wardrobe
and performance lounge are copied on the ground floor; their gameplay/service
bindings are not an integration claim for this new map.

Folders separate `01/ExistingLounge`, the middle and upper decks, seating,
Spectrum windows, stairs, chamber and lighting. All are ordinary editable
actors. The shared chamber is an architectural performance display with an
existing aerial clip; it does not implement a player zero-gravity volume or
solve the outstanding pole-contact animation work.

## Reproduction on a licensed local installation

These scripts are a construction receipt, not a startup hook. Do not replay
them over owner edits. Native vendor art is private and must already exist.

1. Run `build_modules.py` with the existing Blender in background mode. It
   creates twelve centimeter-scale FBX modules with explicit UCX collision
   and `SourceAssets/EntertainmentObservatory/Modules/Observatory_Modules.blend`.
2. Run `prepare_lounge.py` in a full Unreal editor with `-RenderOffscreen`,
   a private profile/layout, `-NoAutoSave` and `-NoAssetRegistryCacheWrite`.
   It refuses an existing destination and exits after copying the source
   workshop plus 414 lounge actors. Do not use a Python commandlet for the
   cross-world actor copy: the installed editor crashes on that route.
3. In a fresh hidden editor, run `author_observatory.py`. Existing `OBS/`
   actors cause a refusal unless an explicit reviewed rebuild override is
   supplied. That override is destructive to generated actors and must not
   be used after the owner starts editing. The source station is never saved.
4. Reopen the new map, inspect opposing views and landings, and test actual
   traversal. Geometry probes alone are insufficient.

The map references installed Spectrum Galaxy windows, sofas, recliners and
cups; its own glass override preserves the vendor material. Character source
packages and four customization Blueprints are reused, not duplicated again.
Native packages, source FBXs, packed Blender file and the full gallery remain
local. Git contains the recipes, concise evidence and four review screenshots.

See [construction and verification](../../../docs/validation/2026-10-23-entertainment-observatory.md)
and [saved station benchmark analysis](../../../docs/validation/2026-10-23-station-benchmark.md).
