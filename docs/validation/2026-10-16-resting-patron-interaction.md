# Resting bar patron conversation — 2026-10-16

## Change

The permanently passed-out corner patron previously remained eligible for the normal talk target despite having no authored actions/chatter. `ASSOutpostAmbientActor::bConversationEnabled` now defaults true and can be disabled per placed character. Disabled crew are excluded from fresh target selection, cached hints/actions and scripted/ambient speech. An existing engagement ends when its partner becomes unavailable; beginning another question rechecks that state. The setting does not replace the idle animation or alter navigation, collisions, body, materials or identity.

Only `SSOutpostAmbientActor_21` (`Crew/Lounge conversation A`, using `A_Nyxar_Laying`) is saved with this setting false. All other 56 crew keep their values, including Joy, Astra and the swaying arcade patron. No global talk-pack/voice setting changes and no sleeping behavior is inferred from a display name or animation filename at runtime.

## Native state and checks

- Worktree editor build 1 succeeds in 50.58 s; canonical combined build 1 succeeds in 54.41 s. Existing engine/third-party deprecation warnings remain. Combined module SHA256 `cd9ed5339257ba3419d5fd42642dfb9d1c7d3641312279df9421864823db0cf0` includes the other locally integrated work; no cook/package/release.
- Focused `SpaceSurvival.NpcTalk.RestingCrew`:1 pass, 0 warnings/errors, 0.562s. Checks existing defaults, available action target, immediate stale hint/action removal, rejected speech/chatter with no queued voice, disengagement and restored availability. The isolated fixture initializes no talk subsystem, microphone, helper or save. Unattended mode disables live talk-pack acquisition, so this does not claim an audible/physical talk-key session.
- 49 structural checks, 13 source-digest tests, Python compilation, content-source validation and scoped clang-format22 pass; exact-head container formatting/source and documentation CI are checked after publication.
- Saved/reloaded map SHA256 `ddc040c15d724938e5a15ba2e9553cb62938e74b527388edeef28c48d55e8670` supersedes `b5141cb691f41cbb197a867aa508da2be8beec407fc3e579beddd4776ffd81cb`. All 9,480 actor transforms/labels/tags and all 57 crew snapshots match except the one intended boolean. Original mesh/material/idle/walk/action/chatter/route fields remain. Backup:`.agent/local/BarResting_20261016/StationBeforeResting.umap`.
- Final preservation passes 175 files with clean packages, including three owner saves. `84` ordinary-Play samples over 17.797 s show the saved flag false, continued sleeping playback (5 loop wraps), stationary patron and both staff available. `SavedRestingPatron.png` records the saved scene. This is not an all-animation or performance test.
- One actual CharacterMovement passage beside the resting corner reaches its goal in 1.734 s, with collision settings unchanged (`Passage.json`). This is a bounded 5.5 m route, not whole-room circulation or physical-input acceptance.
- The first offscreen review helper accepted a command while MAP LOAD was still active and asserted on a null CurrentWorld before adoption. All 175 protected files were unchanged. A dispatcher busy guard prevents command reentrancy; a fresh editor completes save/reload. The failed log and `CrashPreservation.json` are retained. Existing vendor BP_Blinds errors remain unrelated and visible in the raw log.

## Continued fit work and review

A separate volume-preserving skinning comparison for Astra was rejected: front coverage still retracts and side cloth intersects skin. Its six private renders and numerical receipt are under `Waitress_20261015/SeatVolume_20261016`. No source blend/export/native garment changed; approved V16 SHA256 `3015073774d71b23c42fea1bfafcbab1d18fa25d857f89ec428105a42ba2b924` stays intact. Blender's [Armature documentation](https://docs.blender.org/manual/en/4.4/modeling/modifiers/deform/armature.html), accessed October 16, describes the preserve-volume principle; it does not establish Unreal export/runtime compatibility, and no candidate was exported.

Open `C:/Users/j6sis/SpaceSurvival/.agent/local/BarResting_20261016/Review.html` or `Play Development Build.cmd`. Check the resting patron and nearby passage, then confirm Joy/Astra remain conversational. Pending owner checks stay in KNOWN_ISSUES and do not pause independent lead work. Seated shorts, heard laughter/mix, broader prop polish, exterior composition, natural input, performance and packaged acceptance remain open. Hero/squirrels/PR73 remain held; no merge.
