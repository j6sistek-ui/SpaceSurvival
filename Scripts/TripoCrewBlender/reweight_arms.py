"""Tighten a crew character's arm weights so the elbow and wrist bend where the joints are.

  blender -b <rig>.blend --python reweight_arms.py -- [--object Cyborg] [--save] [--elbow 0.15] [--wrist 0.15]

Why (Cyborg, 2026-10-12, owner: "noodle compressed arm that looks squished, and has for a while"): the bone-heat fit
spread the forearm's weight half-way up the upper arm (13% at the middle of the upper arm, 40% at 70%, 72% at 80%)
and the hand's up the forearm, so bending the elbow to 80 deg folded the whole upper arm like a tube. The skeleton
was clean (no scale or translation keys); the skin was the fault.

What it does, for each arm, on vertices within 8 cm of the shoulder-elbow or elbow-wrist line:
  - upper arm (t = 0 at the shoulder .. 1 at the elbow): the lowerarm's share rises only over the last --elbow of the
    length, to half at the elbow; the rest stays split between upperarm and upperarm_twist in the ratio they had;
    lowerarm_twist and hand get nothing here;
  - forearm (t = 0 at the elbow .. 1 at the wrist): the upperarm's share mirrors that over the first --elbow, the
    hand's rises over the last --wrist to half at the wrist; the rest stays split between lowerarm and lowerarm_twist
    in the ratio they had.
Only the five arm groups are rebalanced and their total per vertex is kept, so clavicle, spine and finger weights
are untouched and nothing needs normalising. The shoulder itself (first 15% of the upper arm) and the hand are left
alone. Prints the handover profile before and after, like the measurement that found the fault.
"""
import argparse
import sys

import bpy
import numpy as np
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--object", default="Cyborg")
ap.add_argument("--save", action="store_true")
ap.add_argument("--elbow", type=float, default=0.15, help="fraction of each bone over which the elbow blends")
ap.add_argument("--wrist", type=float, default=0.15)
ap.add_argument("--radius", type=float, default=0.08)
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

o = bpy.data.objects[args.object]
arm = [a for a in bpy.data.objects if a.type == "ARMATURE"][0]
me = o.data
gi = {g.name: g.index for g in o.vertex_groups}


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def weight(v, name):
    i = gi.get(name)
    return next((g.weight for g in v.groups if g.group == i), 0.0) if i is not None else 0.0


def set_weight(v, name, value):
    g = o.vertex_groups[name]
    if value <= 1e-4:
        try:
            g.remove([v.index])
        except RuntimeError:
            pass
    else:
        g.add([v.index], value, "REPLACE")


def profile(side, rows_fn, label):
    ua, la, hd = (arm.data.bones[n + "_" + side] for n in ("upperarm", "lowerarm", "hand"))
    A, B, C = (arm.matrix_world @ ua.head_local), (arm.matrix_world @ la.head_local), (arm.matrix_world @ hd.head_local)
    a1 = B - A
    L1 = a1.length
    a1.normalize()
    a2 = C - B
    L2 = a2.length
    a2.normalize()
    for seg, name in (("upper", "shoulder->elbow"), ("lower", "elbow->wrist")):
        line = []
        for b in range(10):
            sel = []
            for v in me.vertices:
                p = o.matrix_world @ v.co
                t1 = (p - A).dot(a1)
                d1 = ((p - A) - a1 * t1).length
                t2 = (p - B).dot(a2)
                d2 = ((p - B) - a2 * t2).length
                if seg == "upper" and 0 <= t1 < L1 and d1 < args.radius and b / 10 <= t1 / L1 < (b + 1) / 10:
                    sel.append(v)
                elif seg == "lower" and 0 <= t2 < L2 and d2 < args.radius - 0.01 and b / 10 <= t2 / L2 < (b + 1) / 10:
                    sel.append(v)
            if not sel:
                line.append("   -    ")
                continue
            tw = "upperarm_twist_01_" if seg == "upper" else "lowerarm_twist_01_"
            line.append("%2.0f/%2.0f/%2.0f/%2.0f" % (100 * np.mean([weight(v, "upperarm_" + side) for v in sel]),
                                                 100 * np.mean([weight(v, "lowerarm_" + side) for v in sel]),
                                                 100 * np.mean([weight(v, tw + side) for v in sel]),
                                                 100 * np.mean([weight(v, "hand_" + side) for v in sel])))
        print("REWEIGHT| %s %s %s upper/lower/twist/hand %% per tenth: %s" % (label, side, name, "  ".join(line)), flush=True)


for side in ("r", "l"):
    profile(side, None, "before")

for side in ("r", "l"):
    names = {k: k + "_" + side for k in ("upperarm", "lowerarm", "hand")}
    names["ut"] = "upperarm_twist_01_" + side
    names["lt"] = "lowerarm_twist_01_" + side
    for n in names.values():
        if n not in gi:
            o.vertex_groups.new(name=n)
            gi[n] = o.vertex_groups[n].index
    ua, la, hd = (arm.data.bones[names[k]] for k in ("upperarm", "lowerarm", "hand"))
    A, B, C = (arm.matrix_world @ ua.head_local), (arm.matrix_world @ la.head_local), (arm.matrix_world @ hd.head_local)
    a1 = B - A
    L1 = a1.length
    a1.normalize()
    a2 = C - B
    L2 = a2.length
    a2.normalize()
    changed = 0
    for v in me.vertices:
        p = o.matrix_world @ v.co
        t1 = (p - A).dot(a1)
        d1 = ((p - A) - a1 * t1).length
        t2 = (p - B).dot(a2)
        d2 = ((p - B) - a2 * t2).length
        in_upper = 0.15 * L1 <= t1 <= L1 and d1 < args.radius
        in_lower = 0 <= t2 <= L2 and d2 < args.radius - 0.01
        if not (in_upper or in_lower):
            continue
        if in_upper and in_lower:
            in_upper = abs(t1 / L1 - 0.5) < abs(t2 / L2 - 0.5)  # the nearer segment's middle wins
            in_lower = not in_upper
        w = {k: weight(v, n) for k, n in names.items()}
        total = sum(w.values())
        if total <= 1e-4:
            continue
        if in_upper:
            t = t1 / L1
            low = 0.5 * smooth((t - (1 - args.elbow)) / args.elbow)
            keep = w["upperarm"] + w["ut"]
            ru = w["upperarm"] / keep if keep > 1e-6 else 1.0
            new = {"lowerarm": total * low, "upperarm": total * (1 - low) * ru, "ut": total * (1 - low) * (1 - ru), "lt": 0.0, "hand": 0.0}
        else:
            t = t2 / L2
            up = 0.5 * smooth((args.elbow - t) / args.elbow)
            hand = 0.5 * smooth((t - (1 - args.wrist)) / args.wrist)
            keep = w["lowerarm"] + w["lt"]
            rl = w["lowerarm"] / keep if keep > 1e-6 else 1.0
            rest = total * (1 - up - hand)
            new = {"upperarm": total * up, "ut": 0.0, "lowerarm": rest * rl, "lt": rest * (1 - rl), "hand": total * hand}
        for k, val in new.items():
            set_weight(v, names[k], val)
        changed += 1
    print("REWEIGHT| %s arm: %d vertices rebalanced" % (side, changed), flush=True)

for side in ("r", "l"):
    profile(side, None, "after ")

if args.save:
    bpy.ops.wm.save_mainfile()
    print("REWEIGHT| saved " + bpy.data.filepath, flush=True)
