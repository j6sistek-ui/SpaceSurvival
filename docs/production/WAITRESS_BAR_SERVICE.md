# Waitress and Joy bar service

Owner direction, October 15, 2026: fit the purchased corset and shorts to the native female body, retain its rig and jiggle, add drink/table service, and correct Joy's pour/cheers contacts. The product's open laced front and pointed hem are intentional. This authorizes this character/service work; it does not reopen Cyborg, Silver or station-wide appearance changes.

## Current local assets

### Current drinking contacts and patrons — October16

Current local map `5ac00104` uses `A_Waitress_DrinkStanding_RimV4` and
`A_Joy_CheersStanding_RimV3` for normal drinking. Each adjusts three right-arm
rotation tracks against the native mouth landmark, retaining the prior finger
correction, timing, all translations/scales and every other bone track.
`A_Waitress_StaffShot_V1` and `A_Joy_StaffShot_V1` fit the smaller0.55-scale glass.
Assign these through each placed actor's optional **Bar Shot Animation** property;
leave it empty to use the normal drink clip. A wrong-skeleton clip prevents an
ambient break. The normal action list and guest service clip stay unchanged.

Two existing Nyxar actors use private `BarPatrons_20261016/Anims` derivatives:
`A_Nyxar_DrunkIdle` on the arcade visitor and `A_Nyxar_Laying` on the corner
patron. The latter has no route, gestures, actions or ambient chatter so the
resting loop persists. Their original meshes/materials remain; no new NPC is
spawned. `A_Nyxar_SleepingAtTheTable` is prepared but not placed. Lead still owns
nearby interaction/collision review and owner natural-play feedback.

[Current evidence](../validation/2026-10-16-bar-contact-and-patrons.md); the grip-only receipt below is historical.

### Astra drinking grip — October16 correction

Earlier grip-only map `cebb5d83` uses `A_Waitress_DrinkStanding_GraspV2` for Astra's
drink animation and action1. Twelve right-finger rotation tracks now curl toward
the tumbler; the original clip, arm motion, grip transforms, V16 outfit and
physics are retained. Saved reload and407 uninterrupted service samples pass.
Mouth/rim alignment and the other open contact/fit/audio checks remain lead work.
[Before/after and evidence](../validation/2026-10-16-astra-glass-grip.md).

### Footwear and filled glassware — October16 follow-up

Footwear/drink snapshot `fb604de9` supersedes the earlier bar snapshot below. Joy's
blue/black footwear uses `MI_Joy_IndigoSneakers` in slot18 and
`MI_Joy_IndigoPantsTrimShoes` in slot20; the right shoe shares that trim atlas.
Slot19 fabric, other character slots, rigs and animations are retained. Astra
footwear is deferred. `JoyShoes_20261016/Saved_Full.png` and `Saved_Shoes.png`
supersede the old red-shoe pants image for this review.

`CosmicDrinks_20261016/Meshes` contains `SM_CosmicAmberTumbler`,
`SM_CosmicVioletStem` and `SM_CosmicCyanStem`, derived from owned
`CyberPunkBarAssetSet01/StaticMeshes/SM_Glasses01`, `02` and `03`.
They retain exterior bounds/pivots and original glass material. Added liquid,
three ice cubes in the tumbler and subtle violet/cyan glints use private materials.
The amber mesh is assigned to Joy's Glass and Astra's Glass/ServedGlass without
changing grips; counter amber/violet replace two existing meshes and cyan adds
one actor on the solid counter. Blueprint defaults are unchanged: these are
placed-instance overrides. There is no fluid simulation, fill-level progression
or new drink-selection menu.

The saved review now links the shoes and three drink images. Same-editor
unload/reload and a new play session verify 6 assigned meshes, 9,480 actors and
9,479 preserved prior actor transforms. One scripted shared-drink request passes
260 samples; paused inspection stills do not prove continuous hand-to-mouth
contact or hair quality. [Detailed evidence and limits](../validation/2026-10-16-joy-shoes-and-bar-drinks.md).

