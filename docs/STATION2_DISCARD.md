# Station 2 discard persistence

Status: **IMPLEMENTED AND VERIFIED IN FIVE FRESH ISOLATED UNREAL PROCESSES.** This follow-up is outside Package 9/source 4178ff4. It does not change the Phase 1 slice boundary, award victory XP or create a completed-run history entry. No natural Station 2 or physical-input acceptance is implied.

The existing Station 2 action 51 previously invalidated the suspension and cleared the live run without first persisting the account. A run that reached Wave 10 since the last save could therefore lose its highest-wave record after returning to the hangar and closing the process.

`USSGameInstance::DiscardSliceRun` requires an active Station 2 run and performs these operations in order:

1. Persist the account, including the highest wave already recorded by the domain wave transition.
2. Durably invalidate the suspended slot.
3. Clear the live run.

The menu action returns to the hangar only after all three operations succeed. Either write failure leaves the active run and current menu available and displays the existing save error. An account write can succeed while invalidation fails; the prior checkpoint then remains usable, and resuming an older checkpoint does not lower the account's highest wave. This is the existing separate-slot protocol, not a transaction across both slots. No `EndRun`, XP award, completed-run count or history insertion occurs.

## Isolated regression

After rebuilding the Editor target, run the existing guarded wrapper:

```powershell
./Scripts/TestSaveLifecycle.ps1 -Station2Discard -TimeoutSeconds 120
```

This separate opt-in mode uses the same exact GUID UserDir/backend/reparse/production-hash guards as the other lifecycle modes. It launches five owned Unreal processes in sequence:

| Phase | Check |
| --- | --- |
| Preflight | Read-only path/backend verification with no GameInstance initialization or save slots |
| Suspend | Existing real GameInstance fixture writes the three domains at Station 1, highest wave 5 and no death progression |
| FailedDiscardStation2 | Fresh Init/resume, real re-suspension at Station 1, then assisted domain advancement to Station 2; actual action 51 under account and suspension deny-write/delete locks preserves the live run and exact prior checkpoint bytes. The second failure leaves account wave 10 durable and the older checkpoint available |
| DiscardStation2 | Fresh Init retains wave 10; real resume of checkpoint wave 5 does not downgrade it. Assisted advancement and actual action 51 retry consume the checkpoint, clear the run and possess the hangar walker |
| FreshAfterDiscard | Fresh Init retains highest wave 10 with zero XP, zero completed runs, empty history, no Continue and unchanged saved bytes |

The fixture invokes the actual menu action and Windows save replacement path. Its transient world has not begun normal gameplay; station advancement and contract completion are explicit fixture setup. It does not measure natural arrival, rendered UI, balance, input comfort or performance. The harness requires all owned processes to exit, exactly three save domains, no leaked staging files and unchanged production-save hashes. Existing normal lifecycle, staging-fault, corruption and prepared-station modes remain separate.

The combined Editor build succeeded in 32.22 seconds. Its 17-test Unreal suite passed with zero automation warnings or failures at 08:50:18 UTC. The separate five-process discard harness then passed at 08:52:51 UTC on 2026-09-13; each process reported one successful test with zero automation warnings or failures. Final fresh Init retained highest wave 10, XP 0 and zero completed runs. All five owned processes exited, exactly three isolated save domains remained, no staging files leaked, and both production save manifests were unchanged.

The [source- and DLL-bound validation receipt](validation/2026-09-13-station2-discard.json) records the exact reports, hashes, final state, isolation checks and limits. Raw evidence and tested source snapshots are retained under `Artifacts/SaveLifecycle/a7f697ebbecb4f48bd7b318fe9756321`; the driver log is `.agent/local/Station2DiscardHarness.log`. Package 9 remains the historical artifact from source 4178ff4 and does not contain this change.
