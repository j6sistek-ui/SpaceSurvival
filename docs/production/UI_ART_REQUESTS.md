# UI kit art requests

Gaps found while composing real game screens from `SpaceSurvival_UI_Kit_REORGANIZED`. This is an art
request list for the kit's author, not a task queue; open work stays in
[KNOWN_ISSUES](../KNOWN_ISSUES.md). Written September 16, 2026 against the ship upgrade panel pass.

The kit is a template library rather than a set of finished screens, and the owner has confirmed
screens will be composed from its parts. Everything below is a gap in the *parts*.

## Verified good — no action needed

- **Nine-slice works.** `Windows/Frames/Premium_Large.png` (554x214) stretched to 840x470 with a
  46 px corner inset and held up: corners clean, edges straight, no smeared decoration.
- **Alpha is correct.** Straight (unpremultiplied) alpha on transparent ground. The cyan bleed seen
  in preview was a premultiplied compositing artifact, not a defect. Keep it as it is.
- **Icons cover the five upgrade trees exactly**: `sys_hull`, `sys_shield`, `sys_engine`, `thruster`,
  `sys_weapons`. They read clearly down at 34 px.
- **Blank buttons are sufficient.** 5 styles x 3 widths x 5 states, all label-free.

## Gaps, in priority order

### 1. Every window frame has its name baked into the art
`LARGE PANEL`, `MEDIUM PANEL`, `SMALL PANEL`, `SIDE PANEL`, `SQUARE PANEL`, `PORTRAIT PANEL`,
`THIN HEADER PANEL`, `EMPTY CONTENT FRAME`, `CARD FRAME`, `LIST FRAME`, `COMPACT MODULE`,
`TABBED FRAME`, `MODAL DIALOG FRAME`, `POPUP WINDOW (LARGE/MEDIUM/SMALL)`.

The label sits across the top-left corner and top edge, so it survives nine-slicing and cannot be
cropped out without destroying the corner. **Blank versions of every frame are the single highest
value item.** The game draws all titles itself.

### 2. No tier / segment pip
The upgrade panel shows tier I-V. There is no small segmented indicator in the kit — the only bar
assets are full 640x128 framed resource modules, far too heavy for a table row. Needed: a small
segment pip, filled and empty states, roughly 14x14, or a 5-segment strip about 90x14.

### 3. No compact currency readout
`HUD/Resources/Premium_Credits.png` is 642x128, a full framed module. A panel header needs a small
inline coin glyph plus space for a live number, roughly 26x26. Currently substituting
`Icons/Resources/pickup_gold.png`, which works but is a pickup icon rather than a currency mark.

### 4. Row backing plate missing
Table rows are currently flat rects drawn in code. A blank row plate in normal / hover / selected /
disabled, nine-sliceable horizontally, about 756x52, would match the kit's language.

### 5. Settings windows only exist as slivers
5 of 7 files in `Menu_Kits_And_Templates/Settings` are broken crops (`audio` 858x66,
`controls_keyboard_mouse` 178x25, `display` 123x42, `gameplay` 186x51, `graphics` 236x31). The
complete windows exist only inside `Reference_Sheets/neon_sci_fi_settings_ui_asset_sheet.png`.

### 6. Slider and toggle parts are not extracted
The reference sheets show sliders, toggles, checkboxes, radios and dropdowns, but
`Toggles_And_Controls/` only holds one 121x44 tab bar, eight small headers and two settings windows.
Settings needs slider track, slider fill, slider thumb, toggle on/off and checkbox on/off as
separate assets.

### 7. Packaging defects in the reorganized set
- `ship_upgrade_window` / `ship_loadout_window` / `inventory_window` are rotated by one: each holds
  the next one's art. Only the `Premium_` copies are named correctly.
- `Premium_` and plain files are byte-identical (SHA-256) for Main_Menu, Pause_Menu, Objectives and
  Mission_Complete, so those categories offer no actual alternate.
- Both `Mission_Complete` files show the amber NEW ITEM DISCOVERED popup, not a mission-complete
  card. The green card is instead bleeding into the edge of the Inventory crops.
- `HUD/Crosshairs` mixes in non-crosshairs: distance readouts with baked values (`100 m`, `2.8 km`),
  text-only labels, and three demo strips (`COLOR VARIANTS`, `THICKNESS VARIANTS`, `SIZE VARIANTS`).

### 8. Typos baked into pixels
`ANMOR BREAK` (armor), `IMMMEDIATE ACTION REQUIRED` (three Ms), `DAMGE` (damage), and an Objectives
tab reading `HIAN` instead of MAIN.

## Not gaps — deliberately unused

The kit carries oxygen, fuel, radiation, heat, ammo, reload, inventory grid, mission and extraction
concepts the game does not have. The owner has kept them for possible later use. They are not
missing art and need no action.
