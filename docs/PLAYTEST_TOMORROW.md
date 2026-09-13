# Tomorrow's hands-on playtest

**Owner navigation feedback received; acceptance remains open.** On 2026-09-13 the owner reported a stuck station camera, difficulty navigating and requested vertical mouse inversion. The [station camera repair](STATION_CAMERA.md) addresses that defect; a fresh owner retest is required. No listening or replay-motivation result has been received. The owner has already rejected the current graphics as far below acceptable. Generated spacecraft, station and secondary visuals are provisional; a substantial art replacement pass remains open. These checks do not ask the owner to accept that art. The supplied Acornaut remains the starting point for possible external cleanup. HeroAlpha mesh, rig and material experiments are paused and unadopted after the owner prioritized gameplay.

Work down this single list, record an observation, and resume at the first unchecked step next time. Every box starts unchecked. A defect is useful evidence; source code or an automated pass is not a hands-on result. The current source passed 37 Unreal tests. Package 13 repeated the normal-timing Wave 10 fixture with the latest gameplay corrections. Package 12 separately retains the preceding Station 1 transition and Wave 10 audits. These fixtures use seeded durability/scripted input; earlier full-journey automation uses shortened waves/assistance. Earlier isolated storage and prepared-station native checks retain their own source boundaries. None of these results checks any box below.

Session date/time: __________\
Build/commit: __________\
Resolution / graphics / frame cap: __________\
Mouse / controller model and connection: __________\
Preferred mouse sensitivity: __________  Preferred controller sensitivity: __________

**Package directory:** `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows`\
**Produced launcher:** `C:/Users/j6sis/SpaceSurvival/Artifacts/Windows/SpaceSurvival.exe`\
**Current packaged build:** Package 14/source `f4bfec8bb955a9dab23300c55b1ca81c53442504`; [camera fix and build receipt](validation/2026-09-13-station-camera.json). Inner executable SHA-256: `4918a6a0906ca11622ae45928b494870fcf2c7e174df4dbf4748d932a610fb55`. This replaces the shared Package 13 archive; earlier performance records remain historical. No checkbox is marked by automated tests or a defect report.

1. [ ] **Launch the recorded executable and open the home hangar.**\
   Expected: usable game window, visible Acornaut/ship and readable shell; no black view, missing assets or unwanted fullscreen switch.\
   Observation / screenshot / issue: ______________________________________

2. [ ] **Set a comfortable mouse steering dial before judging flight.**\
   Open **Settings → Controls → Mouse sensitivity**. The dial is adjustable from 0.3–2.9 in 0.2 steps, with an upper clamp and wrap to 0.3. The lead verified a change from 1.0 to 1.2 and a later packaged relaunch displaying mouse 1.2/controller 1.0. Your preferred values and their feel still need checking. Record the actual displayed value above. Launch a run, make small horizontal/vertical corrections, and adjust again if too slow or too sharp.\
   Expected: a visible change in response and usable fine corrections. Sensitivity is a preference to tune, not a fixed value the tester must accept.\
   Observation / preferred value: _________________________________________

3. [ ] **Check keyboard/mouse flight and chase camera.**\
   Mouse steers; W/S changes throttle; A/D and R/F move sideways/up/down. Try gentle weaving and a stronger turn.\
   Expected: responsive control with momentum/banking, ongoing forward movement, prominent Acornaut/ship and readable hazards without excessive camera swing.\
   Observation — loose, stiff, sluggish, twitchy or comfortable: ____________

4. [ ] **Try boost, sustained brake and all dodge directions.**\
   Shift exhausts boost; release to recharge. Hold Space until overheating, then cool. Use Q with lateral/vertical direction, including one deliberate obstacle clip during a dodge.\
   Expected: useful boost, meaningful partial braking without permanent parking, obvious resource states, sharp directional dodge and damage on collision.\
   Observation: _________________________________________________________

5. [ ] **Tune comfort/accessibility and return to flight.**\
   Test sensitivity, invert pitch, boost/brake hold versus toggle, camera shake, motion blur, subtitles, UI scale, Graphics and Audio.\
   Expected: ordinary menus pause, settings visibly apply, text stays inside panels, warnings remain understandable without color, and return does not leave stuck inputs.\
   Observation / preferred settings: ______________________________________

6. [ ] **Feel damage, recovery, pickups and Rapid Laser combat.**\
   Observe shield/hull damage and recovery in danger versus clear space. Collect each reward shape; use manual aim/soft brackets against debris/enemies and try an obstructed shot.\
   Expected: shield does not refill automatically; hull can recover; damage/critical state is clear. Pickups justify route risk; laser/destruction/fragments are readable; assistance never fires automatically.\
   Observation — hit feel, aim, recovery, reward clarity: ___________________

7. [ ] **Follow the first block and deliberately accept Salvage Cache.**\
   Approach before pressing E; complete a diversion when comfortable. On another attempt let an event fail.\
   Expected: approach alone does not commit; objectives/reward/failure are clear; event UI leaves the live ship controllable.\
   Observation: _________________________________________________________

