# Independent character handoff and Lira preservation — October 20, 2026

## Identity and scope

The other chat, **Stand by** (`01a1172c-bf34-74e1-9388-622ef3fa6b4c`),
was idle/completed before this review. Its checkout is
`C:/Users/j6sis/.codex/worktrees/hero-select-20261020/SpaceSurvival`;
draft [PR79](https://github.com/j6sistek-ui/SpaceSurvival/pull/79) is open,
unmerged and based on PR76. Live PR readback confirmed head
`d09a664b34e9cd3210858246e5825cc6c1fb85ba`.

This follow-up uses its own `character-followup-20261020` worktree.
Native review uses the canonical development checkout, unchanged Editor DLL
`6476c6e3`, tuning `c3098913`, and station `7431ed23`. These are development
assets, not a new packaged release. No importer worktree, original source,
station map, hero selection file or production save was edited.

## Independently observed

Two hidden, isolated Play sessions used `StationReviewProfile.py` with separate
GUID save directories and native path checks before Play. Both editors exited
normally. No visible owner window, microphone, voice request or paid generation
was used.

| Check | Observation | Limit |
| --- | --- | --- |
| Default selection | An empty explicit preference resolves to `SK_EX7` | Existing saved preferences were preserved |
| Alternates | Green, Blue and Cloth select their own meshes/materials | Physical selector input still needs testing |
| Movement | Four actual pawns move 282–354 cm, reaching 256 cm/s; own-skeleton walk/jog clips advance | Scripted movement, not physical input |
| Jump animations | All four enter `JumpStart`, `JumpAir`, `JumpLand` and return to idle; sampled rise is 79–90 cm | Controller tick disabled temporarily for this animation check |
| Render skins | Existing native inspector reports valid buffers/materials on all four bodies | Bounded views do not prove every armor/finger contact |
| Cloth | No published simulation particles; solver time remains zero | Existing failure remains open, no repair attempted here |
| Appearance | Native movement images reviewed | Green/blue are very dark in the landing-pad lighting; owner appearance acceptance is open |

The first direct `pawn.jump()` probe produced no airborne frames. Inspection of
`ASSPlayerController::PlayerTick` showed that normal input polling immediately
calls `StopJumping()` when Space/A is not held. The second bounded probe disabled
only controller ticking during the jump, leaving character physics and animation
running. It therefore verifies the animation/state transition, **not** keyboard or
gamepad routing. The failed first result is retained.

Native captures and reports:

- `.agent/local/HeroHandoffCheck_20261020/Independent1319/`: twelve first-pass
  screenshots and `Runtime.json`; the images labelled jump in this first pass
  are rejected as jump evidence.
- `.agent/local/HeroHandoffCheck_20261020/IndependentJump1328/`: four actual
  airborne screenshots, fifteen sampled Lira poses and `Runtime.json`.
- Save-isolation profiles: `dce62ad1559343e4b834e478f7cb2bae` and
  `db4dfa5cf679474eb4cb1129f527f349`.

The station retains existing warnings, including non-Nanite virtual-shadow job
overflow and translucent materials assigned to Nanite window/door meshes. There
were no Python review errors. This is not a zero-warning, performance, audio,
packaging or natural-play acceptance claim.

## Lira source and copies

Actual source:
`/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Lira/Rig/SK_Lira`.
All three clips use `SK_Lira_Skeleton`, full poses and disabled root-motion
extraction. Authored root/bone travel is retained.

| Original clip in `Lira/Role` | Duration | Saved copy in `AnimationLibrary/Lira_20261020` |
| --- | ---: | --- |
| `A_Lira_IMG9447` | 19.000 s | `A_Lira_Source_IMG9447` |
| `A_Lira_IMG9451` | 19.625 s | `A_Lira_Source_IMG9451` |
| `A_Lira_IMG9452` | 19.875 s | `A_Lira_Source_IMG9452` |

Nine native CPU-skinned samples per original remain finite. The latter two
clips visibly contain airborne poses; sampled key poses are evidence of useful
motion, not proof of smooth full-length playback, joins or contact. Some sampled
poses travel beyond the fixed preview camera, retained as a framing limitation
rather than cropping or modifying the animation.

`Scripts/PreserveLiraAnimations.py` first produced a dry-run plan, then created
three new native packages with source package/hash metadata. It refuses existing
destinations or changed plans. All 136 original Lira packages remain unchanged.
The copies total 69,083,136 bytes. Receipts live in
`.agent/local/LiraAnimationLibrary_20261020/{DryRun,Applied}.json`.

`Scripts/VerifyLiraAnimations.py` ran in a separate fresh editor
(`ea7dbe5271f94e25bdff410dc39a8f05`). All three saved copies reload with matching
hashes/provenance and duration/skeleton. Twenty-five poses across all 623 bones
produce 15,575 comparisons per clip, with zero position, quaternion or scale
difference from their sources. `FreshReload.json` records success with no errors.
The asset registry reports only Lira's skeleton and physics asset as mesh
referencers; it does not establish a placed actor.

`Personas/Lira.txt` and `Scenarios/PoolSocial.txt` supply the requested personality
and role text. They do not instantiate a waitress service controller or claim
that dialogue can deliver drinks. The ordinary loaded-world survey found no
Lira mesh actor. The later temporary preview actor is explicitly not persistent
placement. Restaurant placement, social animation fitting, native role binding,
voice and actual interaction remain lead-owned under RPT-20261020-02.

## Preservation and owner checks

The initial 140-file guard covers all Lira originals, tuning, both reviewed maps
and the module. Production saves are separately snapshotted by the profile tool.
No original or save may be restored automatically if an unrelated owner edit is
detected. Native copies remain private local assets; GitHub carries their
reproducible authoring/readback scripts, profiles and concise evidence only.

Pending owner checks stay in `docs/KNOWN_ISSUES.md`: hero appearance,
physical movement/jump/selection/seating and the previous bar/audio/fit cases.
Lead retains cloth repair, Lira placement/retargeting, dive/roll and squirrel
duties; none is closed by this review. No automatic merge or redesign.
