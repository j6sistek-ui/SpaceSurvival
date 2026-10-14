"""Measure tail surface envelopes; -ApplyTailFloor writes only the existing Squirrel tuning row.

Run in an owned offscreen editor after the native build. The default is a read-only
dry run. The apply invocation requires an unchanged successful dry-run receipt and
backs up the complete tuning package before saving. No mesh, clip or map is saved.
"""
import hashlib
import json
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / ".agent/local/SurvivalQuality/TailFloor"
OUT.mkdir(parents=True, exist_ok=True)
MESH = "/Game/SpaceSurvival/Licensed/HeroReplacement/Final/SK_SquirrelHeroReplacement"
DATA = "/Game/SpaceSurvival/Data/DA_Phase1"
DATA_FILE = ROOT / "Content/SpaceSurvival/Data/DA_Phase1.uasset"
MESH_FILE = ROOT / "Content/SpaceSurvival/Licensed/HeroReplacement/Final/SK_SquirrelHeroReplacement.uasset"
APPLY = "-ApplyTailFloor" in u.SystemLibrary.get_command_line().split()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(), "Stop Play before authoring"
mesh = u.load_asset(MESH)
data = u.load_asset(DATA)
assert mesh and data, "The actual private replacement and current tuning are required"
before = {"mesh_sha256": sha(MESH_FILE), "tuning_sha256": sha(DATA_FILE)}
receipt = json.loads(u.SSCharacterAuthoringLibrary.measure_replacement_tail_envelopes(mesh))
assert receipt.get("success"), receipt
assert len(receipt["envelopes"]) == 7, receipt
receipt.update(before)
rows = data.get_editor_property("heroes")
index = next(i for i, row in enumerate(rows) if str(row.id) == "Squirrel")
hero = rows[index]
assert hero.mesh_path == mesh.get_path_name() and str(hero.tail_root_bone) == "tail_01", hero.export_text()
dry_file = OUT / "dry-run.json"
if APPLY:
    dry = json.loads(dry_file.read_text(encoding="utf-8"))
    assert all(dry.get(key) == value for key, value in receipt.items()), "Inputs changed after dry run"
    backup = OUT / ("DA_Phase1.before-tail-floor-" + before["tuning_sha256"][:16] + ".uasset")
    if not backup.exists():
        backup.write_bytes(DATA_FILE.read_bytes())
    (OUT / "squirrel-before.txt").write_text(hero.export_text(), encoding="utf-8")
    envelopes = {}
    for entry in receipt["envelopes"]:
        box = u.Box()
        box.set_editor_property("min", u.Vector(*entry["min"]))
        box.set_editor_property("max", u.Vector(*entry["max"]))
        box.set_editor_property("is_valid", True)
        envelopes[u.Name(entry["bone"])] = box
    hero.set_editor_property("tail_floor_envelopes", envelopes)
    rows[index] = hero
    data.set_editor_property("heroes", rows)
    assert u.EditorAssetLibrary.save_loaded_asset(data, False), "Tuning save failed"
    assert sha(MESH_FILE) == before["mesh_sha256"], "Measurement must preserve the private mesh"
    receipt.update(applied=True, backup=str(backup), tuning_after_sha256=sha(DATA_FILE))
    (OUT / "applied.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    (OUT / "squirrel-after.txt").write_text(rows[index].export_text(), encoding="utf-8")
else:
    assert sha(DATA_FILE) == before["tuning_sha256"] and sha(MESH_FILE) == before["mesh_sha256"]
    dry_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
u.log("TAIL_FLOOR_" + ("APPLIED" if APPLY else "DRY_RUN") + " " + json.dumps(receipt))
