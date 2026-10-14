"""Photograph every character in the studio, animated, in play - for the OWNER to judge.

  set SS_STUDIO_OUT=<folder>            optional SS_STUDIO_WHO=Elf,Silver   SS_STUDIO_SHOTS=idle_front,walk_34
  optional SS_STUDIO_EXTRA=Pole,Dance   every Role clip whose name contains one of these gets its own shots
                                        (Pole: front at 15/50/85 % and a 3/4 at 50 %, frozen; others: front 40 %, 3/4 70 %)
  optional SS_STUDIO_POLE=1             a chrome pole on the origin, shown for the Pole shots only (pole_dance.py convention)
  SS_STUDIO_SHOTS=none                  skip the standard eleven and take only the extra shots
  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/CaptureStudio.py"

Spawns each character on the stage (hidden), starts Play in the studio level, views through Studio/Camera, and for
one character at a time unhides it, plays the clip, lets 45 frames pass and takes a HighResShot. The studio map is
never saved; the characters exist only in this run. Nothing here judges the pictures: the owner does.
"""
import hashlib
import json
import math
import os
import time
import traceback

import unreal as u

MAP = "/Game/SpaceSurvival/Licensed/CharacterStudio/L_CharacterStudio"
CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
HERO178 = "/Game/SpaceSurvival/Licensed/HeroReplacement178"
NAMES = ["Robe", "Glyph", "Tribal", "Ember", "Crest", "Olive", "Warden", "Dread", "Seer", "Tendril",
         "Abyss", "Violet", "Cyan", "Silver", "Crystal", "Finhead", "Amethyst", "Elf", "Cyborg", "Squirrel178"]
W, H = 1920, 1080
WARM = 45                 # frames before each shot: animation running, temporal AA settled
TARGET_LUMA = 135.0       # probe target: the EMPTY light-grey set, centre of frame, before any character (0-255)
LIB = u.EditorAssetLibrary
OUT = os.environ["SS_STUDIO_OUT"]
WHO = [w for w in os.environ.get("SS_STUDIO_WHO", "").split(",") if w]
ONLY = [s for s in os.environ.get("SS_STUDIO_SHOTS", "").split(",") if s]
EXTRA = [s for s in os.environ.get("SS_STUDIO_EXTRA", "").split(",") if s]
POLE = os.environ.get("SS_STUDIO_POLE") == "1"


def log(s):
    u.log_warning("STUDIOCAP| " + str(s))


def asset(path):
    return LIB.load_asset(path) if LIB.does_asset_exist(path) else None


def find(name):
    """Mesh + clips for one character: idle, walk and the first role clip (a dance for the dancers)."""
    if name == "Squirrel178":
        mesh = asset(HERO178 + "/SK_SquirrelHero178_RedStreaks")
        return mesh, {"idle": asset(HERO178 + "/A_Idle"), "walk": asset(HERO178 + "/A_Walk"), "role": asset(HERO178 + "/A_Run")}
    base = "%s/%s" % (CREW, name)

    def clip(*stems):                       # base clips sit beside the folders; the tentacle pair keeps theirs in Clips/
        for folder in ("", "/Clips"):
            for stem in stems:
                a = asset("%s%s/A_%s_%s" % (base, folder, name, stem))
                if a:
                    return a
        return None

    idle, walk = clip("Idle", "TentIdle"), clip("Walk", "TentCrawl")
    meshes = [m for m in (asset("%s/%s/SK_%s" % (base, f, name)) for f in ("Mesh", "Rig")) if m]
    # Some characters carry two mesh imports (Mesh/ and Rig/): take the one the clips were authored on.
    mesh = next((m for m in meshes if idle and m.skeleton == idle.get_editor_property("skeleton")), meshes[0] if meshes else None)
    role = None
    if LIB.does_directory_exist(base + "/Role"):
        roles = sorted(p.split(".")[0] for p in LIB.list_assets(base + "/Role", recursive=False, include_folder=False))
        dance = [p for p in roles if "Dance" in p]
        role = asset((dance or roles)[0]) if roles else None
    clips = {"idle": idle, "walk": walk, "role": role}
    if EXTRA and LIB.does_directory_exist(base + "/Role"):
        for p in sorted(LIB.list_assets(base + "/Role", recursive=False, include_folder=False)):
            short = p.split(".")[0].rsplit("/", 1)[1]
            if any(tag in short for tag in EXTRA):
                clips[short] = asset(p.split(".")[0])
    return mesh, clips


