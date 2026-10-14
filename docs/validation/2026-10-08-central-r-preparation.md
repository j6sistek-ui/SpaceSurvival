# Central and R preparation — October 8, 2026

**12:28UTC follow-up:** the owner reports VRAM free. GPU readback confirms
13,874MiB available, but another task repeatedly launches offscreen Unreal NPC
imports with Nwiro disabled. The lead's guarded launcher refused a competing
editor; no station/native edits occurred. Current live/preview/DLL hashes remain
e3ed61ba/e7958758/e2e7b5c7. An eight-view saved-live-map capture helper is prepared
privately and passes syntax; native execution is unverified. Coordinate the other
task's import pause before the fresh baseline. The CPU-only restriction in the
historical preparation below is superseded for central/R; the NPC scope exclusion
and other holds remain.

Owner scope: finish central reception/arrival and R wardrobe/customization first,
establishing the interior layout and visual language before incoming NPC variants
and custom behaviors. This pass performs cook-output housekeeping and CPU-only
preparation while local AI/Blender use VRAM. It does not load, capture or edit Unreal.
**RPT-20261007-01 / RPT-20261006-04** retain room acceptance and lead ownership.

## Preparation delivered

- Reused the existing central furnishing, reception and information-board recipes,
  five-family R display recipe, owned P1–P5 catalog and twelve owner references.
  There is no evidenced artwork shortfall requiring another generation batch.
- Checked the room scripts, guide sources, native monitor/window/material assets
  and two older comparison capture receipts. Exact current file identities and
  availability are in the [preparation manifest](2026-10-08-central-r-preparation.json).
- Identified the next native starting boundary: current saved Wayfarer is
  `e3ed61baf81980c2e5d43a428c6b5eaa2b87eec3b1540248ff8042aae5658501`,
  last written October8 04:50UTC. It differs from close-out `76e3c8c2`; these are
  concurrent/earlier saved changes, not changes made by this preparation.
  Preview `e7958758` remains intact. Fresh native inspection is required before
  changing the live scene. Disk identity does not identify unsaved editor state.
- Existing central/R helpers explicitly target the older owner-preview map.
  Do not bypass their guards or replay them over current Wayfarer. First inspect
  actual live role tags/labels/placements and establish a new protected baseline;
  adapt a bounded recipe only when necessary. Existing props/display actors must
  be adopted rather than duplicated. No script adaptation or placement is claimed here.

## Ready finishing sequence

This is a scoped handoff, not a second priority queue; the issue log owns order.

| Area | First player-camera review when VRAM is available | Bounded finishing target |
| --- | --- | --- |
| Central arrival | View from arrival through reception and wing entrances, then reverse view | Reception is the clear focal point; routes to R, T and departures read at walking distance. Retain white low-gloss floors, cyan structural trim and restrained warm guide accents. Resolve dark desk/upper-frame areas from matched views before selecting any lighting change; avoid global exposure changes. |
| Central information | Directory/Flight Guide front, oblique approach and ordinary walking distance | Full text fits actual apertures and describes implemented services. Retain useful directions/mechanics and at most1–2 ads. Confirm current guide assets survived later live edits; do not invent powerup/leaderboard services. |
| Central dressing and circulation | Around the reception counter, both waiting bays and walk-up Flight | Supported tablets/desk items, coherent seating/planters and unobstructed routes. Keep floor rings legible and visual clutter below the guide hierarchy. Reserve desk/route space for later NPC work; existing figures are visual context, not a new behavior task. |
| R entrance and identity | Enter from central, face services/hologram bays, look back toward the doorway | Wardrobe/customization is obvious. Group related props and functional screens; preserve archive/wardrobe projection controls and their original orientation. Match central's material/trim family while retaining R's service identity. |
| R display installation | West-bay front/oblique/distance views, then all five steady campaigns and transitions | Recheck the existing upright frame/backing and intact copy in the current live scene. Use the owner's many holographic-window examples for appropriate glass hosts; keep graphics embedded and edges blended. Solid-wall and true-window treatments must follow their actual supports. Functional controls remain readable. |
| Both rooms | Natural walking route, doorway turns and seated/standing sightlines | Check furniture support, label occlusion, camera collision and approach clearances. Final layout/vibe needs current saved/reloaded views and owner review before being called finished. This preparation is not that approval. |

The older central wide test shows a strong circular desk/floor organization but
dark reception/upper structure and distant small labels. The older R display test
shows intact copy in the upright case; it is a close crop, so it cannot establish
R's whole-room composition. These observations guide the next review rather than
claiming defects in today's saved map.

Older comparisons, with temporary existing reception/patrol/alien figures and
unfinished contacts/whole-room approval: private
`LiveOperationsPIEReview1_CentralWelcomeFinish3/01_ReceptionReachWide.png` and
`LiveOperationsPIEReview1_RDisplayFixed48/10_SteadyAd.png`, under `.agent/local/Outpost`.
They were unsaved tests at capture time; later save/promotion receipts are separate.
No new photo is presented as the current saved build.

## Housekeeping completed

Six obsolete directories were removed, totaling **13,445,225,796 bytes
(13.45GB / 12.52GiB)** across 192 files:

| Project checkout | Removed outputs | Bytes |
| --- | --- | ---: |
| Canonical `C:/Users/j6sis/SpaceSurvival` | `Saved/Cooked`, `Saved/StagedBuilds`, `Intermediate/Staging` | 3,817,444,426 |
| Old `C:/Users/j6sis/.codex/worktrees/flight-loop-reset/SpaceSurvival` | Same three output directories | 9,627,781,370 |

Newest output files were September19 and October1 respectively. No cook/package
process was active; dry-run inventories preceded removal. Paths were resolved and
checked under the explicitly selected projects, with no reparse entries or tracked
files. Current maps, `.uproject` and three player saves matched before/after SHA256.
Working shader/build caches, autosaves, licensed originals, recovery backups,
Blender/AI outputs, current packaged game and release archives were preserved.
Post-cleanup C free space was60,791,201,792 bytes; concurrent AI/editor writes mean
free-space change is not an exact measure of the removed logical bytes.

`Scripts/CleanCookTemp.ps1` is reusable. It previews by default; `-Apply` removes
only the three fixed output kinds older than48hours. It refuses active cooks,
tracked outputs, reparse paths, save/source-like files and changed preflight data.
It does not clear shader/DDC caches or other temporary directories automatically.
Use the same small housekeeping pass after future package work once the archive
and receipts are retained; [build/run instructions](../BUILD_RUN.md#obsolete-cook-output-housekeeping)
give the command. No recurring automation was enabled.

Private receipts: `.agent/local/CookCleanup/20261008T113109920Z.json` (preview),
`20261008T113148859Z.json` (applied, complete), `ProtectedBefore.json`,
`ProtectedAfter.json`, `20261008T113449847Z.json` (post-cleanup empty preview).
The preparation manifest binds the applied receipt and protected records by hash.

## Verification and limits

PowerShell parsing and `Tests/TestCleanCookTemp.ps1` pass recent-output retention,
dry-run preservation, eligible-output deletion, protected-save preservation,
source-like-file refusal, active-cook refusal and invalid-root refusal. Actual
cleanup reports six removals, zero remaining candidates on the second preview,
and identical protected hashes. Native room fitting, lighting, traversal, saved
scene quality, NPC implementation, package/cook and publication were not run.
Incoming NPC variants and custom behaviors are outside this pass.
