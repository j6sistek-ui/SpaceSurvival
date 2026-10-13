"""Tighten a crew character's hand weights so the palm is the hand's and each finger is its own.

  blender -b <rig>.blend --python reweight_hands.py -- [--object Cyborg] [--save]

Why (Cyborg, 2026-10-12, owner: "the hand is also a bit compressed"): the bone-heat fit let the forearm twist bone
reach deep into the palm (43% at the wrist, 24% a fifth of the way to the knuckles, 8% half way) and smeared the
finger bones across neighbouring fingers (an index vertex: hand 14, index 7/11/2, the rest in other fingers). Rolling
the wrist or curling the fingers then squeezes the whole hand.

What it does, per side:
  - palm vertices (within 5 cm of the wrist->middle-knuckle line, from the wrist to a little past the knuckles, not
    on a finger): the forearm's share (lowerarm + lowerarm_twist, in their existing ratio) falls to nothing over the
    first 15% of the palm; over the last 20% the nearest finger's first bone rises to half; the hand holds the rest;
    every other finger group is cleared;
  - finger vertices (within 1.3 cm of a phalanx, 1.6 cm for the thumb; the nearest phalanx wins): weights only on
    that finger's three bones and the hand, each phalanx full in its middle, blending to the next over the last
    quarter and to the previous (or the hand, at the knuckle) over the first quarter; every other group is cleared.
The per-vertex total of hand, forearm, twist and all finger groups is kept, so nothing else needs normalising.
Prints the palm and finger profiles before and after.
"""
import argparse
import sys

import bpy
import numpy as np
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("--object", default="Cyborg")
ap.add_argument("--save", action="store_true")
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

o = bpy.data.objects[args.object]
arm = [a for a in bpy.data.objects if a.type == "ARMATURE"][0]
me = o.data
FINGERS = ("thumb", "index", "middle", "ring", "pinky")


def gi(name):
    g = o.vertex_groups.get(name)
    return g.index if g else None


def weight(v, name):
    i = gi(name)
    return next((g.weight for g in v.groups if g.group == i), 0.0) if i is not None else 0.0


def set_weight(v, name, value):
    g = o.vertex_groups.get(name)
    if g is None:
        if value <= 1e-4:
            return
        g = o.vertex_groups.new(name=name)
    if value <= 1e-4:
        try:
            g.remove([v.index])
        except RuntimeError:
            pass
    else:
        g.add([v.index], value, "REPLACE")


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def world(p):
    return arm.matrix_world @ p


def profile(side, label):
    hand = arm.data.bones["hand_" + side]
    A = world(hand.head_local)
    B = world(arm.data.bones["middle_01_" + side].head_local)
    ax = B - A
    L = ax.length
    ax.normalize()
    line = []
    for b in range(0, 10):
        sel = []
        for v in me.vertices:
            p = o.matrix_world @ v.co
            t = (p - A).dot(ax)
            if ((p - A) - ax * t).length < 0.05 and b / 10 <= t / L < (b + 1) / 10:
                sel.append(v)
        if not sel:
            line.append("  -  ")
            continue
        line.append("%2.0f/%2.0f/%2.0f" % tuple(100 * np.mean([weight(v, n + "_" + side) for v in sel]) for n in ("lowerarm", "lowerarm_twist_01", "hand")))
    print("REWEIGHT| %s %s palm lowerarm/twist/hand %% per tenth: %s" % (label, side, "  ".join(line)), flush=True)
    for finger in ("index", "middle"):
        chain = ["%s_%02d_%s" % (finger, i, side) for i in (1, 2, 3)]
        for name in chain:
            b0 = arm.data.bones[name]
            A = world(b0.head_local)
            ax = world(b0.tail_local) - A
            L = ax.length
            ax.normalize()
            sel = []
            for v in me.vertices:
                p = o.matrix_world @ v.co
                t = (p - A).dot(ax)
                if 0 <= t < L and ((p - A) - ax * t).length < 0.012:
                    sel.append(v)
            if not sel:
                continue
            others = sum(np.mean([weight(v, "%s_%02d_%s" % (f, i, side)) for v in sel]) for f in FINGERS if f != finger for i in (1, 2, 3))
            print("REWEIGHT| %s %s %s: hand/01/02/03 = %s, other fingers %2.0f" % (label, side, name,
                  "/".join("%2.0f" % (100 * np.mean([weight(v, g) for v in sel])) for g in ["hand_" + side] + chain), 100 * others), flush=True)


