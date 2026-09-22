# Locked main menu: Figma source and export contract

Reviewed 2026-09-21. This records the approved design source, extracted artwork and native integration contract. Build, packaged rendering, physical input and owner acceptance remain separate evidence in the canonical project state and validation receipts.

## Approved source

The source is [SpaceSurvival UI Kit](https://www.figma.com/design/6M3VvUB7jsPDd3E41YpKM0/SpaceSurvival-UI-Kit), file key `6M3VvUB7jsPDd3E41YpKM0`. The owner approved the locked `01 · MAIN MENU` page (`142:1059`) and the currently needed menus from `11 · UI REFRESH — REVIEW` (`203:1058`). The original scenario pages are stale. KIT components may supply their existing artwork; pages 12 and 13 may supply supporting assets only where needed by an approved target. The main-menu extraction uses page 01 only.

The connector initially reported only the KIT page. A read-only Plugin API enumeration of `figma.root.children` found all 16 pages and verified the approved IDs. The inspection used the Figma design-to-code and Figma Plugin API skills. No Figma nodes were created, hidden, recolored, moved or edited.

## Main-menu composition

The main screen is a composition of separate page children, not a containing frame. Its locked background node `144:1103` occupies 3840×2160 at page coordinates (-501, -681). Canvas coordinates in the provenance manifest subtract this origin.

| Element | Source node | 4K canvas position and logical size |
| --- | --- | --- |
| Background | `144:1103` | (0, 0), 3840×2160 |
| Title | `144:1130` | Logical (689, 24), 2961×439; exported glyph bounds (710, 93.5), approximately 2619.9585×230.4 |
| Alien portrait | `145:1169` | (273, 482), 583×1374 |
| Squirrel portrait | `144:1167` | (2792, 383), 1048×1572 |
| Continue | `160:1124` | (1207, 583), 1470×269 |
| New Game | `160:1135` | (1207, 912), 1470×269 |
| Settings | `160:1146` | (1207, 1241), 1470×269 |
| Exit Game | `160:1157` | (1207, 1570), 1470×269 |
| Footer panel | `144:1164` | (86, 1936), 516×146 |

The four instances on the complete screen are **Default**. The separate approved **Hover** instances are `161:1158`, `161:1168`, `161:1178` and `161:1188`; their component masters are `160:1118`, `160:1129`, `160:1140` and `160:1151`. Mouse hover and controller selection use this authored appearance. The corresponding Default masters are `159:1122` through `159:1125`.

Keep visual padding separate from input bounds. Default artwork extends 58 pixels beyond each logical edge at 4K (1586×385 render bounds); Hover extends 69 pixels (1608×407). At 1080p, logical hit rectangles are (603.5, 291.5/456/620.5/785), 735×134.5. Drawing the padded texture inside the smaller logical rectangle would shrink the artwork and clip its glow.

The actual title node uses **Wallpoet Regular, 300 px**, in teal. Button labels use **Keania One Regular, 128 px**. The older page-12 statement reserving Skranji for the title conflicts with the inspected locked node; preserve the actual node. The footer's historical `V1.02` and release-log caption are sample content. The native review substitutes the authorized truthful `DEVELOPMENT REVIEW` label inside the preserved panel.

The approved action mapping is Continue → existing checkpoint continuation, New Game → home hangar and physical ship boarding, Settings → preferences, Exit Game → quit. Boarding provides the existing Start Survival / Continue Survival / Free Flight choices. The four title buttons do not add a second launch implementation.

## Extracted artwork and provenance

The review exports are under ignored `Artifacts/FigmaMainMenu`. `provenance.json` records each source node, filename, extraction method, SHA-256, PNG dimensions, alpha range and both 4K/1080p draw rectangles. The delivery source directory is `ContentSource/FigmaMainMenu`; its copied provenance and bytes are the durable input for the native texture author.

The extraction contains 21 records: 19 runtime images, the entirely transparent outer footer instance (`144:1150`, excluded), and the historical version caption (excluded). The runtime set consists of a background, title, two portraits, four Default and four Hover buttons, footer panel, and six keyboard hint text images. Eighteen runtime images preserve transparency; only the background is intentionally opaque.

The connector's default PNG download path produced opaque white mattes and clipped button padding. Those diagnostic renders remain under ignored `Artifacts/FigmaApproved` and must not be imported. Final button, title, panel and hint images were exported through the read-only Plugin API:

```javascript
await node.exportAsync({
  format: "PNG",
  contentsOnly: true,
  useAbsoluteBounds: false,
  constraint: { type: "SCALE", value: 0.5 }
});
```

Native exports used the actual instances to retain their outer glow. The connector's 20 KB result limit required segmented transfer. Every segment was checked against the complete native byte count and FNV-1a checksum before assembly; the local manifest additionally records SHA-256. The source export scale targets 1920×1080. The integer PNG heights include fractional raster rounding; draw using the measured floating-point rectangles rather than substituting bitmap dimensions.

Both portrait sources came from the visible image fills returned by design context and retain alpha. The alien source is 1792×1008. Its authored image transform is U offset 0.3783482313156128 and U width 0.2388392984867096, with the complete V range. The supplied portrait is a lossless pixel crop (678, 0)–(1106, 1008), preserving the original source separately. No character artwork was generated or repainted.

The buttons include the captured native appearance of the animated `SS Stardust` shader. The WGSL/source context is retained in the ignored extraction receipt. These PNGs are a static captured frame; importing them does not implement shader animation.

Independent extraction checks passed: 11 native byte-count/checksum comparisons, all 21 file hashes and dimensions, alpha ranges for the 19 runtime assets, and exact source-pixel equality for the alien crop. Visual review matched the Default colors, icons, typography and portrait crop to the approved full-page screenshot and confirmed the brighter Hover state. Runtime compositing, focus navigation, 4K sharpness and animation acceptance require their own Unreal evidence.

## Page 11 mapping

These are source references for existing behavior, not instructions to import every frame or hard-code its sample data. All frames are 1920×1080. Balances, prices, progression, availability, current control bindings and save/run outcomes come from the game.

| Existing context | Approved frame node(s) |
| --- | --- |
| Ship upgrades; insufficient funds; purchase success | `203:1059`; `229:1470`; `229:1535` |
| Controls | `208:1087` |
| Flight HUD; critical damage | `210:1109`; `246:1592` |
| Mobile depot | `213:2111` |
| Contract board | `213:2116` |
| Starting chassis | `216:1226` |
| Starting weapon | `216:1231` |
| General settings; graphics; audio | `219:1282`; `219:1287`; `219:1292` |
| Paint; wardrobe | `219:1297`; `219:1302` |
| Pilot record; recent journeys | `219:1307`; `230:1528` |
| Survival results | `219:1312` |
| Suspend/save; end-run confirmation | `219:1317`; `241:1579` |
| On-foot station presentation | `219:1322` |
| Utility vendor; repair service | `219:1327`; `219:1332` |
| Station 2 arrival | `219:1337` |
| Pause | `227:1461` |
| Optional event; event reward | `227:1466`; `230:1533` |
| Asset acknowledgements | `262:1676` |

Design contexts and screenshots were retrieved for Ship Systems, Controls, Pause and Event Reward. Their receipts are alongside the main-menu extraction. No page-11 artwork was imported as part of this extraction.

The sample Controls and HUD text still assigns RT to boost, and the station sample assigns A to interaction. The approved current bindings are RT throttle, B boost, LT brake, RB fire; on foot E/Y interact and Space/A jump. Keep the live reward panel's captured steering and keyboard/controller selection semantics when applying its layout. The current boarding launch choice has no dedicated page-11 frame. Page-13 scene plates remain proposed artwork and do not replace actual gameplay backgrounds through this handoff.
