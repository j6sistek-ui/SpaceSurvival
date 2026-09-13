# Phase 2 integration notes

**Phase 1 remains PARTIAL.** These are future integration notes, not implemented Phase 2 features or production readiness. Package 7 has 12 passing Unreal tests, CI-verified 524 strict/524 sanitizer assertions and native prepared-station save/vendor/resumed-death evidence. Close natural gameplay, physical controller, art/audio, clean-PC portability and representative performance before expanding the roster. Newer source 442ff06 passes all 13 Unreal tests, including authored exit. Package 8 adds guarded slowed exit/service/departure smoke and compatible signed-runtime bundling; natural camera/motion, sky seam/pole/readability and clean-PC acceptance remain open. Later candidate work is outside that package.

## Preserve the locked loop

Keep continuous survival, hidden durations, short breathing windows, a climax/station every fifth wave, deliberate credit purchases, non-regenerating shield and death-ended runs. Permanent progression unlocks possibilities; most power remains earned within each run. All additions must respect Director admission and readable combinations.

The Station 2 boundary is explicit in AtSliceBoundary, LaunchFromStation, codecs, Director clamps and contract eligibility. Its live summary reuses services/save/discard; native save/relaunch retained the purchased utility, without Wave 11 or completion XP. Discard and completion appeal remain open. Later waves need coordinated rules/content/schema/tests/shell changes; enabling one menu item would expose unsupported state. No additional waves are implemented.

## Reuse and required future work

| Area | Existing integration point | Work required later |
| --- | --- | --- |
| Hazards/structures/regions | World-body contact/weapon/force contract, admission, six hazard definitions | Stable identities, behavior classes/assets and validated warning/composition policy |
| Enemies/elites | Two enemy definitions, committed shot telegraphs, shared obstacle interaction | Additional behavior/class policies; preserve behavior/composition scaling rather than inflated health |
| Weapons | One active weapon, effective stats, trace/projectile path | Definitions/firing strategies and migration-safe identities; current two weapons are native branches |
| Utilities | One slot/stat composition and guarded 150-credit station purchases; free event fitting remains separate | Additional definitions/effect policies; retain deliberate choices, commit-time eligibility and no charge for a fitted utility |
| Events/contracts | Explicit acceptance, objective callbacks/deadlines, pending reward, station resolution | Additional objective/modifier definitions, disclosed failure terms and serialization; current execution is native |
| Depots/stations | Data-defined timing/subsets, proximity checks, paid shield-only depot service and station service lookup | Designer-authored layout/offer classes and intentional replacement of the Phase 1 exactly-once guarantee |
| Account/ships/history | XP levels, starting-option guards, per-run stats, account v2 history | Unlock/ship catalog and explicit migrations; preserve reset, history provenance and once-only awards |
| Challenge modes | Canonical tuning, reset, score calculation | Explicit ruleset identity and separate record/save provenance |
| Inventory/storage | Existing deliberate utility/weapon replacement | New bounded inventory domain, identity, persistence and station UI; no inventory exists to activate |
| Presentation/audio | Imported assets, skeleton/animations, retained ship/exit, HUD and audio hooks | Production LODs, animations, VFX, content classes and measured mix/performance |
| Steam/cloud/records | Local storage adapter and service-independent codecs | Offline/conflict/privacy decisions, service adapters and version/generation metadata |
| Eventual co-op | Portable rules and separate world/presentation owners | Authority, participant identity, replication, prediction and shared save/death policy; substantial work remains |

The editable fixed-size catalog already exposes current hazard, enemy, pickup and encounter values. It does not instantiate arbitrary Blueprint behavior classes. New types need explicit factories/class references and verified cook dependencies. Keep rules in the session, admission/composition in the Director, objective execution in encounters and choice presentation in UI.

## Save evolution

Account payload v2 reads v1, preserving existing progression/summary/tutorial fields and leaving unavailable history empty. It retains at most ten completed-run identities. Run/settings payloads, envelope and slot names remain v1. Numeric enum values and fixed field order are serialized: do not reorder them or add fields without versioned migration and fixtures.