for side in ("r", "l"):
    profile(side, "before")

for side in ("r", "l"):
    hand_name = "hand_" + side
    finger_groups = ["%s_%02d_%s" % (f, i, side) for f in FINGERS for i in (1, 2, 3)]
    related = [hand_name, "lowerarm_" + side, "lowerarm_twist_01_" + side] + finger_groups
    # phalanx segments
    segs = []
    for f in FINGERS:
        for i in (1, 2, 3):
            name = "%s_%02d_%s" % (f, i, side)
            if name not in arm.data.bones:
                continue
            b0 = arm.data.bones[name]
            A = world(b0.head_local)
            d = world(b0.tail_local) - A
            segs.append((f, i, A, d.normalized(), d.length, 0.016 if f == "thumb" else 0.013))
    hand = arm.data.bones[hand_name]
    P0 = world(hand.head_local)
    knuckles = [world(arm.data.bones["%s_01_%s" % (f, side)].head_local) for f in ("index", "middle", "ring", "pinky") if "%s_01_%s" % (f, side) in arm.data.bones]
    pax = world(arm.data.bones["middle_01_" + side].head_local) - P0
    Lp = pax.length
    pax.normalize()
    done_f = done_p = 0
    for v in me.vertices:
        p = o.matrix_world @ v.co
        # nearest phalanx
        best = None
        for f, i, A, ax, L, r in segs:
            t = (p - A).dot(ax)
            dist = ((p - A) - ax * max(0.0, min(L, t))).length
            if dist < r and -0.2 * L <= t <= 1.15 * L and (best is None or dist < best[0]):
                best = (dist, f, i, max(0.0, min(1.0, t / L)))
        total = sum(weight(v, n) for n in related)
        if total <= 1e-4:
            continue
        new = {}
        if best is not None:
            _, f, i, t = best
            prev_share = 0.5 * smooth((0.25 - t) / 0.25)
            next_share = 0.5 * smooth((t - 0.75) / 0.25) if i < 3 else 0.0
            own = 1.0 - prev_share - next_share
            new["%s_%02d_%s" % (f, i, side)] = total * own
            if i == 1:
                new[hand_name] = total * prev_share
            else:
                new["%s_%02d_%s" % (f, i - 1, side)] = total * prev_share
            if next_share > 0:
                new["%s_%02d_%s" % (f, i + 1, side)] = total * next_share
            done_f += 1
        else:
            t = (p - P0).dot(pax)
            if not (-0.005 <= t <= 1.1 * Lp and ((p - P0) - pax * t).length < 0.05):
                continue
            tt = t / Lp
            fore = 0.5 * smooth((0.15 - tt) / 0.15)
            wl, wt = weight(v, "lowerarm_" + side), weight(v, "lowerarm_twist_01_" + side)
            rl = wl / (wl + wt) if wl + wt > 1e-6 else 0.0
            new["lowerarm_" + side] = total * fore * rl
            new["lowerarm_twist_01_" + side] = total * fore * (1 - rl)
            fshare = 0.5 * smooth((tt - 0.8) / 0.2)
            if fshare > 0 and knuckles:
                # the nearest finger root
                near = min(("index", "middle", "ring", "pinky"), key=lambda f: (p - world(arm.data.bones["%s_01_%s" % (f, side)].head_local)).length)
                new["%s_01_%s" % (near, side)] = total * fshare
            new[hand_name] = total * (1 - fore - fshare)
            done_p += 1
        for n in related:
            set_weight(v, n, new.get(n, 0.0))
    print("REWEIGHT| %s hand: %d palm vertices, %d finger vertices rebalanced" % (side, done_p, done_f), flush=True)

for side in ("r", "l"):
    profile(side, "after ")

if args.save:
    bpy.ops.wm.save_mainfile()
    print("REWEIGHT| saved " + bpy.data.filepath, flush=True)
