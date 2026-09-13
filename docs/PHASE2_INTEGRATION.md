# Phase 2 integration notes

**Phase 1 remains PARTIAL.** These are future integration notes, not implemented Phase 2 features or production readiness. Current committed source a9da95e passes 17 Unreal tests, 641 strict/641 sanitizer assertions and CI run 34748775072. It includes contract tuning, electrical timing and fresh-process Station 2 discard protection. Package 9 remains source4178 with exact asset/runtime audit, native deck residency and a full rendered Wave 10 fixture; it does not contain a9 or the subsequent worktree. Historical package 7/8 evidence keeps its original prepared/assisted/slow-motion limits.

Newer economy/audio/Station 5 capture source compiled in 21.30 seconds, with 744/744 portable assertions and ten parser tests; the fixture-only 4.71-second rebuild and final 21-test suite passed at 09:29:16 UTC with zero test warnings/failures, and fresh content validation passed at 09:26:42 UTC. Photographic rock adoption and the six ship material-graph repairs have separate fresh asset readback, not a new package or final art approval. Close natural gameplay, physical controller, art/audio, clean-PC portability and representative performance before expanding the roster. See the [audio receipt](validation/2026-09-13-audio-hooks.json) and [economy receipt](validation/2026-09-13-economy-tuning.json) for final source/DLL/report binding and the retained first-attempt limits.

## Preserve the locked loop

Keep continuous survival, hidden durations, short breathing windows, a climax/station every fifth wave, deliberate credit purchases, non-regenerating shield and death-ended runs. Permanent progression unlocks possibilities; most power remains earned within each run. All additions must respect Director admission and readable combinations.

The Station 2 boundary is explicit in AtSliceBoundary, LaunchFromStation, codecs, Director clamps and contract eligibility. Its live summary reuses services/save/discard; native save/relaunch retained the purchased utility, without Wave 11 or completion XP. The committed discard transaction persists highest-wave progression before consuming suspension and clearing the run. Five fresh processes test both write failures, old-checkpoint resume, actual action 51 retry and final highest wave 10 with zero XP/history. Native discard usability and completion appeal remain open. Later waves need coordinated rules/content/schema/tests/shell changes; enabling one menu item would expose unsupported state. No additional waves are implemented.

## Reuse and required future work

| Area | Existing integration point | Work required later |
| --- | --- | --- |
| Hazards/structures/regions | World-body contact/weapon/force contract, admission, six hazard definitions | Stable identities, behavior classes/assets and validated warning/composition policy |
| Enemies/elites | Two enemy definitions, committed shot telegraphs, shared obstacle interaction | Additional behavior/class policies; preserve behavior/composition scaling rather than inflated health |
| Weapons | One active weapon, effective stats, trace/projectile path | Definitions/firing strategies and migration-safe identities; current two weapons are native branches |
| Utilities | Two validated Data Asset rows feed prices/effects and guarded station purchases; defaults 150, free event fitting remains separate | Additional definitions/effect policies; retain deliberate choices, commit-time eligibility and no charge for a fitted utility |
| Events/contracts | Explicit acceptance, callbacks/deadlines, pending reward; validated contract magnitudes/rewards and subsequent per-encounter completion amounts | Additional objective/modifier definitions, disclosed failure terms and serialization; current execution is native |
| Depots/stations | Data-defined timing/subsets, proximity checks, paid shield-only depot service and station service lookup | Designer-authored layout/offer classes and intentional replacement of the Phase 1 exactly-once guarantee |
| Account/ships/history | XP levels, starting-option guards, per-run stats, account v2 history | Unlock/ship catalog and explicit migrations; preserve reset, history provenance and once-only awards |
| Challenge modes | Canonical tuning, reset, score calculation | Explicit ruleset identity and separate record/save provenance |
| Inventory/storage | Existing deliberate utility/weapon replacement | New bounded inventory domain, identity, persistence and station UI; no inventory exists to activate |
| Economy | Existing domain income/prices plus subsequent validated Data Asset amounts and identity-correct legacy encounter migration | New price/reward policies need explicit ownership, bounds, save compatibility and conservation tests |
| Presentation/audio | Imported assets, retained ship/exit, HUD; subsequent world spatial-audio subsystem with role overrides, gain/concurrency/lifetime limits | Production LODs, animations, VFX, content classes and measured mix/performance |
| Steam/cloud/records | Local storage adapter and service-independent codecs | Offline/conflict/privacy decisions, service adapters and version/generation metadata |
| Eventual co-op | Portable rules and separate world/presentation owners | Authority, participant identity, replication, prediction and shared save/death policy; substantial work remains |

The editable fixed-size catalog exposes current hazard, enemy, pickup, encounter and utility values; contract magnitudes/rewards have a validated bridge. Subsequent economy fields retain the original defaults and native identities. New audio fields resolve a role preset by default, accept a compatible override or use explicit null for silence. Audio is presentation state, never a save or gameplay authority. The content catalog does not instantiate arbitrary Blueprint behavior classes. New types need explicit factories/class references and verified cook dependencies. Keep rules in the session, admission/composition in the Director, objective execution in encounters and choice presentation in UI.

