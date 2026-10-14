"""Prepare fixed scalp and moving tail groups from the private owned groom.

Inputs are JSON from SSGroomAuthoring.ReadSilverStrands and the existing Silver
head vertex export. This writes a new description, never edits a vendor asset.
Run with the existing Python environment containing numpy; see the dated receipt.
"""

import argparse
import json
from pathlib import Path

import numpy as np


def prepare(source, head_points):
    rows = []
    for curve in source["curves"]:
        points = np.asarray(curve["points"], float)
        if len(points) < 2:
            continue
        parts = [(0, points)]
        if points[-1, 2] < 157 and points[-1, 1] < -9:
            crossing = np.flatnonzero(points[:, 1] < -9.5)
            if len(crossing):
                i = int(crossing[0])
                if i > 0:
                    t = (-9.5 - points[i - 1, 1]) / (points[i, 1] - points[i - 1, 1])
                    tie = points[i - 1] + t * (points[i] - points[i - 1])
                    parts = [(0, np.vstack([points[:i], tie])), (1, np.vstack([tie, points[i:]]))]
                else:
                    parts = [(1, points)]
        for group, part in parts:
            if len(part) < 2 or np.linalg.norm(np.diff(part, axis=0), axis=1).sum() < .02:
                continue
            fitted = part * [1.18, 1.10, 1] + [0, -4, 3]
            rows.append({"points": fitted.round(6).tolist(), "guide": int(bool(curve["guide"])),
                         "uv": curve["uv"], "group": group})
    # Derive independent guide sets: a tail guide must never influence the crown.
    for group in [0, 1]:
        for curve in [c for c in rows if c["group"] == group and not c["guide"]][::10]:
            rows.append(dict(curve, guide=1))

    head = np.asarray(head_points, float)
    head = head[(abs(head[:, 0]) > 5) & (head[:, 1] > .8) &
                (head[:, 2] > 162) & (head[:, 2] < 174)].copy()
    if len(head) < 12:
        raise ValueError("Head export does not cover the measured temple surface")
    head[:, 0] = abs(head[:, 0])
    rng = np.random.default_rng(74)
    patches = []
    for _ in range(550):
        t = np.linspace(0, 1, 28)
        width = rng.uniform(-.8, .8)
        top = rng.uniform(170.2, 171.8)
        bottom = rng.uniform(163.5, 164.6)
        y = 2.55 + width * (1 - .5 * t) - .95 * t + .16 * np.sin(t * np.pi)
        z = top + (bottom - top) * t
        x = []
        for yy, zz in zip(y, z):
            distances = (head[:, 1] - yy) ** 2 + (head[:, 2] - zz) ** 2
            ids = np.argsort(distances)[:12]
            weights = 1 / (distances[ids] + .03)
            x.append(np.sum(head[ids, 0] * weights) / weights.sum())
        x = np.convolve(np.pad(x, 2, mode="edge"), np.ones(5) / 5, mode="valid")
        x += .04 + rng.uniform(0, .025)
        for sign in [-1, 1]:
            patches.append({"group": 0, "guide": 0, "uv": [.5, .5],
                            "points": np.column_stack([sign * x, y, z]).round(6).tolist()})
    rows += patches
    rows += [dict(c, guide=1) for c in patches[::10]]
    return {"curves": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strands", type=Path, required=True)
    parser.add_argument("--head-points", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(json.loads(args.strands.read_text()), json.loads(args.head_points.read_text()))
    # Exclusive creation prevents accidentally replacing the reviewed description.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, separators=(",", ":"))
    print([[sum(c["group"] == g and c["guide"] == v for c in result["curves"])
            for v in [0, 1]] for g in [0, 1]])


if __name__ == "__main__":
    main()
