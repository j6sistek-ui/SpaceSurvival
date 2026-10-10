"""Inventory every animation pack on this machine: where it is, how many clips, which skeleton, installed or not.

  python Scripts/InventoryAnimationSources.py [extra_root ...] > Artifacts/AnimationSources.md

Plain Python, reads files only, never writes into a pack. Downloads land in several places on this machine
(two launcher vault folders on C:, M:/Downlloaded, Fab "add to project" copies, other projects), and the owner
moves packs between drives, so the roots are searched rather than remembered.

A .uasset counts as a clip when its header names both AnimSequence and SequenceLength and is not a montage or
blend space; names alone are no use because some packs name clips with random codes. (BoneCompressionSettings
alone misses UE4-era packs such as Mobility and MCO, which never serialise it.) Skeleton is guessed from bone
names in the first clip read: UE5 Manny (spine_05), UE4 mannequin (spine_03, no spine_04), Mixamo (mixamorig),
3ds Max Biped (Bip01). An FBX under an animation-looking path counts as a clip.
"""
import collections
import os
import re
import sys
import zipfile

ROOTS = [
    r"C:\Users\j6sis\SpaceSurvival\Content",
    r"C:\Users\j6sis\SpaceSurvival\User downloaded assets",
    r"C:\Users\j6sis\Downloads",
    r"C:\Users\j6sis\Documents\Unreal Projects",
    r"C:\Users\j6sis\OneDrive\Documents\Unreal Projects",
    r"M:\Downlloaded",
    r"M:\SpaceSurvival",
    r"M:\Extra Content",
] + sys.argv[1:]
PROJECT_CONTENT = r"C:\Users\j6sis\SpaceSurvival\Content"
SKIP = re.compile(r"(?i)[\\/](Saved|Intermediate|DerivedDataCache|\.git|\.claude|Binaries|Artifacts)[\\/]")
ANIMPATH = re.compile(r"(?i)anim|mocap|motion|emote|dance|/A_|\\A_|AS_")


def skeleton_of(blob):
    if b"mixamorig" in blob:
        return "Mixamo"
    if b"Bip01" in blob:
        return "3dsMax Biped"
    if b"spine_05" in blob:
        return "UE5 Manny"
    if b"spine_03" in blob and b"spine_04" not in blob:
        return "UE4 Mannequin"
    if b"spine_03" in blob:
        return "UE5 Manny"
    return "?"


def pack_of(path):
    p = path.replace("\\", "/")
    m = re.search(r"/FabLibrary/([^/]+)", p)
    if m:
        return "Fab:" + m.group(1)
    m = re.search(r"/([^/]+V\d+)/data/Content/([^/]+)", p)
    if m:
        return "Vault:" + m.group(2)
    m = re.search(r"/Content/([^/]+)", p)
    if m:
        return m.group(1)
    return p.rsplit("/", 2)[-2]


def scan():
    packs = collections.defaultdict(lambda: {"clips": 0, "fbx": 0, "skeleton": "?", "where": set(), "sample": []})
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, files in os.walk(root):
            if SKIP.search(dirpath + os.sep) or "worktrees" in dirpath:
                dirnames[:] = []
                continue
            for f in files:
                full = os.path.join(dirpath, f)
                low = f.lower()
                if low.endswith(".uasset"):
                    try:
                        with open(full, "rb") as h:
                            head = h.read(262144)
                    except OSError:
                        continue
                    if not (b"SequenceLength" in head and b"AnimSequence" in head) or                             b"AnimMontage" in head or b"BlendSpace" in head:
                        continue
                    pk = packs[pack_of(full)]
                    pk["clips"] += 1
                elif low.endswith(".fbx") and ANIMPATH.search(full):
                    pk = packs[pack_of(full)]
                    pk["fbx"] += 1
                    try:
                        with open(full, "rb") as h:
                            head = h.read(2_000_000)
                    except OSError:
                        head = b""
                elif low.endswith(".zip"):
                    try:
                        with zipfile.ZipFile(full) as z:
                            n = sum(1 for i in z.namelist() if i.lower().endswith(".fbx") and ANIMPATH.search(i))
                    except Exception:
                        continue
                    if n:
                        pk = packs["zip:" + f]
                        pk["fbx"] += n
                        pk["where"].add(root.split("\\")[0])
                    continue
                else:
                    continue
                pk["where"].add(full[:2])
                if pk["skeleton"] == "?" and head:
                    pk["skeleton"] = skeleton_of(head)
                if len(pk["sample"]) < 4:
                    pk["sample"].append(os.path.splitext(f)[0])
    return packs


def main():
    installed = set(os.listdir(PROJECT_CONTENT)) if os.path.isdir(PROJECT_CONTENT) else set()
    packs = scan()
    print("| Pack | Clips (.uasset) | Clips (.fbx) | Skeleton | Drive | In project | Sample |")
    print("|---|---|---|---|---|---|---|")
    for name, p in sorted(packs.items(), key=lambda kv: -(kv[1]["clips"] + kv[1]["fbx"])):
        if p["clips"] + p["fbx"] < 3:
            continue
        base = name.split(":", 1)[-1]
        inproj = "yes" if (base in installed and not name.startswith(("Fab:", "Vault:", "zip:"))) or base in installed else ""
        print("| %s | %d | %d | %s | %s | %s | %s |" % (name, p["clips"], p["fbx"], p["skeleton"],
              ",".join(sorted(p["where"])), inproj, ", ".join(p["sample"])))


main()
