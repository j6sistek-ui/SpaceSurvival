# SS Link v0.4.0 focused validation - 2026-09-22

Scope: RPT-20260922-04, large Blender library window, full current static-mesh catalog,
portable Export/Import, incremental refresh and private simple material overrides.
Source branch `codex/blender-library-popout`, based on `1719f15`; no gameplay C++ changes.

## Results

| Check | Evidence / result |
| --- | --- |
| Current Unreal inventory and GLB export | 677 static meshes from `/Game`, all 677 GLBs exported, no failed proxies. Owner project read through installed UE5.8.2 offscreen; output staged separately before deployment. |
| Thumbnails | 665 engine previews; background Blender filled 12 missing previews, no failed fallback renders. |
| Native library build | Blender5.2.2: 677 native asset files, 677 rebuilt, no unavailable meshes. Real GLB geometry, stable asset paths and categories; library templates have no reusable placement IDs. |
| Focused Blender batch | `Tools/SSLiveLink/test_library_workflow.py` with `--background --factory-startup --python-exit-code 1`: PASS. Registration/re-registration, private material isolation, material-only update signature, duplicate IDs, prefab material roundtrip, unsupported graph rejection, native library registration, native asset identity, unchanged rebuild=0, archive relocation, traversal/tampering rejection and stale export refusal. |
| Unreal material batch | `Scripts/TestBlenderSurfaces.py` through `UnrealEditor-Cmd.exe <owner-project> -unattended -RenderOffscreen -NoSound -DisablePlugins=UAssetBrowser -ExecutePythonScript=<test>`: process0, `SS_SURFACE_TEST_OK`. Opaque/translucent creation, deterministic reuse, unchanged engine Cube default material and invalid slot refusal. Exactly two test materials removed afterward. |
| Desktop installation | Existing Blender5.2.2 user add-on upgraded and enabled, project root `C:/Users/j6sis/SpaceSurvival`, native library registered. Installer backs up prior add-on/config/preferences. |
| Portable ZIP | 677 entries, 2,057 manifested files, no missing previews. Every manifested file independently re-read from the final ZIP and SHA256 verified. ZIP 2,912,891,185 bytes; SHA256 `a84112b1a4889e65dd9231857db8ee7b133bf9f117f5c36376b2d1c2053d9a18`. |
| Source checks | Python compileall for changed tools/editor modules/test; `Scripts/CheckProject.py` PASS37; `Scripts/CheckPrDocumentation.py --repo .` PASS; `git diff --check` clean. No C++ build/full gameplay suite: Python authoring tools only, actual Blender asset build and Unreal script execution above. |

Raw logs/JSON and portable ZIP are in the implementation worktree's ignored `Artifacts/LibraryReview`.
The ZIP is `SpaceSurvival-Library-0.4.0-20260922.zip`; it is private owned content, not a GitHub attachment.
Desktop cache is `C:/Users/j6sis/SpaceSurvival/Artifacts/PrefabLibrary`.

## Failures retained and fixes

- Initial relative native-library output resolved outside the intended directory and failed. Explicit
  absolute output fixed it; final full677 build passed.
- Restricted Unreal export could not write its existing DDC. Approved offscreen rerun using the
  installed cache succeeded. No toolchain packages installed.
- First real add-on install exposed Blender5.2's unsupported `APPEND_REUSE` enum. Changed to supported
  `APPEND`, added actual native-library registration to the focused test, then installed successfully.
- First full ZIP hit a full disk. Deleted only the failed ZIP and this task's redundant staging copies
  after verifying the deployed native677 cache. Original library backup remains. Added free-space
  checks, temporary archive cleanup and refusal to overwrite an existing export. Final ZIP verifies;
  approximately5.4GiB disk free afterward. Raw logs retain export/install failures.

## Deployment boundaries and remaining checks

Before local deployment, every pre-existing changed authoring file in the original checkout matched
the implementation base. Backups of those sources and the old cache are under
`Artifacts/LiveLink/Backups/Library-0.4.0-20260922`. Only scoped Python/add-on sources and generated cache
were deployed. Owner map/uproject/imports preserved. This is local delivery, not a Git merge; no game
package or itch publication was performed. Blender5.1 was not upgraded or validated in this batch.

Blender MCP returned unavailable/429. Headless checks do **not** establish live pop-out drag/drop,
cross-monitor usability, idle Unreal auto-refresh behavior, desktop/laptop physical transfer or final
glass/reflection appearance. Those remain open with the lead under RPT-20260922-04. Open Blender5.2,
SS Link > Pop Out Library; check placing a mesh, then Export/Import on the laptop. Restart Unreal for
the updated Python refresh/material handlers. Material output is six constant PBR properties only;
mirror finish depends on scene reflections. Full shader/Blueprint/rig fidelity is not claimed.
