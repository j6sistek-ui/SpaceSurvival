"""Where the gripping hand really is relative to the pole axis (x = y = 0), per frame of a pole clip."""
import math
import os
import sys

import bpy
from mathutils import Vector

POLE = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "pole_dance.py")
CLIP = sys.argv[sys.argv.index("--") + 1]
src = open(POLE, encoding="utf-8").read()
sys.argv = [sys.argv[0], "--", os.path.join(os.environ.get("TEMP", "."), "grip_measure"), "Cyborg", CLIP]
g = {"__name__": "pole_dance", "__file__": POLE}
exec(compile(src[:src.index("action = author(CLIP)")], POLE, "exec"), g)
g["author"](CLIP)
PB, sc, arm = g["PB"], g["sc"], g["arm"]
mw = arm.matrix_world
fingers = [b.name for b in PB if b.name.endswith("_r") and any(k in b.name for k in ("index", "middle", "ring", "pinky"))]
print("GRIP| finger bones:", fingers[:6], "...", len(fingers))


def radial(p):
    return math.hypot(p.x, p.y)


n = sc.frame_end
for side in ("l", "r"):
    fingers = [b.name for b in PB if b.name.endswith("_" + side) and any(k in b.name for k in ("index", "middle", "ring", "pinky")) and b.name.split("_")[1] in ("03", "3")]
    worst_palm, worst_tip, on = 0.0, 0.0, 0
    for f in range(1, n + 1, 3):
        sc.frame_set(f)
        hand = PB["hand_" + side]
        palm = mw @ (hand.head + hand.vector.normalized() * g["PALM_L"])
        if radial(palm) > 0.20:
            continue                                   # this hand is not on the pole in this frame
        on += 1
        worst_palm = max(worst_palm, radial(palm) - 0.047)          # 0.047 = palm bone line with the skin on the pole
        tips = [radial(mw @ PB[b].tail) for b in fingers]
        worst_tip = max(worst_tip, max(tips) - 0.06)                 # a wrapped fingertip stays within ~6 cm of the axis
    verdict = "OFF POLE" if on and (worst_palm > 0.015 or worst_tip > 0.03) else ("ok" if on else "free hand")
    print("GRIP| %-9s %s: on the pole in %d sampled frames, palm up to %+.3f m off, fingertip up to %+.3f m out -> %s"
          % (CLIP, side, on, worst_palm, worst_tip, verdict))
