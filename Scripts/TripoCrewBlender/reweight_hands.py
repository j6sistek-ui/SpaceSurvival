"""Tighten a crew character's hand weights so each finger bends at its own joints and the palm is the hand's.

  blender -b <rig>.blend --python reweight_hands.py -- [--object Cyborg] [--save]

Why (Cyborg, 2026-10-12, owner: "the hand is also a bit compressed"): the bone-heat fit let the forearm twist bone
reach deep into the palm (43% at the wrist, 24% a fifth of the way to the knuckles) and smeared each finger's three
bones along the whole finger (a proximal index vertex: hand 14, index 7/11/2). Curling a finger then pulls its root
toward the palm while its tip bones drag its base: the finger shortens instead of bending.

What it keeps: WHICH finger (or the palm) a vertex belongs to, as bone heat decided it. The Cyborg's finger bones sit
1.8 cm apart inside fingers 2 cm thick, so no distance rule can tell the fingers apart - the first two versions tried,
and tore the fingers wherever the rule gave up (measured 2026-10-12: the worst edges joined a vertex the rule had
handed to the hand to a neighbour it had skipped). Bone heat diffused through the mesh and knows.

What it changes, per side, for every vertex carrying any of hand, lowerarm, lowerarm_twist or a finger bone:
  - along each finger the vertex's share of that finger is re-split by where it sits on the chain (the last bone runs
    on to the fingertip): each bone full in its middle, half-and-half over the last/first quarter at a joint, the
    root quarter blending into the hand;
  - a palm share that sits out on a finger (over the first 30% of its first bone) moves to that finger - not for the
    thumb, whose first bone lies inside the palm;
  - of the palm share, the forearm's part (lowerarm + twist, in their existing ratio) fades from half at the wrist
    to nothing a quarter of the way to the knuckles, never rising above what the vertex had; the hand holds the rest;
  - behind the wrist nothing changes (the arm pass owns the forearm); the change fades in over 1 cm either side.
Every rule is continuous in position and in the old weights, so no two neighbours ever jump apart. Per-vertex totals
of the groups involved are kept, so nothing else needs normalising. Prints the palm and finger profiles before and
after; the stretch gate (scratch stretch_check.py, 99th percentile and worst edge against a known-good clip) is the
proof, not the profile.
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


def chain_split(segs, p, side, f, hand_name):
    """How finger f's share at p splits along its chain; the last bone runs on past its tail to the fingertip."""
    best = None
    for i, (A, ax, L) in enumerate(segs, start=1):
        t = (p - A).dot(ax)
        tc = max(0.0, t) if i == len(segs) else max(0.0, min(L, t))
        dist = ((p - A) - ax * tc).length
        if best is None or dist < best[0]:
            best = (dist, i, tc / L)
    dist, i, u = best
    prev_share = 0.5 * smooth((0.25 - u) / 0.25)
    next_share = 0.5 * smooth((u - 0.75) / 0.25) if i < len(segs) else 0.0
    split = {"%s_%02d_%s" % (f, i, side): 1.0 - prev_share - next_share}
    split[hand_name if i == 1 else "%s_%02d_%s" % (f, i - 1, side)] = prev_share
    if next_share > 0:
        split["%s_%02d_%s" % (f, i + 1, side)] = next_share
    return split


for side in ("r", "l"):
    profile(side, "before")

for side in ("r", "l"):
    hand_name = "hand_" + side
    fore_names = ("lowerarm_" + side, "lowerarm_twist_01_" + side)
    chains = {}
    for f in FINGERS:
        segs = []
        for i in (1, 2, 3):
            name = "%s_%02d_%s" % (f, i, side)
            if name not in arm.data.bones:
                break
            b0 = arm.data.bones[name]
            A = world(b0.head_local)
            d = world(b0.tail_local) - A
            segs.append((A, d.normalized(), d.length))
        if segs:
            chains[f] = segs
    groups_of = {f: ["%s_%02d_%s" % (f, i, side) for i in range(1, len(segs) + 1)] for f, segs in chains.items()}
    related = [hand_name, *fore_names] + [n for g in groups_of.values() for n in g]
    P0 = world(arm.data.bones[hand_name].head_local)
    pax = world(arm.data.bones["middle_01_" + side].head_local) - P0
    Lp = pax.length
    pax.normalize()
    done = 0
    for v in me.vertices:
        old = {n: weight(v, n) for n in related}
        total = sum(old.values())
        if total <= 1e-4:
            continue
        p = o.matrix_world @ v.co
        along = (p - P0).dot(pax)
        mask = smooth((along + 0.01) / 0.02)  # nothing behind the wrist, all of it 1 cm past it
        if mask <= 0.0:
            continue
        tt = along / Lp
        m = {f: sum(old[n] for n in groups_of[f]) / total for f in chains}
        palm_old = sum(old[n] for n in (hand_name, *fore_names))
        palm = palm_old / total
        splits = {f: chain_split(segs, p, side, f, hand_name) for f, segs in chains.items()}
        # a palm share out on a finger belongs to that finger (the thumb's first bone is inside the palm: left alone)
        fm = {f: m[f] for f in m if f != "thumb"}
        fsum = sum(fm.values())
        if palm > 0 and fsum > 1e-6:
            moved = 0.0
            for f, mf in fm.items():
                A, ax, L = chains[f][0]
                x = palm * (mf / fsum) * smooth(((p - A).dot(ax) / L) / 0.3) * smooth(fsum / 0.15)
                m[f] += x
                moved += x
            palm -= moved
        new = {}
        if palm > 0:
            wl, wt = old[fore_names[0]], old[fore_names[1]]
            have = (wl + wt) / palm_old if palm_old > 1e-9 else 0.0
            fore = min(0.5 * smooth((0.25 - tt) / 0.25), have)
            rl = wl / (wl + wt) if wl + wt > 1e-9 else 0.0
            new[fore_names[0]] = palm * fore * rl
            new[fore_names[1]] = palm * fore * (1 - rl)
            new[hand_name] = palm * (1 - fore)
        for f, mf in m.items():
            for n, s in splits[f].items():
                new[n] = new.get(n, 0.0) + mf * s
        for n in related:
            set_weight(v, n, (1 - mask) * old[n] + mask * total * new.get(n, 0.0))
        done += 1
    print("REWEIGHT| %s hand: %d vertices rebalanced" % (side, done), flush=True)

for side in ("r", "l"):
    profile(side, "after ")

if args.save:
    bpy.ops.wm.save_mainfile()
    print("REWEIGHT| saved " + bpy.data.filepath, flush=True)
