"""Read-only native VFX probe, executed by the lead in disposable CryoStage.

No maps/assets are created, modified, saved, or simulated. A transient unregistered
NiagaraComponent reads typed user defaults. JSON is the only persistent output.
Importing this module outside Unreal safely exposes the exact preliminary copy list.
"""
from pathlib import Path
import json
import os
import traceback


WORK = Path(__file__).resolve().parent
SOURCE_CONTENT = Path("C:/Users/j6sis/SpaceSurvival/Content")
SMOKE_PLUME_FILES = [
    "NiagaraExamples/FX_Smoke/NS_Smoke_Plume.uasset",
    "NiagaraExamples/FX_Smoke/Emitters/NE_Smoke.uasset",
    "NiagaraExamples/EffectTypes/NET_Environment_Looping.uasset",
    "NiagaraExamples/NPC_NiagaraExamples.uasset",
    "NiagaraExamples/MPC_NiagaraExamples.uasset",
    "NiagaraExamples/Materials/MI_SmokePuffLight_8x8.uasset",
    "NiagaraExamples/Materials/MasterMaterials/M_SmokeAndFire_Sprites.uasset",
    "NiagaraExamples/Materials/MaterialFunctions/MF_ExposureCompensation.uasset",
    "NiagaraExamples/Materials/MaterialFunctions/MF_FastSphereNormal.uasset",
    "NiagaraExamples/Textures/Sprites/T_SmokePuffLight_EOO_Loop.uasset",
    "NiagaraExamples/Textures/Sprites/T_SmokePuffLight_Normals_Loop.uasset",
    "NiagaraExamples/Textures/Utils/CutoutMask_8x8.uasset",
    "NiagaraExamples/Textures/Utils/BaseEOO.uasset",
    "NiagaraExamples/Textures/Utils/BaseNormal.uasset",
    "NiagaraExamples/Textures/ColorCurves/Atlas_FXColorCurves.uasset",
    "NiagaraExamples/Textures/ColorCurves/EmissiveColorCurve.uasset",
]
STEAM_FILES = [
    "NERVES/FX/NS_Steam_Blue.uasset",
    "NERVES/MAT/INST/MI_Steam_Blue.uasset",
    "NERVES/MAT/INST/MI_Steam_Yellow.uasset",
    "NERVES/MAT/M_Steam.uasset",
    "NERVES/TXT/TX_Steam_SubUv.uasset",
]
SYSTEMS = ["/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume", "/Game/NERVES/FX/NS_Steam_Blue"]


