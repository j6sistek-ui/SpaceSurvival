# Replacement squirrel authoring

These scripts preserve the original hero and import a separate candidate. They run against the installed Blender 5.2 and Unreal 5.8 toolchains; no host packages are installed.

Set process environment `SS_HERO_SOURCE` to the private ReplacementHero directory containing the verified FBXs, textures and `main_game_import_plan.json`. On this desktop it is `C:/Users/j6sis/SpaceSurvival/.agent/local/ReplacementHero`. Do not publish those private inputs or licensed retargeted clips.

1. Run `NormalizeUnits.py` in background Blender. It reconstructs the same rest skeleton/weighted mesh in centimeters and scales animation translations, preventing the imported 100x root scale from shrinking retargeted poses. Original FBXs remain untouched; derivatives go in `UnrealUnits`.
2. In the repaired project editor, with Play stopped, run `Import.py`, `Materials.py`, `Retarget.py`, `Compose.py`, and `MeasureFit.py`, in that order through native Unreal Python. Imports use `/Game/SpaceSurvival/Licensed/HeroReplacement/Final`; existing output packages are retained. Retarget sources are the installed MoCap Online body clips, original hero pilot, and SampleAnimationPack Manny jump/fall/land clips.
3. Inspect actual evaluated animation in Play; the non-playing editor preview can remain at reference pose even with editor animation enabled. Verify grounding, tail silhouette and cockpit fit. Do not equate imported tracks with rendered acceptance.
4. Build the runtime changes, then run `Activate.py`. It checks skeleton/clip compatibility, backs up the tuning asset and original Squirrel definition, and changes only the Squirrel row. Stable selection IDs and saves remain unchanged. `tail_root_bone=tail_01` lets the landing tail continue when movement resumes.

`Compose.py` samples all body tracks at 30 fps and replaces only the seven tail tracks. Idle has two body cycles per 12.267s tail cycle. Pilot keeps its rest tail to avoid broad cockpit swaying. The eight final clips share one 69-bone skeleton. `MeasureFit.py` records approximate planted-toe gait speeds and preserves the original seated pelvis anchor; those measurements do not substitute for visual contact/seat review.

This recipe does not package, publish, replace source art, remove other imported assets, or edit the sandbox. The first import is intentionally non-destructive; delete/re-author only explicitly owned candidate packages when revising inputs.
