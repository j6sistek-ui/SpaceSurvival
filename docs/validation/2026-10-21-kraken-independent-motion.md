# October21 Kraken independent tentacle motion

RPT-20261015-03: owner requests upright, partly independent octopus-like tentacle
movement instead of the human gait. This does not request crawling on the floor.
The new routine is locally adopted; natural-play feel and clothing simulation
remain open. No new packaged release.

## Motion and preservation

The original V12 mesh uses a243-bone Blender rig (244 after the FBX object root),
including20 lower chains, four arm branches and two antenna chains. These are
rig controls, not a claim that the creature has20 anatomical legs. Both its old
idle and travel references selected the same one-second human-derived walk.

`A_Kraken_IndependentCrawl_24s` replaces those two references with a24-second,
25FPS seamless routine. Different phases/cycle counts and smooth amplitude changes
produce staggered reach/pull/curl motion. Attachment roots, torso and human leg
bones stay fixed. This is seeded authored variation, not runtime randomness,
physical suction or terrain-aware contact IK. Idle and travel deliberately share
one continuous routine so stopping does not reset all tentacles simultaneously.

The body, skin weights, skeleton, outfit, materials, Purple Mandala eyes, fitted
hair and route are unchanged. Original Blender file and walking clip are retained.
The separate armature/action library is6,716,210bytes and contains no duplicate
body mesh or textures; a fresh Blender reopen confirms243bones, frames0–600 and
one retained42-vertex custom control shape. The first library check wrongly rejected
that harmless control shape; the corrected check explicitly excludes body/outfit copies.

Only Kraken's idle/travel references and its component's editor preview animation
changed in the saved station. All9,079 loaded actor identities/classes/transforms
and other exposed Kraken actor/component properties were checked before/after.
The previous map is hash-verified in
`D:/SpaceSurvival_AssetArchive/KrakenMotion_20261021`. Active files stay on C.

- Previous map: `23fef47d5fa11cff79dffdaf1b74f85167a97101a7891edff8238c7ca23620fd`.
- Adopted map: `56c18f661f6975ef35998e6a424c82c97791f172f5a3f3f9d3866cadbde838a7`.
- New animation: `2e67d68971a9c13136684db045563dd21fd412bcf09526ba3e26bfd31877c812`.
- Editor DLL remains the quality-pass `5e546820`; no additional C++ motion system.

## Checks and limits

The candidate's real-RHI PIE review records83samples across before, full new loop
and a12-second route segment. Sampled lower end-bone travel is4.27–14.43cm;
arm end-bone travel6.42–8.73cm. Attachment roots have zero component-space travel.
Blender's actual bone tails have slightly different larger spans; the endpoints
are not interchangeable measurements. The playback crosses the24-second seam.
Route travel is813.20cm in the sampled segment, not proof of the entire route.
Full-body front/rear frames show distinct curls and no human stepping/hip gait.
Original gown stiffness and fine fused-contact/hem intersections are not closed.

All checks use private saves, local AI disabled, hidden offscreen Unreal and
1200x900 capture output. The first smaller framed captures cropped head/feet;
those were retained and superseded by full-body captures. The initial importer
used two incorrect Python property access forms; import succeeded after correction
and the separate verification reopened it successfully. A stale-plan guard rejected
unbound delegate wrapper addresses and cross-load layout text variation. Corrected
guards retain the exact saved-map hash and same-process layout/property checks;
failed attempts did not save the map.

Fresh saved-world runtime selection passes25samples with the new clip selected
automatically, empty script errors and production saves unchanged. It is recorded
separately in `.agent/local/KrakenMotion_20261021/Reload/Review.json` and consolidated
in `Verified.json`. The raw reload report inherited a stale `native_adopted:false`
label from the candidate harness; actual saved references and the running instance's
`actual_saved_clip` establish adoption. The harness label is corrected for future runs.

Private evidence and the motion review are in
`C:/Users/j6sis/SpaceSurvival/.agent/local/KrakenMotion_20261021`:
`Candidate.json`, `Imported.json`, `Framed/Review.json`, `AdoptionPlan.json`,
`LeadReview.json`, `Adopted.json`, `LibraryReload.json`, `Exit.json` and `Review.html`.
Original fit source is
`.agent/local/KrakenOutfit_20261015/CuffClearance_20261016/Kraken_Outfit_Mandala_V12.blend`;
animation library is `Kraken_IndependentCrawl_Animation.blend` in the evidence folder.

## Reproduction

`AuthorKrakenCrawl.py` runs in background Blender with the preserved fit source
open and explicit `--output`, `--chains` and `--source-sha256` arguments after `--`.
The chain manifest is the existing private `Kraken_20261015/FinalChains.json`.
It writes a separate animation FBX/library and refuses an existing candidate folder.
`ImportKrakenCrawl.py` refuses an existing destination; it imports animation only
on the existing skeleton. `ApplyKrakenCrawl.py` defaults to a read-only plan and
requires `-SSApplyKrakenCrawl`, the unchanged map/clip plan, private review receipts
and a lead visual-review record before its backed-up save. These are provenance
recipes, not startup scripts; do not replay them against the adopted station.