def serial(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    if hasattr(value, "get_path_name"):
        return value.get_path_name()
    if hasattr(value, "to_tuple"):
        return serial(list(value.to_tuple()))
    if all(hasattr(value, k) for k in ("r", "g", "b", "a")):
        return [value.r, value.g, value.b, value.a]
    if hasattr(value, "export_text"):
        return value.export_text()
    return str(value)


def property_value(obj, name):
    try:
        return serial(obj.get_editor_property(name))
    except Exception as error:
        return {"unavailable": str(error)}


def main(output=None):
    import unreal as u
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    if project != (WORK / "CryoStage").resolve():
        raise RuntimeError("Read-only probe is restricted to disposable CryoStage")
    result = {"engine": u.SystemLibrary.get_engine_version(), "project": str(project),
              "scope": "READ_ONLY_NATIVE_VFX_PROBE_NO_SIMULATION", "systems": [], "errors": []}
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    options = u.AssetRegistryDependencyOptions()
    options.set_editor_property("include_hard_package_references", True)
    options.set_editor_property("include_soft_package_references", True)
    for path in SYSTEMS:
        row = {"path": path}
        result["systems"].append(row)
        if not u.EditorAssetLibrary.does_asset_exist(path):
            row["status"] = "NOT_COPIED_TO_STAGE"
            continue
        try:
            system = u.load_asset(path)
            if not isinstance(system, u.NiagaraSystem):
                raise RuntimeError("Loaded asset is not UNiagaraSystem")
            row["class"] = system.get_class().get_name()
            row["settings"] = {key: property_value(system, key) for key in (
                "fixed_bounds", "warmup_time", "warmup_tick_count", "warmup_tick_delta", "effect_type")}
            # An unregistered component has no scene/world and is never activated.
            component = u.NiagaraComponent()
            component.set_auto_activate(False)
            component.set_asset(system)
            row["user_parameters"] = []
            for info in u.NiagaraFunctionLibrary.get_all_user_parameters(system):
                name = str(info.get_editor_property("parameter_name"))
                kind = str(info.get_editor_property("type_name"))
                size = int(info.get_editor_property("parameter_size_bytes"))
                param = {"name": name, "type": kind, "size_bytes": size}
                try:
                    if "bool" in kind.lower():
                        value = component.get_variable_bool(name)
                    elif size == 4 and "float" in kind.lower():
                        value = component.get_variable_float(name)
                    elif size == 4 and "int" in kind.lower():
                        value = component.get_variable_int(name)
                    elif size == 16 and "color" in kind.lower():
                        value = component.get_variable_color(name)
                    elif size == 8:
                        value = component.get_variable_vec2(name)
                    elif size == 12:
                        value = component.get_variable_vec3(name)
                    else:
                        value = "TYPE_REQUIRES_EXPLICIT_REVIEW"
                    param["default_and_validity"] = serial(value)
                except Exception as error:
                    param["default_read_error"] = str(error)
                row["user_parameters"].append(param)
            emitters = list(u.NiagaraFunctionLibrary.get_all_emitters(system))
            row["emitter_count"] = len(emitters)
            row["emitters"] = [{key: property_value(info, key) for key in (
                "emitter_name", "is_enabled", "is_lightweight", "used_renderer_materials", "used_renderer_meshes")}
                for info in emitters]
            # Native private reflection can be unavailable in some builds. This
            # is diagnostic only; a failed reflection read is retained honestly.
            try:
                details = []
                for handle in system.get_editor_property("emitter_handles"):
                    version = handle.get_editor_property("versioned_instance")
                    emitter = version.get_editor_property("emitter")
                    detail = {"handle": property_value(handle, "name"), "emitter": serial(emitter), "versions": []}
                    for data in emitter.get_editor_property("version_data"):
                        d = {key: property_value(data, key) for key in ("local_space", "sim_target", "fixed_bounds", "calculate_bounds_mode")}
                        try:
                            d["renderers"] = [{"class": r.get_class().get_name(), "path": r.get_path_name(),
                                               "material": property_value(r, "material"),
                                               "sub_image_size": property_value(r, "sub_image_size")}
                                              for r in data.get_editor_property("renderer_properties")]
                        except Exception as error:
                            d["renderer_reflection_error"] = str(error)
                        detail["versions"].append(d)
                    details.append(detail)
                row["emitter_details"] = details
            except Exception as error:
                row["private_reflection_error"] = str(error)
            pending = [path]
            visited = set()
            while pending:
                package = pending.pop()
                if package in visited:
                    continue
                visited.add(package)
                pending.extend(str(dep) for dep in registry.get_dependencies(package, options)
                               if str(dep).startswith("/Game/") and str(dep) not in visited)
            row["game_dependency_closure"] = sorted(visited)
            row["missing_game_packages"] = [p for p in sorted(visited) if not u.EditorAssetLibrary.does_asset_exist(p)]
            row["materials"] = []
            materials = {m.get_path_name(): m for info in emitters for m in info.get_editor_property("used_renderer_materials") if m}
            for material_path, material in materials.items():
                item = {"path": material_path, "class": material.get_class().get_name(), "parent": property_value(material, "parent")}
                item["scalar_parameters"] = {str(name): u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
                                             for name in u.MaterialEditingLibrary.get_scalar_parameter_names(material)} if isinstance(material, u.MaterialInstanceConstant) else {}
                item["vector_parameters"] = {str(name): serial(u.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, name))
                                             for name in u.MaterialEditingLibrary.get_vector_parameter_names(material)} if isinstance(material, u.MaterialInstanceConstant) else {}
                row["materials"].append(item)
            row["status"] = "LOADED_AND_READ_NO_SIMULATION"
        except Exception:
            row["status"] = "PROBE_ERROR"
            row["error"] = traceback.format_exc()
            result["errors"].append(path)
    destination = Path(output or os.environ.get("CRYO_NIAGARA_PROBE", WORK / "NiagaraProbe.json")).resolve()
    if not destination.is_relative_to(WORK.parent):
        raise RuntimeError("Probe output must stay within this task workspace")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("CRYO_NIAGARA_PROBE " + str(destination), flush=True)
    return result


if __name__ == "__main__":
    main()
