"""Run in Unreal with DESCRIPTION_PATH, CANDIDATE_NAME and optional APPLY globals.

Default is a dry run. Creates a new private groom only; never replaces Silver's
Blueprint, source groom or map. See docs/validation/2026-10-14-silver-ponytail.md.
"""

import json
from pathlib import Path

import unreal as u

ROOT = "/Game/SpaceSurvival/Licensed/SilverPonytail_20261014"
assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(), "Stop PIE before authoring"
source = u.load_asset(ROOT + "/Source/ponytail")
description = Path(DESCRIPTION_PATH).read_text(encoding="utf-8")
result = json.loads(u.SSGroomAuthoring.create_silver_strands(
    source, description, CANDIDATE_NAME, bool(globals().get("APPLY", False))))
assert result["success"], result


def tune(obj, prop, values):
    sub = obj.get_editor_property(prop)
    for key, value in values.items():
        sub.set_editor_property(key, value)
    obj.set_editor_property(prop, sub)


if result["applied"]:
    groom = u.load_asset(result["path"])
    lods = list(groom.hair_groups_lod)
    physics = list(groom.hair_groups_physics)
    interpolation = list(groom.hair_groups_interpolation)
    rendering = list(groom.hair_groups_rendering)
    for i in range(2):
        row = lods[i]
        levels = list(row.get_editor_property("lods"))
        for level in levels:
            level.set_editor_property("binding_type", u.GroomBindingType.RIGID)
            level.set_editor_property("simulation", u.GroomOverrideType.ENABLE if i else u.GroomOverrideType.DISABLE)
        row.set_editor_property("lods", levels)
        lods[i] = row
        row = physics[i]
        tune(row, "solver_settings", {"enable_simulation": bool(i),
                                     "niagara_solver": u.GroomNiagaraSolvers.COSSERAT_RODS,
                                     "sub_steps": 5, "iteration_count": 8})
        tune(row, "external_forces", {"air_drag": .35, "gravity_vector": u.Vector(0, 0, -981)})
        constraints = row.get_editor_property("material_constraints")
        tune(constraints, "bend_constraint", {"bend_stiffness": .2, "bend_damping": .1, "project_bend": True})
        tune(constraints, "stretch_constraint", {"stretch_stiffness": 1., "stretch_damping": .1, "project_stretch": True})
        tune(constraints, "collision_constraint", {"collision_radius": .15, "solve_collision": True, "project_collision": True})
        row.set_editor_property("material_constraints", constraints)
        tune(row, "strands_parameters", {"strands_size": u.GroomStrandsSize.SIZE32})
        physics[i] = row
        row = interpolation[i]
        tune(row, "interpolation_settings", {"guide_type": u.GroomGuideType.IMPORTED, "use_unique_guide": True})
        interpolation[i] = row
        row = rendering[i]
        tune(row, "geometry_settings", {"hair_width": .02, "hair_root_scale": 1.15, "hair_tip_scale": .4})
        rendering[i] = row
    groom.set_editor_property("hair_groups_lod", lods)
    groom.set_editor_property("hair_groups_rendering", rendering)
    groom.set_editor_property("enable_simulation_cache", True)
    groom.set_editor_property("hair_groups_physics", physics)
    groom.set_editor_property("hair_groups_interpolation", interpolation)
    assert u.EditorLoadingAndSavingUtils.save_packages([groom.get_outermost()], False)
print(json.dumps(result))
