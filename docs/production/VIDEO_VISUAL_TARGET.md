# Owner video visual target

Owner-designated reference: [Space Survival Concept](https://www.youtube.com/watch?v=y8I_wlOLkJU), 47 seconds. Supplied September 14, 2026. This establishes presentation intent alongside the existing scope; incidental text and objects do not authorize additional mechanics.

## Observed reference and implementation implications

| Sample | Observed presentation | Next implementation target |
|---|---|---|
| Opening, 0:10 and 0:20 | Bronze ship, bright pale-blue/white exhaust, many rock scales, illuminated cool haze, silhouettes and bright combat streaks | Layer background, middle-distance rocks and local dust; preserve a readable flight corridor. Light the hull and threats separately from atmospheric depth. Match exhaust placement and readable combat reactions. |
| 0:35 | Ship parked within an enclosed, populated industrial bay; visible cockpit, character, floor markings, workstations, crates and banners | Build coherent room scale and connected bay geometry, use practical lighting and deliberate prop placement, retain readable navigation. |
| 0:40 | Squirrel character at a bright service console, hands directed toward its controls | Improve terminal scale, interaction framing, character contact/pose and clear service feedback using scoped services. |

These are sampled-frame observations, not a frame-by-frame animation, audio or full-resolution review. A sampled 0:30 frame was black; no transition mechanics are inferred from it. Video was inspected in the browser, not downloaded.

## Acceptance direction

The published 0.1.15-alpha environment did not meet this target at the September 14 review. Asset integration alone is insufficient. Compare the same short flight with whole-ship framing, layered depth, controlled highlights and readable threats, then arrival, bay layout and terminal interaction. Keep early-wave difficulty independent of decorative density. Do not implement incidental pickup, weapon, currency or menu text from the concept as new game rules.

Later on September 14, the owner explicitly requested a visibly new provisional player hull from the purchased Havolk kit, including a closed cockpit. This supersedes the earlier visible-pilot-default constraint for that interim hull. It is an interpretation pending owner art review, not a final identity decision; the regular artist retains long-term hero/iconic-starter ownership. The sampled video observations above remain unchanged.

The older published itch release keeps its experimental volume banks disabled after opaque artifacts. The current private visual pass enables thinner local banks and a new regional sky; consult [project state](../PROJECT_STATE.md) and [validation](../VALIDATION.md) for the exact package and rendered evidence. Station/player follow-up source `4dc45ac` has two additional walkway fill lights, unlit service labels, passing native integration tests and audited Package 3 captures. The lead's inspected views show the new hull framed, the station furnished, its walking pilot visible and service labels clearly lit. The [Package 3 receipt](../validation/2026-09-14-visual-enhancement.json) preserves that checkpoint.

The owner then found the stars overpowering forward flight and station views. Material-only follow-up `cf6296f` reduces their brightness and adds fixed directional variation while preserving nebula brightness and object lighting. Package 4's authoring/archive audit and both packaged captures pass; the [star-adjusted receipt](../validation/2026-09-14-visual-enhancement-stars.json) preserves their identity. The lead inspected Cruise, Approach and StationOverview: stars are quieter, object contrast is improved, and station lights/labels remain visible. This targets focal-object readability without changing the sampled video observations or establishing owner acceptance. Broader presentation remains provisional.
