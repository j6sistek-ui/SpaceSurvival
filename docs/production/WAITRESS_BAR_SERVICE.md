# Waitress and Joy bar service

Owner direction, October 15, 2026: fit the purchased corset and shorts to the native female body, retain its rig and jiggle, add drink/table service, and correct Joy's pour/cheers contacts. The product's open laced front and pointed hem are intentional. This authorizes this character/service work; it does not reopen Cyborg, Silver or station-wide appearance changes.

## Current local assets

The canonical project is `C:/Users/j6sis/SpaceSurvival`. Licensed source assets and derivatives stay private, outside Git. No new purchase or runtime plugin is required.

| Asset | Location |
|---|---|
| Original body | `/Game/Perfect_Female_Body/Mesh/SK_Perfect_Female_Body_01WithoutClothes` |
| Original skeleton / physics / post-process | `S_PerfectFemaleBody`, `PA_Perfect_Female_Body_01`, `BP_UnrealJiggle` in the same mesh folder |
| Derived content root | `/Game/SpaceSurvival/Licensed/StationAssets/Waitress_20261015` |
| Waitress / bartender | `Blueprints/BP_BarWaitress`, `Blueprints/BP_JoyBarService` under that root |
| Fitted clothing | `Mesh/SK_WaitressOutfit_V16` under that root |
| Blender source | `.agent/local/Waitress_20261015/Waitress_GarmentFit_V16.blend` |
| Clothing-only FBX | `.agent/local/Waitress_20261015/Waitress_Garments_V16.fbx` |
| Saved placement | `/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime` |

The original body, face, skeleton, physics asset, post-process and vendor materials are preserved. Both garments share one skeletal mesh on the Corset component; the separate Shorts component is unused. The corset follows the body's final pose through Leader Pose, including the post-process breast movement. It is skinned clothing, not a separate Chaos cloth simulation.

V16 preserves the corset and original body. It restores the original shorts waistband/hem heights, smooths the horizontal fitting displacement, transfers skin weights again and checks clearance through six rest/walking samples. UVs and separate material slots remain. Native idle/walk/carry views improve, but the shorts still ride up in the seated pose: clothing remains unfinished. V14 is retained for recovery; V17 weights and V18–V20 seated corrective-shape trials were rejected and are not game assets.

## Change colors and fit

Open `MI_WaitressCorset` or `MI_WaitressShorts` under the private `Materials` folder. Their inherited material parameters separate the main fabric, laces and trim. Current fabric is dark graphite, laces cyan and trim pale metal. The exact `Roughness_Intensity` parameter is 1.5 and `Normal_Intensity` is 0.65. Do not use the nonexistent `RoughnessIntensity` name.

The private `MI_WaitressHair` keeps the native hair, with Brightness 1 and Roughness 0.55. Room lighting and exposure were not changed. Camera-only exposure comparisons are diagnostics, not adopted lighting.

For another fit, edit a copy of the final Blender source. Export only the garments and their unchanged reference armature with animation baking and leaf bones disabled. Import clothing against the existing `S_PerfectFemaleBody`; do not reimport the original body or skeleton. Match material slots by their imported names, compile the Blueprint, save with PIE stopped, then check walking, carrying, serving and sitting in Unreal. The private fitting scripts and pose samples are retained beside the source; they are historical authoring records, not an unattended all-in-one pipeline.

## Behavior and authoring

`ASSBarCrew` extends the existing ambient crew. `ASSBarTable` contains Approach, Seat and DrinkContact markers on existing furniture. No table geometry is generated. Blueprint properties own animations, hand grips, prop visibility windows, route points, colors and contacts; C++ owns service transitions and cleanup.

Four actions use the existing action menu/keyword route: order a drink, share a drink, sit together, and dismiss. Requests require the player within 4 m. Drink/sit requests need an available authored table within 3 m. The waitress reserves Joy while she pours, carries the glass back, serves it and optionally drinks. Sitting persists until dismissal or the player moves 6.5 m from the request location. A delivered glass remains on the table until the next order. This is social presentation, not an inventory purchase or consumable buff.

