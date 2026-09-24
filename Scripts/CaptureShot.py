"""Turn an nwiro captureviewport result into a viewable PNG.

`ue_editorapptoolset_captureviewport` returns the image as inline base64. That payload is ~1-2 MB
and blows the tool-result token limit every single time, so the harness spills it to a file under
.claude/.../tool-results/ instead. This reads the newest such spill, decodes it, lifts the exposure
and writes a PNG you can actually look at.

    python Scripts/CaptureShot.py out.png [gamma]

gamma defaults to 0.45. Lower = brighter. The station is graded dark on purpose
(DIM_INTENSITY = 0.34 in MakeStationRecipe.py), so raw frames come back at mean luminance ~0.03 and
look like a black rectangle. Lifting here is far cheaper than re-lighting the level and re-shooting.

Prints the RAW frame statistics before lifting - read those, not the lifted image, when deciding
whether something is genuinely unlit. `pct_black` counts pixels below 2% luminance.

Also deletes older spills, because a run of captures at ~2 MB each has filled this disk before.
"""
import sys
import os
import glob
import base64
import re

import numpy as np
from PIL import Image

TOOL_RESULTS = os.path.join(
    os.path.expanduser("~"), ".claude", "projects", "C--Users-j6sis-SpaceSurvival",
)


def newest_spill():
    hits = []
    for session in glob.glob(os.path.join(TOOL_RESULTS, "*", "tool-results")):
        hits += glob.glob(os.path.join(session, "*captureviewport*.txt"))
    if not hits:
        raise SystemExit("no captureviewport spill found - run the capture first")
    return sorted(hits, key=os.path.getmtime), sorted(hits, key=os.path.getmtime)[-1]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "shot.png"
    gamma = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
    every, src = newest_spill()

    blob = open(src, encoding="utf-8", errors="replace").read()
    match = re.search(r"([A-Za-z0-9+/]{5000,}={0,2})", blob)
    if not match:
        raise SystemExit("spill contained no base64 image: " + src)
    raw = base64.b64decode(match.group(1))

    tmp = out + ".raw.png"
    open(tmp, "wb").write(raw)
    img = Image.open(tmp).convert("RGB")
    arr = np.asarray(img).astype(np.float32) / 255.0
    print("RAW  mean %.4f  max %.4f  pct_black %.1f%%  size %dx%d"
          % (arr.mean(), arr.max(), 100 * (arr.max(axis=2) < 0.02).mean(), img.width, img.height))

    arr = np.power(arr, gamma)
    arr = np.clip(arr / max(arr.max(), 1e-6), 0.0, 1.0)
    Image.fromarray((arr * 255).astype("uint8")).save(out)
    os.remove(tmp)
    print("wrote", out, "at gamma", gamma)

    for stale in every[:-1]:
        try:
            os.remove(stale)
        except OSError:
            pass


if __name__ == "__main__":
    main()
