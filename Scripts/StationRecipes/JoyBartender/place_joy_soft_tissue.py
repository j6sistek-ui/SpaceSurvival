"""Give the bartender Joy's placed actor Silver's body dynamics: a BodyDynamics (USSSoftTissueComponent) instance component
on the 'Crew/Lounge guest' actor in L_WayfarerRuntime, bound to SK_Joy's ST_<Region>_<Axis> morphs with the anchors from
author_soft_tissue.py and the spring values Silver's adopted component uses (RuntimeDynamics/Candidate.json, 2026-10-13).

  set SS_JOY_ST_DIR=<soft_tissue export folder>   (SoftTissue.json; SK_Joy already reimported by reimport_joy_soft_tissue.py)
  set SS_JOY_ST_REPORT=<json>                      (back the map up first)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/place_joy_soft_tissue.py"

Needs the editor built with USSSoftTissueComponent (PR 71's Source/SpaceSurvival/*/SSSoftTissueComponent.*).
"""
import itertools
import json
import os

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
MESH = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender/Mesh/SK_Joy"
SRC = os.environ["SS_JOY_ST_DIR"]
REPORT_PATH = os.environ.get("SS_JOY_ST_REPORT", "")
DATA = json.load(open(os.path.join(SRC, "SoftTissue.json")))
# Silver's adopted values (.agent/local/ViableEldFinish_20261013/RuntimeDynamics/Candidate.json: 135/.3/.9/1.6 and
# 300/.36/.85/1.2) made "a bit more sensitive" at the owner's request 2026-10-14: softer spring, lighter damping, more
# drive, a quarter more travel. The jacket is held clear of the skin by these caps (author_soft_tissue.py MAX_OFFSET_CM).
SPRING = {"Breast": dict(mass_kg=.55, stiffness=110., damping_ratio=.26, strength=1.15, axis_response=u.Vector(1.5, .8, 1.), max_offset_cm=2.0),
          "Hip": dict(mass_kg=.9, stiffness=240., damping_ratio=.32, strength=1.1, axis_response=u.Vector(1.4, .85, 1.), max_offset_cm=1.5)}
COMPONENT = "BodyDynamics"


def log(s):
    u.log_warning("JOYST| " + str(s))


assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
mesh = u.load_asset(MESH)
morphs = {str(n) for n in mesh.get_all_morph_target_names()}
for region in DATA["regions"]:
    for axis in "XYZ":
        assert "ST_%s_%s" % (region, axis) in morphs, region

# Blender rest centimetres -> the imported reference mesh: find the axis signs from six reference bones
pose = u.AnimPoseExtensions.get_reference_pose(mesh.skeleton)
ref = DATA["reference_bones_blender_cm"]
native = {n: u.AnimPoseExtensions.get_bone_pose(pose, n, u.AnimPoseSpaces.WORLD).translation for n in ref}


def error(signs):
    return max((native[n] - u.Vector(*[v * s for v, s in zip(ref[n], signs)])).length() for n in ref)


signs = min(itertools.product((-1, 1), repeat=3), key=error)
err = error(signs)
log("axis signs %s, reference bone error %.3f cm" % (signs, err))
assert err < 1.0, (signs, err, {n: (list(native[n].to_tuple()), ref[n]) for n in ref})

regions = []
for name, row in DATA["regions"].items():
    region = u.SSSoftTissueRegion()
    region.set_editor_property("morph_prefix", "ST_" + name)
    anchors = []
    for a in row["anchors"]:
        v = u.SSSoftTissueAnchor()
        v.set_editor_property("bone", a["bone"])
        v.set_editor_property("weight", a["weight"])
        v.set_editor_property("rest_position", u.Vector(*[x * s for x, s in zip(a["rest_position_blender_cm"], signs)]))
        anchors.append(v)
    region.set_editor_property("anchors", anchors)
    region.set_editor_property("morph_axis_signs", u.Vector(*signs))
    region.set_editor_property("centimetres_per_morph_unit", float(DATA["key_cm"]))
    for k, v in SPRING["Breast" if name.startswith("Breast") else "Hip"].items():
        region.set_editor_property(k, v)
    regions.append(region)

assert u.EditorLevelLibrary.load_level(MAP)
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
bar = next((a for a in actors if a.get_actor_label() == LABEL), None)
assert bar and isinstance(bar, u.SSOutpostAmbientActor), bar
assert bar.character_mesh.get_skeletal_mesh_asset().get_path_name() == mesh.get_path_name(), bar.character_mesh.get_skeletal_mesh_asset().get_path_name()
mesh_name = bar.character_mesh.get_name()
existing_comps = bar.get_components_by_class(u.SSSoftTissueComponent)
comp = existing_comps[0] if existing_comps else None
how = "updated existing component" if comp else ""
try:
    if comp:
        raise StopIteration
    S = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    F = u.SubobjectDataBlueprintFunctionLibrary
    handles = S.k2_gather_subobject_data_for_instance(bar)
    h, why = S.add_new_subobject(u.AddNewSubobjectParams(parent_handle=handles[0], new_class=u.SSSoftTissueComponent))
    assert F.is_handle_valid(h), str(why)
    S.rename_subobject(h, u.Text(COMPONENT))
    comp = F.get_object(F.get_data(h))
    how = "SubobjectDataSubsystem"
except StopIteration:
    pass
except Exception as e:  # noqa
    log("subobject route failed (%s); adding the component by class" % e)
if not isinstance(comp, u.SSSoftTissueComponent):
    comp = bar.add_component_by_class(u.SSSoftTissueComponent, False, u.Transform(), False)
    how = "add_component_by_class"
assert isinstance(comp, u.SSSoftTissueComponent), comp
comp.set_editor_property("mesh_component_name", mesh_name)
comp.set_editor_property("dynamics_enabled", True)
comp.set_editor_property("regions", regions)
bar.modify()
assert u.EditorLevelLibrary.save_current_level(), "map save failed"
log("component added via %s; saved" % how)

# read back from disk
assert u.EditorLevelLibrary.load_level(MAP)
bar2 = next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == LABEL)
comps = bar2.get_components_by_class(u.SSSoftTissueComponent)
assert len(comps) == 1, comps
c = comps[0]
rows = []
for r in c.get_editor_property("regions"):
    anchors = r.get_editor_property("anchors")
    total = sum(a.get_editor_property("weight") for a in anchors)
    rows.append({"prefix": str(r.get_editor_property("morph_prefix")), "anchors": [(str(a.get_editor_property("bone")), round(a.get_editor_property("weight"), 4),
                 [round(v, 2) for v in a.get_editor_property("rest_position").to_tuple()]) for a in anchors], "weight_total": total,
                 "stiffness": r.get_editor_property("stiffness"), "max_offset_cm": r.get_editor_property("max_offset_cm"), "signs": list(r.get_editor_property("morph_axis_signs").to_tuple())})
    assert abs(total - 1) < 1e-4, rows[-1]
after = {"component": c.get_name(), "mesh_component_name": str(c.get_editor_property("mesh_component_name")), "regions": rows, "how": how, "signs": signs, "reference_error_cm": err}
assert len(rows) == 4 and after["mesh_component_name"] == mesh_name, after
if REPORT_PATH:
    json.dump(after, open(REPORT_PATH, "w"), indent=1)
log("DONE " + json.dumps(after))
