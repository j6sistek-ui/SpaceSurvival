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
| Fitted clothing | `Mesh/SK_WaitressOutfit_V14` under that root |
| Blender source | `.agent/local/Waitress_20261015/Waitress_GarmentFit_V14.blend` |
| Clothing-only FBX | `.agent/local/Waitress_20261015/Waitress_Garments_V14.fbx` |
| Saved placement | `/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime` |

The original body, face, skeleton, physics asset, post-process and vendor materials are preserved. Both garments share one skeletal mesh on the Corset component; the separate Shorts component is unused. The corset follows the body's final pose through Leader Pose, including the post-process breast movement. It is skinned clothing, not a separate Chaos cloth simulation.

V14 keeps the corset's V9 shape. Its shorts use a body-surface fit, smoothed displacement, transferred normalized skin weights and clearance sampled over six walking poses. The original UVs/material separation and garment details remain. The final walking clearance adjustment is capped at 0.8 cm. Earlier closed-front, elongated-hem and hanging-flap candidates are rejected, not delivery alternatives.

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

See [the dated validation receipt](../validation/2026-10-15-waitress-bar-service.md) and [RPT-20261015-01](../KNOWN_ISSUES.md). Native scripted service is separate from physical keys, controller, microphone/audio and owner acceptance. Sitting currently snaps between the approach and seat transforms; dangling shorts ties follow thigh skinning and are not simulated. Custom eye selection/reusable eye rig remains pending the supplied files. No packaged build or release upload is included.
