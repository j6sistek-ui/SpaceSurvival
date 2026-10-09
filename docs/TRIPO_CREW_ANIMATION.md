# Tripo crew: adding animations

Reference for putting new clips on the 20 Tripo crew NPCs under
`/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/<Name>/`. Open owner decisions and known limits are tracked in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md) (RPT-20261008-01); this page says what each character needs.

## Is a new animation standard or extra work?

**Standard for every character.** One run of the retarget script does it. Every per-character extra (tail,
tentacles, hair) runs automatically at the end of that run (`Scripts/AuthorTripoCrewPost.py`), so nothing has to be
remembered. What stays character-specific is **choosing clips that suit the body** - the per-character log below.
Two characters are exceptions to "one run": **Abyss** needs wiring before her first humanoid clip, and Kraken's
**tentacle-only** motions are authored in Blender, not retargeted (both in the log).

Measured cost on this machine (CPU only, no VRAM). Each post step re-bakes **every** clip that character has, on
every run, so its cost scales with the character's total clip count, not with the clips just added:

| Step | Cost |
| --- | --- |
| Retarget (any character) | ~0.6 s per clip retargeted |
| Crest tail bake | ~0.3 s x all of Crest's clips (57 today: ~16 s) |
| Kraken tentacle lower body | ~1.3 s x all of Kraken's clips (33 today: ~45 s) |
| Elf / Silver hair simulation | ~5 s x all of that character's clips (Elf 129: ~11 min, Silver 46: ~4 min) |
| Check render (export + 8 clay frames) | ~10 s per clip |

## The standard procedure

1. **Know the pack's skeleton.** Three source families are wired. UE4 mannequin (MCO_Mocap_Basics, Mobility,
   RamsterZ_FreeAnims_Volume1, Merchant Vendor) -> crew retargeter `RTG_<Name>`; UE5 Manny (Paragon, Space_Crew,
   the dance and gesture packs) -> `RTG_<Name>_Manny`; 3ds Max Biped (Bar Counter People) -> `RTG_<Name>_Biped`. A
   pack on any other skeleton needs a source rig added to `SOURCES` in `Scripts/AuthorTripoCrewRoles.py`.
2. **Make the clips reachable.**
   - A pack already in `Content/` is used in place by full `/Game/...` path. **Give a new pack a `PACK_TAG` entry**
     in `AuthorTripoCrewRoles.py`: output names are `<tag>_<clip>`, two packs that both ship e.g. `AS_Dance1`
     otherwise overwrite each other silently, and the tag is what Crest's tail mood and Kraken's lower body read.
   - An FBX-only pack is imported with `Scripts/ImportStationClipLibrary.py` into `ClipLibrary/<Library>/`:
     `SS_CLIPLIB_SOURCE` and `SS_CLIPLIB_NAME` are required; a Manny pack needs `SS_CLIPLIB_SKELETON` set to the
     Manny skeleton (the default is UE4) and a Biped pack ships its own mesh (`SS_CLIPLIB_WITH_MESH=1`). A new
     library also needs its own `(source, library, clips)` tuple in the role's `sets`.
3. **Cast them** - two routes:
   - **Role clips** (most new work): add names to the role's list in `AuthorTripoCrewRoles.py` and run it, limited
     with `SS_ROLES_ONLY=<ROLES key>` and `SS_ROLES_WHO=<Name>`. ROLES keys: `Merchant`, `Worker`, `Dancer`,
     `Performer`, `Flirt` (the adult nightclub set), `Bartender`, `Desk`, `Maintenance`, `Waitress`, `Security`,
     `Lounge`. Moving a character to another role: `SS_ROLES_PRUNE=<Name>` clears its old role clips first.
   - **Base clips** (the walk/turn/talk set): add to `CLIPS` in `AuthorTripoCrew.py`. That route takes only UE4
     mannequin clips found under its `CLIP_ROOTS`, is limited with `SS_TRIPOCREW_ONLY=<Name>`, and rebuilds the
     whole base set of every character it touches. It skips Kraken and Abyss unless `SS_TRIPOCREW_ONLY` names them.
   - The post steps run on their own for every character the run touched (`SS_POST=0` skips them). To re-apply one
     after editing it - e.g. a new word in Crest's `AGITATED` / `GAIT` lists - run `AuthorTripoCrewPost.py` with
     `SS_POST_WHO=Crest`.
