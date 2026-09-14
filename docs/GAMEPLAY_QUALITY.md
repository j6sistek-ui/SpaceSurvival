# Gameplay quality pass

**Phase 1 remains PARTIAL.** The owner prioritized gameplay quality and Phase 1 adherence, and may clean up the hero externally. HeroAlpha source studies are paused; none is selected by the game.

The follow-up build passed **37 Unreal tests at 2026-09-13 15:12:50 UTC**, zero warnings/failures/not-run, in 3.083320 seconds; Editor build 33.08 seconds. It adds synchronized projectile/ship contact with cover ordering, preserves Director budget after failed wreckage admission, and keeps contract outcomes visible with subtitles disabled. Container formatting and 23 source checks passed. [Follow-up evidence](validation/2026-09-13-gameplay-fairness-followup.json) records all 213 unchanged build inputs and the actual regression cases. This source is now independently audited in [Package 13](validation/2026-09-13-windows-gameplay-fairness-package.json), with a successful normal-timing Wave 10 capture and [native settings-selection check](validation/2026-09-13-native-settings-focus.json).

Package 12's previous source passed independent artifact and both normal-timing rendered audits: [package](validation/2026-09-13-windows-gameplay-quality-package.json), [performance](validation/2026-09-13-gameplay-quality-performance.json). These receipts retain their source3536 boundary and do not measure the three follow-up fixes.

The earlier integrated gameplay build passed **35 Unreal tests at 2026-09-13 14:50:03 UTC**, with zero warnings, failures or unrun cases, in 2.892839 seconds. The final Editor build took 21.69 seconds. Container formatting and 23 source structural checks passed. All 120 content packages remain byte-identical to the previously validated station/sky assets. [Exact evidence](validation/2026-09-13-gameplay-quality.json) binds the build inputs, DLL and test reports.

| Player-visible problem | Implemented behavior | Focused verification |
| --- | --- | --- |
| Collisions weakened as frame rate increased | A contact applies a bounded velocity impulse; gravity remains continuous acceleration | Same 600 cm/s grazing deflection at 30/60/120/144 Hz; quarter-second travel differs by 0.268 cm; center-crossing direction also tested |
| Cannon ignored configured weapon range | Player cannon and laser tracers stop at the configured muzzle travel range; final sweeps also respect lifetime | Real cannon shots hit inside 4000 cm and expire before outside targets at 30/144 Hz and 350 ms hitch |
| Fast movement skipped crossed pickups; magnet movement could overshoot | Continuous relative crossing collection plus bounded local magnet motion | 30/60/144 Hz, 100 ms hitch, nearby-lane miss, once-only credit, drifting pickup, origin shift, first update and partial expiry |
| Medium-rock fragments could appear in the player or immediately collide | Bounded spawn attempts reject initial overlap and the existing reaction interval along relative motion | Close/far breakup, moving fragments at 144 Hz, threat cap, and deliberate later collision still damaging |
| Assistance could pull the ship through station structure | Inbound lane, heading, full-body margins and a clear sphere-swept route required | Rotated/translated hub; roof/rear/side/low/off-angle entry rejected; blocked sweep rejected; ordinary 3 s docking retained |
| Adjusting a setting reset controller/keyboard selection | Same settings panel preserves the selected action | Real panel rebuild across repeated in-memory adjustments; no persistence writes in this fixture |
| An already-fitted reward could consume the earned choice | Fitted rows disabled/labeled; stale actions rechecked before consumption | Both modules and Heavy Cannon duplicate/stale/valid alternate choices |
| Upgrades lacked benefit information and Tier V showed a negative price | Actual effective stat previews, capacity-only repair explanation, clear MAX TIER | All five I-to-II previews preserve money/current stats; all five Tier V rows disabled |
| Contract outcome vanished on station arrival | 18 s notification reports success and actual paid credits, or failure with no reward | Hunter below/exact target and Pressure completion, real exit ticks, no repeat award |

The initial combined suite passed 33/34. Its sole failure was a new test's incorrect total-collision-piece expectation, not a docking failure. The existing station includes 16 deck/boundary pieces, 7 consoles and 2 crates. The redundant assertion was removed; the existing exact station boundary regression and all new admission checks remain. Independent review also found and prompted the center-crossing impulse correction before the final pass.

Independent review additionally caught first-update and partial-expiry pickup crossings; seeded history and clipped live-time collection now pass regressions, including after-expiry cases that must not pay. The earlier 35-test pass and final correction are separately identified in the receipt.

The contract notice is arrival feedback, not a saved receipt; it is not reconstructed on resume. No save schema, progression rule, content roster, five-wave cadence or post-Wave-10 behavior changed.

The existing full-journey fixture still uses shortened waves, enlarged durability and assistance. These tests do not establish natural pacing, the 2–3-purchase economy target, physical input comfort, audio quality or replay appeal. Continue the owner's [hands-on protocol](PLAYTEST_TOMORROW.md); all 19 boxes remain unchecked. Graphics remain below acceptance. The failed wreckage-passage debit is now corrected and covered by the follow-up regression. Optional active play can fund a fourth first-station purchase; this is a balance question for a natural spending record, not justification for an untested price change.
