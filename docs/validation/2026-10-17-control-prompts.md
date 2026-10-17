# October17 controls instruction correction

RPT-20261016-01 remains partial. The current input code steers with the left stick, but one flight tutorial message still described sideways movement. The dodge message also omitted the right bumper. The Controls guide lacked the later talk, crew-action, photo, seating and settings-tab shortcuts.

The bounded change corrects those instructions in `SSGameMode.cpp` and renames the existing guide heading to CURRENT CONTROLS in `SSHUDRefresh.cpp`. It changes no binding, input ownership, character, layout, font, artwork, save schema or gameplay behavior. Throttle wording is shorter to retain clearance at the maximum text scale.

## Design lookup

The connected SpaceSurvival Figma file `6M3VvUB7jsPDd3E41YpKM0` contains Key Map UI page `307:1058`. Read-only Plugin API and metadata both returned an empty page. Existing Controls frame `208:1087` still has obsolete example bindings. No Figma mutation, asset import or new design adoption occurred. The owner was asked for the newer location while independent work continued. The provenance note now correctly records A to fire and LB/RB dash/roll; the older RB-fire sentence was stale.

## Verification

- Worktree editor build39.31s and initial combined build136.40s passed. Final combined build after shortening one line passed6.96s; final worktree build passed87.57s. Existing installed-engine/plugin deprecations and the nonpreferred Visual Studio version warning remain; no new compiler error.
- 49 structural checks,13 source-digest tests and scoped clang-format pass. The first formatting check found one newly short string still split by TEXT; corrected before final source check. No test was added to mirror display strings.
- Initial large-text capture `f16a78078ebc42be894dfbf08813c140` produced the controls image but timed out later at120seconds. It remains a failed full fixture. Production saves, module and test-save checks passed. The last guide line was too close to the border, so throttle wording was shortened.
- Final hidden native capture `0228647b636a42d0acb9d9462a547ef7` passes all seven screen cases at1920x1080 and UI scale1.4, process exit0. The Controls image was visually checked: all guide lines fit within the frame with bottom clearance. Actual account/run/settings and production saves are preserved; no save slots were written. This is scripted rendering, not physical controller/device-switching or performance acceptance.
- Current combined module SHA-256 is `6566a2572ee70ebca6148b60fbb9fb82949ff1899e76638c10a59a56a419123d`. Station map remains `7431ed23ef99770ebe369746c8f6ab164c658558126d96a9a3c415ce625b23dc`. The226-path bar guard, excluding the intentionally rebuilt module, and all six original replacement clips have no unexpected changes.

Open the local image `M:/SpaceSurvival/Artifacts/EndgameSoak/0228647b636a42d0acb9d9462a547ef7/UIControls.png`, or Settings > Controls in the current local editor build. Check the shortcut wording and text size. New Figma options, contextual glyph readability and physical input switching remain open under RPT-20261016-01; other bar/garment/audio checks remain separate. No merge, package or release.

Private build logs, source backups and preservation receipt: `.agent/local/ControlPrompt_20261017/`. The capture receipt records exact source/module/save identities. Native/private artwork is not published with this source change.
