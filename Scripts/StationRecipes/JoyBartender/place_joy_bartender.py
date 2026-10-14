"""Make the original Joy the bartender: the one placed 'Crew/Lounge guest' actor in L_WayfarerRuntime gets her mesh,
her clips, her actions, her unprompted lines and her talk identity. Dread's assets are untouched; only this actor changes.

  set SS_JOY_PLACE_REPORT=<json>   (back the map up first: Content/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime.umap)
  UnrealEditor-Cmd.exe <project> -unattended -NullRHI ... -ExecutePythonScript="<abs>/place_joy_bartender.py"

Needs the editor built with FSSNpcAction/Actions/Chatter on ASSOutpostAmbientActor (branch claude/joy-bartender), SK_Joy
imported (import_joy_original.py) and the A_Joy_Bar* clips retargeted (retarget_joy_bartender.py).
Owner 2026-10-14: "she's going to replace the bartender ... fully animate bartender scenes ... add ways to interact ...
constantly chatty, audibly ... calling out the aliens for scratching in pool ... the life of the room".
"""
import json
import os

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime"
LABEL = "Crew/Lounge guest"
JOY_LABEL = "HomeHub/Residents/Joy"
B = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
LB = "/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117/Animations"
MESH = B + "/Mesh/SK_Joy"
REPORT_PATH = os.environ.get("SS_JOY_PLACE_REPORT", "")
L = u.EditorAssetLibrary


def log(s):
    u.log_warning("JOYPLACE| " + str(s))


def clip(*candidates):
    for c in candidates:
        for folder in (B + "/Animations", LB):
            p = folder + "/" + c
            if L.does_asset_exist(p):
                a = u.load_asset(p)
                if isinstance(a, u.AnimSequence):
                    return a
    return None


def need(*candidates):
    a = clip(*candidates)
    assert a, candidates
    return a


# the clip set: Dread's take as the resting loop, everything else as gestures so she is never still
IDLE = need("A_Joy_BarBartender_Type02", "A_Joy_Bar_Bartender")
WALK = need("A_Joy_Walk")
GESTURES = [c for c in [clip("A_Joy_Bar_Bartender"), clip("A_Joy_Bar_Bartender2"), clip("A_Joy_Bar_TalkAtTheBar"), clip("A_Joy_Bar_PourAndServe"),
                        clip("A_Joy_Bar_Bartender4"), clip("A_Joy_Bar_AtTheBar"), clip("A_Joy_Bar_TalkAtTheBar2"), clip("A_Joy_BarBartender_Type05"),
                        clip("A_Joy_Bar_CheersAndDrink2"), clip("A_Joy_Bar_Bartender3"), clip("A_Joy_Gesture_ExcitedHello"), clip("A_Joy_Bar_TalkAtTheBar3"),
                        clip("A_Joy_BarBartender_Type08"), clip("A_Joy_Bar_AtTheBar2"), clip("A_Joy_Emote_Greeting"), clip("A_Joy_Bar_TalkAtTheBar4"),
                        clip("A_Joy_Fidget1"), clip("A_Joy_Bar_CheersAndDrink3")] if c]
assert len(GESTURES) >= 8, [g.get_name() for g in GESTURES]

ACTIONS = [
    ("Pour a drink", ["pour", "drink", "gin", "ale", "nebula", "cocktail", "beer", "whisky", "shot", "thirsty", "round"],
     need("A_Joy_Bar_PourAndServe"), False, 0.0, "One Nebula, poured the way I like it. Careful, it glows."),
    ("Cheers", ["cheers", "toast", "to the pilots", "drink with me"], need("A_Joy_Bar_CheersAndDrink", "A_Joy_Bar_CheersAndDrink2"), False, 0.0,
     "To the ones who come back. Drink."),
    ("Dance", ["dance", "music", "show me", "move"], need("A_Joy_Dance_ClubDance", "A_Joy_Sensual_Dance1"), True, 12.0,
     "Watch the bar for me. Not really, nobody touches my bottles."),
    ("Story", ["story", "tell me", "joke", "news", "gossip"], need("A_Joy_Bar_TalkAtTheBar2", "A_Joy_Bar_TalkAtTheBar"), False, 0.0,
     "Pull up a stool. This one is about a pilot who tried to pay in asteroid dust."),
]
CHATTER = [
    "Scratch! Kett, that is the third one tonight. The table is not out to get you.|Story",
    "Who wants a Nebula? It glows. It is supposed to glow.|Pour a drink",
    "Pim, you are holding that cue like it owes you money.",
    "Fresh pour, do not let it get warm. Warm Nebula is a crime on three decks.|Pour a drink",
    "Rue, if you sink the eight ball again I am cutting you off. I mean it this time.",
    "The gin is from Europa and the ice is from the galley. One of those is a lie.",
    "Cheers to whoever just docked. You look like you need this.|Cheers",
    "Dax, that was a foul. Everyone saw it. Brakk, back me up. Brakk?",
    "I never forget a face. Names, every time. Drinks, never.",
    "Three pilots came back from the belt today and all three ordered the same thing. Guess.",
    "Mica, the cue goes in your hands, not under the table. Again.",
    "Synth-ale for the quiet ones, gin for the loud ones, Nebula for the ones who want a story.|Pour a drink",
    "Somebody put money on Kett missing that shot. I would.",
    "If you are waiting for the maintenance crew, they are still out there floating. Have a drink.",
    "This one is on me. No it is not. But I like saying it.|Cheers",
    "The last pilot who told me the Director was easy flew home sideways.",
    "Brakk, two scratches in a row. The table wants a word.",
    "Watch the pour. No, watch it. There. That is why they come back.|Pour a drink",
    "Rue says the Nebula is too strong. Rue drank four.",
    "Dock tired, drink well, fly straight. House rules.",
]

