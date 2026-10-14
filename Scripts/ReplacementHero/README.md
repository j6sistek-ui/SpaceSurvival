# Replacement squirrel authoring

These scripts preserve the original hero and import a separate candidate. They run against the installed Blender 5.2 and Unreal 5.8 toolchains; no host packages are installed.

Set process environment `SS_HERO_SOURCE` to the private ReplacementHero directory containing the verified FBXs, textures and `main_game_import_plan.json`. On this desktop it is `C:/Users/j6sis/SpaceSurvival/.agent/local/ReplacementHero`. Do not publish those private inputs or licensed retargeted clips.

1. Run `NormalizeUnits.py` in background Blender. It reconstructs the same rest skeleton/weighted mesh in centimeters and scales animation translations, preventing the imported 100x root scale from shrinking retargeted poses. Original FBXs remain untouched; derivatives go in `UnrealUnits`.
2. In the repaired project editor, with Play stopped, run `Import.py`, `Materials.py`, `Retarget.py`, `Compose.py`, and `MeasureFit.py`, in that order through native Unreal Python. Imports use `/Game/SpaceSurvival/Licensed/HeroReplacement/Final`; existing output packages are retained. Retarget sources are the installed MoCap Online body clips, original hero pilot, and SampleAnimationPack Manny jump/fall/land clips.
3. Inspect actual evaluated animation in Play; the non-playing editor preview can remain at reference pose even with editor animation enabled. Verify grounding, tail silhouette and cockpit fit. Do not equate imported tracks with rendered acceptance.
4. Build the runtime changes, then run `Activate.py`. It checks skeleton/clip compatibility, backs up the tuning asset and original Squirrel definition, and changes only the Squirrel row. Stable selection IDs and saves remain unchanged. `tail_root_bone=tail_01` lets the landing tail continue when movement resumes.

`Compose.py` samples all body tracks at 30 fps and replaces only the seven tail tracks. Idle has two body cycles per 12.267s tail cycle. Pilot keeps its rest tail to avoid broad cockpit swaying. The eight final clips share one 69-bone skeleton. `MeasureFit.py` records approximate planted-toe gait speeds and preserves the original seated pelvis anchor; those measurements do not substitute for visual contact/seat review.

This recipe does not package, publish, replace source art, remove other imported assets, or edit the sandbox. The first import is intentionally non-destructive; delete/re-author only explicitly owned candidate packages when revising inputs.

## Jump tail floor clearance

`MeasureTailFloor.py` measures all skin-weighted tail surface vertices from the existing private mesh and produces seven bone-local bounds. Its default invocation is read-only. After reviewing `.agent/local/SurvivalQuality/TailFloor/dry-run.json`, repeat the invocation with `-ApplyTailFloor` to back up `DA_Phase1` and write only the Squirrel row's optional `tail_floor_envelopes`. The apply step refuses changed mesh/tuning inputs. No animation, mesh or map package is changed.

The runtime pose proxy applies the measured bounds after body and landing-tail blending. If the tail approaches a real walkable floor, it makes the smallest upward rotation about the attached tail root needed to clear the bounds. The other tail joints keep their authored bend and recoil; the body remains unchanged. When the floor is clear below the airborne tail, the original pose is unchanged. Other heroes have no envelopes and retain their existing behavior.

After the Editor build, run `SpaceSurvival.Integration.SquirrelTailFloor` for actual deformed-surface coverage of the three jump clips and landing follow-through over walk/run. It samples at 60 Hz and checks body/attachment preservation and unchanged airborne poses. Then capture ordinary takeoff, descent and landing, including movement immediately after landing; the conservative bounds and rendered fur still need visual acceptance. `SpaceSurvival.Integration.WalkerSupportRecovery` separately covers walking support/recovery at threshold edges and furniture.
