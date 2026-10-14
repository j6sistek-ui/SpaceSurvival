# October8 live station close-out

Owner requested publication into the live Unreal project, GitHub handoff of open
topics and a pause. This is local runtime-map promotion, not an itch/package
release or owner visual acceptance.

## Saved identity

- Source `/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006`:
  `e7958758a861d17fe189601b17b486db9ea75086080a8e1b5f17e56cbb7b18db`.
- Live `/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime`:
  `76e3c8c2918bcb90a630852c857ca2f0b64386840cef78c3d19795787a521703`.
- Previous live map, retained offline:
  `9c83968d9765467a05b104eaadc65dd44ff06dbfdbe797c8a38a58645756ca9c`.
- Loaded Build49 DLL:
  `e2e7b5c7ba25ce9e77f50545a6dbeea3f7f29531d332b9b9f33dcd57508560ff`.
- Native `.agent/local/Outpost/Closeout50_LiveVerified.json`:
  `f35bee741ce9d4ea6428634d9cd1ec545a63186e8405b2d459aec0332970f44f`.

`Edit Current Station.cmd` opens the promoted map. Existing runtime source loads
that package for home and Survival visits; the unchanged sandbox GameMode
redirects Play from its exact name to Survival. A fresh complete gameplay visit
after promotion was not run.

## Operation and verification

`Scripts/PromoteStationPreview.py` is import-inert, checks exact source/runtime
hashes and stopped Play/clean packages, provides a dry run and preserves backups.
It refreshes direct actors' OutpostLabel tags without changing their other tags.
It does not regenerate rooms, edit child levels, cook or publish a package.

The first overwrite was refused because Unreal could not delete the destination
world; both files stayed unchanged. The clean editor was closed gracefully, the
old live file retained offline, and the same Build49 reopened offscreen. Native
Save As into the empty destination succeeded. Its next assertion incorrectly
expected SaveMap to select the new world; explicitly loading it fixed verification
without another save. A later comparison included Unreal struct allocation
addresses; excluding those addresses allowed value-only placement comparison.
Failed receipts remain retained. The helper now requires offline replacement,
explicitly loads its saved target and compares address-free transform values.

Final native readback verifies8,462 direct actor names/classes/labels and displayed
transform values;66 missing/stale runtime labels are refreshed. Nine source maps
stay byte-identical, including preview and child levels. Both R actors retain
NoCollision and original/new material assignments. Seven plain NPCs retain one
configuration each, visible head-attached lights, receiver/frame links and exact
40lm/100cm/12cm channel profile. The berth retains QueryAndPhysics collision and
terminal actions/display names are present. PIE is stopped, dirty lists empty,
and one offscreen editor remains on the live map (PID8552 at verification).

Rollback copies: `.agent/local/StationPromotion/20261008T020629097332Z` and
`20261008T020913046949Z`. Restore only with the editor closed and after hash
verification; never overwrite a loaded package on disk. Nine owner material edits
and the owner's `.uproject` remain unstaged. Private maps/derivatives/receipts are
not a GitHub asset backup.

## Handoff limits

PR69 lists bounded open topics against existing issue IDs. T's P1-P5 choice stays
held. Market/L ads, fresh gameplay/visual checks, contact/warp/cabin/voice work,
controller comfort, stability, performance and Phase1 acceptance remain open.
Future NPC variants were not created or certified. Published0.1.22-alpha,
build2048604/source`e6c2a87` remains unchanged. Progress reports are paused.
