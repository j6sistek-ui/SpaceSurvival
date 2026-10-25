# NVIDIA graphics integration and Unreal folder repair

October23,2026. Active follow-ups: RPT-20261022-01 (graphics),
RPT-20261023-01 (engine paths), RPT-20261020-04 (performance/shaders).

## Delivered locally

Pause > Settings > Graphics contains Image & Performance, Advanced and Display.
The existing Figma art and fonts are retained. Controls bind to the installed
NVIDIA capability APIs, including supported DLSS quality and frame-generation
modes. DLSS, DLAA, native TSR and NIS are alternatives. FG requires Reflex;
the prior Reflex preference is restored when FG is disabled. Unsupported
options explain their requirements. Ray Reconstruction remains unavailable
with the current hardware-ray-tracing path disabled.

Changes remain a draft until Apply; Back cancels, and Defaults only stages.
Existing quality, blur, FPS limit and diagnostics remain available. The new
`NVIDIA1` settings suffix retains old-save decoding and rejects invalid values.
The UI reports rendered/displayed FPS separately; unknown values are not zero.
Range rows use click or left/right steps, not pointer dragging.

Latest combined local Editor DLL SHA256:
`70234269350d35c2533a0ea14ee1c5d3a6f9452bcce5eaef7e8b658f934d9c57`.
This is the owner's combined development checkout, not an isolated PR-only
binary or a new packaged release. Native maps/characters were not changed.

## Engine repair

- Complete UE5.8.4 (CL58902052, compatibility55116800) now resides at
  `C:/Program Files/Epic Games/UE_5.8`. The owner moved it after our attempted
  folder move was denied by Windows permissions. No reinstall occurred.
- The previous standard location contained plugins only. All1218files were
  copied and SHA-verified at
  `D:/SpaceSurvival_AssetArchive/UnrealFolderRepair_20261023/PluginOnlyPreviousFolder`.
  Its manifest is `ArchivedFiles.json`. Unique Fab/Bridge files were retained
  in the full engine, and nine NVIDIA plugin folders moved under Marketplace.
- Ten launcher files now point to the standard path, preserving unrelated
  records. The stale engine version entry now matches the engine's5.8.4 item.
  Desktop shortcut and Blender5.1/5.2 SS Link configuration paths also resolve
  there. Original records are backed up under the same archive's LauncherRecords.
- Native build succeeds from the new location. Launcher UI/project reopening
  still needs the owner's normal-use check; the launcher was not opened here.
- Temporary project NVIDIA copies remain. Automatic approval review blocked
  the combined cleanup/script command with `blocked by policy`; it made no
  changes and was not retried. They are private, not committed.

## Verification

- Editor Build4:251actions,110.96seconds, PASS after relocation; existing engine
  and vendor deprecation warnings remain. Final startup repair Build5:8.82s PASS.
- Portable native C++17 `/W4 /WX`:780assertions PASS. Docker was unavailable;
  this is not a replacement for the container CI/sanitizer gates.
- Seven targeted native settings/menu tests:0failed,0not-run,3clean successes
  and4successes-with-warnings. Existing welcome-footprint and HTTP warnings
  prevent calling this a clean strict suite. No full game suite was run.
- D3D12/SM6 mode check on RTX5080/driver621.01: native100%, DLSS Quality66.70%,
  DLAA100%, NIS66.67%; FG/Reflex enable/restore assertions pass. Queried support:
  DLSS/DLAA/FG/Reflex/NIS/vibrance yes, RR no. The repeat has0test warnings.
  Mode state does not prove generated frames reached a physical display.
- Three1920x1080 standalone `-game -RenderOffscreen` pages were inspected.
  Final capture483fcfcd53a34cf1b907a7fd508165e5 passes hit bounds, unchanged
  account/run/settings state, production-save hashes, no test save slots and
  compiled-artifact preservation. Normal exit0; no NVIDIA error/ensure.
- First capturefcedcb6fb3134bc9912faa69760aadc4 is retained as a **failed startup
  result**, despite its older screenshot-only harness success. It exposed
  premature API calls from GameInstance::Init, including NIS caching a missing
  cvar. Renderer readiness now waits for engine/vendor readiness, and OnStart
  reapplies on the first engine tick. The capture gate now rejects those errors.
- Source structural50, UI provenance34, Python compile, content formats26meshes/
  17WAV and documentation navigation checks pass. Production save hashes and
  the owner's HEAD/index are preserved; publication uses an isolated worktree.

Private evidence: `.agent/local/NvidiaIntegration_20261023` (build/test reports,
launcher readback, backups and guards). Capture pointer:
`Artifacts/EnvironmentRefresh/NvidiaGraphicsFinal.json`.

## Shader findings and remaining work

Ordinary startup reports writable DDC and unchanged shader autogen, not a
proven full-cache rebuild. First NVIDIA rendering compiled120 NIS variants;
the next mode test did not repeat that batch. Full game startup identifies
recurring missing Nanite usage flags on M_Lights, MI_InteriorGraphic_Clear and
M_Reg_Glass. Their exact packages and translucent/Nanite warnings are retained
under RPT-20261020-04. Check intended mesh/material compatibility before saving
flags. PSO hitches also remain; no cache purge or stutter fix is claimed.

AI retains physical-presentation/frame-pacing investigation, representative
VRAM/latency/image comparisons and packaged validation. James should check
normal launcher use, Apply/restart persistence and motion/HUD quality. Builds,
synthetic navigation and screenshots do not establish physical controller,
ghosting, performance or owner acceptance. ClickUp updates are queued privately
while its connector quota is exhausted; no remote sync claim.

## Rendered menu pages

[Image & Performance](images/nvidia-graphics-20261023/UIGraphicsMain.png),
[Advanced](images/nvidia-graphics-20261023/UIGraphicsAdvanced.png),
[Display](images/nvidia-graphics-20261023/UIGraphicsDisplay.png).
These are actual uncooked-game captures; displayed measurements are capture-time
observations, not benchmark results.