# (name, clip, azimuth deg from the front, target z as a fraction of height, framing fraction of height, fov[, time fraction])
# a 7th value freezes the clip at that fraction of its length for the shot; without it the clip plays through the warm-up
SHOTS = [("idle_front", "idle", 0, .50, .62, 35), ("idle_34", "idle", 40, .50, .62, 35), ("idle_side", "idle", 90, .50, .62, 35),
         ("idle_back", "idle", 180, .50, .62, 35), ("idle_legs", "idle", 20, .18, .26, 30), ("idle_head", "idle", 15, .86, .18, 30),
         ("walk_front", "walk", 10, .50, .62, 35), ("walk_34", "walk", 45, .50, .62, 35), ("walk_back", "walk", 170, .50, .62, 35),
         ("role_front", "role", 0, .50, .62, 35), ("role_34", "role", 45, .50, .62, 35)]
if ONLY:
    SHOTS = [s for s in SHOTS if s[0] in ONLY]


def extra_shots(clips):
    """Shots for the Role clips SS_STUDIO_EXTRA picked: a pole clip from the front at three times plus a 3/4, others two."""
    out = []
    for key in clips:
        if key in ("idle", "walk", "role") or clips[key] is None:
            continue
        short = key.split("_", 2)[-1]
        if "Pole" in key:
            out += [(short + "_f15", key, 0, .50, .62, 35, .15), (short + "_f50", key, 0, .50, .62, 35, .50),
                    (short + "_f85", key, 0, .50, .62, 35, .85), (short + "_q50", key, 40, .50, .62, 35, .50)]
        else:
            out += [(short + "_f40", key, 0, .50, .62, 35, .40), (short + "_q70", key, 40, .50, .62, 35, .70)]
    return out

os.makedirs(OUT, exist_ok=True)
lvl = u.get_editor_subsystem(u.LevelEditorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not editor.get_game_world(), "fresh process required"
assert lvl.load_level(MAP), "studio missing: run BuildStudio.py"
map_file = os.path.join(u.Paths.project_content_dir(), MAP[len("/Game/"):] + ".umap")
map_sha = hashlib.sha256(open(map_file, "rb").read()).hexdigest()
actors = u.get_editor_subsystem(u.EditorActorSubsystem)

chars = []
for name in (WHO or NAMES):
    mesh, clips = find(name)
    if not mesh:
        log("%s: no mesh, skipped" % name)
        continue
    a = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(0, 0, 0), u.Rotator(0, 0, 0))
    a.set_actor_label("Shot/" + name)
    c = a.skeletal_mesh_component
    c.set_skeletal_mesh_asset(mesh)
    c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    if clips["idle"]:
        c.set_editor_property("animation_data", u.SingleAnimationPlayData(anim_to_play=clips["idle"], saved_looping=True,
                                                                          saved_playing=True, saved_position=0.0, saved_play_rate=1.0))
    a.set_actor_hidden_in_game(True)
    b = mesh.get_bounds()
    chars.append({"name": name, "label": "Shot/" + name, "height": b.origin.z + b.box_extent.z, "clips": clips, "mesh": mesh.get_path_name(),
                  "clip_paths": {k: v.get_path_name() if v else None for k, v in clips.items()}, "shots": SHOTS + extra_shots(clips)})
if POLE:
    # pole_dance.py puts the pole on the clip origin: 2.5 cm radius, chrome (the Warden boot instance is grey, metallic 1)
    pole = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, 130), u.Rotator(0, 0, 0))
    pole.set_actor_label("Shot/Pole"); pole.set_mobility(u.ComponentMobility.MOVABLE)
    pole.static_mesh_component.set_static_mesh(LIB.load_asset("/Engine/BasicShapes/Cylinder"))
    pole.set_actor_scale3d(u.Vector(0.05, 0.05, 2.6))
    chrome = asset(CREW + "/Warden/Mat/MI_WardenBoot")
    if chrome:
        pole.static_mesh_component.set_material(0, chrome)
    pole.set_actor_hidden_in_game(True)
log("%d characters staged, %d shots" % (len(chars), sum(len(c["shots"]) for c in chars)))

report = {"map": MAP, "map_sha256": map_sha, "shots": [], "errors": [], "characters": [
    {k: c[k] for k in ("name", "height", "mesh", "clip_paths")} for c in chars]}
state = {"phase": "wait", "start": time.monotonic(), "ci": 0, "si": 0, "busy": False, "handle": None, "bias": 0.0,
         "probed": False, "frames": 0, "path": None, "stop_at": None}


def ch_shots(ci):
    return chars[ci]["shots"]


