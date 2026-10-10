"""Per-character bakes that must follow ANY retarget onto the Tripo crew. Runs by itself or from the retarget scripts.

  UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/AuthorTripoCrewPost.py"
  SS_POST_WHO=Crest,Elf   limit to those characters (default: every character that has a post step)

AuthorTripoCrew.py and AuthorTripoCrewRoles.py call run() themselves at the end for the characters they touched
(set SS_POST=0 to skip), because a retarget writes fresh clips with these bones at their reference pose and silently
undoes the bake. Every step is idempotent - it rebuilds from the skeleton's rest pose or the source clips, never from
what is already in the clip - so re-running over all of a character's clips is always safe.

Which characters, what, and why: docs/TRIPO_CREW_ANIMATION.md.
"""
import os
import runpy

import unreal as u

HERE = os.path.dirname(os.path.abspath(__file__))
# character -> [(script, env)] in order
POST = {
    "Crest": [("AuthorTripoCrewTail.py", {"SS_TAIL_WHO": "Crest"})],                 # tail + cord sway
    "Abyss": [("AuthorTripoCrewTentacleBlend.py", {"SS_TENT_WHO": "Abyss"})],       # her own tentacle lower body, once she has humanoid clips
    "Elf": [("AuthorTripoCrewHair.py", {"SS_HAIR_WHO": "Elf"})],                    # simulated hair
    "Silver": [("AuthorTripoCrewHair.py", {"SS_HAIR_WHO": "Silver"})],
}


def run(who):
    """Run the post steps for these characters (unknown names and characters with no step are ignored)."""
    for w in who:
        for script, env in POST.get(w, []):
            if w == "Abyss" and not u.EditorAssetLibrary.does_directory_exist(
                    "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Abyss/Role"):
                continue
            old = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            try:
                u.log_warning("POST| %s: %s" % (w, script))
                runpy.run_path(os.path.join(HERE, script), run_name="__main__")
            finally:
                for k, v in old.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


if __name__ == "__main__":
    run([w for w in os.environ.get("SS_POST_WHO", ",".join(POST)).split(",") if w])