### Bar art direction — saved local candidate, October 16

The owner supplied four images as the visual reference for bar design,
materials, colors, uniforms and drinks, then explicitly authorized room colors,
pink Illuminated Wall panels and large observation windows. Paraphrased direction:
an intimate, welcoming cosmic lounge, with playful service and a lively mix of patrons.

- Use deep midnight blue, indigo and near-black as the base; violet/magenta neon
  leads, with smaller cyan accents and restrained warm brass/gold details.
- Pair dark satin/leather-like fabrics and subtle metallic trim with worn dark
  metal, polished counter surfaces and clear glass. Keep their roughness distinct
  so the scene does not read as uniformly glossy plastic.
- Light faces and hands warmly and clearly; reserve colored glow for edges,
  signage and drinks. Preserve dark depth and local pools of table light, with
  reflections that retain surface detail. Apply the direction within the bar;
  global exposure or station-wide recoloring is not implied.
- Give drinks different silhouettes: a tall violet/pink cocktail, a cyan martini
  or highball, an amber drink over ice in a short tumbler, and small dark shots.
  Use visible liquid, restrained sparkle/bubbles, ice and simple citrus or star
  garnishes. Keep glass rims and the liquid surface readable when carried or poured.
- Carry celestial motifs into restrained piping, badges, menus and small signs;
  keep the atmosphere social through conversation, laughter and service. Large
  exterior-view windows are now explicitly requested; a clear starfield remains
  an unresolved composition goal.

Astra and Joy keep their names, identities, accepted voices and existing rigs.
Venue/staff names and menu text visible in the pictures are reference content,
not approved renames or a fixed drink menu. Outfit replacement is not inferred
from the images. Adapt the owned assets as their fit and contact issues are repaired.

Private originals are retained under
`.agent/local/Waitress_20261015/ArtDirection_20261016/`, with a hash manifest.
`Adopted.json` records saved local map `5fd8e257`: all 9,473 original actor
transforms are preserved, with six new actors (two window frames, two glass
panes and two pink wall panels). The two observation bays reuse owned Genesis
6 m window parts, scaled to a nominal 7.43 m wide by 4 m high each. Nearby
asteroid terrain blocks an open starfield view; the windows do not yet achieve
that requested exterior composition.

Thirteen private material instances, the new `M_Joy_IndigoFabric` parent,
431 material-slot assignments and six local light-intensity reductions implement
the darker room, Astra's indigo/violet/gold and Joy's plum hair/indigo pants.
The pants parent desaturates the original diffuse before tinting; normal,
roughness, metallic and emissive inputs are retained. These derivatives live
under `/Game/SpaceSurvival/Licensed/StationAssets/BarArt_20261016/Materials`;
character geometry, rigs, existing animations and accepted voices are unchanged.

The fresh saved-scene views are `Saved_Lounge.png`, `Saved_Astra.png`,
`Saved_Joy.png`, `Saved_JoyPants.png` and `Saved_WindowLeft.png`, recorded in
`SavedCapture.json`. `PantsIndigoFixed.png` remains the earlier correction
preview. `Review.html` is the local visual-review destination.
`FreshReload.json` verifies the same map hash, 9,479 actors, all 9,473 original
transforms, 431 assignments, six added actors and six reduced lights, with zero
dirty packages. Existing window collision and character meshes/idle/walk clips
are retained. `FinalPreservation.json` checks 62 guarded files, with all 61
non-map originals (including three project saves) unchanged; it records 14 new
material hashes, zero dirty packages and an ended play world. Lead next action
under RPT-20261015-01: review the darker room,
character colors and window shape with the owner, then resolve the exterior
composition. Stills do not validate costume fit in motion,
animation contacts, voices or performance. Seated shorts, native audio/laughter,
bar behaviors and the reference drink presentation retain their existing open
checks; this is not visual acceptance or a packaged release.
[Saved-scene validation and limits](../validation/2026-10-16-bar-lounge-art-direction.md).

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

