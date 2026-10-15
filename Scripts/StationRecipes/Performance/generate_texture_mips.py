"""Give textures that were imported with "No Mipmaps" a mip chain, so the texture streamer can drop their detail at a
distance instead of holding every one at full size.

Measured 2026-10-15 on the station map: 412 P1toP5_Bundle textures (almost all 4096 x 4096) were imported with Mip Gen
Settings = NoMipmaps. A one-mip texture cannot stream, so all of them sat in video memory at full size: 3.67 GB of the
8.1 GB the station holds. Owner: "mipmaps". Close up they look the same; at a distance they lose their shimmer.

  In the open editor: Output Log > Python > py "<abs>/generate_texture_mips.py"   (the station's list beside it)
  set SS_MIPS_LIST=<json list of {"object": "/Game/.../T.T", ...}>   (another list; nothing else is touched)
  set SS_MIPS_DRY_RUN=1          report only
  set SS_MIPS_REPORT=<file.json> before/after per texture (the "before" makes the change reversible)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/generate_texture_mips.py"

Skipped: textures whose sides are not powers of two (no mip chain without resizing), UI textures, and anything not set
to NoMipmaps. Run it either inside the one open editor, or headless with no editor open (it saves the packages).
"""
import json
import os
import time

import unreal as u

L = u.EditorAssetLibrary
DRY = os.environ.get("SS_MIPS_DRY_RUN") == "1"
HERE = os.path.dirname(os.path.abspath(__file__))
# Without settings (run from the editor's Output Log: py "<this file>") it does the station's list beside this file.
ITEMS = json.load(open(os.environ.get("SS_MIPS_LIST") or os.path.join(HERE, "station_bundle_nomips.json")))
REPORT = os.environ.get("SS_MIPS_REPORT") or os.path.join(
    os.path.abspath(u.Paths.project_saved_dir()), "Logs", "generate_texture_mips_%s.json" % ("dry" if DRY else "applied"))


def log(s):
    u.log_warning("MIPS| " + str(s))


def pow2(n):
    return n > 0 and (n & (n - 1)) == 0


assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(), "stop Play first"
rows, changed, skipped, failed = [], 0, 0, 0
t0 = time.time()
for i, item in enumerate(ITEMS):
    path = item["object"].split(".")[0]
    row = {"object": item["object"]}
    try:
        tex = u.load_asset(path)
        if not isinstance(tex, u.Texture2D):
            row["skip"] = "not a Texture2D"
            skipped += 1
            rows.append(row)
            continue
        w, h = tex.blueprint_get_size_x(), tex.blueprint_get_size_y()
        before = {"mip_gen_settings": str(tex.get_editor_property("mip_gen_settings")),
                  "lod_group": str(tex.get_editor_property("lod_group")),
                  "never_stream": bool(tex.get_editor_property("never_stream")), "size": [w, h]}
        row["before"] = before
        if tex.get_editor_property("mip_gen_settings") != u.TextureMipGenSettings.TMGS_NO_MIPMAPS:
            row["skip"] = "already has a mip setting"
        elif not (pow2(w) and pow2(h)):
            row["skip"] = "sides are not powers of two"
        elif tex.get_editor_property("lod_group") == u.TextureGroup.TEXTUREGROUP_UI:
            row["skip"] = "UI texture"
        if "skip" in row:
            skipped += 1
            rows.append(row)
            continue
        if not DRY:
            tex.set_editor_property("mip_gen_settings", u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
            if tex.get_editor_property("never_stream"):
                tex.set_editor_property("never_stream", False)
            assert L.save_loaded_asset(tex, False), path
            row["after"] = {"mip_gen_settings": str(tex.get_editor_property("mip_gen_settings")),
                            "never_stream": bool(tex.get_editor_property("never_stream"))}
        changed += 1
    except Exception as e:  # noqa: BLE001 - one bad asset must not stop the batch; it is reported
        row["error"] = str(e)
        failed += 1
    rows.append(row)
    if (i + 1) % 25 == 0:
        log("%d/%d done (%d changed, %d skipped, %d failed) %.0f s" % (i + 1, len(ITEMS), changed, skipped, failed,
                                                                     time.time() - t0))
if REPORT:
    json.dump({"dry_run": DRY, "changed": changed, "skipped": skipped, "failed": failed, "rows": rows},
              open(REPORT, "w"), indent=1)
log("DONE dry_run=%s changed=%d skipped=%d failed=%d in %.0f s" % (DRY, changed, skipped, failed, time.time() - t0))
