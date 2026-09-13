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

Preserve separate account/settings/suspension domains and consume-before-play semantics. The adapter protects unreadable accounts, verifies writes and rejects suspensions matching the latest or retained awarded IDs. Ten retained IDs are bounded history, not an unlimited anti-replay ledger.

Cloud support needs revisions/generations and a conflict policy that cannot resurrect consumed/dead runs. Current synchronous SaveGame calls do not provide atomic multi-domain commits, automatic backups or multi-device conflict resolution. Test interruption at each write/consume stage before extending storage claims.

Logical station snapshots do not serialize world actors. If later objectives survive docking or content introduces multiple persistent hubs, define exactly what survives before adding scene serialization.

## Multiplayer boundary

Current code intentionally uses one GameInstance session, one possessed ship/walker, player index 0, local GameMode orchestration and direct authoritative mutations. No replicated state, RPCs, network prediction or co-op lifecycle is implemented.

Future co-op must decide host/server authority for wave time, Director spending, damage, rewards, contracts and suspension. Separate player/account/local settings from shared run state. Define collective docking, disconnect/rejoin and death-ended-run semantics. Add replication and prediction only after those rules are explicit; local portable tests do not establish synchronized simulation.

## Validation before expansion

The module, map/data and Windows package exist. Twelve Unreal tests pass without test warnings/failures, including flight adapters and an accelerated ten-wave journey. Actual GameInstance storage across three fresh processes also passes, with owner save hashes unchanged. The journey uses 12-second waves, enlarged durability and forced/assisted objectives; neither harness establishes the complete natural player experience.

First complete the natural ten-wave packaged slice acceptance with both physical inputs, station/UI storage interactions, earned unlocks and restart appeal. Resolve the current Station 2 boundary and replace the owner-rejected provisional art. Measure actor scans/spawn bursts, synchronous loads, hero geometry and rendering before choosing pooling, spatial indexing, preloading or LOD changes. Preserve simulation, response and hazard readability before increasing presentation cost.

For every later system, add deterministic rules coverage, meaningful engine integration tests and actual overlap/feel scenarios. Keep source availability, build success, package success and player acceptance as separate evidence claims.
