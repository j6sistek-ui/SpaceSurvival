# Building sandbox and library refresh - 2026-09-23

Scope: RPT-20260922-04; private authoring tools/content only. Source branch
`codex/blender-library-popout`, PR60. No gameplay C++ build, package or itch update.

## Delivery and checks

- Unreal5.8.2 full library refresh:1,325 meshes/proxies;1,301 engine thumbnails plus24 Blender fallback
  thumbnails. Native Blender5.2.2 library:1,325 assets, no unavailable meshes. SS Link0.4.1 installed;
  prior add-on/preferences and project sources backed up.
- Private `/Game/Blender/Sandbox/BuildingSandbox_20260922`: Genesis High Settings saved natively at its
  origin; WorkStation113, StarterPack625, ComputerStation317 and FruitSeller2,685 actors copied with
  offsets. ComputerStation World Partition actors explicitly loaded. Other scenes share Genesis's
  environment; copied lights are movable. Five original source-map SHA256 hashes remain unchanged.
- Solid platform approximately242m by91m, four ramps, First Person template game-mode override and one
  PlayerStart.144 template assets copied privately from the installed engine. No gameplay map changed.
- Actual Unreal destination guard rejects wrong-map Push before material mutation. One linked floor
  moved10cm and restored successfully; final map saved.7,431 mesh placements exported with stable IDs.
- `BuildingSandbox.blend` built then reopened in Blender5.2.2:7,431 placements, area collections and
  correct destination map. Unreal keeps actor Blueprints, lights, effects and materials. Blueprint
  components are not editable Blender exports; only Genesis's level script carries into the sandbox.
- `OpenBuildingSandbox.ps1 -CheckOnly` passes with the launcher's ExecutionPolicy Bypass invocation.
- Focused `test_library_workflow.py` passes registration, per-object surfaces, material-only changes,
  duplicate IDs, prefab roundtrip, native assets, archive relocation and tampered/unsafe archive refusal.
- Changed Python compile checks,37 source structural checks, documentation gate and diff whitespace pass.
  No full gameplay suite: this change is authoring Python/configuration, exercised in actual UE/Blender.

## Private artifacts

`Artifacts` resolves to `M:/SpaceSurvival/Artifacts` on this desktop.

- `BuildingSandbox/build.json`, `layout.json`, `scene.json`: exact map/source hashes and links.
- `BuildingSandbox/BuildingSandbox.blend`:173,979,444 bytes; reopened successfully.
- `BuildingSandbox/SpaceSurvival-Library-0.4.1-final.zip`:1,325 assets,4,002 manifested files;
  Final ZIP 3,336,954,234 bytes; all4,002 hashes independently verified. SHA256
  `b688da3b3c2d94f9f7d37d88f1970d282798b4fe95bd3ab80c1472794415a670`; full receipt `portable-verified.json`.
- `VaultRefresh-20260922`: raw refresh/build/install/copy logs, cleanup proof and manifests.
- `PrefabLibrary`: active catalog, proxies, thumbnails and native Blender asset library.

## Authorized cleanup

All4,944 new bundle files and2,827 files in22 other complete native packs matched retained project
files by SHA256. Resolved retained paths were checked against all deletion roots: zero references
back into those downloads. The cleanup dry-run preceded application; every target was validated before
removal.23 folders removed,54,980,195,863 bytes (about51.2GiB), from the C: VaultCache and M:/Downlloaded.
Non-content metadata copied and verified under `VaultRefresh-20260922/RetainedManifests` first. Project
assets, unique FBX/GLB/Blender sources and incomplete or modified packs retained. A separate intermediate
ZIP produced by this task was also removed after the final ZIP verified (3,336,954,027 bytes).

## Retained failures and limits

- Empty foliage infrastructure initially caused a copy-count mismatch; excluded after inspecting the
  engine export behavior. FruitSeller's later mismatch was one editor-only GroupActor; non-group actor
  class counts match. No populated foliage component appeared in the source/target probe.
- Loading the assembled inactive world in the same process hit Unreal's retained-world GC assertion.
  Saved areas survived; finalization in a fresh process passes. Builder now requires a fresh resume pass.
- Blender initially refused the engine Plane because it was outside the catalog. Explicit1m plane
  geometry repaired it; final scene build/reopen passes.
- SceneCapture previews: initial and fixed-exposure shots white; final diagnostic with post-process
  volume disabled in memory dark. No exposure/lighting edits saved. These images do not establish visual
  acceptance. Three bounded capture cycles stopped; owner editor view/physical walking and performance
  remain open, including passage clearance and final material appearance.
- One preview-only directional-light accessor was corrected to component lookup; first launcher check
  omitted ExecutionPolicy Bypass and was rerun with the actual launcher setting. ZIP verification was
  started before packaging finished and rerun only after completion; no partial ZIP was accepted.

Next: open the owner launcher, press Play, walk between the scenes and try one selected Blender prop
Push with the sandbox open. Lead retains visual/live-window/refresh checks under RPT-20260922-04.