4. **Look before shipping** with `Scripts/TripoCrewBlender/validate/` (each docstring has the full options):
   `export_clips.py` in Unreal (`-RenderOffscreen`; `SS_AF_OUT=<folder>`, `SS_AF_WHO=<Name>`, optional
   `SS_AF_FILTER=<text>`) -> `render_strip.py` per FBX in Blender (`SS_YAW`, close-ups with `SS_TARGET=neck_01` or
   `pelvis`) -> `python -I sheets.py <frames> <out> <Name>` for the contact sheet. Renders come from what Unreal
   actually holds; the Elf's thigh fault only showed up that way.

**Full character rebuild** (new mesh or new bones): `ImportTripoCrew.py` (`SS_TRIPOCREW_FBX=<folder>`,
`SS_TRIPOCREW_ONLY=<Name>`) -> `AuthorTripoCrew.py` (`SS_TRIPOCREW_ONLY=<Name>`; add `SS_POST=0` so the hair sim does
not run twice) -> `AuthorTripoCrewRoles.py`. `AuthorTripoCrew.py` deletes **every** asset directly in
`TripoCrew/<Name>/` - base clips, IK rig, `RTG_<Name>` and also `RTG_<Name>_Manny` / `_Biped` - and rebuilds the base
set and `RTG_<Name>`; the roles run recreates the other retargeters. A changed skeleton must not be imported over the
old one (a surviving skeleton at the import path is silently reused and drops the new bones): delete the character's
generated folder first, or list it in `RIG_FOLDER` (in all three scripts) to import into a fresh `Rig/`. A new
character goes into the `CREW` tables of both `ImportTripoCrew.py` and `AuthorTripoCrew.py`.

Materials are never imported: Elf and Cyborg slots take the instances from the repair chat's native meshes in
`CharacterRepairs_20261008` (their restored roughness is kept), every other character's from `/Game/TripoModels` by
slot name. Morph targets are not imported.

## Per-character log

"Automatic" means a post step handles it - no extra work. "Choose clips" is the part that needs judgement.