assert u.EditorLevelLibrary.load_level(MAP)
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
bar = next((a for a in actors if a.get_actor_label() == LABEL), None)
joy_blue = next((a for a in actors if a.get_actor_label() == JOY_LABEL), None)
assert bar and isinstance(bar, u.SSOutpostAmbientActor), bar
mesh = u.load_asset(MESH)
assert isinstance(mesh, u.SkeletalMesh), MESH
before = {"mesh": bar.character_mesh.get_skeletal_mesh_asset().get_path_name() if bar.character_mesh.get_skeletal_mesh_asset() else None,
          "tags": [str(t) for t in bar.tags], "location": list(bar.get_actor_location().to_tuple()), "rotation": list(bar.get_actor_rotation().to_tuple()),
          "mesh_rel_rot": list(bar.character_mesh.get_editor_property("relative_rotation").to_tuple()),
          "mesh_rel_loc": list(bar.character_mesh.get_editor_property("relative_location").to_tuple())}
# how the light-blue Joy's body is turned on her Blueprint: the same mesh family, so the same yaw
yaw = None
if joy_blue:
    for comp in joy_blue.get_components_by_class(u.SkeletalMeshComponent):
        yaw = comp.get_editor_property("relative_rotation").yaw
        break
log("before: %s ; light-blue JoyBody yaw %s" % (json.dumps(before), yaw))

cm = bar.character_mesh
cm.set_skeletal_mesh_asset(mesh)
half = bar.body.get_scaled_capsule_half_height()
cm.set_editor_property("relative_location", u.Vector(0.0, 0.0, -half))
# Joy's FBX came through the same Blender -Y-forward export as the crew, so she faces +Y in asset space like SK_Dread:
# keep the actor's existing mesh yaw (-90) rather than the light-blue Blueprint's 0, whose actor is turned instead.
cm.set_editor_property("relative_rotation", u.Rotator(0.0, before["mesh_rel_rot"][2], 0.0))
cm.set_editor_property("relative_scale3d", u.Vector(1.0, 1.0, 1.0))
cm.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
cm.set_editor_property("animation_data", u.SingleAnimationPlayData(anim_to_play=IDLE, saved_looping=True, saved_playing=True, saved_position=0.0, saved_play_rate=1.0))
bar.set_editor_property("idle_animation", IDLE)
bar.set_editor_property("walk_animation", WALK)
bar.set_editor_property("gesture_animations", GESTURES)
bar.set_editor_property("gesture_interval", 3.0)
bar.set_editor_property("talk_name", "Joy")
bar.set_editor_property("talk_role", "Bartender")
bar.set_editor_property("talk_activity", "mixing drinks behind the bar and heckling the pool table across the room")
bar.set_editor_property("head_fill_socket", "CC_Base_Head")
acts = []
for name, words, c, loop, secs, line in ACTIONS:
    a = u.SSNpcAction()
    a.set_editor_property("name", name)
    a.set_editor_property("keywords", words)
    a.set_editor_property("clip", c)
    a.set_editor_property("loop", loop)  # bLoop in C++; Python drops the b prefix
    if loop:
        a.set_editor_property("loop_seconds", secs)
    a.set_editor_property("line", line)
    acts.append(a)
bar.set_editor_property("actions", acts)
bar.set_editor_property("chatter", CHATTER)
bar.set_editor_property("chatter_interval", 26.0)
tags = [u.Name("StationCrew:Joy") if str(t) == "StationCrew:Dread" else t for t in bar.tags]
bar.set_editor_property("tags", tags)
bar.modify()
assert u.EditorLevelLibrary.save_current_level(), "map save failed"

# read back
assert u.EditorLevelLibrary.load_level(MAP)
bar2 = next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == LABEL)
after = {"mesh": bar2.character_mesh.get_skeletal_mesh_asset().get_path_name(), "tags": [str(t) for t in bar2.tags],
         "idle": bar2.get_editor_property("idle_animation").get_path_name(), "walk": bar2.get_editor_property("walk_animation").get_path_name(),
         "gestures": [g.get_name() for g in bar2.get_editor_property("gesture_animations")],
         "actions": [(x.get_editor_property("name"), x.get_editor_property("clip").get_name(), len(x.get_editor_property("keywords"))) for x in bar2.get_editor_property("actions")],
         "chatter": len(bar2.get_editor_property("chatter")), "talk": [bar2.get_editor_property(k) for k in ("talk_name", "talk_role", "talk_activity")],
         "mesh_rel_rot": list(bar2.character_mesh.get_editor_property("relative_rotation").to_tuple()),
         "mesh_rel_loc": list(bar2.character_mesh.get_editor_property("relative_location").to_tuple()),
         "gesture_interval": bar2.get_editor_property("gesture_interval"), "chatter_interval": bar2.get_editor_property("chatter_interval")}
assert after["mesh"].endswith("SK_Joy") and "StationCrew:Joy" in after["tags"] and after["chatter"] == len(CHATTER) and len(after["actions"]) == 4, after
if REPORT_PATH:
    json.dump({"before": before, "after": after}, open(REPORT_PATH, "w"), indent=1)
log("DONE " + json.dumps(after))
