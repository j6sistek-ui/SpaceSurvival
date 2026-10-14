"""Remove Joy's original waistcoat from the project (owner 2026-10-14: "delete the original shirt. no need"): the material
instance and its two textures in JoyBartender, once nothing references them. SK_Joy dropped the waistcoat slot when the
fitted jacket replaced it (reimport_joy_soft_tissue.py). Each .uasset is copied to SS_WAISTCOAT_BACKUP first.

  set SS_WAISTCOAT_BACKUP=<folder>
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/remove_joy_waistcoat.py"
"""
import json
import os
import shutil

import unreal as u

B = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
ASSETS = [B + "/Materials/MI_Joy_FS_waistcoat", B + "/Textures/T_Joy_FS_waistcoat_Diffuse", B + "/Textures/T_Joy_FS_waistcoat_Normal"]
BACKUP = os.environ["SS_WAISTCOAT_BACKUP"]
L = u.EditorAssetLibrary


def log(s):
    u.log_warning("WAISTCOAT| " + str(s))


mesh = u.load_asset(B + "/Mesh/SK_Joy")
assert not any(str(s.material_slot_name) == "FS_waistcoat" for s in mesh.materials), "SK_Joy still has the waistcoat slot"
os.makedirs(BACKUP, exist_ok=True)
report = {"deleted": [], "kept": []}
# the material instance first, so the textures lose their last referencer
for path in ASSETS:
    if not L.does_asset_exist(path):
        report["kept"].append([path, "absent"])
        continue
    refs = [str(r) for r in L.find_package_referencers_for_asset(path, False) if not str(r).startswith(tuple(ASSETS))]
    if refs:
        report["kept"].append([path, refs])
        continue
    asset = u.load_asset(path)
    shutil.copy2(u.SystemLibrary.get_system_path(asset), BACKUP)
    assert L.delete_asset(path), path
    report["deleted"].append(path)
log("DONE " + json.dumps(report))
