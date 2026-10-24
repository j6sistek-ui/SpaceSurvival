# Native cryo interaction

`ASSCryoChamber` owns a four-second cosmetic cycle. It has no Python, ShipCore,
save-game or networking dependency. Bind each required frost pane actor through
`FrostSurfaces`, assign `JetSystem`, and place `LeftNozzle`/`RightNozzle` at the
two upper outlets. The final authored system emits downward along local -Z with
an inward local -Y component to clear the curved glass. Set `UsePoint` at the
accessible front console in chamber-local coordinates.

`BodyCollision` supplies a simple walking boundary for imported bodies that have
no collision: a capsule with radius 80 cm, half-height 160 cm and center Z160.
It blocks only Pawn queries, ignores visibility, generates no overlap events and
does not affect navigation or simulate physics. Fit this component if the chamber
dimensions change; the source body mesh remains untouched.

Each pane must expose a scalar `FreezeAmount` (0 normal, 1 fully frozen). At
BeginPlay the actor creates private dynamic material instances; an incomplete
binding fails closed. A valid use rechecks distance/line of sight, activates both
nozzles, keeps the window clear for 0.65 seconds, raises frost through 1.25
seconds, holds until 3.4 seconds, then clears it by four seconds. Repeated use
during a cycle cannot extend it. The world timer
ends emission immediately and restores each material's original scalar value.
EndPlay clears the timer and restores original material assignments. Idle actors
do not tick. No source material asset is edited at runtime.

Production integration uses the existing `ASSOutpostTerminal` controls and HUD:
set `Action=CryoChill` and `PresentationTarget` to the chamber. Its normal range
and sight checks run before the chamber's own checks; other station services are
unchanged. The chamber's `UsePoint` and terminal access point should coincide.

The asset-only review map uses `ASSCryoPreviewGameMode`, a small walking pawn,
controller and Canvas HUD in this same plugin. WASD/left stick walks,
mouse/right stick looks, and E/controller X calls the same chamber action.
It is a separate review mode and does not replace the production walker.

Native build and actual rendered interaction validation are required after any
code, pane or jet change. A compile, an active-system flag or a Python-driven
material change cannot establish the saved walk-up interaction.
