# Club crowd: starter clip table proposal (RPT-20261120-01, step 3)

Proposed 2026-11-21 for owner approval before any asset is created. Source of every length and skeleton:
a headless inventory of the project on this date (`X:\Claude_Work\ClubCrowd\inventory\anims.json`, 2,456 clips).
The director only plays a clip on a patron whose skeleton matches the clip, so the table is organised by
**skeleton family** first and activity second.

## Who the patrons are (saved `L_FullVexaChamber`, 2026-11-21 01:04)

| Family | Mesh / skeleton | In the club now | Clips already on the skeleton |
| --- | --- | --- | --- |
| Nyxar | `SKM_Nyxar` / `SKEL_Nyxar`, 6 recolour instances | the majority of the 44 `OUT_` patrons | 54: 18 `A_Nyxar_*` tavern/drunk/dance retargets (14 already in the map), 18 `A_Alien_*` MCO idles/walks/convo |
| Tripo crew with patron retargets | `SK_Warden`, `SK_Finhead` (own skeletons) | bar, booths, dancers | 12 `A_<Body>_Pat_*` each (tavern/drunk/3 dances) + idle/talk/listen/fidget/walk |
| Tripo crew without | `SK_Ember`, `SK_Glyph`, `SK_Olive`, `SK_Robe`, `SK_Seer`, `SK_Tendril` | dealer, ad reader, walkers, talkers | idle/talk/listen/fidget/walk; `SeatedVisitor` on Glyph/Robe/Seer/Tendril |
| Wardrobe bodies | `SK_Allison`, `SK_Femme2` | socialisers and walkers (2026-11-20) | own `A_<Name>_AS_*` sets |

**Proposed:** build the first table for **Nyxar, Warden and Finhead** (every activity), and let the other six
Tripo bodies take **Social and Moving only** from the clips they already have. **Allison and Femme2 stay out**
of the director for now: the other session is working on them (hair physics, cm re-export of the mesh and every
clip is still pending) and the continuity file marks them ON HOLD until you say go.

Every retargeter needed already exists: `RTG_DrunkToNyxar` (UE5 Manny → Nyxar, made the `A_Nyxar_*` set),
`RTG_MannequinToNyxar` (UE4 Manny → Nyxar, made the `A_Alien_*` set) and `RTG_<Body>_Manny` for every Tripo body
(made the `Pat_*` sets in pass 17). All owned packs below are on a UE5 `SK_Mannequin` copy except AD_* and MCO (UE4).

## Legend

- **have** = the asset exists on that skeleton today. **RT** = create by batch retarget through the retargeter named.
- Length in seconds. Loop = plays as a loop in the director (clip is a loop or long enough to hold 15–40 s).
- The director forbids repeats of a patron's last two clips and near-identical phase within 8 m, so 6–10 per
  activity is the minimum that keeps the floor from cloning; long mocap takes count double because the random start
  point lands in different moments.

## Dancing — three styles (a dancer keeps one style all night)

**Style 1 — Club, energetic** (the floor in front of the DJ)

| Source clip | Len | Nyxar | Warden / Finhead | Why |
| --- | --- | --- | --- | --- |
| VarietyDanceAnims `AS_ClubDance` | 54.4 | have `A_Nyxar_ClubDance` | have `Pat_ClubDance` | in the map today; long, full-body |
| VarietyDanceAnims `AS_ClubDance2` | 87.7 | have | RT | longest take, most variety per loop |
| VarietyDanceAnims `AS_PartyDance` | 36.8 | have | have `Pat_PartyDance` | in the map today |
| VarietyDanceAnims `AS_PartyDane2` (pack typo) | 26.2 | RT | RT | different footwork from PartyDance |
| VarietyDanceAnims `AS_PartyDance3` | 42.5 | have | RT | in the map today |
| VarietyDanceAnims `AS_SimpleDance` | 65.4 | have | have `Pat_SimpleDance` | low-key bob for the edge of the floor |
| TavernAnims `AS_Dance3` | 24.2 | RT | RT | stomping tavern dance, reads drunk-happy |
| TavernAnims `AS_Dance` | 20.8 | RT | RT | arms-up sway, cheap filler between big takes |

