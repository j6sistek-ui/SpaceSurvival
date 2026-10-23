# Bar seating and photo-mode follow-up — October 16, 2026

Linked work: RPT-20261015-01/02 and RPT-20261016-02. Owner feedback remains pending in KNOWN_ISSUES; these checks did not pause lead work.

## One saved cushion repair

`Seat/Refine/Social/Conversation 1/Sofa south/2` was available after moving its former occupant to the resting corner, but all three authored exits overlapped the existing low coffee table. The actual sit request correctly rejected them. A first shorter 65 cm trial collided with the sofa and was rejected too.

Only this seat's local `StandOffsets` changed: `(95,0,0), (95,-60,0), (95,60,0)` became `(80,0,0), (85,-105,0), (85,105,0)` cm. The table and sofa retain their positions and collision. Save/reload preserves all 9,480 actor transforms and 132 guarded non-map files, including three owner saves. Current map SHA-256: `fbb69f362ed086b16b1f0e79da6cb4010e0024d3efad363f7bf8b29e48905402`; combined module remains `a841a562`. The original map is backed up locally.

Ordinary Play from the saved scene passes sit/stand on both tested south-sofa cushions and both authored ArcadeWaitingBench seats. The latter bench is elsewhere in the station, not beside the drunk arcade patron. Each repaired exit also passes independently with the other two temporarily excluded; restored authored offsets remain unchanged on disk. The existing Squirrel body is only the test subject, not a changed hero or rig. Physical controls and all other seats are not claimed tested.

The resting patron retains its prior disabled collision and no route/action/chatter; the arcade patron retains its normal capsule. These observations do not establish full contact comfort or sleeping-conversation behavior. Those lead checks remain open.

## Native photo checks

From the current pad spawn `(-1550,0,90.15)`, the bar actor is 70.448 m away. A large camera request toward it stops on scene geometry at 10.477 m from the anchor. A large upward request reaches exactly the 40 m tether; left/down requests stop earlier on geometry. Reset returns exactly to the entry camera. A second camera move reaches a concourse viewpoint 29.045 m from the anchor.

Both actual photo captures write PNGs inside the isolated test profile. Exit restores the player view and unpauses; the player's transform is unchanged. These images used the small offscreen viewport after its bounded resize expired: they prove screenshot creation and bounds, not final image quality or market composition. D-pad input, natural camera feel, all walls, and packaged behavior remain unverified. No new photo-mode source change was needed.

## Preservation and evidence

The final check verifies the intended map plus all 132 other protected files, clean map/content packages and a clean owned-editor exit. Initial probe property errors, the original rejected seat, the rejected 65 cm trial and small-viewport captures are retained. Existing vendor BP_Blinds errors remain outside this change.

Private evidence is under `.agent/local/Diagnostics_20261016`: `SeatExitAdopted.json`, `SavedSeatChecks.json`, `SavedSeatAlternatives.json`, `SavedSeatLayout.png`, `PhotoRangeChecks.json`, `PhotoMarket.json` and `PostSeatPhotoPreservation.json`. Raw captures/logs and licensed map assets remain local. No merge, package or acceptance is implied.
