# Owner playtest findings

Recorded 2026-09-13. Paraphrased from direct owner feedback. These are player observations, not reproduced defects or verified diagnoses. Exact played build, wave, weapon, target identity and contract acceptance are UNCONFIRMED. The follow-up identifies mouse-control discomfort and controller preference; no physical controller playtest is established. Do not assume the latest itch upload was the tested build.

Current priority: appearance and controls for core mechanics. More detailed feedback will follow. Preserve the reasonably good entry-level handling baseline; this report does not request a flight redesign or immediate gameplay changes.

| ID | Owner observation | Follow-up when work resumes | WBS |
| --- | --- | --- | --- |
| F01 | Movement/controls feel decent so far for an entry-level ship. | Preserve this as positive baseline feedback, not complete controller/flight acceptance. Compare future changes against it before retuning. | 2.1-2.3 |
| F02 | An unidentified optional event or depot appeared partway through and seemed to follow the player for the whole wave; it was distracting. | Identify actor versus HUD marker, offer/accepted state, movement and persistence. Reproduce before deciding whether to change tracking, dismissal, range or presentation. | 6.4-6.6,9.1 |
| F03 | A contract may have been accepted, but the player did not know its objective. | Verify acceptance and distinguish contract from event. Review offer terms, acceptance confirmation, current objective/progress and outcome visibility. | 6.7,9.1 |
| F04 | A station interaction resembling "keep the beacon lit" had no understandable purpose. Wording is approximate. | Identify actual interaction; explain purpose, required action, optionality and consequence/reward at the point of use. Do not invent a beacon mechanic from this report. | 8.3-8.4,9.1 |
| F05 | Shooting/pointing at enemies felt too easy. | Reproduce with actual weapon, input and assistance setting; separate steering/aim assistance, enemy evasion and encounter pressure. Do not globally nerf controls or inflate enemy health based on this alone. | 5.1-5.4 |
| F06 | After attacking/killing enemies, the player was not sure they had died. | Check actual destruction versus target loss/despawn, visual/audio death cue, target marker retirement and reward confirmation. | 5.1-5.4,6.1,10.1 |
| F07 | Some other objects had yellow names rather than red; the player could not tell whether they were allies or enemies. | Identify actual actors and labels; establish consistent hostile/friendly/neutral/interactable cues using shape/icon/text as well as color. No affiliation is inferred from yellow alone. | 6.6,9.1 |

These findings inform the short core-mechanics benchmark, especially targeting, death feedback and target identification. Event/contract/station findings remain tracked for their workflow passes; they should not pull today's planning into implementation. No fixes, new tests or owner acceptance boxes are claimed from this record.

## Wormhole and input follow-up

| ID | Owner observation / expectation | Follow-up when work resumes | WBS |
| --- | --- | --- | --- |
| F08 | Wormhole was recognizable but felt like travelling through a tube and then it was over. Arrival should feel far away and unfamiliar: different colors/space, a disruptive ejection and animation, and uncertainty about where the player emerged. Owner frames the fuller experience as a long-term intention. | Treat destination contrast, transit/ejection, ship/pilot reaction, audio and recovery as one experience. Proposed direction: anticipation/pull, transit, bounded ejection disturbance, readable recovery into an unfamiliar scene. Do not infer actual new galaxies, new hazard families or arbitrary input reversal. Preserve the scoped hostile-combat-to-station sequence; reconcile any abrupt region-change proposal with GAME_SCOPE's gradual-region rule before implementation. Duration, force and control interruption are not yet specified or approved. | 4.2,2.3,7.3,10.1-10.3 |
| F09 | Forward play felt well supported, but movement did not feel very free. The player also felt constrained by inverse mouse input being opposite their normal expectation. | Separate the intended forward bias, actual maneuvering envelope, camera response and input inversion. Compare with preferred pitch direction and a physical controller before diagnosing the flight model or retuning base movement. | 2.1-2.3,9.2 |
| F10 | Owner is primarily a controller player; computer controls are not intuitive for them. | Prioritize a controller-first owner comparison when testing resumes, while retaining keyboard/mouse parity. Record device/layout/sensitivity/inversion. This is preference and context, not a passed or failed controller test. | 2.1,9.2,11.1 |

The intended wormhole experience includes temporary uncertainty about location, while the player must still regain understandable control and receive fair warning of the next danger. This is a proposed interpretation for review, not a new mechanic implemented today.