Ten authored corridor points are relative to the waitress's home. A visibility graph uses capsule sweeps; each movement step also checks deck support and uses swept movement. Blocked routes/timeouts return a refusal and release reservations. Keep route points clear of the counter and seats. The saved waitress label `Crew/Bar waitress` is explicitly retained by the station's temporary crew-trimming filter. Her component tags identify the Waitress persona/scenario.

Joy retains her current native body, pink bob, clothing and original animations. Only private `_Contact` derivative clips are corrected. Pour uses left-hand glass/right-hand bottle; cheers uses the right-hand glass. Walk root translation is removed from the waitress's derivative while actor movement supplies travel at 95 cm/s. No native rig or original animation is overwritten.

Saved markers: waitress `(3970,-3690,85)`, Joy `(4150,-4140,85)`, table approach `(3800,-3630,85)`, seat `(3730,-3645,85)`, drink contact `(3690,-3560,45.5)`. These are local station coordinates, not runtime-origin assumptions.

## Review limits

See [the dated validation receipt](../validation/2026-10-15-waitress-bar-service.md) and [RPT-20261015-01](../KNOWN_ISSUES.md). Native scripted service is separate from physical keys, controller, microphone/audio and owner acceptance. Sitting currently snaps between the approach and seat transforms; dangling shorts ties follow thigh skinning and are not simulated. The selected WhitePurpleRings eyes and reusable rig are saved; automatic eye gaze is not added. No packaged build or release upload is included.

## Astra, eyes and voices

The waitress is now **Astra**: her own adult personality/backstory lives in `Content/SpaceSurvival/NpcTalk/Personas/Astra.txt`. `Personas/Waitress.txt` is the reusable type fallback; `Scenarios/Waitress.txt` supplies the shared job behavior. The existing name-first/type-fallback resolver combines the personal file with the role scenario. These are editable prompt files, not trained LoRA weights.

The owner selected preview `3_WhitePurpleRings.png`. Native `Eyes/SK_Eyes_WhitePurpleRings`, `MI_Eye_WhitePurpleRings` and `S_AstraEyes` live under the private root above. An independent poseable eye pair attaches to the unchanged body's `head` socket; the component masks the original eye material only. Five fitted variants share the reference rig, each retaining its own UV0 and maps. `USSBarEyeAuthoring` only initializes/reuses that bounded private rig and rejects differing names, parents or reference transforms. It does not change the body skeleton.

Reusable Blender library: `C:/Users/j6sis/OneDrive/Documents/Blender/Assets/AstraEyes_20261015/Astra_Eyes_SharedRig.blend`, with packed images, five named presets and matching FBXs. Eye_L/Eye_R are rigidly weighted, available for later gaze animation. Do not swap only the material between eyes whose UVs differ; swap the matching mesh/material pair.

`Voices/Astra.wav` is an original local synthetic adult reference (Qwen3-TTS VoiceDesign, October15); `Astra.txt` selects pace 0.88, no treatment. After the owner rejected Joy's robotic delivery, Joy received a fresh original VoiceDesign reference on October15 local time (October16 UTC), reserved for her: pace 0.90, no treatment, cache revision `4ea4ddf6b41e0b12`. Astra and all other references are unchanged. Runtime speech uses existing CPU LuxTTS and exact-name routing; no other character or alias selects Astra/Joy. Nine new Joy clips (greeting and eight replies) pass word-coverage checks; the 26 prior Astra clips and old Joy audio remain preserved. Listening, expressive laughter and native audible mix remain open; transcription does not establish natural delivery.

Listen at `.agent/local/Waitress_20261015/Voice/JoyOriginal_20261016/index.html`: new Joy greeting, same-line old/new comparison, then Astra. `Joy_New_00.wav` also plays independently. Restart the game/talk sidecar after reference/settings changes. [Voice provenance, cache repair and limits](../validation/2026-10-16-joy-original-voice.md).

