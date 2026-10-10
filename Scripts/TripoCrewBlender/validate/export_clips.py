"""Export crew clips from Unreal as FBX (clip + its preview mesh) for the Blender check renders.

  set SS_AF_OUT=<folder>
  set SS_AF_WHO=Elf,Cyborg            every A_* clip of these characters (base + Role), or
  set SS_AF_PATHS=/Game/...,/Game/... exact clip paths
  optional SS_AF_FILTER=Dance          only clips whose name contains this
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/export_clips.py"

-RenderOffscreen, not -NullRHI: skeletal FBX export crashes without a renderer. Renders come from what Unreal
actually holds (its skin, its bind pose), which is the point - the Elf's thigh fault only showed up this way.
"""
import os

import unreal as u

CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
LIB = u.EditorAssetLibrary
out = os.environ["SS_AF_OUT"]
os.makedirs(out, exist_ok=True)
paths = [p for p in os.environ.get("SS_AF_PATHS", "").split(",") if p]
for who in [w for w in os.environ.get("SS_AF_WHO", "").split(",") if w]:
    for folder in ("%s/%s" % (CREW, who), "%s/%s/Role" % (CREW, who)):
        paths += [p.split(".")[0] for p in LIB.list_assets(folder, recursive=False, include_folder=False)
                  if p.rsplit("/", 1)[1].startswith("A_")]
flt = os.environ.get("SS_AF_FILTER")
ok = tried = 0
for path in paths:
    if "/Game/" in path and not path.startswith("/Game/"):
        path = path[path.index("/Game/"):]          # Git Bash rewrites /Game/... into a Windows path
    name = path.rsplit("/", 1)[1]
    if flt and flt not in name:
        continue
    tried += 1
    task = u.AssetExportTask()
    task.object = LIB.load_asset(path); task.filename = os.path.join(out, name + ".fbx")
    task.automated = True; task.prompt = False; task.replace_identical = True
    opt = u.FbxExportOption()
    for prop, value in (("export_preview_mesh", True), ("export_morph_targets", False), ("level_of_detail", False), ("collision", False)):
        opt.set_editor_property(prop, value)
    task.options = opt
    ok += bool(u.Exporter.run_asset_export_task(task))
u.log_warning("EXPORTCLIPS| %d of %d exported to %s" % (ok, tried, out))
