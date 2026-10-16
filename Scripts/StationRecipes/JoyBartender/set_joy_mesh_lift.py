"""Raise the bartender's mesh by the sole depth of her shoes (author_soft_tissue.py reports it as pants.sole_depth_cm):
her bare-foot mesh offset puts the soles under the floor. Owner 2026-10-14 asked for the sci-fi pants with sneakers.

  set SS_JOY_LIFT_CM=<cm>     (back the map up first)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/set_joy_mesh_lift.py"
"""
import os

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
LIFT = float(os.environ["SS_JOY_LIFT_CM"])
assert 0.0 <= LIFT <= 8.0, LIFT
assert u.EditorLevelLibrary.load_level(MAP)
bar = next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == LABEL)
half = bar.body.get_scaled_capsule_half_height()
loc = bar.character_mesh.get_editor_property("relative_location")
bar.character_mesh.set_editor_property("relative_location", u.Vector(loc.x, loc.y, -half + LIFT))
bar.modify()
assert u.EditorLevelLibrary.save_current_level()
assert u.EditorLevelLibrary.load_level(MAP)
bar = next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == LABEL)
z = bar.character_mesh.get_editor_property("relative_location").z
assert abs(z - (-half + LIFT)) < 0.01, z
u.log_warning("JOYLIFT| DONE mesh z %.2f (capsule half %.2f, lift %.2f)" % (z, half, LIFT))