**Style 2 — Casual groove** (bar side of the floor, people who came to drink and ended up dancing)

| Source clip | Len | Nyxar | Warden / Finhead | Why |
| --- | --- | --- | --- | --- |
| VarietyDanceAnims `AS_FunnyDance` | 33.2 | RT | RT | comic, breaks the "everyone is a pro" look |
| VarietyDanceAnims `AS_PJ_Dance` | 72.6 | RT | RT | loose, long |
| VarietyDanceAnims `AS_PJ_Dance2` | 81.7 | RT | RT | loose, long, different phrase |
| TavernAnims `AS_Dance2` | 16.8 | RT | RT | small shuffle |
| TavernAnims `AS_Dance4` | 14.1 | RT | RT | small shuffle, second variant |
| KawaiiAnimations `Anim_KA_Idle16_WaveHands` | 8.0 | RT | RT | hands-in-the-air crowd beat, loops cleanly |
| FreeAnimsMixPack `AS_DiscoDance` | tbc | RT | RT | classic disco; length to confirm at creation |

**Style 3 — Sensual, slow** (hips, lower energy; keeps the pro routines for the stage girls)

| Source clip | Len | Nyxar | Warden / Finhead | Why |
| --- | --- | --- | --- | --- |
| SensualMoves `AS_Dance1` | 13.9 | RT | RT | |
| SensualMoves `AS_Dance2` | 20.0 | RT | RT | |
| SensualMoves `AS_Dance3` | 17.4 | RT | RT | |
| SensualMoves `AS_Dance4` | 34.6 | RT | RT | longest of the pack |
| SensualMoves `AS_Dance5` | 19.4 | RT | RT | |
| SensualMoves `AS_Dance7` | 27.2 | RT | RT | |
| SensualMoves `AS_Dance8` | 28.7 | RT | RT | |
| SensualMoves2 `AS_Dance3` | 20.1 | RT | RT | |
| SensualMoves2 `AS_Dance6` | 21.9 | RT | RT | |

