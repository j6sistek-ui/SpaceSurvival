# UI kit art requests

Art request list for the kit's author, not a task queue; open work stays in
[KNOWN_ISSUES](../KNOWN_ISSUES.md).

Packages, newest last. Build from the newest.

| Folder | Source zip | Note |
| --- | --- | --- |
| `SpaceSurvival_UI_Kit_REORGANIZED` | `..._REORGANIZED_UE5_8.zip` | Original full library, baked text throughout |
| `UIKit_Runtime` | `..._RUNTIME_COMPONENTS_PLUS_REFERENCE_TEMPLATES_UE5_8.zip` | First textless pass; frames were stripped of artwork |
| `UIKit_Patched` | `..._RUNTIME_COMPONENTS_PATCHED_PLUS_NEW_UE5_8.zip` | **Current.** Frames repaired, pips/rows/settings added |

## Verified fixed in the patched package

- **Frame artwork restored.** `Premium_Large_Window` again has the thick border, angled corner
  plates and inner outline. Confirmed against the broken version and the original art at identical
  size. Medium, Small, Portrait, Compact Module, Modal Dialog, Side Panel, NPC dialogues and the
  three Settings windows are all rich too.
- **Tier pips solved, better than requested.** `HUD/Progression_Pips` ships hex and star families in
  Empty / Filled / Current / Completed / Locked / Premium, plus 5-step bars. At 18 px they read
  clearly and differentiate strongly, which is exactly what the diamond substitute failed at.
- **Settings windows recovered** in Large / Medium / Small with section and row components.
- **Row plates added** in Default / Hover / Selected / Disabled.
- **Sliders expanded** to blue default/hover/active/disabled plus green, amber and red.
- **Also added:** icon backplates, checkbox family, vertical scrollbar, arrow controls, extra toggle
  colours.

## Still open

### 1. Baked text returned on 11 assets
The defect the textless pass existed to remove is back on:

`Windows/Frames/Premium_Card_Frame` ("CARD FRAME"), `Windows/Frames/Premium_List_Frame`
("LIST FRAME"), `Windows/Settings/Premium_Settings_Row_Default` / `_Hover` / `_Selected`
("SETTINGS ROW (NORMAL/HOVER/SELECTED)"), `Windows/Settings/Premium_Settings_Tab_Default` /
`_Empty` (caught the source sheet's "SETTINGS COMPONENTS" header across the top), and all four
`Windows/Rows/Premium_Row_*` plates ("ROW (DEFAULT)" and so on).

The Settings tabs in particular look like crops that caught the sheet title rather than the asset.

### 2. Nine-slice metadata declares impossible margins on 21 of 169 entries
The declared `margin_px` is larger than half the source's smaller dimension, so the slice is
mathematically invalid — the engine either clamps it or drops the border image entirely.

| Asset | Declared | Max possible | Source |
| --- | --- | --- | --- |
| Thin_Header | 42 | 14 | 323x28 |
| Info / Warning CompactBackplate | 38 | 16 | 326x33 |
| Critical / Success CompactBackplate | 38 | 17 | 326x35 |
| Compact_Module | 42 | 26 | 153x53 |
| Hull / Shields / Credits StatusModule | 56 | 42 | ~220x84 |
| List_Frame | 52 | 38 | 176x76 |
| All four popup backplates | 48 | 38 | ~180x76 |
| Large_Window | 66 | 58 | 264x117 |
| Card_Frame | 46 | 38 | 160x76 |

The metadata was not regenerated against the new, much smaller source images.

### 3. Source resolutions collapsed
`Premium_Large_Window` went from 1280x720 in the previous package to **264x117**. Card Frame is
160x76, the popups ~180x76. Stretched to the game's real 840 px panel these are being enlarged
roughly 3x, and the patch notes acknowledge 4K validation was deferred. Re-export the repaired
frames at the previous resolution.

### 4. Two broken crops
- `Windows/Frames/Premium_Tabbed_Frame` is not a frame. It renders as loose tab pills over vertical
  scratch marks, clearly a bad crop from a component sheet.
- `Windows/Rows/Premium_Row_Disabled` renders as a fragmented dashed outline rather than a coherent
  plate.

### 5. Interior fill is inconsistent across the frame family
About half carry a tinted interior (Compact Module, Medium, Portrait, Side Panel, Modal Dialog, NPC
dialogues, Settings windows and rows). The other half are fully transparent inside (Large Window,
Card, List, Small Window, Thin Header, all four popups, Settings tabs), so those need a fill drawn
underneath in code. Pick one convention.

### 6. Catalog does not match the package
`Docs/Asset_Catalog.json` lists 371 entries against **552 PNGs on disk**:
- **192 files are undocumented**, including the entire Stardust button family, the new pips, rows
  and settings components.
- **11 entries point at files that are not in the zip** — every
  `Reference_Templates_DO_NOT_IMPORT/*_ScreenBackplate_TEXTLESS.png`.

The 9-slice metadata has no phantom entries, but covers only 169 of 552 files.

### 7. Thruster icon still missing
`Icons/Systems` has Comms, Engine, Lock, Navigation, Repair, Scanner. The five upgrade trees are
Hull, Shield, Engine, **Thrusters**, Weapon, so the Engine icon is currently used twice.

### 8. Cannon icon ambiguous at row size
`Icons/Weapons/Premium_Cannon` reduces to a thin diagonal stroke at 34 px. Worth comparing against
`Premium_Laser` at 32-40 px, since both weapons need a legible row icon.

## Not gaps — deliberately unused

Oxygen, fuel, radiation, heat and progress modules are kept for possible later use and need no
action.