8. [ ] **Use the one mobile depot while moving.**\
   Inspect its upgrade subset/deal and buy an affordable upgrade. With missing shield, explicitly buy the shield-only recharge (21 credits at default prices). Steer/brake with the panel open, then try a purchase/recharge after leaving range.\
   Expected: limited offers, retained control, a paid shield refill with no hull repair, and out-of-range rejection without spending credits.\
   Observation: _________________________________________________________

9. [ ] **Play Wave 5 and approach Station 1.**\
   Watch the wormhole emerge, counter the pull, survive hostile arrival, approach manually and enter landing assistance. If the run ends earlier, record death/retry notes in Step 14 and resume this route on another run.\
   Expected: continuous journey, noticeable climax, useful warnings, consistent controls and understandable/satisfying docking.\
   Observation — tension, fairness, visibility, docking: ____________________

10. [ ] **Walk Station 1 and choose meaningful purchases.**\
    WASD/Shift/E walk/run/interact. Visit all five upgrade paths, repair, Mica, contracts, the story beacon and launch. Buy what you want; try the beacon reward twice.\
    Expected: coherent feet/camera/exit, easy service discovery, roughly 2–3 useful purchases, compact visit and once-only side reward. Pressure discloses reduced shield/added pressure; Hunter explains target/reward.\
    Observation / purchases / visit length: ________________________________

11. [ ] **Save & Quit, relaunch, Continue and leave for Wave 6.**\
    First record ship/weapon, wave, credits, tiers, hull/shield, utility and contract. Compare after relaunch.\
    Expected: same station run/build, retained contract, Wave 6 departure and a consumed suspension that cannot act as a reusable checkpoint.\
    Before / after / discrepancy: _________________________________________

12. [ ] **Play Waves 6–10, Distress and both utility choices across attempts.**\
    Compare Vector Thrusters with Overdrive Cooling and try Heavy Cannon when rewarded/unlocked. Observe electrical/gravity pressure with debris and both enemies.\
    Expected: stronger compositions without unreadable hits, deliberate rewards, distinct weapons/utilities and time to respond to warning direction/sound.\
    Observation — weapon/utility feel, enemy distinction, unfair moment: _____

13. [ ] **Reach Wave 10's compound climax and Station 2.**\
    Look for simultaneous gravity, asteroids and enemies; inspect second-station services and contract resolution.\
    Expected: difficult but readable pressure and clean landing. Current slice behavior has no Wave 11; services/suspension remain and labelled abandonment gives no death XP. That boundary remains under review.\
    Observation — climax, reward and boundary friction: _____________________

14. [ ] **Inspect ordinary death, resumed death, progression and another run.**\
    Review XP/score, unlock messages, history and loadout. Use Heavy Cannon and Swift after their early unlocks; compare Swift agility/durability.\
    Expected: one award, permanently ended run, no reloadable dead checkpoint, clear next milestone, retained account options and fresh run-specific power.\
    Observation — clarity and immediate desire to relaunch: _________________

15. [ ] **Switch to a physical controller and calibrate its own dial.**\
    **Settings → Controls → Controller sensitivity** is separately adjustable from 0.3–2.9. Right stick steers, left stick moves laterally/vertically, D-pad up/down changes throttle.\
    Expected: comfortable fine control and a stable resting stick; mouse preference does not force the controller value.\
    Observation / preferred value / drift: _________________________________

16. [ ] **Repeat controller actions and live menus.**\
    RT boost, LT brake, LB directional dodge, RB fire, A interact, Menu shell and B back. Test hold/toggle, live depot/reward choices and disconnect/reconnect.\
    Expected: keyboard/mouse capability parity, no lost steering, accidental selection/fire or stuck inputs.\
    Observation: _________________________________________________________

17. [ ] **Complete the two-block station/save/death route on controller.**\
    Left stick walks, X runs, A interacts. Repeat services, events, contracts, utility/reward choices, both climaxes, Save & Quit/Continue and next-run selection across natural attempts.\
    Expected: no keyboard rescue; comfortable combat/walking and usable menus/terminals.\
    Observation / keyboard rescue needed: _________________________________

18. [ ] **Listen and judge readability in the busiest scenes.**\
    Compare engine/weapon/impact/pickup cues, alarm frequency/direction, pressure music and station decompression. Check pilot/tail/feet, bloom, hazards, telegraphs and maximum UI scale.\
    Expected: essential sounds/cues remain distinct without constant alarms/chatter or a hidden route. Rejected provisional art still requires replacement regardless of functional readability.\
    Observation / wave or timestamp: ______________________________________

19. [ ] **Record the decisive player verdict and next adjustment.**\
    After ordinary death and the available boundary, record whether another run is immediately appealing. Identify one biggest source of friction. Perceived smoothness is useful; measured FPS belongs in the separate performance record.\
    Immediate retry: __________  Why / why not: ____________________________\
    Biggest next adjustment: ______________________________________________\
    First unchecked step / next place to resume: ___________________________