Left out on purpose: `AS_StripDance*` (five takes; the 18+ kiosk rule and pass 20's bare-chest ruling say patrons
stay clothed and tame), AD_Pro_Club_Girl / AD_Goddess / AD_SensualDancer (UE4 skeleton, 30 s pro routines already
used for Vexa's stage: patrons would clone the performers), Dance_Set (2–5 s snippets, too short to hold).

## Bar — standing (`Bar`, `Standing`)

| Source clip | Len | Nyxar | Warden / Finhead | Prop | Why |
| --- | --- | --- | --- | --- | --- |
| TavernAnims `AS_AtTheBar` | 19.3 | have `A_Nyxar_AtTheBar` | have `Pat_AtTheBar` | none | leaning on the counter |
| TavernAnims `AS_TalkAtTheBar` | 12.1 | have | have | none | in the map today |
| TavernAnims `AS_CheersAndDrink` | 11.5 | have | have | glass | in the map today |
| DrunkAnimations `AS_DrunkTalk` | 28.7 | have | have | glass (left) | pass 9 grip maths already fitted |
| DrunkAnimations `AS_DrunkIdle` | 21.0 | have | have | none | sway, tipsy |
| TavernAnims `AS_AtTheBar2` | 12.7 | RT | RT | none | second lean |
| TavernAnims `AS_TalkAtTheBar2` | 15.1 | RT | RT | none | |
| TavernAnims `AS_TalkAtTheBar4` | 17.8 | RT | RT | none | |
| Bar_NPC_Mocap `ANIM_IP_customer_stand_bar_01` | 69.5 | RT | RT | none | real mocap, a minute of small changes |
| Bar_NPC_Mocap `ANIM_IP_customer_stand_bar_04` | 78.7 | RT | RT | none | real mocap, longest |
| Bar_NPC_Mocap `ANIM_IP_customer_stand_bar_against_seat_01` | 45.0 | RT | RT | none | leans on a stool: needs a stool spot |

## Bar — seated on a stool (`Bar`, `Seated`)

| Source clip | Len | Nyxar | Warden / Finhead | Prop | Why |
| --- | --- | --- | --- | --- | --- |
| DrunkAnimations `AS_DrinkSitting` | 32.6 | have `A_Nyxar_DrinkSitting` | have `Pat_DrinkSitting` | glass | upright stool sit; pass 20: Finhead's legs went through the tub stool, so Finhead gets no stool spot until seats are fitted |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_bar_01` | 45.0 | RT | RT | none | mocap |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_bar_03` | 40.7 | RT | RT | none | mocap (`_02` has root motion, skipped) |

Thin on purpose: only three usable stool takes exist. The 200+_Bar pack has `He_Sit_Counter` in 1.5–3.4 s
segments that could be stitched later. Stools are few, so three takes do not clone.

## Lounge — seated at tables and booths (`Lounge`, `Seated`)

| Source clip | Len | Nyxar | Warden / Finhead | Others | Why |
| --- | --- | --- | --- | --- | --- |
| TavernAnims `AS_TalkAtTheTable` | 22.3 | have | have `Pat_TalkAtTheTable` | | in the map today |
| TavernAnims `AS_LaughAtTheTable` | 14.6 | have | have | | in the map today |
| `A_Nyxar_SeatedLounge` (station crew) | 4.0 | have | | `SeatedVisitor` on Glyph/Robe/Seer/Tendril | quiet loop, the resting pose between talk takes |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_table_01` | 30.3 | RT | RT | | |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_table_03` | 34.3 | RT | RT | | |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_table_04` | 44.5 | RT | RT | | |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_table_06` | 66.1 | RT | RT | | longest |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_table_drink_01` | 19.4 | RT | RT | glass | |
| Bar_NPC_Mocap `ANIM_IP_customer_sit_table_drink_03` | 38.4 | RT | RT | glass | |

Known limit: seat fitting is phase 4. In the first run a seated patron stands on the spot origin raised by the
spot's `SeatHeight`; the chair takes put the actor origin on the floor under the heels with the pelvis about 57 cm up
and 32 cm back (pass 14 numbers), so the first captures will show seat offsets to correct, not finished sitting.

## Social — standing in groups (`Social`, `Standing`)

| Source clip | Len | Nyxar | All Tripo bodies | Why |
| --- | --- | --- | --- | --- |
| MCO `Convo_01_Low_Key_Loop` | 29.4 | have `A_Alien_Convo_01_Low_Key_Loop` | have `A_<Body>_Talk` | the talker; in the map today |
| MCO `Convo_11_Listening_Loop` | 24.8 | have | have `A_<Body>_Listen` | the listener; in the map today |
| MCO `MOB1_Stand_Relaxed_Idle_v2` | 6.1 | have | have `A_<Body>_Idle` | pass 20 WORKS as the wall patron |
| MCO `MOB1_Stand_Relaxed_Fgt_v1` | 5.0 | have | have `A_<Body>_Fidget1` | weight shift |
| MCO `MOB1_Stand_Relaxed_Fgt_v4` | 6.8 | have | have `A_<Body>_Fidget2` | second weight shift |
| `TalkDramatic1` / `TalkDramatic2` | 5.7 / 6.0 | — | have | big-gesture talker for the Tripo bodies |
| `IdleBoredLean_Lt` / `_Rt` | 8.3 | — | have on Glyph/Robe/Seer/Tendril | someone waiting for a friend |
| KawaiiAnimations `Anim_KA_Idle28_Laugh` | 8.3 | RT | RT (Warden, Finhead) | the laugh in a group |
| `A_ReceptionVendor_AS_TalkLoop` | 8.8 | have | | third talk variant for the Nyxar |

ExpressiveGestures (hand-shake, wave, finger-wag, 57 one-shots on UE5 Manny) are the phase 5 flavour layer for
groups, not loops; left out of the starter.

## Moving — walking between zones (`Moving`, `Standing`)

| Source clip | Len | Nyxar | All Tripo bodies | Why |
| --- | --- | --- | --- | --- |
| MCO `MOB1_Walk_F_Loop_IPC` | 1.2 | have `A_Alien_MOB1_Walk_F_Loop_IPC` | have `A_<Body>_Walk` | in-place walk, the baseline |
| MCO `Walk_02_Cheerful_Loop_IP` | 1.2 | have | have `A_<Body>_WalkCheerful` | bouncier |
| MCO `Walk_06_Look_Around_Loop_IP` | 11.9 | have | have `A_<Body>_WalkLookAround` | head turns while crossing the room |
| MCO `Walk_04_Texting_Loop_IP` | 3.3 | have | RT via `RTG_<Body>_Manny` from the UE4 source (needs the UE4→UE5 step first) | phone walk |
| MCO `Walk_13_Power_Walk_Loop_IP` | 4.2 | have | same | someone late for a friend |
| MCO `Walk_08_Listen_Music_Loop_IP` | 7.0 | RT via `RTG_MannequinToNyxar` | same | headphones bob |

Walk rule to settle in step 4: the director moves walkers at a fixed 120 cm/s and plays every clip at a random
0.9–1.1 rate, so feet will slide up to 10 %. I propose to measure the Nyxar in-place walk's foot speed in one frame
pair, set `walkSpeed` to it, and exempt `Moving` clips from the random rate (a two-line rules change with a test).

## Special (`Special`; 0–2 patrons each)

| Source clip | Len | Posture | Nyxar | Warden / Finhead | Why |
| --- | --- | --- | --- | --- | --- |
| DrunkAnimations `AS_SleepingAtTheTable` | 13.1 | seated | have `A_Nyxar_SleepingAtTheTable` | RT | asleep in a booth |
| TavernAnims `AS_SleepAtTheBar` | 13.6 | seated | RT | RT | asleep on the counter |
| DrunkAnimations `AS_Drunk` | 49.8 | standing | RT | RT | long sway, the drunk |
| DrunkAnimations `AS_VeryDrunk` | 17.4 | standing | RT | RT | worse |
| DrunkAnimations `AS_DrunkIsSmoking` | 29.8 | standing | RT | RT | no prop yet; smoking reads as VIP corner |
| Finhead `A_Finhead_Emote_ChillOut_T3` | tbc | standing | — | have (Finhead) | the VIP who owns the room |

Left out: `AS_Vomits*`, `AS_RelieveOneself*`, `AS_Laying*`, `AS_AggressiveDrunkard*`, the fights. Say so if you want
any of them; they are one row each.

## What creating this costs

- New retargeted clips: about **42 for the Nyxar** (`RTG_DrunkToNyxar`, one batch), about **38 each for Warden and
  Finhead** (`RTG_<Body>_Manny`). Batch retargets run in the hidden editor in minutes; the review is the cost.
- Every new clip gets looked at once on its body in the offscreen run (sheet per activity) before it stays in the
  table. Retargets of the tavern/drunk packs onto these three bodies are proven (passes 9–20); the mocap bar pack and
  SensualMoves are new onto them.
- One `DT_ClubClips` table (row type `SSClubClipRow`) under `/Game/SpaceSurvival/Club/`, tracked in Git.

## Decisions wanted

1. Approve the three dance styles as cut above (Club / Casual groove / Sensual), or move clips between them.
2. First-run crowd of about 24 as **16 Nyxar + 4 Warden + 4 Finhead**, with the other Tripo bodies on Social and
   Moving only, and Allison / Femme2 left to the other session. Yes or change.
3. The walk-rate exemption for `Moving` clips (rules change).
4. Any of the excluded clips you want back in.
