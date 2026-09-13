# Phase 2 integration notes

**Phase 1 remains PARTIAL.** These are future integration notes, not implemented Phase 2 features or a declaration of production readiness. The Windows package, 12-test Unreal suite and isolated fresh-process storage lifecycle pass. Close broader packaged acceptance, natural gameplay, UI save/restart, controller, visual/audio and performance gates before expanding the roster.

## Preserve the locked loop

Keep continuous survival, hidden durations, short breathing windows, a climax/station every fifth wave, deliberate credit purchases, non-regenerating shield and death-ended runs. Permanent progression unlocks possibilities; most power remains earned within each run. All additions must respect Director admission and readable combinations.

The current Station 2 boundary is explicit in `AtSliceBoundary`, `LaunchFromStation`, run/account codecs, Director clamps and contract eligibility. Supporting later waves needs coordinated rules, content, schema/tests and shell changes. Enabling a menu item alone would expose unsupported state. No additional waves are implemented.

## Reuse and required future work

| Area | Existing integration point | Work required later |
| --- | --- | --- |
| Hazards/structures/regions | World-body contact/weapon/force contract, admission, six hazard definitions | Stable identities, behavior classes/assets and validated warning/composition policy |
| Enemies/elites | Two enemy definitions, committed shot telegraphs, shared obstacle interaction | Additional behavior/class policies; preserve behavior/composition scaling rather than inflated health |
| Weapons | One active weapon, effective stats, trace/projectile path | Definitions/firing strategies and migration-safe identities; current two weapons are native branches |
| Utilities | One explicit equip/replacement slot and stat composition | Additional definitions/effect policies; preserve deliberate reward flow |
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

Cloud support needs revisions/generations and a conflict policy that cannot resurrect consumed/dead runs. Per-file staged replacement does not provide atomic multi-slot commits, automatic backups, multi-device conflict resolution or a demonstrated hardware/power-loss guarantee. The new writer compiled and passed source checks, all 12 Unreal regressions and the actual locked-destination failure/retry lifecycle. Those failures preserved prior bytes and successful retries retained once-only progression. Process interruption remains untested. Exercise interruption at each staging/replacement/consume boundary before extending storage claims, including the gap between account and suspension commits.

Logical station snapshots do not serialize world actors. If later objectives survive docking or content introduces multiple persistent hubs, define exactly what survives before adding scene serialization.

## Multiplayer boundary

Current code intentionally uses one GameInstance session, one possessed ship/walker, player index 0, local GameMode orchestration and direct authoritative mutations. No replicated state, RPCs, network prediction or co-op lifecycle is implemented.

Future co-op must decide host/server authority for wave time, Director spending, damage, rewards, contracts and suspension. Separate player/account/local settings from shared run state. Define collective docking, disconnect/rejoin and death-ended-run semantics. Add replication and prediction only after those rules are explicit; local portable tests do not establish synchronized simulation.

## Validation before expansion

The module, map/data and Windows package exist. Twelve Unreal tests pass without test warnings/failures, including flight adapters and an accelerated ten-wave journey. The updated GameInstance storage lifecycle across three fresh processes passes with owner save hashes unchanged, including real locked-suspension/account replacement failures and successful retries. It does not establish forced-interruption or hardware-loss behavior. The journey uses 12-second waves, enlarged durability and forced/assisted objectives; neither harness establishes the complete natural player experience.

First complete the natural ten-wave packaged slice acceptance with both physical inputs, station/UI storage interactions, earned unlocks and restart appeal. Resolve the current Station 2 boundary and replace the owner-rejected provisional art. Measure actor scans/spawn bursts, synchronous loads, hero geometry and rendering before choosing pooling, spatial indexing, preloading or LOD changes. Preserve simulation, response and hazard readability before increasing presentation cost.

For every later system, add deterministic rules coverage, meaningful engine integration tests and actual overlap/feel scenarios. Keep source availability, build success, package success and player acceptance as separate evidence claims.
