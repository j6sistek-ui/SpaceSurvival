"""Every /Game/ path the source loads by string, against the cook directories that would ship it.

The cooker follows hard references. It cannot follow a string, so an asset named only in a string
literal ships only if some DirectoriesToAlwaysCook entry covers it. Nothing else in this repository
can see that: the automation suite runs against installed content on a developer machine, so it is
green whether or not a package would contain the same assets.

This is a report, not yet a gate. It is not wired into CheckProject.py because it currently finds
pre-existing gaps that are not this script's to decide - see the issue it was written for. Wire it in
once those are resolved, and it will fail on the next one instead of shipping it.

A file may mark a region NOTCOOKED-BEGIN / NOTCOOKED-END where the paths are candidates rather than
content - an audition table a console variable selects between, whose default lives under a cooked
root. The marker sits at the reference site so it is read by whoever is reading the paths.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cook_rules(text):
    """Read explicit directory rules and nonrecursive, exact primary-asset exclusions."""
    cooked = re.findall(r'^\+DirectoriesToAlwaysCook=\(Path="([^"]+)"\)', text, re.MULTILINE)
    never = re.findall(r'^\+DirectoriesToNeverCook=\(Path="([^"]+)"\)', text, re.MULTILINE)
    exact = set()
    for line in text.splitlines():
        if line.startswith("+PrimaryAssetTypesToScan=") and "CookRule=NeverCook" in line:
            if "bApplyRecursively=False" not in line or "Directories=()" not in line:
                raise ValueError("Coverage checker requires exact, nonrecursive primary-asset exclusions")
            assets = re.search(r'SpecificAssets=\((.*?)\),Rules=', line)
            if not assets:
                raise ValueError("NeverCook rule has no explicit SpecificAssets list")
            exact.update(path.split(".", 1)[0] for path in re.findall(r'"([^"]+)"', assets[1]))
    return cooked, never, exact


def is_covered(path, cooked, never, exact):
    package = path.split(".", 1)[0].casefold()

    def beneath(root):
        root = root.casefold().rstrip("/")
        return package == root or package.startswith(root + "/")

    return (package not in {p.casefold() for p in exact}
            and not any(beneath(root) for root in never)
            and any(beneath(root) for root in cooked))


def main():
    cooked, never, exact = cook_rules((ROOT / "Config/DefaultGame.ini").read_text(encoding="utf-8"))
    if not cooked:
        raise SystemExit("FAIL: Config/DefaultGame.ini declares no cook directories")
    referenced = {}
    for source in sorted((ROOT / "Source").rglob("*.cpp")) + sorted((ROOT / "Source").rglob("*.h")):
        exempt = False
        for line in source.read_text(encoding="utf-8").splitlines():
            if "NOTCOOKED-BEGIN" in line:
                exempt = True
            elif "NOTCOOKED-END" in line:
                exempt = False
            elif not exempt:
                for found in re.findall(r'"(/Game/[A-Za-z0-9_/.\-]+)"', line):
                    # A trailing slash is a matching prefix, not an asset being loaded.
                    if not found.endswith("/"):
                        referenced.setdefault(found, source.name)
    missing = {path: where for path, where in referenced.items()
               if not is_covered(path, cooked, never, exact)}
    print(f"{len(cooked)} cook roots; {len(never)} excluded directories; {len(exact)} excluded packages; "
          f"{len(referenced)} string-loaded paths; {len(missing)} not covered.")
    for path in sorted(missing):
        print(f"  NOT COOKED  {path}   ({missing[path]})")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
