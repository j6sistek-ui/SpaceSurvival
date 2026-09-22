# Approved page 11 UI sources

Read-only exports from SpaceSurvival UI Kit, file `6M3VvUB7jsPDd3E41YpKM0`, page `203:1058`, retrieved 2026-09-22 UTC. Figma was not modified. The locked main menu remains in the separate FigmaMainMenu family.

Native HUD and settings layouts use flight `210:1109`, General `219:1282`, Graphics `219:1287`, Audio `219:1292`, Controls `208:1087`, Pause `227:1461`, and walking `219:1322`. The KIT supplies the exact frame/tab/toggle/slider/pip/radar/reticle/button PNGs. The background comes from `219:1283`. Every asset node, dimension and SHA256 is in provenance.json. Other pages remain stale design references; pages12/13 did not authorize additional features.

Owner amendment: hull, shields and brake heat retain labels and segmented bars, with no blue backing or percentage labels. Actual runtime values/actions replace illustrative mockup text. Gameplay renders over the real world, not the static concept background. Settings keep native cycle-on-activation semantics; slider art is a value indicator, not a new drag control. Existing sensitivity/invert/hold settings remain; preset selection/remapping stays deferred.

Service panels reuse the common approved frame and current native actions; this is not an exact recreation of every page11 service composition, wardrobe portrait preview or result illustration. Static button exports do not implement the original animated shader. Native input focus is drawn explicitly.

Keania One Regular is the unmodified Google Fonts source by Julia Petretta, SIL Open Font License1.1, with Reserved Font Name Keania. Exact TTF and OFL.txt are retained here and staged under Content/SpaceSurvival/UI/Fonts. Hashes/source URLs are in provenance.json. Runtime Canvas uses a UFont provider containing this composite face; a filename-only Slate font measures successfully but Canvas skips it because FontObject is null.

Run `python Scripts/ImportFigmaUIRefresh.py --validate-only` for exact PNG/font verification. In the isolated hidden editor, run the script without flags for dry-run; add `-SSApplyUIRefresh` only after reviewing it. The importer creates only missing `/Game/SpaceSurvival/UI/Refresh/T_*` textures, refuses unknown source metadata, and never changes an existing texture. The project cook root includes those assets; the explicit UFS Fonts directory stages TTF/license.