def camera_for(shot, height):
    _, _, az, tz, frac, fov = shot[:6]
    vfov = 2 * math.atan(math.tan(math.radians(fov) / 2) * H / W)
    dist = (frac * height) / math.tan(vfov / 2)
    a = math.radians(az)
    target = u.Vector(0, 0, tz * height)
    loc = u.Vector(math.sin(a) * dist, math.cos(a) * dist, target.z + 0.08 * dist)   # the crew face +Y: azimuth 0 is the front
    return loc, u.MathLibrary.find_look_at_rotation(loc, target), fov


def png_ready(path):
    if not os.path.isfile(path):
        return False
    data = open(path, "rb").read()
    return len(data) > 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[-8:-4] == b"IEND"


def centre_luma(path):
    """Mean luma of the middle third of the frame, from the PNG's raw rows (no PIL inside Unreal)."""
    import struct
    import zlib
    data = open(path, "rb").read()
    pos, idat, w, h, ct = 8, b"", 0, 0, 0
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]; typ = data[pos + 4:pos + 8]; body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, _, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
        pos += 12 + n
    bpp = {2: 3, 6: 4}[ct]
    raw = zlib.decompress(idat); stride = w * bpp + 1
    prev = bytearray(w * bpp); total = count = 0
    for y in range(h):
        f = raw[y * stride]; line = bytearray(raw[y * stride + 1:(y + 1) * stride])
        for i in range(len(line)):
            a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        if h // 3 <= y < 2 * h // 3:
            for x in range(w // 3, 2 * w // 3):
                r, g, bl = line[x * bpp], line[x * bpp + 1], line[x * bpp + 2]
                total += 0.299 * r + 0.587 * g + 0.114 * bl; count += 1
        prev = line
    return total / max(1, count)


def set_bias(bias):
    cam = state["cam"]; comp = cam.get_component_by_class(u.CameraComponent)
    pp = comp.get_editor_property("post_process_settings")
    pp.set_editor_property("override_auto_exposure_bias", True); pp.set_editor_property("auto_exposure_bias", bias)
    comp.set_editor_property("post_process_settings", pp); comp.set_editor_property("post_process_blend_weight", 1.0)
    state["bias"] = bias


def begin_shot():
    ch, shot = chars[state["ci"]], ch_shots(state["ci"])[state["si"]]
    clip = ch["clips"][shot[1]]
    if clip is None:                                   # no such clip for this character: skip the shot
        state["si"] += 1; return advance()
    a = state["pie"][ch["label"]]
    a.set_actor_hidden_in_game(False)
    comp = a.skeletal_mesh_component
    frozen = shot[6] if len(shot) > 6 else None
    if frozen is not None:
        comp.play_animation(clip, True); comp.set_position(frozen * clip.get_play_length(), False); comp.set_play_rate(0.0)
        state["playing"] = None
    elif comp.get_anim_instance() is None or state.get("playing") != (ch["name"], shot[1]):
        comp.play_animation(clip, True); comp.set_play_rate(1.0); state["playing"] = (ch["name"], shot[1])
    if state.get("pole"):
        state["pole"].set_actor_hidden_in_game("Pole" not in shot[1])
    loc, rot, fov = camera_for(shot, ch["height"])
    cam = state["cam"]; cam.set_actor_location_and_rotation(loc, rot, False, False); cam.get_component_by_class(u.CameraComponent).set_field_of_view(fov)
    state.update(phase="warm", frames=0, path=os.path.join(OUT, "%s_%s.png" % (ch["name"], shot[0])))
    return True


def advance():
    """Move to the next (character, shot); hide the finished character. Returns False when everything is done."""
    while state["ci"] < len(chars):
        if state["si"] >= len(ch_shots(state["ci"])):
            state["pie"][chars[state["ci"]]["label"]].set_actor_hidden_in_game(True)
            state["ci"] += 1; state["si"] = 0; state["playing"] = None
            continue
        return begin_shot()
    return False


def stop():
    if state["phase"] not in ("stop", "done"):
        state.update(phase="stop", stop_at=time.monotonic()); lvl.editor_request_end_play()


def finish():
    state["phase"] = "done"
    try:
        report["map_unchanged"] = hashlib.sha256(open(map_file, "rb").read()).hexdigest() == map_sha
        report["exposure_bias"] = state["bias"]
        report["status"] = "CAPTURED" if report["shots"] and not report["errors"] else "FAILED"
        json.dump(report, open(os.path.join(OUT, "capture.json"), "w"), indent=1)
        log("DONE %s: %d shots, bias %.2f, map unchanged %s -> %s" % (report["status"], len(report["shots"]), state["bias"], report["map_unchanged"], OUT))
    finally:
        u.unregister_slate_post_tick_callback(state["handle"])
        u.EditorPythonScripting.set_keep_python_script_alive(False); u.SystemLibrary.quit_editor()


def tick(dt):
    if state["busy"] or state["phase"] == "done":
        return
    state["busy"] = True
    try:
        now = time.monotonic()
        if state["phase"] == "stop":
            if not editor.get_game_world() or now - state["stop_at"] > 12:
                finish()
            return
        if now - state["start"] > 1500:
            raise RuntimeError("capture timeout")
        world = editor.get_game_world()
        if not world:
            if state["phase"] != "wait" or now - state["start"] > 120:
                raise RuntimeError("PIE world missing")
            return
        if state["phase"] == "wait":
            pc = u.GameplayStatics.get_player_controller(world, 0)
            if not pc:
                return
            pawn = u.GameplayStatics.get_player_pawn(world, 0)
            if pawn:
                pawn.set_actor_hidden_in_game(True); pawn.set_actor_location(u.Vector(0, 1500, 200), False, True)
            cams = [c for c in u.GameplayStatics.get_all_actors_of_class(world, u.CameraActor) if c.get_actor_label() == "Studio/Camera"]
            state["cam"] = cams[0]; state["pc"] = pc; state["world"] = world
            state["pie"] = {a.get_actor_label(): a for a in u.GameplayStatics.get_all_actors_of_class(world, u.SkeletalMeshActor)}
            state["pole"] = next((a for a in u.GameplayStatics.get_all_actors_of_class(world, u.StaticMeshActor) if a.get_actor_label() == "Shot/Pole"), None)
            pc.set_view_target_with_blend(state["cam"], 0.0, u.ViewTargetBlendFunction.VT_BLEND_LINEAR, 0.0, False)
            set_bias(0.0)
            # The sun, the sky cubemap and the floor's shaders come online at different times after Play starts;
            # a probe taken too early metered a half-lit stage (4.9 one run, 37 the next). Load textures fully and
            # keep probing the empty stage until two readings agree before trusting one.
            for cmd in ("r.TextureStreaming 0", "r.Streaming.FullyLoadUsedTextures 1"):
                u.SystemLibrary.execute_console_command(world, cmd, pc)
            u.GameplayStatics.set_game_paused(world, False)
            loc, rot, fov = camera_for(("probe", "idle", 0, .50, .62, 35), 178.0)   # the empty stage, standard framing
            state["cam"].set_actor_location_and_rotation(loc, rot, False, False)
            state["cam"].get_component_by_class(u.CameraComponent).set_field_of_view(fov)
            state.update(phase="probe", frames=0, path=os.path.join(OUT, "_probe.png"), probes=[])
            return
        state["frames"] += 1
        if state["phase"] in ("warm", "probe") and state["frames"] >= WARM:
            state["phase"] = "probe_capture" if state["phase"] == "probe" else "capture"
            u.SystemLibrary.execute_console_command(world, 'HighResShot %dx%d filename="%s"' % (W, H, state["path"]), state["pc"])
        elif state["phase"] == "probe_capture" and png_ready(state["path"]):
            luma = centre_luma(state["path"]); os.remove(state["path"])
            probes = state["probes"]; probes.append(luma)
            settled = len(probes) >= 2 and abs(probes[-1] - probes[-2]) <= 0.04 * max(probes[-1], 1.0)
            if not settled and len(probes) < 12:
                state.update(phase="probe", frames=0)
                return
            bias = max(-6.0, min(6.0, math.log2(TARGET_LUMA / max(1.0, luma))))
            log("empty-stage probes %s -> luma %.1f, exposure bias %.2f%s" % (
                [round(p, 1) for p in probes], luma, bias, "" if settled else " (NOT settled after 12 probes)"))
            report["probes"] = probes
            set_bias(bias)
            if not advance():
                stop()
        elif state["phase"] == "capture" and png_ready(state["path"]):
            ch, shot = chars[state["ci"]], ch_shots(state["ci"])[state["si"]]
            report["shots"].append({"character": ch["name"], "shot": shot[0], "clip": ch["clip_paths"][shot[1]], "png": state["path"]})
            state["si"] += 1
            if not advance():
                stop()
    except Exception:
        report["errors"].append(traceback.format_exc()); u.log_error(report["errors"][-1]); stop()
    finally:
        state["busy"] = False


u.EditorPythonScripting.set_keep_python_script_alive(True)
state["handle"] = u.register_slate_post_tick_callback(tick)
lvl.editor_request_begin_play()
