# Runtime diagnostics — October 16, 2026

Issue: RPT-20261016-07. Source candidate atop the unmerged PR76/PR74 stack. No merge or packaged release.

Graphics settings now contains an off-by-default Diagnostics switch using the existing toggle artwork and navigation. The gameplay HUD shows frame rate/time, game/render/GPU timing, process CPU/RAM, available DXGI video-memory budget, and local conversation/voice status. The panel disappears in menus, photo mode and the gallery.

The panel samples timing across approximately 0.75 seconds. Memory and helper-process queries run only at that interval while visible. Hiding it clears the samples; a gap longer than two seconds returns it to Sampling. GPU timing and video-memory budget report unavailable when absent. GPU milliseconds are not GPU utilization. Available DXGI budget is not total physical free VRAM. Process measurements include editor overhead when running PIE. A running LLM/STT process is not a health check or model-readiness claim.

The status snapshot does not launch or contact a helper. It contains no model paths, endpoints, prompts, transcripts or raw response bodies. Conversation errors are a presence flag; voice request failures/restarts are session counters. This is not an engine-wide error log or a system-wide task manager.

## Verification

- Existing MSVC toolchain: 773 portable domain assertions pass, including old settings without the optional field, round-trip enabled preference and rejected malformed/trailing values. Docker Desktop was not running; container/sanitizer confirmation remains a CI gate.
- Source structure: 49 checks pass. Python compilation and content-source format validation pass.
- Isolated worktree Editor build passes in 83.05 seconds; canonical Editor build passes in 47.93 seconds. Existing licensed-plugin/engine deprecation and toolchain-preference warnings remain; no new build errors.
- Display-validation module SHA-256: `54b789bb558c38f9a4daf0c21dd2071af50063fe9b68ce9438a0229c6329e1c2`. Follow-up builds pass in 26.49s (settings API) and 4.10s (scaled width and timing availability).
- Focused `SpaceSurvival.Menu.Diagnostics` on initial module `24542844`: one success, zero failures/warnings/not-run, 2.038 seconds. Checks the real Graphics row, refresh after changing the preference, preserved account/settings and repeated status reads without helper launch or queued speech. It does not claim physical-input acceptance.
- Native 1600x900 views verify the panel on/off, hidden in photo mode and restored on return. The setting survives a fresh PIE session. The final build also reloads the preference and fits enlarged UI text. Zero timing counters report unavailable; tiny positive timing can round to 0.0ms.
- The first bridge used an old private command directory; its preservation assertion stopped it before any asset action. Three save-fixture attempts could not edit protected reflected properties or seed the intended payload; failures remain retained. A small Blueprint-callable settings getter/setter now uses the normal persistence path, and native review successfully saves and reloads through it. [Epic reflection guidance](https://dev.epicgames.com/documentation/en-us/unreal-engine/exposing-gameplay-elements-to-blueprints-visual-scripting-in-unreal-engine) was checked October 16 against the installed 5.8 headers.

- Final-build Graphics menu capture shows the correct default-Off toggle and readable layout. The broader `CaptureSpaceLook -UIRefresh` run `0d523a8996e74b8b8ca3d2f18b6624d9` fails later at `Wardrobe focus, clipping or pointer scrolling failed.` Its old list/scroll assumptions do not match the hologram selector. This initial full capture remains failed. The repaired fixture now checks five visible controls and actual Next/Previous hit targets, preserving legacy artifact names. Its receipt confirms preserved account/run/settings and no save slots written.

- Follow-up module `a841a562d86967fb3d5d934c6cb9464328f5875f6d59fd90169052c146618ddf` builds in 12.52 seconds. Complete UI capture `d50aca5397e14f368b4839f5e8d9d807` and browse follow-up `85429d56286847db83eda38e6a75983f` pass. Account/run/settings conservation and no-save receipts pass. The fixture does not equip a character; this distant menu capture is not a new hologram-at-pad acceptance. The final-module focused diagnostics test also passes: one success, zero failures/warnings/not-run, 1.531 seconds.

Final preservation verifies all 133 guarded native/save files unchanged, including station `5ac00104` and three owner saves; no dirty map/content packages. The owned rendered editor exited without saving. Raw logs, source backups and captures live locally in `.agent/local/Diagnostics_20261016`; they are not a packaged release.

## Remaining acceptance

Lead: confirm exact-head CI and continue the bar backlog. Hidden paths clear samples before any telemetry call; no separate overhead benchmark was performed. Owner: natural-play readability and physical controller toggling. The overlay itself does not establish the broader 60 FPS/performance target. Old executable versions do not understand the appended settings field; account and run formats are unchanged.
