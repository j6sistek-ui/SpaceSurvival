# Combat presentation

The current source replaces the large emissive rings around enemy ships with small muzzle lights and screen-space identity cues. The Wave 10 preview showed the rings dominating nearby hazards; the change makes room for the actual ship and environment silhouettes. It does not alter enemy behavior, collision, accuracy, weapon timing or roster.

Pursuers use one forward chevron. Flankers use split wings, so identity does not rely on red versus amber. A bright underline and an exclamation mark accompany an on-screen committed shot; off-screen charging enemies retain directional glyphs. The same existing charge clock drives the compact muzzle light. The current soft target receives four corner marks and its existing world-body label. Labels use measured font width and move left when the right edge lacks room.

The contextual radar retains the existing more-than-three-active-threats trigger. It shows enemy positions in ship-local forward/lateral space, with a circular 100 m range and radial clamping outside that range. The outer edge indicates bearing for more distant contacts, not their exact distance. Archetype shapes and charge underlines match the world cues. The announcement strip and radar heading occupy separate vertical areas.

The helper methods live in `SSHUD`; `SSWorldBody::UpdateVisual` owns only the compact auxiliary muzzle geometry. Imported material slots remain intact. The existing `ThreatIndicator` component stays available for presentation and has no collision or shadow casting.

The final source compiled in 6.43 seconds. Before two narrow layout repairs, all 21 existing Unreal tests passed, and a normal-frame editor-game fixture completed Wave 9, breathing, the full Wave 10 climax and approach. The lead observed the updated enemy cues and found the announcement/header overlap, subsequently fixed. The final label/radar placement still needs rendered verification; physical threat recognition, busy-scene readability and owner art acceptance remain open. Package 10 predates these changes. See the [exact preview record](validation/2026-09-13-combat-cue-preview.json).
