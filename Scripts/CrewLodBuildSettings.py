"""Show, and optionally change, a crew skeletal mesh's LOD 0 build settings.

  set SS_LOD_MESH=/Game/.../SK_Cyborg   [SS_LOD_SET=recompute_normals=0,recompute_tangents=1]
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/CrewLodBuildSettings.py"

Why: 2026-10-12 the 45k Cyborg came into the game as a patchwork of flat facets while her FBX carried clean
smooth normals. A reimport keeps the asset's existing LOD build settings, and "Recompute Normals" there is applied
to the render mesh AFTER its vertices are split at UV seams, so every one of Tripo's 13,909 texture islands gets
its own normals. This script reads those settings and, with SS_LOD_SET, changes them and rebuilds.
"""
import os

import unreal as u


def game_path(p):
    return p[p.index("/Game/"):] if p and "/Game/" in p else p


MESH = game_path(os.environ["SS_LOD_MESH"])
mesh = u.load_asset(MESH)
assert isinstance(mesh, u.SkeletalMesh), "not a skeletal mesh: " + MESH
sub = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
settings = sub.get_lod_build_settings(mesh, 0)
NAMES = ("recompute_normals", "recompute_tangents", "use_mikk_t_space", "compute_weighted_normals", "remove_degenerates",
         "use_high_precision_tangent_basis", "use_full_precision_u_vs", "use_backwards_compatible_f16_trunc_u_vs")
before = {}
for n in NAMES:
    try:
        before[n] = settings.get_editor_property(n)
    except Exception:
        pass
u.log_warning("LODBUILD| %s LOD0 before: %s" % (mesh.get_name(), before))
wanted = os.environ.get("SS_LOD_SET", "")
if wanted:
    for item in wanted.split(","):
        k, v = item.split("=")
        settings.set_editor_property(k.strip(), v.strip() in ("1", "true", "True"))
    sub.set_lod_build_settings(mesh, 0, settings)
    sub.regenerate_lod(mesh, 0, False, True) if hasattr(sub, "regenerate_lod") else None
    u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    after = {n: sub.get_lod_build_settings(mesh, 0).get_editor_property(n) for n in before}
    u.log_warning("LODBUILD| %s LOD0 after: %s" % (mesh.get_name(), after))