Preserve the three existing account/settings/suspension slots and consume-before-play semantics. `WriteDomain` serializes through Unreal's compatible `SaveGameToMemory` envelope and verifies its in-memory readback. `SSLocalSave` writes a unique same-directory `.tmp`, calls `Flush(true)`, closes and byte-verifies it, then performs a native same-volume replacement with `MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH)`. It never pre-deletes the live slot or enables a copy/delete fallback. The successful replacement acknowledges consumption before the resume candidate becomes playable; a subsequent transient read cannot reverse that acknowledgement. See [Local save protocol](ARCHITECTURE.md#local-save-protocol) for the API references and exact boundaries.

This implementation permits only Windows with the exact engine generic SaveGame backend; it rejects a configured alternative. A future platform/cloud adapter must explicitly implement an equivalent acknowledgement contract and retain serialization compatibility, rather than bypassing the backend guard. Failed writes attempt cleanup of only their staging file. Orphan `.tmp` files are ignored, never automatically recovered as playable suspensions.

The adapter protects unreadable accounts and rejects suspensions matching the latest or retained awarded IDs. Ten retained IDs are bounded history, not an unlimited anti-replay ledger.

Cloud support needs revisions/generations and a conflict policy that cannot resurrect consumed/dead runs. Per-file staged replacement does not provide atomic multi-slot commits, automatic backups, multi-device conflict resolution or a demonstrated hardware/power-loss guarantee. The new writer compiled and passed source checks, all 12 Unreal regressions and the actual locked-destination failure/retry lifecycle. Those failures preserved prior bytes and successful retries retained once-only progression. Package 7 separately passed native prepared-station Save & Quit/Continue, utility retention, resumed death and fresh account/unlock readback. Those seeded, assisted, muted sessions do not establish natural play. Process interruption remains untested. Exercise interruption at each staging/replacement/consume boundary before extending storage claims, including the gap between account and suspension commits.

Logical station snapshots do not serialize world actors. If later objectives survive docking or content introduces multiple persistent hubs, define exactly what survives before adding scene serialization.

## Multiplayer boundary

Current code intentionally uses one GameInstance session, one possessed ship/walker, player index 0, local GameMode orchestration and direct authoritative mutations. No replicated state, RPCs, network prediction or co-op lifecycle is implemented.

Future co-op must decide host/server authority for wave time, Director spending, damage, rewards, contracts and suspension. Separate player/account/local settings from shared run state. Define collective docking, disconnect/rejoin and death-ended-run semantics. Add replication and prediction only after those rules are explicit; local portable tests do not establish synchronized simulation.

## Validation before expansion

The package 7 milestone has 12 Unreal test successes and CI-verified 524 strict/524 sanitizer assertions. Newer source 442ff06 passes all 13 Unreal tests, adding geometric contact/pose/handoff coverage for the authored exit; a guarded slowed package 8 replay passed, while natural animation/camera acceptance remains open. The journey uses 12-second waves, enlarged durability and forced/assisted objectives; vendor/boundary tests open menus programmatically. Separate native prepared profiles exercised both station save/relaunch paths, utility payment/duplicate guards and resumed death/account retention. Fresh-process locked-file failures/retries also passed with owner hashes unchanged. Neither fixture route establishes natural ten-wave pacing, interruption/hardware-loss behavior or the complete player experience.

First complete natural ten-wave packaged acceptance with both physical inputs, complete service/contract/loadout decisions, naturally earned unlocks and retry appeal. Evaluate the live Station 2 handoff and unexercised discard action without inventing a victory award. Extend package 8's guarded exit/prompt smoke to natural docking/camera and panorama readability; replace rejected art and verify clean-PC startup. New starless-sky/ship candidates need their own build/package/evidence. Measure actor scans, spawn bursts, synchronous loads, hero geometry and rendering before choosing pooling/indexing/preloading/LODs. Preserve simulation, response and hazard readability before increasing presentation cost.

For every later system, add deterministic rules coverage, meaningful engine integration tests and actual overlap/feel scenarios. Keep source availability, build success, package success and player acceptance as separate evidence claims.
