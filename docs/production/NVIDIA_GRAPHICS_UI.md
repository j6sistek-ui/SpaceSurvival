# NVIDIA graphics menu

Owner request: October 22, 2026. Engineering follow-up: **RPT-20261022-01** in
[the canonical issue log](../KNOWN_ISSUES.md). The October22 Figma proposal was implemented locally after the owner explicitly
authorized integration on October23; the earlier VRAM hold is superseded.

## Open the design

[Graphics menu](https://www.figma.com/design/6M3VvUB7jsPDd3E41YpKM0/SpaceSurvival-UI-Kit?node-id=334-1426),
on `15 · GRAPHICS / NVIDIA — Oct 22 staging` (`334:1424`):

- Pause graphics-entry study: `334:1425`.
- Image and performance: `334:1426`.
- Advanced controls: `334:1427`.
- Unsupported-feature example: `334:1428`.
- Scope, mode rules and integration notes: `334:1430`.

Four 1920×1080 frames use editable text, existing kit artwork, six reusable
setting-row components, existing colour/spacing variables and the established
Keania One, Rajdhani and IBM Plex Mono fonts. Fourteen prototype links connect
the staged screens and review notes. These are navigation examples, not a
working renderer/settings implementation. Apply, Defaults and switch values
are illustrative. The pause study shows the new entry rather than replacing
the complete existing pause action list. Existing main-menu and review pages
were preserved.

## Controls and intended behaviour

| Control | Staged options / rule |
| --- | --- |
| Image reconstruction | Native/TSR, DLSS Super Resolution, DLAA, NVIDIA Image Scaling; one active method. |
| DLSS quality | Populate from supported modes; the proposal lists Quality, Balanced, Performance and Ultra Performance. DLAA uses native resolution, so upscaling quality is disabled/hidden. Do not expose an unsupported Ultra Quality enum. |
| Frame Generation | Independent On/Off switch, plus a supported-mode selector. Package enums contain Auto, Dynamic and 2×–6×. Runtime capability queries decide which appear; Auto and Dynamic are not both supported in every configuration. |
| NVIDIA Reflex Low Latency | Off / On; advanced Boost maps to On + Boost. Treat these as one underlying preference. Keep Reflex enabled while Frame Generation needs it and explain the dependency. Restore the user's prior preference when appropriate. |
| Frame rate limit | Explicit FPS target; final values and interaction with generated-frame pacing need runtime verification. The 120 FPS example is not a measured result. |
| Performance statistics | Optional display. Keep base FPS, displayed FPS, frame timing, latency and VRAM distinct; unavailable readings remain blank, not zero or fabricated. |
| Ray Reconstruction | On/Off only when the current rendering path and capability query support it. An RTX GPU alone is not proof. |
| NVIDIA sharpening | On/Off plus a strength slider, gated by actual supported configuration. |
| RTX Dynamic Vibrance | Off by default; independent enable, intensity and saturation boost. |
| Apply / Defaults / Back | Stage changes, persist accepted supported settings, support cancellation and preserve a reliable native fallback. Implemented locally; physical input/restart acceptance remains open. |

Unavailable controls keep an accurate reason: hardware, driver, OS/HAGS or
rendering configuration. Never infer support from the enum or device name alone.
Do not conflate the in-game Reflex setting with changing NVIDIA Control Panel
settings. No global driver settings are authorized by this design.

## Download and evidence

Read-only inspection found the owner's archive in Downloads:
`2026.10.16_UE5.8_DLSS4.5Plugin_v8.9.0.zip` (1,166,608,575 bytes).
That October22 inspection read the archive in place without installing or
launching anything. October23 integration subsequently installed the SDK and
completed native build, renderer and menu checks; see the current receipt.

The included `DLSSLibrary.h`, `StreamlineLibraryDLSSG.h`,
`StreamlineLibraryReflex.h`, `StreamlineLibraryDeepDVC.h` and `NISLibrary.h`
establish the candidate controls and support-query APIs. The frame-generation
implementation explicitly filters modes using device capability, including
Dynamic versus Auto. SDK files remain private and are not committed.

[NVIDIA's DLSS overview](https://developer.nvidia.com/rtx/dlss) was checked on
October 22, 2026; the page labels the plugin update October 2026 and lists
Super Resolution, DLAA, Ray Reconstruction, Multi/Dynamic Frame Generation,
Reflex and NVIDIA Image Scaling. The official
[May 27, 2026 developer announcement](https://developer.nvidia.com/blog/whats-new-for-game-developers-in-nvidia-rtx-dlss-4-5-for-ue5-and-multilingual-ai-characters/)
describes the DLSS 4.5 Unreal integration and 6×/Dynamic modes.
October23 build and D3D12 checks confirm local5.8.4 compatibility.

## Verification and later integration gate

Visual review corrected a wrapped Defaults button, a crowded selector label,
disabled range controls and selector labels after a component swap. Final
graphics frames have no text outside screen bounds and use the established
three font families. Screens are semantic layers; the only image fills are
pre-existing discrete background scene art, not flattened UI. This verifies
the design structure and appearance, not game behaviour or owner approval.

For completion of the now-authorized integration, the AI owns: plugin/engine compatibility and
backup, capability-aware settings binding, save/load/fallback, keyboard and
controller navigation, driver/HAGS reasons, and measured comparisons with
Frame Generation off/on. Check ghosting around character motion, fine hair,
HUD/chat and photo mode; measure frame pacing, input response and actual VRAM.
Frame Generation and DLSS are not a texture-pool repair or a promise of lower
VRAM use. Keep the existing texture/PSO/chat issues open independently.

James can use Pause > Settings > Graphics in the current development game.
Image & Performance, Advanced and Display retain separate controls. Click a row
or use left/right to change it, then Apply; Back cancels unapplied changes, and
Defaults only stages values. DLAA and DLSS are alternative methods. Frame
Generation forces Reflex on while retaining the previous preference. RR is
unavailable while hardware ray tracing is off. Natural-play quality, physical
controller interaction, responsiveness and preferences after restart remain open. ClickUp synchronization is queued privately
while its previously reported daily connector quota is exhausted; this file
does not claim those new remote tasks were created.

## Current native evidence

[October23 integration and engine-path receipt](../validation/2026-10-23-nvidia-graphics.md)
records the compiled module, queried capabilities, three rendered pages,
startup-order repair and remaining presentation/performance acceptance.