## Save evolution

Account payload v2 reads v1, preserving existing progression/summary/tutorial fields and leaving unavailable history empty. It retains at most ten completed-run identities. Run/settings payloads, envelope and slot names remain v1. Numeric enum values and fixed field order are serialized: do not reorder them or add fields without versioned migration and fixtures.

Preserve the three existing account/settings/suspension slots and consume-before-play semantics. `WriteDomain` serializes through Unreal's compatible `SaveGameToMemory` envelope and verifies its in-memory readback. `SSLocalSave` writes a unique same-directory `.tmp`, calls `Flush(true)`, closes and byte-verifies it, then performs a native same-volume replacement with `MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH)`. It never pre-deletes the live slot or enables a copy/delete fallback. The successful replacement acknowledges consumption before the resume candidate becomes playable; a subsequent transient read cannot reverse that acknowledgement. See [Local save protocol](ARCHITECTURE.md#local-save-protocol) for the API references and exact boundaries.

This implementation permits only Windows with the exact engine generic SaveGame backend; it rejects a configured alternative. A future platform/cloud adapter must explicitly implement an equivalent acknowledgement contract and retain serialization compatibility, rather than bypassing the backend guard. Failed writes attempt cleanup of only their staging file. Orphan `.tmp` files are ignored, never automatically recovered as playable suspensions.

The adapter protects unreadable accounts and rejects suspensions matching the latest or retained awarded IDs. Ten retained IDs are bounded history, not an unlimited anti-replay ledger.

Cloud support needs revisions/generations and a conflict policy that cannot resurrect consumed/dead runs. Per-file staged replacement does not provide atomic multi-slot commits, automatic backups, multi-device conflict resolution or a demonstrated hardware/power-loss guarantee. Actual locked-destination retry and eight-process staging-create/readback-denial/interruption scenarios passed with production hashes unchanged. The parent held a required-acknowledgement oplock until the owned writer was confirmed terminated before replacement; fresh Init preserved the original checkpoint and ignored the orphan stage. Later death/retry retained 475 XP and one completed run. The four-process corrupt-account test protects invalid domain text inside a valid Unreal envelope, blocks New Run/Resume/persistence and verifies a manually restored exact test copy after fresh Init. No arbitrary binary corruption or automatic recovery feature is established.

The Station 2 regression additionally tests the gap between account persistence and suspension invalidation. Failure preserves the live run/checkpoint; fresh Init can resume an older Wave 5 checkpoint while max-preserving the durable Wave 10 record, and actual discard retry leaves no playable checkpoint or invented death award. These bounded scenarios are in [storage faults](validation/2026-09-13-storage-faults.json), [account protection](validation/2026-09-13-corrupt-account.json) and [Station 2 discard](validation/2026-09-13-station2-discard.json). Disk-full/short writes, all interruption boundaries and hardware loss remain unverified. Package 7 separately passed native prepared-station save/continue and resumed death; seeded state, assisted positioning and muted audio limit its claim.

Logical station snapshots do not serialize world actors. If later objectives survive docking or content introduces multiple persistent hubs, define exactly what survives before adding scene serialization.

## Multiplayer boundary

Current code intentionally uses one GameInstance session, one possessed ship/walker, player index 0, local GameMode orchestration and direct authoritative mutations. No replicated state, RPCs, network prediction or co-op lifecycle is implemented.

Future co-op must decide host/server authority for wave time, Director spending, damage, rewards, contracts and suspension. Separate player/account/local settings from shared run state. Define collective docking, disconnect/rejoin and death-ended-run semantics. Add replication and prediction only after those rules are explicit; local portable tests do not establish synchronized simulation.

## Validation before expansion

The current committed 17-test suite adds contract Data Asset and electrical cadence/boundary coverage to the utility/runtime Tail V2 suite. The accelerated journey uses 12-second waves, enlarged durability and forced/assisted objectives; it is not a natural ten-wave pass. Source a9 has CI-verified 641/641 assertions. The subsequent four economy/audio tests also pass in the final 21-test suite after a fixture-only offer-seen correction; their component and payment assertions do not establish rendered sound, balance or human input.

First complete natural ten-wave packaged acceptance with both physical inputs, complete service/contract/loadout decisions, naturally earned unlocks and retry appeal. Evaluate native Station 2 discard usability without inventing victory XP. Package 9 verified full-resolution floor residency and a complete normal-timing Wave 10 scripted capture; Wave 5/docking/exit/station timing is the next bounded measurement via the new Station5 scenario. Natural camera/animation, sky seam/pole/readability, rejected art, clean-PC startup and representative full-run performance remain open. Subsequent photographic surfaces, ship graphs, economy and audio need their own integrated package/evidence. Measure actor scans, spawn bursts, synchronous loads, hero geometry and rendering before choosing pooling/indexing/preloading/LODs. Preserve simulation, response and hazard readability before increasing presentation cost.

For every later system, add deterministic rules coverage, meaningful engine integration tests and actual overlap/feel scenarios. Keep source availability, build success, package success and player acceptance as separate evidence claims.
