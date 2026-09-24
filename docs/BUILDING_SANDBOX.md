# Building sandbox workflow

This authoring sandbox combines copies of the owned Sci-Fi Bundle examples: Genesis High Settings,
WorkStation, StarterPack Classic, ComputerStation and FruitSeller. It is a candidate architectural
foundation to review before changing the gameplay station. Vendor source maps remain separate.
Current preparation and acceptance status belongs to RPT-20260922-04 in [KNOWN_ISSUES](KNOWN_ISSUES.md).

## Open and edit

The generated `Artifacts/BuildingSandbox/build.json` identifies the exact Unreal map and its source
examples. Double-click **Open Building Sandbox.cmd**, or open that map in the original SpaceSurvival project. Use Play to walk with the sandbox's
First Person template pawn. This map has its own game-mode override; it does not start a survival run.

Open `Artifacts/BuildingSandbox/BuildingSandbox.blend` in Blender with SS Link 0.4.1 or newer installed.
Use that version on both desktop and laptop so the destination-map safeguard is active. Collections
group the examples. The scene contains linked static-mesh placements, using the library's real mesh
proxies. Proxies are for layout: Unreal's original material graphs, lighting, effects and Blueprint
actors remain in Unreal. They are not converted into equivalent Blender shader graphs or scripts.

1. Save a working copy of the `.blend` before experimenting.
2. In Unreal, open the sandbox map named in the Blender file's `START HERE` text.
3. In Blender, use **SS Link > Connect**, select the parts you changed, then **Push**.
4. Inspect the result in Unreal and save the map. Save your `.blend` too.

Start with one moved wall or prop to learn the round trip. Keep Live off until that is comfortable.
The scene's `ss_target_map` property blocks Push/Live into another map, before creating materials or
moving actors. Do not remove it. A newly created unrelated Blender file has no such destination lock.
Deleting a Blender object is not a request to delete every unmatched Unreal actor; normal explicit
Push sends the selected placements. The existing Live removal safeguards still apply.

Simple per-placement material presets and properties use SS Link's surface overrides, described in
[Prefab live link](PREFAB_LIVE_LINK.md). Arbitrary Blender shader nodes are not translated into Unreal.
Vendor mesh and material defaults remain shared originals; edit individual placement overrides when
you want only one wall to become glass or a mirror.

## Laptop use

Export the refreshed library with **Export Library** on the desktop and import that ZIP through
**Import Library** on the laptop. Copy the `.blend` separately. Mesh paths and placement IDs remain
inside the scene, so the file can return to the desktop and reconnect to the same sandbox. The laptop
does not need Unreal for arranging the mesh proxies. It does need Blender and SS Link. New assets
created after the export require another library export/import.

## Rebuilding the initial sandbox

`Scripts/SurveyBuildingSandbox.py` records source actors, bounds, floor candidates and light settings.
`Scripts/AuthorBuildingSandbox.py` consumes the reviewed layout in
`Scripts/BuildingSandboxLayout.json` (an artifact layout can override it); it refuses to overwrite an existing destination. Run these
inside the installed Unreal editor with the offscreen flags in [CLAUDE.md](../CLAUDE.md).

The authoring pass copies actors into a separate `/Game/Blender/Sandbox/` map, adds a connected solid
floor, assigns the First Person template game mode, and exports static-mesh links to `scene.json`.
Genesis is saved as a native map copy to preserve its High Settings world and level-script setup.
Lights copied from the other four scenes use movable lighting because their source maps' baked lighting
cannot follow actor duplication. Genesis provides the shared sky/post-process setup; duplicate global
environments from the other examples are omitted. This is a dynamic authoring preview, not a claim
that the combined scenes meet the game's performance target.

`Tools/SSLiveLink/build_sandbox_scene.py`, run in background Blender, consumes `scene.json` and builds
the `.blend`. It refuses to overwrite a working scene and rejects missing library proxies. Neither
script changes the game's default map or the published package. Template content, vendor content,
generated maps, previews and `.blend` files stay local/private; the scripts and handoff documents are
the reviewable repository changes.

After native actor copies save, run the authoring script again in a fresh editor process with
`SS_SANDBOX_RESUME=1` to finalize. This avoids retaining the inactive copied world across map-load GC.
The vendor maps are checksum-protected. Only Genesis retains its level script; other examples retain
actor Blueprints but do not merge their level scripts. Final visual/walking acceptance remains open.

### September 24 UTC: sandbox whiteout and editor camera drift

Owner reported an unreadable exterior and doors without usable controls. The open sandbox
inherited manual physical exposure compensation +10.7 and FFT bloom intensity8/size4.
Sandbox-only histogram exposure, zero compensation and moderate standard bloom were applied
and saved after a dry run and private map backup. Overview and ground-level captures show
the exterior again. Fog visibility was restored after an inconclusive diagnostic.
Editor joystick navigation was separately disabled and persisted in local user preferences:
the camera had drifted from roughly16m to1.6km high. Gameplay controller input is unchanged.

All60 door-labelled placements inspected are static meshes. Lit lock graphics are materials;
the sandbox builder adds no opening control. Genesis level-script interaction remains
unverified. No door animation/interaction was added. Next: owner Play check outside/inside.
See [repair evidence](validation/2026-09-24-sandbox-visibility.json).

Color follow-up: the owner rejected the amber cast. The sandbox's full-strength Kodak02
film LUT and depth-fog post-process material were disabled, white balance/tint reset, warm
4250K sunlight disabled and Rayleigh scattering returned to the engine default. Native
materials and original vendor scenes remain intact. Candidate saved; owner color and
interior-walking acceptance still open. Editor joystick navigation remains disabled only
in local editor preferences.
