# Economy content bridge

Status: **Unreal build, content migration, fresh validation and both economy tests passed.** Portable strict and ASan/UBSan checks each passed 744 assertions; the final combined Unreal suite passed 21/21 with zero warnings or failures at 2026-09-13 09:29:16 UTC. Phase 1 remains **PARTIAL**. This change follows source `a9da95e18be56fe55b230b0ad48b4fad2317360b`; Package 9 remains a historical artifact and does not contain it. No natural economy or 2–3-purchases-per-station acceptance is implied.

The existing numeric terms now connect the Phase 1 Data Asset to their runtime uses. Defaults, five upgrade identities and I–V tiers, three encounter identities, pending reward choices, service eligibility, station cadence and save formats remain unchanged.

| Asset property | Default | Actual use |
| --- | ---: | --- |
| `WaveCredits` | 75 | Existing native wave reward plus the unchanged 5-credit increase per later wave |
| `UpgradeBasePrice` | 130 | Existing first upgrade price |
| `Economy.KillCredits` | 12 | Enemy kill credit award |
| `Economy.UpgradePriceStep` | 90 | Existing price increase for each later purchased tier |
| `Economy.RepairPrice` | 35 | Station full service; moving depot shield service retains its existing rounded-up 60% price |
| `Economy.StationRewardCredits` | 25 | Once-per-station lost-crew beacon interaction; the menu and payout use the same accessor |
| Salvage encounter `CompletionCredits` | 70 | Completion bonus after its accepted objective resolves |
| Distress/combat encounter `CompletionCredits` | 100 | Completion bonus after its accepted objective resolves |
| Mobile depot `CompletionCredits` | 0 | No event completion reward or new depot mechanic |

The original flat `WaveCredits` and `UpgradeBasePrice` asset names are retained to preserve existing authored values. `ApplyEconomyTuning` maps those and the three existing domain fields during real GameMode BeginPlay. Event completion and station interaction use bounded Data Asset accessors. Salvage cache pickup amounts, enemy drops, contract payouts, utility prices and deliberate reward fitting remain on their existing independent paths.

Amounts are bounded before entering arithmetic: payouts are nonnegative and at most 100,000,000; repair price is at least 1; upgrade base is 1–25,000,000 and its step is 0–25,000,000, keeping the highest purchasable tier within the existing credit counter. Wave base has 45 credits of headroom for the unchanged Wave 10 bonus. Invalid content is reported; no codec format changes or new run fields are required. A zero credit amount does not remove an event's existing pending module/weapon choice.

## Existing asset compatibility

An older serialized encounter array can default-construct the newly added completion field before restoring its stored `Kind`. The unset value is therefore `-1`, with runtime fallback to the correct existing identity default. New explicitly typed rows start at 70/100/0. Authoring calls `initialize_legacy_economy_defaults()` before `has_valid_economy_tuning()` and saving; only unset fields change, and a second migration is a no-op. The validator checks all economy bounds and exactly one of each existing encounter identity, then records the amounts in its persisted-content receipt. This is content migration, not player-save migration.

Custom values survive authoring. Resumed runs load current content magnitudes; tuning is not snapshotted in the existing run payload. Existing reward availability and claimed flags remain serialized exactly as before.

## Verification

`Scripts/TestCore.ps1` passed **744 strict + 744 ASan/UBSan assertions**, including custom kill/wave income, all five upgrade tracks through Tier V, stepped and discounted prices, insufficient funds, full repair, depot shield-only service, credit conservation and unchanged run codec roundtrip. Raw output: `.agent/local/EconomyCore.log`.

Two focused Unreal tests passed:

- `SpaceSurvival.Content.EconomyDataAssetBounds` reads the persisted asset, checks unchanged defaults, reconstructs a legacy combat row, proves identity-correct fallback and idempotent migration without overwriting custom salvage, and checks malformed/extreme arithmetic and the existing codec boundary.
- `SpaceSurvival.Integration.EconomyRewardBridge` runs actual GameMode BeginPlay in an isolated world, then uses real menu actions for repairs/upgrades/station tips and real encounter acceptance/completion/failure paths. It checks custom rewards, duplicate rejection, pending reward serialization and free module/weapon selection.

The engine fixture never initializes the GameInstance from disk and blocks account writes. It uses explicit station placement and objective progress, without a normal Director journey, rendered UI, physical input, economy balance or performance claim. The initial combined Editor build took 21.30 seconds; content imported at 09:23:45 UTC and fresh validation passed at 09:26:42 UTC. The first suite passed 20/21: the assisted beacon fixture omitted the Director's corresponding offer-seen flags, so the unchanged strict codec correctly rejected two payload checks. The fixture now reproduces those flags and reports decode diagnostics. A test-only 4.71-second rebuild produced the final 21/21 suite in 2.318785 seconds, without runtime or codec relaxation.

The [focused receipt](validation/2026-09-13-economy-tuning.json) binds exact final source, Data Asset, DLL, logs and report. Raw and LF-normalized domain source hashes were read from the exact immutable Docker image in EconomyCore.log and match the current source bytes. The first failing report, original failing test source and DLL were not copied or hashed before replacement; only its retained log and observed summary are recorded. The separate initial generic asteroid material validator failure was corrected to the exact approved override without weakening the geometry guard.