| Character | ROLES key | Special rig | Automatic extra | Choose clips / known limits |
| --- | --- | --- | --- | --- |
| Robe | Merchant | - | - | - |
| Glyph | Merchant | re-skinned (Tripo weights were scrambled); floor-root weights removed | - | - |
| Tribal | Merchant | arrived unrigged: fitted crew skeleton, bone-heat weights; floor-root weights removed | - | face tentacles have no bones and never move |
| Ember | Worker | second pair of arms (`*_low_*` bones) | lower arms follow the main arms inside every retarget (`EXTRA_CHAINS`, `EXTRA_MAP`) | lower arms copy the upper pair exactly, no independent motion; hands-to-body clips can make the lower hands touch the torso |
| Crest | Worker | tail (8 bones) + a cord beside it (5) | tail and cord sway baked per clip; pace and size from the generated clip name (`AuthorTripoCrewTail.py`: words in `AGITATED` = flick, words in `GAIT` such as Walk, Run, Carry, Haul, Move_Forward, Turn = per-stride, else slow drift) | clip names are generated (pack tag + clip), not chosen: steer the mood by adding words to `AGITATED` / `GAIT`, then re-run the post step |
| Olive | Security | owner's newer Tripo export, re-skinned; floor-root weights removed | - | no weapons or salutes (owner: not military) |
| Warden | Maintenance | arrived unrigged: fitted crew skeleton, bone-heat weights; floor-root weights removed | - | zero-G and carry clips carry root motion; no helmet in vacuum |
| Dread | Bartender | re-skinned; floor-root weights removed | - | nothing on the floor behind a bar (lying, deep squats); no standing drink or toast clip exists in any owned pack |
| Kraken | Waitress (1-2 on the whole station) | tentacle body; her human arm bones carry almost no skin, so the long arm tentacles `LArmTent0/RArmTent0` take the arm motion (`EXTRA_CHAINS`, `EXTRA_MAP`) and the short ones keep their own wiggle | her own tentacle crawl / turn / idle replaces everything below the waist, **root included**, chosen by the clip name (`AuthorTripoCrewTentacleBlend.py`: Walk/Carry/Run/Haul = crawl, TurnL / Turn_Left = left turn, TurnR / Turn_Right = right turn, else idle) | a source clip's legs, hips and root motion are discarded, so kicks, squats, sits and travelling moves do not transfer; hand and finger gestures read weakly (no hands); her imported tentacle clips carry no visible pelvis bob (exported 100x too small; `tentacles/export_for_unreal.py` now scales it, so a re-export and re-import restores it); new tentacle-only motion is a new `make("Tent<Name>", ...)` in `tentacles/animate_tentacles.py` plus the clip name added in three places - the clip tuple in `ImportTripoCrew.py` `import_clips` (which also decides the `Kraken_<Clip>.fbx` file it looks for), `TentacleBlend`'s fixed clip list and its `source_for` - then `ImportTripoCrew.py` with `SS_TRIPOCREW_ONLY=Kraken` (re-imports her mesh) |
| Abyss | none (owner choosing Abyss or Kraken) | tentacle body like Kraken, **but no arm-tentacle wiring yet** | none yet - her tentacle blend starts only once `TripoCrew/Abyss/Role` exists | before her first humanoid clip: add Abyss to `EXTRA_CHAINS` (AuthorTripoCrew.py) and `EXTRA_MAP` (AuthorTripoCrewRoles.py), run `AuthorTripoCrew.py` with `SS_TRIPOCREW_ONLY=Abyss`, then the roles run with `SS_ROLES_REBUILD_RTG=Abyss`; base clips alone stay on human legs |
| Seer, Tendril | Desk | cloak / robe tails blended toward the pelvis | - | seated terminal clips need a chair; deep squats lay the cloak on the floor |
| Violet | Dancer | re-skinned; floor-root weights removed | - | - |
| Cyan | Dancer, Flirt | arrived unrigged: fitted crew skeleton, bone-heat weights; floor-root weights removed | - | - |
| Silver | Dancer | 5 hair chains x 7 bones | hair simulation baked per clip | **PARKED (2026-10-08): both thighs are twisted in every clip.** The damage came in with the Tripo plugin's first Unreal import, before rigging; Tripo's original file is clean. Same Tripo character as the Elf. See KNOWN_ISSUES RPT-20261008-01 |
| Crystal | Performer | - | - | tall heavy crown: no big head rolls or neck throws; prop mimes need the prop (guitar, staff spin and marching band were cut; ShamaWnithStaff was checked and reads without one); check loop ends |
| Finhead | Lounge | - | - | `Emote_Guitar` in the lounge set is an air-guitar mime with no guitar |
| Amethyst | Lounge | arrived unrigged: fitted crew skeleton, bone-heat weights; floor-root weights removed | - | as Finhead |
| Elf | Dancer, Flirt, Lounge (base body, outfits later) | repair-chat rig with rebuilt pelvis/thigh frames; 7 hair chains x 7 bones; hair resting on the shoulders rides the shoulder | hair simulation baked per clip | T-pose bind; check very fast moves for hair overshoot; a faint hair crease at the back of the shoulder remains in a few clips |
| Cyborg | Dancer, Flirt, Lounge (base body, outfits later) | repair-chat rig; mechanical hips and legs are the design | - | large bust: clips where the arms cross or the hands press the chest pass into it (the clips were made for flatter bodies; weights cannot fix it); an arm-spread retarget offset would clear most of it at the cost of looser hand contacts - owner's call, not applied. Owner (2026-10-08): the model itself may be redone |

## Any character

- Seated clips sit on nothing: the scene needs a chair or stool where they play.
- Root motion: Space_Crew carry and zero-G clips, and some Paragon emotes, move the root. Play them with root motion
  or pick the in-place variant (Kraken excepted: her root always comes from her own tentacle clip).
- Mouths never move: no character has jaw bones, and mouth shapes are not imported. Talking is body language only.
- Hands-on-body moves authored for slimmer bodies can clip on fuller ones; look at the render.
- Outfits (Elf, Cyborg, later others) skin to the same skeleton by weight transfer, so every existing clip carries over.

## Fixes already in the meshes (no per-animation work)

Floor-`root` weights stripped from the eight auto-weighted bodies (`strip_root_weights.py`; `check_weights.py`
reports `on_root`), Seer/Tendril cloaks (`cloak_to_pelvis.py`), the Elf's pelvis/thigh frames
(`fix_leg_frames.py`). Every script's docstring has the measurement behind it; the order is in
[Scripts/TripoCrewBlender/README.md](../Scripts/TripoCrewBlender/README.md). The per-character Blender sources the
re-rigs start from are in the main checkout's untracked folder
`C:/Users/j6sis/SpaceSurvival/.agent/local/CharacterAssets/TripoCrew_Sources_20261008/` on this machine only - not in
Git.
