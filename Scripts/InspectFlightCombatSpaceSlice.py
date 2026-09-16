"""Read-only owned-candidate audit for the flight/combat/space vertical slice.

Loads exact candidates and their native metadata without saving vendor content,
levels, Blueprints, materials, systems, maps, or project settings. The report is
an audition input; it is not rendered, performance, listening, or play acceptance.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Scripts"))

import InspectCombatVisualAssets
import InspectEnvironmentVFX

OUT = ROOT / "Artifacts/FlightCombatSpaceSlice"

ASTEROID_FIELDS = [
    "/Game/Asteroid_Library/Blueprints/BP_AsteroidField_Arch",
    "/Game/Asteroid_Library/Blueprints/BP_AsteroidField_Globular",
    "/Game/Asteroid_Library/Blueprints/BP_AsteroidField_Linear",
]
REGION_CUBES = [
    "/Game/SpaceNebulaFantasy/Textures/Skybox_8/T_Nebula_Turquoise_Dark_8",
    "/Game/SpaceNebulaFantasy/Textures/Skybox_6/T_Nebula_Orange_6",
    "/Game/SpaceNebulaFantasy/Textures/Skybox_1/T_Nebula_Blue_1",
    "/Game/Vefects/Stylized_Galaxy_Shader/Galaxy/Textures/T_VFX_Lush_Galaxy_Space_Panorama_Cube_02",
    "/Game/Vefects/Stylized_Galaxy_Shader/Galaxy/Textures/T_VFX_Lush_Galaxy_Space_Panorama_Cube_04",
]
COSMIC_MATERIALS = [f"/Game/CosmicMaterial/Material/MI_Master_{i}" for i in (3, 8, 12, 16, 20)]
ELECTRICAL = [
    "/Game/NERVES/FX/NS_ElectircBeams_Blue",
    "/Game/NiagaraExamples/FX_Player/NS_Player_Electricity_Looping",
    "/Game/NiagaraExamples/FX_Ribbons/NS_TeslaCoil",
    "/Game/Sci_Fi_Weapons_VFX_AIO/VFX/NS_Lightning_Damage_Land_Mid",
]


def package_dependencies(registry, path):
    options = u.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )
    return sorted(str(item) for item in registry.get_dependencies(path, options))


def describe(path, registry):
    obj = u.load_asset(path)
    row = {"path": path, "loaded": obj is not None}
    if obj is None:
        return row
    row["class"] = obj.get_class().get_name()
    row["dependencies"] = package_dependencies(registry, path)
    if isinstance(obj, u.Texture):
        for key in ("blueprint_get_size_x", "blueprint_get_size_y"):
            if hasattr(obj, key):
                row[key.removeprefix("blueprint_get_")] = getattr(obj, key)()
        row["maximum_texture_size"] = obj.get_editor_property("max_texture_size")
    if isinstance(obj, u.NiagaraSystem) and hasattr(u, "SSVFXPresentationLibrary"):
        row["native_audit"] = json.loads(u.SSVFXPresentationLibrary.describe_system(obj))
    if isinstance(obj, u.MaterialInstanceConstant):
        edit = u.MaterialEditingLibrary
        row["parent"] = obj.get_editor_property("parent").get_path_name()
        row["scalar_parameters"] = [str(x) for x in edit.get_scalar_parameter_names(obj)]
        row["vector_parameters"] = [str(x) for x in edit.get_vector_parameter_names(obj)]
        row["texture_parameters"] = [str(x) for x in edit.get_texture_parameter_names(obj)]
    if isinstance(obj, u.Blueprint):
        generated = obj.generated_class()
        row["generated_class"] = generated.get_path_name() if generated else None
        if generated:
            cdo = u.get_default_object(generated)
            components = cdo.get_components_by_class(u.ActorComponent) if cdo else []
            row["components"] = [
                {"name": component.get_name(), "class": component.get_class().get_name()}
                for component in components
            ]
    return row


def main():
    InspectCombatVisualAssets.main()
    InspectEnvironmentVFX.main()
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    report = {
        "engine": u.SystemLibrary.get_engine_version(),
        "status": "READ_ONLY_CANDIDATE_AUDIT_REQUIRES_RENDERED_COMPARISON",
        "asteroid_blueprints": [describe(path, registry) for path in ASTEROID_FIELDS],
        "region_cubemaps": [describe(path, registry) for path in REGION_CUBES],
        "cosmic_materials": [describe(path, registry) for path in COSMIC_MATERIALS],
        "electrical_candidates": [describe(path, registry) for path in ELECTRICAL],
        "wormhole_plugin_assets": [
            str(asset.package_name)
            for asset in registry.get_assets_by_path("/WormholePortal/WormholePortal", recursive=True)
        ],
        "limits": [
            "Blueprint component metadata does not prove density, motion, scale, or performance.",
            "Material and Niagara metadata does not establish appearance.",
            "Plugin asset discovery does not enable or integrate Wormhole Portal.",
            "No vendor asset was saved or edited.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "OwnedCandidateAudit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    u.log("FLIGHT_COMBAT_SPACE_OWNED_CANDIDATES_INSPECTED")


if __name__ == "__main__":
    main()