## Unprompted staff breaks

When idle and the player is nearby, Astra can walk to Joy for a quick shared shot every randomized 3–7 minutes. `BarBreakInterval`, `bAmbientBarBreaks`, `BarBanter` and `BarShotScale` are Blueprint tunables. `ResetBarBreakTimer` reschedules after an interval change. Eight authored exchanges use a shuffle bag: all play before reuse, with no immediate cycle-boundary repeat. This is a finite curated bank, not unlimited generated dialogue.

The routine reserves Joy, waits for the existing speech channel, alternates their own voices, starts both native drink clips together, and returns Astra to service. A small glass scale preserves the grip center. Guest service, menus and active conversations block a new break; guest requests interrupt an active break and send Astra home. Broken routes, missing partners and a 100-second bound release the reservation. No currency, inventory purchase or intoxication effect is added.

## Hero seating and side conversation panel

**E / gamepad Y** toggles Sit/Stand at nearby authored seats. `ASSStationSeat` is separate from cockpit boarding. The current station has 55 markers, 51 enabled; four plant-covered bench contacts are deliberately disabled. Armchairs, sofas, a bench and bar stools have scripted native checks. Other chairs require an authored marker and a compatible hero sit clip; this does not promise every arbitrary static mesh or hero rig works automatically.

The current 178-bone hero uses `HeroSeating_20261015/A_SquirrelSocialSit`, with hands on the lap. Seat pose/actor transitions blend, movement resumes on stand, and all three exit candidates are checked for floor, capsule and NPC clearance. Blocked exits keep the hero safely seated. Occupied NPC/hero contacts are excluded; waitress table reservations also respect hero seating. Head/camera look remains available.

Conversation history is now below the compass/radar in the game's existing frame/font/color style. The last 12 utterances are held for the session; the visible rows scroll upward, wrap long words, and leave the newest lines at the bottom. Captions enter when speech is actually released; menus hide the panel. It hides after 24 seconds without conversation. It is a display panel; existing talk input is unchanged.

Extension evidence is indexed in [the Astra social/UI receipt](../validation/2026-10-15-astra-social-ui.md). Natural input, listening, owner appearance and representative performance remain separate acceptance checks.

## Photo mode and controller shortcuts

Press **D-pad Up / F8** during play to pause and enter photo mode. The camera stays within 40 metres of the pawn's entry position and sweeps a 15 cm sphere against visibility collision. Walls stop travel. The landing-pad-to-bar distance exceeds that radius; nearby market viewpoints remain reachable within the radius. The radius does not move with the camera. Reset returns to the original view, and exit restores the previous view target/pause state without moving or repossessing the pawn.

| Action | Controller | Keyboard/mouse |
|---|---|---|
| Move / look | Left / right stick | WASD / mouse |
| Rise / fall | RB / LB | E / Q |
| Fast / slow | RT / LT | Shift / Ctrl |
| Zoom | D-pad Left / Right | Mouse wheel |
| Save PNG without HUD | A | Enter |
| Reset / hide controls | X / Y | Home / H |
| Exit | B / D-pad Up | Esc / F8 |

Files save under the running instance's `Saved/Screenshots/PhotoMode`, with unique timestamped names. The success message requires a nonempty file. The offscreen validation instance uses its isolated user directory; the ordinary owner launch uses its normal Saved location. Source checks do not establish physical-controller acceptance or every resolution/UI scale.

In settings, **LB / RB immediately switches General, Graphics, Audio and Controls**, wrapping at either end without changing a value. D-pad/stick navigation within a tab remains available. During play, **hold LB near a crew member to display the actual action names with UP / RIGHT / DOWN / LEFT labels**; press that direction while holding LB. Keyboard actions remain 1–4. D-pad Up alone is photo mode. Cockpit mode selection remains D-pad Left without LB. The microwave prop alone is rotated -90 degrees about its bounds centre; its door faces the working aisle.