Open `MI_Astra_IndigoCorset` or `MI_Astra_IndigoShorts` under the private `BarArt_20261016/Materials` folder for the current saved color candidate. Their inherited parameters separate indigo fabric, violet laces and gold trim; the prior `MI_WaitressCorset` and `MI_WaitressShorts` remain preserved. The exact inherited `Roughness_Intensity` parameter is 1.5 and `Normal_Intensity` is 0.65. Do not use the nonexistent `RoughnessIntensity` name.

The private `MI_WaitressHair` keeps the native hair, with Brightness 1 and Roughness 0.55. The October16 candidate reduces six local bar lights; earlier camera-only exposure comparisons remain diagnostics, not adopted global exposure changes.

For another fit, edit a copy of the final Blender source. Export only the garments and their unchanged reference armature with animation baking and leaf bones disabled. Import clothing against the existing `S_PerfectFemaleBody`; do not reimport the original body or skeleton. Match material slots by their imported names, compile the Blueprint, save with PIE stopped, then check walking, carrying, serving and sitting in Unreal. The private fitting scripts and pose samples are retained beside the source; they are historical authoring records, not an unattended all-in-one pipeline.

## Behavior and authoring

`ASSBarCrew` extends the existing ambient crew. `ASSBarTable` contains Approach, Seat and DrinkContact markers on existing furniture. No table geometry is generated. Blueprint properties own animations, hand grips, prop visibility windows, route points, colors and contacts; C++ owns service transitions and cleanup.

Four actions use the existing action menu/keyword route: order a drink, share a drink, sit together, and dismiss. Requests require the player within 4 m. Drink/sit requests need an available authored table within 3 m. The waitress reserves Joy while she pours, carries the glass back, serves it and optionally drinks. Sitting persists until dismissal or the player moves 6.5 m from the request location. A delivered glass remains on the table until the next order. This is social presentation, not an inventory purchase or consumable buff.

Ten authored corridor points are relative to the waitress's home. A visibility graph uses capsule sweeps; each movement step also checks deck support and uses swept movement. Blocked routes/timeouts return a refusal and release reservations. Keep route points clear of the counter and seats. The saved waitress label `Crew/Bar waitress` is explicitly retained by the station's temporary crew-trimming filter. Her component tags identify the Waitress persona/scenario.

Joy retains her native body, bob geometry, clothing and original animations; the October16 color candidate changes her hair to plum and pants to indigo. Only private fit derivatives are corrected; original vendor clips remain. Pour uses left-hand glass/right-hand bottle; cheers uses the right-hand glass. Walk root translation is removed from the waitress's derivative while actor movement supplies travel at 95 cm/s. No native rig or original animation is overwritten.

Saved markers: waitress `(3970,-3690,85)`, Joy `(4150,-4140,85)`, table approach `(3800,-3630,85)`, seat `(3730,-3645,85)`, drink contact `(3690,-3560,45.5)`. These are local station coordinates, not runtime-origin assumptions.

## Review limits

See [the dated validation receipt](../validation/2026-10-15-waitress-bar-service.md) and [RPT-20261015-01](../KNOWN_ISSUES.md). Native scripted service is separate from physical keys, controller, microphone/audio and owner acceptance. Sitting currently snaps between the approach and seat transforms; dangling shorts ties follow thigh skinning and are not simulated. The selected WhitePurpleRings eyes and reusable rig are saved; automatic eye gaze is not added. No packaged build or release upload is included.

## Astra, eyes and voices

The waitress is now **Astra**: her own adult personality/backstory lives in `Content/SpaceSurvival/NpcTalk/Personas/Astra.txt`. `Personas/Waitress.txt` is the reusable type fallback; `Scenarios/Waitress.txt` supplies the shared job behavior. The existing name-first/type-fallback resolver combines the personal file with the role scenario. These are editable prompt files, not trained LoRA weights.

