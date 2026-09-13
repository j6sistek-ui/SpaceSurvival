# Owner playtest findings

Recorded 2026-09-13. Paraphrased from direct owner feedback. These are player observations, not reproduced defects or verified diagnoses. Exact played build, wave, device, weapon, target identity and contract acceptance are UNCONFIRMED. Do not assume the latest itch upload was the tested build.

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
