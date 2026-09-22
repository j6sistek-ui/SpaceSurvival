# Approved main-menu source

These exact PNGs come from the owner's locked **01 · MAIN MENU** in
[SpaceSurvival UI Kit](https://www.figma.com/design/6M3VvUB7jsPDd3E41YpKM0/SpaceSurvival-UI-Kit?node-id=142-1059).
`provenance.json` records each node, original byte hash, dimensions, transparency,
export method and rendered rectangle. Figma was read without modifying the design.

The 19 runtime assets preserve the background, both portraits, title, four normal
and four hover buttons, footer panel and six keyboard instruction labels. The
fully transparent outer panel and historical V1.02 caption are retained as source
evidence only. The runtime footer says `DEVELOPMENT REVIEW`; it does not advertise
an unwired release-log action. Continue remains visible but dimmed when no saved
run is available. Native actions determine availability.

Button/title/text exports were made at half of the authored 3840×2160 size for
1920×1080 use. Their glow padding is preserved, while hit rectangles use the
logical button bounds. The left portrait is a lossless crop at the exact authored
Figma image transform; its original source PNG and crop coordinates are retained.
The button shader is represented by the exact static export, not runtime shader
animation. Larger-display and final rendered acceptance remain separate checks.

Validate with `python Scripts/ImportFigmaMainMenu.py --validate-only`. The integration
lead runs `Scripts/ImportFigmaMainMenu.py` in the isolated offscreen editor first
as a dry-run and then with `-SSApplyFigmaMainMenu`. It creates only the named
`/Game/SpaceSurvival/UI/MainMenu` textures. Unknown or modified existing outputs
are rejected; a matching ownership receipt permits unchanged reuse. The script
does not fetch network assets or alter these sources. Local import receipts live
in `Artifacts/FigmaMainMenu/author.json` and `author-dry-run.json`.