The owner selected preview `3_WhitePurpleRings.png`. Native `Eyes/SK_Eyes_WhitePurpleRings`, `MI_Eye_WhitePurpleRings` and `S_AstraEyes` live under the private root above. An independent poseable eye pair attaches to the unchanged body's `head` socket; the component masks the original eye material only. Five fitted variants share the reference rig, each retaining its own UV0 and maps. `USSBarEyeAuthoring` only initializes/reuses that bounded private rig and rejects differing names, parents or reference transforms. It does not change the body skeleton.

Reusable Blender library: `C:/Users/j6sis/OneDrive/Documents/Blender/Assets/AstraEyes_20261015/Astra_Eyes_SharedRig.blend`, with packed images, five named presets and matching FBXs. Eye_L/Eye_R are rigidly weighted, available for later gaze animation. Do not swap only the material between eyes whose UVs differ; swap the matching mesh/material pair.

`Voices/Astra.wav` is an original local synthetic adult reference (Qwen3-TTS VoiceDesign, October15); `Astra.txt` selects pace 0.88, no treatment. After the owner rejected Joy's robotic delivery, Joy received a fresh original VoiceDesign reference on October15 local time (October16 UTC), reserved for her: pace 0.90, no treatment, cache revision `4ea4ddf6b41e0b12`. Astra and all other references are unchanged. Runtime speech uses existing CPU LuxTTS and exact-name routing; no other character or alias selects Astra/Joy. Nine new Joy clips (greeting and eight replies) pass word-coverage checks; the 26 prior Astra clips and old Joy audio remain preserved. Owner accepted Joy's replacement on October15; retain it and Astra's separately designed voice. Expressive laughter and native audible mix remain open. Four private CPU laugh drafts are under `.agent/local/Waitress_20261015/Voice/Laughter_20261016`; they are not adopted, and text/PCM checks do not establish natural laughter.

Listen at `.agent/local/Waitress_20261015/Voice/JoyOriginal_20261016/index.html`: new Joy greeting, same-line old/new comparison, then Astra. `Joy_New_00.wav` also plays independently. Restart the game/talk sidecar after reference/settings changes. [Voice provenance, cache repair and limits](../validation/2026-10-16-joy-original-voice.md).

## Unprompted staff breaks

When idle and the player is nearby, Astra can walk to Joy for a quick shared shot every randomized 3–7 minutes. `BarBreakInterval`, `bAmbientBarBreaks`, `BarBanter` and `BarShotScale` are Blueprint tunables. `ResetBarBreakTimer` reschedules after an interval change. Eight authored exchanges use a shuffle bag: all play before reuse, with no immediate cycle-boundary repeat. This is a finite curated bank, not unlimited generated dialogue.

The routine reserves Joy, waits for the existing speech channel, alternates their own voices, starts both native drink clips together, and returns Astra to service. A small glass scale preserves the grip center. Guest service, menus and active conversations block a new break; guest requests interrupt an active break and send Astra home. Broken routes, missing partners and a 100-second bound release the reservation. No currency, inventory purchase or intoxication effect is added.

Crew speech now keeps its full PCM duration on the update that starts playback; countdown begins on later updates. This fixes a start-frame timing error without changing the two-second banter minimum or drink clips. Isolated and canonical builds pass. The first CPU-only native run passed assertions but failed the strict gate on two station-placement fixture warnings; the existing `-SSLegacyStation` isolated retry passes one test with zero warnings/errors in 8.23s. Heard audio and hand/glass contact still require separate verification. [Repair and evidence limits](../validation/2026-10-16-bar-speech-timing.md).

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


## Resting corner patron

The permanently sleeping Nyxar keeps the owned lying loop with **Conversation Enabled** false on the placed actor. Joy, Astra and the drunk arcade visitor remain available. Disabling conversation also clears stale hints/actions and rejects chatter; it does not change animation, collision or character identity. [Source, reload and playback evidence](../validation/2026-10-16-resting-patron-interaction.md). Astra's later preserve-volume trial remains rejected; V16 is unchanged and seated fit stays open.
