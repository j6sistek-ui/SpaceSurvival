# Wayfarer tester release — October1

Owner authorizes the current station and furnished apartment in the game, preservation of the separate build area, and an itch update for testers with known unfinished behavior. This is not owner acceptance or Phase1 completion. No GitHub merge is authorized.

## Integration

The existing repaired checkout combines station PR64 with harder-director PR66 and wormhole PR67. Runtime station composition is derived from the saved outpost; original outpost, apartment and flat BuildingSandbox hashes are unchanged. [Map receipt](2026-10-01-wayfarer-runtime-map.json) identifies the runtime asset and 7,782 stable actor tags. The original outpost/ULAT authoring checkout and second building sandbox remain available. Actual player ship, paint, home loadout, survival services and Free Flight use the existing game systems. Supplemental service anchors cover the prior preview-only gaps. No progression, survival cadence or difficulty reduction.

## Focused checks

- Native Editor builds pass. Final fixture build8: 5.24seconds; prior substantive build4:23.39seconds. Existing engine C4996 warnings remain.
- Changed C++ formatting, runtime Python syntax,39 source checks and documentation navigation gate pass. No full panel or whole gameplay suite run.
- Runtime map preparation passes source hash preservation. Raw UWorld duplication first crashed because a vendor particle component retained the transient duplicate; normal level Save As avoids that path. A second Save As to the existing target was refused; final saved-level tagging uses the current-level save API. The failed logs remain private.
- First integration fixture had an incorrect mobile-depot mooring assertion for a parked station ship; repaired to verify disabled flight tick and exact pad position. Second fixture passes four real service openings and all27 apartment floor/clearance probes, and renders pad/services/apartment. It stopped on the harness's incorrect assertion that the temporary practice account's last-run identity must remain unchanged. Corrected to require unchanged state during service calls and exact account/run restoration after Free Flight.
- Final editor/packaged fixture and package/publication identity are pending at this commit. Later records below supersede this pending status.

## Explicit limits

Synthetic pawn approaches and route probes are not a natural keyboard/controller walkthrough. The fixture skips moving door leaves during geometric clearance sampling. Departure uses public StartFreeFlight, return uses public EndFreeFlight; this does not establish natural approach/landing or physical boarding/cockpit seating. The Wave5 station portion seeds an isolated in-memory state rather than playing five waves. No purchase/save action is selected; existing production saves are protected by capture snapshots. Screenshots and blocking streaming checks are not representative 60FPS/VRAM or visual acceptance. Existing apartment blind-material warnings and editor-only agent-tool Python startup errors are retained as known issues; neither is presented as a clean all-log run.

## Packaging follow-up

The first full cook found two source IK rigs in HeroReplacement (root and Final/RTG_Body_Source) referencing deliberately never-cooked MocapSource/SK_Mannequin. The existing exact-package authoring exclusion now includes those two helpers without recursion. ReplacementHero/Retarget.py identifies them as source retarget inputs; meshes, skeletons and baked runtime clips remain selected. Original source assets are not modified. The initial packaging attempt under Windows PowerShell5.1 also rejected Tee-Object -Encoding; the installed pwsh7 runs the existing packaging script correctly.

The final editor fixture d349effd403d41c0bde9d25a1755ec18 passes all six runtime stages, eight service openings,27 probes and exact Free Flight state restoration. Its outer wrapper correctly fails because HEAD changed while the identical built sources were being committed. It is limited runtime evidence; the packaged fixture must supply stable end-to-end artifact validation.

The first exclusion exposed duplicate short-name PrimaryAssetIDs between the root and Final folders and the parent RTG_Body retargeters. Final rules use two distinct primary asset types, each excluding its RTG_Body and RTG_Body_Source packages without recursion (four packages total). The duplicate-ID warning and missing-reference cook failure are retained; source files remain untouched.
