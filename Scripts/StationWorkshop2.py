"""Station Workshop v2 - build an editable workshop from the CURRENT layout, with controls.

Why this exists: OpenStationWorkshop hard-codes one map name and, if that map exists, loads it
"unchanged" and never rebuilds. The recipe pipeline writes BP_StationVisualLayout directly, so the
saved workshop silently fell 2,400 components behind the Blueprint - and Apply would have
overwritten the station with the stale copy. This rebuilds from whatever the Blueprint holds now,
under its own name, and never deletes anything.

Controls (call after `import StationWorkshop2 as w`):
    w.build()                      explode the live Blueprint into editable actors
    w.find("kiosk")                labels + positions matching a substring
    w.move("trophy_plinth_3", dz=40)   nudge one piece
    w.place("cargo_2", x=..,y=..,z=..) set an absolute position
    w.look(x, y, z, pitch, yaw)    capture the editor viewport from a pose -> png path
    w.stats()                      what is in the workshop right now
"""
import unreal, collections

LAYOUT = "/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout"
FOLDER = "Station Layout"


def _actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def build():
    """New blank map, spawn the live layout, explode every component into its own actor."""
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    bp = unreal.EditorAssetLibrary.load_asset(LAYOUT)
    if not bp:
        unreal.log_error("WS2: could not load %s" % LAYOUT)
        return 0
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    src = eas.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, 0, 0))
    if not src:
        unreal.log_error("WS2: could not spawn the layout")
        return 0
    made = 0
    for comp in src.get_components_by_class(unreal.SceneComponent):
        if comp == src.get_editor_property("root_component"):
            continue
        if not isinstance(comp, (unreal.StaticMeshComponent, unreal.PointLightComponent)):
            continue
        t = comp.get_world_transform()
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor
                                       if isinstance(comp, unreal.StaticMeshComponent)
                                       else unreal.PointLight, t.translation, t.rotation.rotator())
        if not a:
            continue
        a.set_actor_scale3d(t.scale3d)
        if isinstance(comp, unreal.StaticMeshComponent):
            smc = a.static_mesh_component
            smc.set_static_mesh(comp.static_mesh)
            for i in range(comp.get_num_materials()):
                smc.set_material(i, comp.get_material(i))
            smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        else:
            lc = a.light_component
            lc.set_mobility(unreal.ComponentMobility.MOVABLE)
            lc.set_intensity(comp.intensity)
            c = comp.light_color          # FColor 0-255; SetLightColor wants LinearColor
            lc.set_light_color(unreal.LinearColor(c.r / 255.0, c.g / 255.0,
                                                  c.b / 255.0, 1.0))
            lc.set_attenuation_radius(comp.attenuation_radius)
        a.set_actor_label(comp.get_name())
        a.set_folder_path(FOLDER)
        made += 1
    eas.destroy_actor(src)
    _exposure(eas)
    _environment(eas)
    unreal.log_warning("WS2: built %d editable pieces from the live Blueprint" % made)
    return made


def _environment(eas):
    """A blank map has no sun, no skylight and no atmosphere, so everything exterior reads pure
       black and every judgement about the outside is wrong. These match what the game's own
       Survival level and AuthorStationLarge put in: a cool key, a warm opposing fill at sane LUX,
       and a dim blue ambient. Editor-only - none of it is part of the layout."""
    for label, pitch, yaw, lux, col in (
            ("WS2 key", -38.0, 25.0, 18.0, (0.66, 0.76, 1.00)),
            ("WS2 fill", -22.0, 205.0, 6.0, (1.00, 0.74, 0.48))):
        d = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 4000),
                                       unreal.Rotator(0.0, pitch, yaw))
        lc = d.light_component
        lc.set_mobility(unreal.ComponentMobility.MOVABLE)
        lc.set_intensity(lux)
        lc.set_light_color(unreal.LinearColor(col[0], col[1], col[2], 1.0))
        d.set_actor_label(label)
    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 900))
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_intensity(0.22)
    sky.light_component.set_light_color(unreal.LinearColor(0.18, 0.26, 0.44, 1.0))
    sky.set_actor_label("WS2 ambient")
    eas.spawn_actor_from_class(unreal.SkyAtmosphere,
                               unreal.Vector(0, 0, 0)).set_actor_label("WS2 atmosphere")
    unreal.log_warning("WS2: added key/fill/ambient/atmosphere matching the game")


def _exposure(eas):
    """A blank map has no post-process volume, so auto-exposure runs wild and every capture
       comes back white. The game's Survival level has ReadableSpaceExposure doing this job;
       without a match here the workshop lies about the lighting."""
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    ppv.set_editor_property("unbound", True)
    st = ppv.get_editor_property("settings")
    st.set_editor_property("override_auto_exposure_method", True)
    st.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    st.set_editor_property("override_auto_exposure_bias", True)
    st.set_editor_property("auto_exposure_bias", 3.6)   # calibrated: 0 -> mean 10, 11 -> 88% clipped
    ppv.set_editor_property("settings", st)
    ppv.set_actor_label("WS2 exposure (matches the game, not exported)")
    unreal.log_warning("WS2: fixed manual exposure so captures are comparable")


def stats():
    c = collections.Counter()
    for a in _actors():
        if str(a.get_folder_path()) == FOLDER:
            c[a.get_actor_label().rstrip("0123456789_").split("_")[0]] += 1
    print("pieces:", sum(c.values()))
    for k, v in c.most_common(16):
        print("   %-24s %d" % (k, v))
    return sum(c.values())


def find(sub, limit=25):
    out = []
    for a in _actors():
        lbl = a.get_actor_label()
        if sub.lower() in lbl.lower():
            L = a.get_actor_location()
            out.append((lbl, round(L.x, 1), round(L.y, 1), round(L.z, 1)))
    for row in out[:limit]:
        print("   %-34s %9.1f %9.1f %8.1f" % row)
    print("   (%d matched)" % len(out))
    return out


def _one(label):
    for a in _actors():
        if a.get_actor_label() == label:
            return a
    print("no actor labelled", label)
    return None


def move(label, dx=0.0, dy=0.0, dz=0.0):
    a = _one(label)
    if not a:
        return
    L = a.get_actor_location()
    a.set_actor_location(unreal.Vector(L.x + dx, L.y + dy, L.z + dz), False, True)
    print("moved %s -> %s" % (label, a.get_actor_location()))


def place(label, x=None, y=None, z=None, yaw=None):
    a = _one(label)
    if not a:
        return
    L = a.get_actor_location()
    a.set_actor_location(unreal.Vector(x if x is not None else L.x,
                                       y if y is not None else L.y,
                                       z if z is not None else L.z), False, True)
    if yaw is not None:
        r = a.get_actor_rotation()
        a.set_actor_rotation(unreal.Rotator(r.roll, r.pitch, yaw), False)
    print("placed %s -> %s" % (label, a.get_actor_location()))


def look(x, y, z, pitch=-20.0, yaw=0.0, name="ws2_view"):
    """Point the EDITOR viewport and screenshot it. Works because the station is in the editor
       world here, not in PIE - which is what made every angle unreachable before."""
    les = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    les.set_level_viewport_camera_info(unreal.Vector(x, y, z), unreal.Rotator(0.0, pitch, yaw))
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name + ".png")
    print("captured", name)
