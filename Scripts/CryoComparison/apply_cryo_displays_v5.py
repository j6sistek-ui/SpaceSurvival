"""New-only v5 font-mesh screens and physical glass, restricted to CryoStage.

Default is a filesystem-only dry run. Root owns engine launches. Execute
runpy.run_path(...)["main"](True) inside the isolated editor to apply.
Existing asset packages, including freeze/FX/sequence/body, are never saved.
Only newly imported mesh/material packages and the owned map may change.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
STAGE = WORK / "CryoStage"
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
MANIFEST = OUT / "assembly_displays_v5.json"
PREVIOUS = OUT / "assembly_fit_v4_4.json"
API = runpy.run_path(str(WORK / "author_cryo_unreal.py"))
FIT = runpy.run_path(str(WORK / "upgrade_cryo_fit_unreal.py"))
require, digest, hashes = FIT["require"], FIT["digest"], FIT["package_hashes"]
ROLE_NAMES = {
    "glass": "M_Glass_V5", "console_glass": "M_DisplayLens_V5",
    "display_glass": "M_DisplayLens_V5", "holo_panel": "M_HoloPanel_V5",
    "holo": "M_VectorReadout_V5", "status": "M_VectorReadout_V5",
    "console": "M_VectorReadout_V5", "console_backing": "M_DisplayBacking_V5",
    "console_frame": "M_DisplayFrame_V5",
}
ROLE_PATHS = {role: BASE + "/Materials/DisplayV5/" + name for role, name in ROLE_NAMES.items()}
MAP_RELATIVE = "Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap"


class V5Author(API["Author"]):
    def new_asset(self, name, folder, cls, factory, role, model_id="Shared"):
        if cls == self.u.Material:
            folder = BASE + "/Materials/DisplayV5"
        return super().new_asset(name, folder, cls, factory, role, model_id)


def package_path(asset):
    require(asset.startswith(BASE + "/"), "Asset outside owned namespace")
    return "Content\\" + asset[len("/Game/"):].replace("/", "\\") + ".uasset"


def obj_surface_signature(path):
    """Compare serialized positions, topology and UVs while excluding normals."""
    vertices, uv, faces, normals = [], [], [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            vertices.append(tuple(float(v) for v in fields[1:]))
        elif fields[0] == "vt":
            uv.append(tuple(float(v) for v in fields[1:]))
        elif fields[0] == "vn":
            normals.append(tuple(float(v) for v in fields[1:]))
        elif fields[0] == "f":
            faces.append(tuple(tuple(int(v) for v in corner.split("/")[:2]) for corner in fields[1:]))
    require(vertices and uv and faces and normals, "Incomplete glass OBJ geometry")
    surface = hashlib.sha256(json.dumps([vertices, uv, faces], separators=(",", ":")).encode()).hexdigest()
    normal_hash = hashlib.sha256(json.dumps(normals, separators=(",", ":")).encode()).hexdigest()
    return {"surface_sha256": surface, "normal_sha256": normal_hash,
            "vertices": len(vertices), "uvs": len(uv), "faces": len(faces), "normals": len(normals)}


def prepare(manifest_path):
    path = Path(manifest_path).resolve()
    require(path == MANIFEST.resolve() and path.is_file(), "Expected final v5 manifest on D")
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8-sig"))
    require([m["id"] for m in manifest["models"]] == list("ABCD"), "Expected ordered four candidates")
    require(manifest["shared"] == previous["shared"], "Shared generated inputs changed")
    require(manifest["source_manifest_sha256"] == digest(PREVIOUS), "Previous manifest chain differs")
    sources = {str(path): {"sha256": digest(path)}, str(PREVIOUS): {"sha256": digest(PREVIOUS)}}
    changes, bindings, changed_names = [], [], []
    for model, old in zip(manifest["models"], previous["models"]):
        for field in ("source", "textures", "height_cm"):
            require(model[field] == old[field], "Original body metadata changed: " + field)
        require(digest(model["source"]) == old["source_sha256"], "Original download changed")
        old_rows = {row["name"]: row for row in old["components"]}
        current = {row["name"]: row for row in model["components"]}
        require(len(current) == len(model["components"]) == 21, "Expected 21 unique components")
        require(set(current) == set(old_rows) | {"Holo_Panel", "Status_Glass"}, "Unexpected component additions")
        names = set()
        for row in model["components"]:
            file = Path(row["file"]).resolve()
            require(file.is_relative_to(WORK.parent) and file.is_file() and file.suffix.lower() == ".obj",
                    "Only explicit D-drive OBJ sources supported")
            sha = digest(file)
            sources[str(file)] = {"sha256": sha}
            old_row = old_rows.get(row["name"])
            old_sha = digest(old_row["file"]) if old_row else None
            if old_row:
                require(row["role"] == old_row["role"], "Existing role changed")
                sources[str(Path(old_row["file"]).resolve())] = {"sha256": old_sha}
            actor = model["id"] + "_" + row["name"]
            if sha != old_sha:
                require(row["role"] in ROLE_PATHS,
                        "Protected enclosure/body/frost geometry changed: " + actor)
                normal_audit = None
                if row["role"] == "glass":
                    require(old_row is not None, "Existing glass required")
                    old_surface, new_surface = obj_surface_signature(old_row["file"]), obj_surface_signature(file)
                    require(old_surface["surface_sha256"] == new_surface["surface_sha256"],
                            "Glass change exceeds shading normals: " + actor)
                    normal_audit = {"before": old_surface, "after": new_surface,
                                    "positions_topology_uvs_identical": True}
                names.add(row["name"])
                changes.append({"model_id": model["id"], "name": row["name"], "role": row["role"],
                                "file": str(file), "source_sha256": sha, "previous_source_sha256": old_sha,
                                "actor": actor, "new_actor": old_row is None,
                                "asset": BASE + "/Meshes/DisplayV5/" + model["id"] + "/SM_" + actor + "_DisplaysV5"})
                if normal_audit:
                    changes[-1]["normals_only_audit"] = normal_audit
            if row["role"] in ROLE_PATHS:
                bindings.append({"actor": actor, "role": row["role"], "material": ROLE_PATHS[row["role"]]})
        changed_names.append(names)
        for source in [model["source"], *model["textures"].values()]:
            sources[source] = {"sha256": digest(source)}
    require(all(names == changed_names[0] for names in changed_names), "Unequal treatment across candidates")
    for source in manifest["shared"].values():
        sources[source] = {"sha256": digest(source)}
    return manifest, sources, digest(path), changes, bindings


def materials(u, author, report):
    """Mesh silhouette supplies the type edge; no bitmap glyph alpha or dither."""
    made = {}

    def lit_glass(name, lens=False):
        mat = author.material(name, translucent=True, two_sided=True)
        mat.set_editor_property("translucency_lighting_mode", u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        mat.set_editor_property("screen_space_reflections", True)
        mat.set_editor_property("refraction_method", u.RefractionMode.RM_NONE)
        mat.set_editor_property("disable_depth_test", False)
        uv = author.node(mat, "MaterialExpressionTextureCoordinate", coordinate_index=0)
        # Smooth broad condensation, deliberately free of binary/dither/random alpha.
        haze = author.custom(mat, "return 0.5+0.24*sin(UV.x*29.0+sin(UV.y*13.0))*sin(UV.y*37.0)+0.14*sin(UV.x*11.0-UV.y*19.0);", {"UV": uv})
        fresnel = author.node(mat, "MaterialExpressionFresnel", exponent=4.0, base_reflect_fraction=0.0)
        opacity = author.custom(mat,
            "return 0.045+F*0.30+Haze*0.008;" if lens else "return 0.075+F*0.34+Haze*0.020;",
            {"F": fresnel, "Haze": haze})
        rough = author.custom(mat, "return 0.065+Haze*0.030;" if lens else "return 0.105+Haze*0.065;", {"Haze": haze})
        author.prop(author.color(mat, (.075, .16, .20) if lens else (.11, .21, .255)), "MP_BASE_COLOR")
        author.prop(opacity, "MP_OPACITY")
        author.prop(rough, "MP_ROUGHNESS")
        author.prop(author.scalar(mat, .5), "MP_SPECULAR")
        author.prop(author.scalar(mat, 0), "MP_METALLIC")
        author.compile(mat)
        made[name] = mat
        return mat

    lit_glass("M_Glass_V5")
    lit_glass("M_DisplayLens_V5", True)
    panel = author.material("M_HoloPanel_V5", translucent=True, unlit=True, two_sided=True)
    panel.set_editor_property("disable_depth_test", False)
    uv = author.node(panel, "MaterialExpressionTextureCoordinate", coordinate_index=0)
    edge = author.custom(panel, "float2 q=abs(UV-0.5)-float2(0.465,0.445); float d=length(max(q,0.0))+min(max(q.x,q.y),0.0)-0.03; return (1.0-smoothstep(-0.006,0.004,d))*0.10;", {"UV": uv})
    author.prop(author.color(panel, (.016, .080, .11)), "MP_EMISSIVE_COLOR")
    author.prop(edge, "MP_OPACITY")
    author.compile(panel)
    made["M_HoloPanel_V5"] = panel

    glyph = author.material("M_VectorReadout_V5", unlit=True, two_sided=True)
    glyph.set_editor_property("has_pixel_animation", True)
    uv = author.node(glyph, "MaterialExpressionTextureCoordinate", coordinate_index=0)
    clock = author.node(glyph, "MaterialExpressionTime")
    sweep = author.custom(glyph,
        "float s=frac(Clock/6.5); float d=abs(UV.y-s); float band=exp(-d*d*720.0); return 0.88+0.04*sin(Clock*1.04719755)+0.30*band;",
        {"UV": uv, "Clock": clock})
    author.prop(author.multiply(glyph, author.color(glyph, (.23, .85, 1.10)), sweep), "MP_EMISSIVE_COLOR")
    author.compile(glyph)
    made["M_VectorReadout_V5"] = glyph

    backing = author.material("M_DisplayBacking_V5", two_sided=True)
    author.prop(author.color(backing, (.003, .008, .012)), "MP_BASE_COLOR")
    author.prop(author.scalar(backing, .22), "MP_METALLIC")
    author.prop(author.scalar(backing, .32), "MP_ROUGHNESS")
    author.compile(backing)
    made["M_DisplayBacking_V5"] = backing
    frame = author.material("M_DisplayFrame_V5", two_sided=True)
    author.prop(author.color(frame, (.012, .04, .055)), "MP_BASE_COLOR")
    author.prop(author.scalar(frame, .65), "MP_METALLIC")
    author.prop(author.scalar(frame, .26), "MP_ROUGHNESS")
    author.prop(author.color(frame, (.006, .045, .065)), "MP_EMISSIVE_COLOR")
    author.compile(frame)
    made["M_DisplayFrame_V5"] = frame

    report["native_material_sidedness"] = []
    for name, mat in made.items():
        row = {"asset": mat.get_path_name(), "roles": sorted(role for role, value in ROLE_NAMES.items() if value == name),
               "two_sided": bool(mat.get_editor_property("two_sided")),
               "blend_mode": str(mat.get_editor_property("blend_mode")),
               "shading_model": str(mat.get_editor_property("shading_model")),
               "uses_bitmap_text": False, "uses_dither": False}
        if name in ("M_Glass_V5", "M_DisplayLens_V5"):
            row.update(lighting_mode=str(mat.get_editor_property("translucency_lighting_mode")),
                       screen_space_reflections=bool(mat.get_editor_property("screen_space_reflections")),
                       depth_test_enabled=not bool(mat.get_editor_property("disable_depth_test")),
                       refraction_method=str(mat.get_editor_property("refraction_method")))
        report["native_material_sidedness"].append(row)
    return {role: made[name] for role, name in ROLE_NAMES.items()}


def main(apply=False, manifest_path=None):
    report = {"status": "FAILED", "apply": apply, "utc": datetime.now(timezone.utc).isoformat(),
              "manifest": str(manifest_path or MANIFEST), "materials": [], "meshes": [], "actors": [],
              "cameras": [], "textures": [], "errors": [], "role_materials": ROLE_PATHS,
              "limits": ["New glass uses more expensive per-pixel translucent lighting; no performance measurement claimed.",
                         "Specular/readout quality requires native A trial and final all-four views.",
                         "Native M_FrostFreeze, Niagara, four-second timing, light sequence and original body packages stay byte-identical."]}
    receipt_path = WORK / ("CryoDisplayV5Apply.json" if apply else "CryoDisplayV5Plan.json")
    u, allowed = None, False
    try:
        manifest, sources, manifest_hash, changes, bindings = prepare(manifest_path or MANIFEST)
        report.update(manifest_sha256=manifest_hash, changes=changes, role_bindings=bindings, protected_source_files=sources)
        before = hashes()
        baseline = json.loads((WORK / "CryoRearConsoleApply.json").read_text(encoding="utf-8"))
        require(baseline["status"] == "REAR_CONSOLE_SAVED_PENDING_VISUAL_REVIEW" and before == baseline["native_after_hashes"],
                "Stage native content changed since final v4_4 receipt")
        expected_added = sorted([package_path(row["asset"]) for row in changes] + [package_path(path) for path in sorted(set(ROLE_PATHS.values()))])
        require(not set(expected_added) & set(before), "New v5 package already exists")
        report.update(native_before_hashes=before, planned_new_packages=expected_added)
        if not apply:
            report["status"] = "DRY_RUN_READY"
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), "Only isolated CryoStage is allowed")
        require(not u.EditorLevelLibrary.get_pie_worlds(False), "Refusing active PIE")
        allowed = True
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, "Map load failed")
        subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
        actors = {actor.get_actor_label(): actor for actor in subsystem.get_all_level_actors()}
        before_states = {name: FIT["actor_state"](u, actor) for name, actor in actors.items()}
        for model in manifest["models"]:
            body = actors[model["id"] + "_Body"].get_component_by_class(u.StaticMeshComponent).get_editor_property("static_mesh")
            source = next(row["file"] for row in model["components"] if row["role"] == "body")
            require(u.EditorAssetLibrary.get_metadata_tag(body, "CryoSourceSHA256") == digest(source), "Original body provenance differs")
        for row in changes:
            require(not u.EditorAssetLibrary.does_asset_exist(row["asset"]), "New mesh exists")
            require((row["actor"] not in actors) == row["new_actor"], "Unexpected actor existence")
        for row in bindings:
            if row["actor"] in actors:
                comp = actors[row["actor"]].get_component_by_class(u.StaticMeshComponent)
                require(comp and comp.get_num_materials() == 1, "Expected single-slot mesh actor")
        backup = WORK / ("pre_display_v5_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup.mkdir(exist_ok=False)
        shutil.copy2(STAGE / MAP_RELATIVE, backup / "L_CryoComparison.umap")
        require(digest(backup / "L_CryoComparison.umap") == before[MAP_RELATIVE], "Map backup differs")
        report["map_recovery"] = str(backup / "L_CryoComparison.umap")
        author = V5Author(u, manifest, manifest_hash, report)
        mats = materials(u, author, report)
        created = list(author.created)
        for row in changes:
            mesh = FIT["import_mesh"](u, row, mats[row["role"]], manifest_hash)
            u.EditorAssetLibrary.set_metadata_tag(mesh, "CryoAuthoringVersion", "CryoVectorDisplaysV5")
            created.append(mesh)
            if row["new_actor"]:
                x = API["X_OFFSETS"][list("ABCD").index(row["model_id"])]
                actor = author.actor(u.StaticMeshActor, row["actor"], (x, 0, 0), folder="CryoComparison/" + row["model_id"])
                actors[row["actor"]] = actor
                comp = actor.get_component_by_class(u.StaticMeshComponent)
                comp.set_collision_profile_name("NoCollision")
                comp.set_cast_shadow(False)
            else:
                comp = actors[row["actor"]].get_component_by_class(u.StaticMeshComponent)
                row["previous_mesh"] = comp.get_editor_property("static_mesh").get_path_name()
            comp.set_static_mesh(mesh)
        for row in bindings:
            comp = actors[row["actor"]].get_component_by_class(u.StaticMeshComponent)
            row["previous_material"] = comp.get_material(0).get_path_name() if comp.get_material(0) else None
            comp.set_material(0, mats[row["role"]])
            # Actual distance sorts glass behind/over readouts. Do not force HUD over full frost.
            comp.set_editor_property("translucency_sort_priority", 0)
            row["readback_material"] = comp.get_material(0).get_path_name()
            row["readback_sort_priority"] = int(comp.get_editor_property("translucency_sort_priority"))
            require(row["readback_material"].split(".")[0] == row["material"], "Role material readback differs")
        after_states = {actor.get_actor_label(): FIT["actor_state"](u, actor) for actor in subsystem.get_all_level_actors()}
        change_map = {row["actor"]: row for row in changes}
        bind_map = {row["actor"]: row for row in bindings}
        for name, old in before_states.items():
            expected = json.loads(json.dumps(old))
            if name in change_map:
                asset = change_map[name]["asset"]
                expected["mesh"] = asset + "." + asset.rsplit("/", 1)[-1]
            if name in bind_map:
                expected["materials"] = [bind_map[name]["readback_material"]]
                expected["translucency_sort_priority"] = 0
            require(after_states[name] == expected, "Unexpected actor/effect change: " + name)
        require(set(after_states) - set(before_states) == {row["actor"] for row in changes if row["new_actor"]}, "Unexpected new actors")
        for path, info in sources.items():
            require(digest(path) == info["sha256"], "Input changed during authoring: " + path)
        for asset in created:
            require(u.EditorAssetLibrary.save_loaded_asset(asset, False), "New asset save failed")
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Comparison map save failed")
        after = hashes()
        changed_existing = sorted(path for path in before if before[path] != after.get(path))
        added = sorted(set(after) - set(before))
        require(changed_existing == [MAP_RELATIVE], "An existing package beyond the map changed")
        require(added == expected_added, "New package set differs from plan")
        report.update(status="DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW", native_after_hashes=after,
                      changed_existing_packages=changed_existing, added_packages=added,
                      unchanged_original_bodies=True, unchanged_freeze_niagara_sequence_packages=True,
                      unchanged_non_display_actors=True, saved_assets=[asset.get_path_name() for asset in created],
                      changed_component_counts=dict(Counter(row["model_id"] for row in changes)))
        return report
    except Exception:
        report["status"] = "FAILED"
        report["errors"].append(traceback.format_exc())
        if u:
            u.log_error(report["errors"][-1])
        return report
    finally:
        receipt_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("CRYO_DISPLAY_V5_RESULT " + json.dumps({"status": report["status"], "receipt": str(receipt_path)}), flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main(False)
