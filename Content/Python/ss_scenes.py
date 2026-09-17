"""Open Scene / Apply, editor side: rebuild the station's layout Blueprint from a recipe Blender wrote.

Blender's Apply (Tools/SSLiveLink/ss_live_link/scenes.py) writes Prefabs/Scenes/StationInterior.json and
calls apply_station_recipe(path) here over the live link. This is Scripts/AuthorStationEditableLayout.py
with --layout-recipe <path> --reset-layout, done inside the open editor: the same native call, the same
byte-for-byte backup of the saved Blueprint, the same receipt under .agent/local/StationVisualPass. That
script stays the headless route and is not changed; nothing is shared with it but the steps.

Three things differ, because this runs in an editor that stays open afterwards:
  - The recipe is checked here first. The layout library clears the Blueprint's components before it
    builds, so a recipe it refuses half way leaves a gutted Blueprint in memory. What it refuses
    (duplicate name, zero scale, a mesh or material that does not load, an empty material slot) is
    found before it is called, by name. Should it still refuse, its logged reason is read back from
    the editor log and the Blueprint is reloaded from disk.
  - The library reads a part's location/rotation/scale and ignores 'matrix'. Blender writes both, but a
    part that has only a matrix (a prefab opened as the station, a hand edit) would land at the origin,
    so such parts are given the three fields before the recipe is handed over.
  - The Blueprint is already loaded, with the last build's components in it. The library only unhooks
    those, so their names stay taken and a part that kept its name comes back renumbered; here they
    are deleted first the way the Blueprint editor deletes a component (_clear_components).

The flight lane is checked here as well as in Blender, by the same rule and from the same file
(Tools/SSLiveLink/context/station_interior.json): a recipe edited by hand, or applied from a command
line, never went through Blender's Apply.

apply_station_recipe(path, target=...) builds a copy of the layout somewhere else and leaves the owner's
Blueprint file alone; Scripts/TestSendScenes.py applies the real recipe that way. Such a target must be a
free path, or an earlier copy of the layout: no other asset is ever replaced by one.

The recipe is not the layout's only writer. The Station Workshop's Save + Apply rebuilds the same
Blueprint, and docs/STATION_EDITING.md lets the owner compose in the Blueprint editor. Neither shows up in
Blender, which opens the recipe and never the Blueprint, so before the layout is rebuilt its saved file is
compared with the one the newest receipt recorded: when something else has saved it since, the apply is
refused until it is asked for again with force=True (Blender's Apply Anyway). Unsaved changes in an open
Blueprint editor are refused the same way.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil
import time
import uuid

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
PACKAGE = '/Game/SpaceSurvival/Licensed/StationVisualPass/BP_StationVisualLayout'
RECEIPTS = ROOT / '.agent' / 'local' / 'StationVisualPass'
RULES = ROOT / 'Tools' / 'SSLiveLink' / 'context' / 'station_interior.json'   # 'rules' -> 'flight_lane'; Blender reads the same file
LANE_EPSILON = 0.01   # cm, as in the add-on's scenes.py: a part set exactly against the lane is not in it
LAYOUT_PARENT = 'SSStationVisualLayout'          # the native class every layout Blueprint derives from
STALE = 'layout changed outside a recipe'        # how the refusal that force=True overrides begins; the add-on's scenes.py looks for it


def _log(msg):
    u.log(f'SSScenes: {msg}')


def _exists(path):
    """Asked before load_asset: loading a path that is not there costs an error line in the log for every such part."""
    try:
        return u.EditorAssetLibrary.does_asset_exist(path)
    except Exception:
        return False


# ---------------------------------------------------------------- the recipe, made ready
def _rows_from_part(part):
    """Unreal matrix rows from location/rotation[pitch, yaw, roll]/scale: FScaleRotationTranslationMatrix."""
    loc, rot = part.get('location', [0, 0, 0]), part.get('rotation', [0, 0, 0])
    scale = part.get('scale', [1, 1, 1])
    scale = list(scale) if isinstance(scale, (list, tuple)) else [scale] * 3
    pitch, yaw, roll = (math.radians(v) for v in rot)
    sp, cp, sy, cy, sr, cr = math.sin(pitch), math.cos(pitch), math.sin(yaw), math.cos(yaw), math.sin(roll), math.cos(roll)
    rows = [[cp * cy, cp * sy, sp], [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp],
            [-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp]]
    return [[v * scale[i] for v in rows[i]] for i in range(3)] + [list(loc)]


def _decompose(rows):
    """(location, [pitch, yaw, roll], scale) from matrix rows, as FTransform::SetFromMatrix and
    FMatrix::Rotator do it; None for a matrix with a zero axis."""
    a, b, c = ([float(v) for v in rows[i][:3]] for i in range(3))
    scale = [math.sqrt(sum(v * v for v in axis)) for axis in (a, b, c)]
    if min(scale) <= 1e-8:
        return None
    if a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0]) < 0.0:
        scale[0] = -scale[0]   # a mirror goes into the X scale
    x, y, z = ([v / scale[i] for v in axis] for i, axis in enumerate((a, b, c)))
    pitch = math.atan2(x[2], math.hypot(x[0], x[1]))
    yaw = math.atan2(x[1], x[0])
    side = (-math.sin(yaw), math.cos(yaw))   # the Y axis before any roll
    roll = math.atan2(z[0] * side[0] + z[1] * side[1], y[0] * side[0] + y[1] * side[1])
    return ([float(v) for v in rows[3][:3]], [math.degrees(v) + 0.0 for v in (pitch, yaw, roll)], scale)


def _matrix_ok(rows):
    return (isinstance(rows, (list, tuple)) and len(rows) == 4
            and all(isinstance(r, (list, tuple)) and len(r) >= 3 and _numbers(list(r[:3])) for r in rows))


def fill_transforms(recipe):
    """Give matrix-only parts the location/rotation/scale the layout library reads. Returns how many
    were filled, and the names of parts whose two forms disagree (the library's form wins; it is said).
    A part whose matrix or numbers cannot be read is left as it is, for check_recipe to name."""
    filled, disagree = 0, []
    rows = recipe.get('static_meshes', []) if isinstance(recipe, dict) else []
    for part in rows if isinstance(rows, list) else []:
        if not isinstance(part, dict) or 'matrix' not in part or not _matrix_ok(part['matrix']):
            continue
        if 'location' not in part and 'rotation' not in part and 'scale' not in part:
            parts = _decompose(part['matrix'])
            if parts:
                part['location'], part['rotation'], part['scale'] = parts
                filled += 1
            continue
        if not all(_numbers(part.get(key, [0, 0, 0])) for key in ('location', 'rotation', 'scale')):
            continue
        theirs, ours = part['matrix'], _rows_from_part(part)
        if any(abs(float(theirs[i][j]) - ours[i][j]) > (0.05 if i == 3 else 1e-3) for i in range(4) for j in range(3)):
            disagree.append(part.get('name', '?'))
    return filled, disagree


def _numbers(values, count=3):
    return (isinstance(values, (list, tuple)) and len(values) == count
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values))


def lane_rules():
    """The flight lane from the context file Blender shows and checks against, or None when it is not there."""
    try:
        lane = json.loads(RULES.read_text(encoding='utf-8'))['rules']['flight_lane']
        return lane if _numbers(lane['min']) and _numbers(lane['max']) else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def part_bounds(part, mesh):
    """(lo, hi): the part's bounds in station space, the mesh's measured box carried through its transform.
    The generator's rule (Scripts/PrepareStationPitStopLayout.py) for any rotation, and the add-on's."""
    rows = part['matrix'] if 'location' not in part and _matrix_ok(part.get('matrix')) else _rows_from_part(part)
    b = mesh.get_bounds()
    o, e = (b.origin.x, b.origin.y, b.origin.z), (b.box_extent.x, b.box_extent.y, b.box_extent.z)
    centre = [sum(o[k] * rows[k][i] for k in range(3)) + rows[3][i] for i in range(3)]
    half = [sum(abs(rows[k][i]) * e[k] for k in range(3)) for i in range(3)]
    return [centre[i] - half[i] for i in range(3)], [centre[i] + half[i] for i in range(3)]


def in_lane(lo, hi, lane):
    """The generator's overlap test, with the floor panel exception; scenes.py in the add-on has the same."""
    floor = lane.get('floor_top_z')
    if floor is not None and hi[2] <= floor + lane.get('floor_tolerance', 0.0):
        return False
    return all(lo[i] < lane['max'][i] - LANE_EPSILON and hi[i] > lane['min'][i] + LANE_EPSILON for i in range(3))


def _lane_reason(name, lo, hi, lane):
    box = ', '.join(f'{axis} {lo[i]:.0f}..{hi[i]:.0f}' for i, axis in enumerate('XYZ'))
    keep = ', '.join(f'{axis} {lane["min"][i]:g}..{lane["max"][i]:g}' for i, axis in enumerate('XYZ'))
    return (f"'{name}': in the flight lane (its bounds {box} reach into {keep}, which a docking ship flies): "
            f"move it out to the side, or above Z {lane['max'][2]:g}")


def check_recipe(recipe, lane='file'):
    """Every reason this recipe must not be built, as sentences naming the part. Empty when there is none.

    The layout library's own rules (Source/SpaceSurvival/Private/SSStationVisualLayout.cpp): names are
    compared without case, across meshes and lights alike; a transform needs finite numbers and no zero
    scale; the mesh must load; an override must name a slot the mesh has and a material that loads; a
    slot left to the mesh must not be empty. Names the library harvests from the native station
    (Shell_..., BayLight_n, the staff) are not known here and are left to it.

    And one rule the library does not know: no part's bounds may reach into the flight lane. lane is the
    rule as a dict, None for no such check, or 'file' (the default) for what lane_rules() reads.
    """
    if lane == 'file':
        lane = lane_rules()
    problems, names, meshes = [], set(), {}
    if not isinstance(recipe, dict):
        return ['the recipe is not a JSON object']
    if isinstance(recipe.get('static_meshes', []), list) and not recipe.get('static_meshes'):
        # The layout library takes '{}' and builds the native shell alone: a hangar with no dressing, saved over the
        # owner's. Nothing that writes recipes means that; a scene emptied by mistake, or the wrong file, does.
        problems.append('the recipe has no parts (static_meshes is empty): an empty station layout is never built')
    for kind, key in (('part', 'static_meshes'), ('light', 'point_lights')):
        rows = recipe.get(key, [])
        if not isinstance(rows, list):
            problems.append(f'{key} is not a list')
            continue
        for place, row in enumerate(rows):
            if not isinstance(row, dict):
                problems.append(f'{kind} {place} of {key} is not an object')
                continue
            name = str(row.get('name') or '')
            if not name:
                problems.append(f'{kind} {place} of {key} has no name')
                name = f'{kind} {place}'
            elif name.lower() in names:
                problems.append(f"'{name}': duplicate name (names are compared without case, parts and lights together)")
            names.add(name.lower())
            sound = True
            for field in ('location', 'rotation', 'scale'):
                if field in row and not _numbers(row[field]):
                    problems.append(f"'{name}': {field} is {row[field]!r}, not three finite numbers")
                    sound = False
            if _numbers(row.get('scale', [1, 1, 1])) and min(abs(v) for v in row.get('scale', [1, 1, 1])) <= 1e-8:
                problems.append(f"'{name}': zero scale")
                sound = False
            if kind == 'light':
                for field in ('intensity', 'attenuation_radius'):
                    if not _numbers([row.get(field)], 1):
                        problems.append(f"'{name}': {field} is {row.get(field)!r}, not a number")
                if 'color' in row and not _numbers(row['color']):
                    problems.append(f"'{name}': color is {row['color']!r}, not three finite numbers")
                continue
            if 'matrix' in row and 'location' not in row and not (_matrix_ok(row['matrix']) and _decompose(row['matrix'])):
                # The layout library reads location/rotation/scale alone; fill_transforms derives them from a sound matrix.
                problems.append(f"'{name}': its matrix is not four rows of finite numbers with three axes of some length, "
                                f"and it has no location/rotation/scale")
                sound = False
            asset = row.get('asset', '')
            if not isinstance(asset, str) or not asset:
                problems.append(f"'{name}': no asset path")
                continue
            if asset not in meshes:
                meshes[asset] = _load(asset, u.StaticMesh)
            mesh = meshes[asset]
            if mesh is None:
                problems.append(f"'{name}': mesh {asset!r} did not load (is the path right, and the pack in the project?)")
                continue
            slots = len(list(mesh.get_editor_property('static_materials')))
            overrides = row.get('materials') or []
            if not isinstance(overrides, list):
                problems.append(f"'{name}': materials is not a list")
                overrides = []
            if len(overrides) > slots:
                problems.append(f"'{name}': overrides material slot {slots}, which {mesh.get_name()} lacks")
            for slot in range(slots):
                if slot < len(overrides):
                    if _load(overrides[slot], u.MaterialInterface) is None:
                        problems.append(f"'{name}': material {overrides[slot]!r} for slot {slot} did not load")
                elif mesh.get_material(slot) is None:
                    problems.append(f"'{name}': material slot {slot} of {mesh.get_name()} is empty and the part names no material for it")
            if lane and sound:
                lo, hi = part_bounds(row, mesh)
                if in_lane(lo, hi, lane):
                    problems.append(_lane_reason(name, lo, hi, lane))
    return problems


def _load(path, cls):
    try:
        asset = u.load_asset(path) if path and isinstance(path, str) and _exists(path) else None
    except Exception:
        asset = None
    return asset if asset is not None and isinstance(asset, cls) else None


# ---------------------------------------------------------------- when the library still says no
def _log_sizes():
    try:
        # project_log_dir() is relative to the engine's binaries; made absolute, it holds wherever the process stands.
        logs = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_log_dir()))
        return {p: p.stat().st_size for p in logs.glob('*.log')}
    except Exception:
        return {}


def _logged_reasons(before, wait=1.5):
    """The errors the layout library logged since 'before' was taken. Its only way of saying why is
    UE_LOG, and the log file is written from another thread, so this waits a moment for the lines."""
    deadline = time.time() + wait
    while True:
        reasons = []
        for path, size in _log_sizes().items():
            start = before.get(path, 0)
            if size <= start:
                continue
            try:
                with open(path, 'rb') as f:
                    f.seek(start)
                    text = f.read().decode('utf-8', errors='replace')
            except OSError:
                continue
            for line in text.splitlines():
                if 'Error:' in line and 'tation layout' in line:
                    reasons.append(line.split('Error:', 1)[1].strip())
        if reasons or time.time() >= deadline:
            return reasons
        time.sleep(0.1)


def _reload_from_disk(package=PACKAGE):
    """Drop the rebuilt Blueprint from memory, so it is neither shown nor saved by accident."""
    try:
        loaded = u.find_package(package) or u.load_package(package)
        # Left to itself the engine asks first ('... have been modified. Would you like to reload?'): a dialog in the
        # middle of Blender's call in the open editor, and a silent No in a commandlet. The answer here is always yes.
        mode = getattr(u, 'ReloadPackagesInteractionMode', None)
        ok = u.EditorLoadingAndSavingUtils.reload_packages([loaded], mode.ASSUME_POSITIVE) if mode else \
            u.EditorLoadingAndSavingUtils.reload_packages([loaded])
        return bool(ok[0] if isinstance(ok, tuple) else ok)
    except Exception as e:
        u.log_warning(f'SSScenes: could not reload {package} ({e})')
        return False


def _clear_components(blueprint):
    """Delete the layout's components as the Blueprint editor's Delete does, before the library rebuilds them.
    Returns how many went.

    The library takes the old nodes out of the construction script and no more, which leaves their
    templates and variables holding their names; every part that kept its name would then come back
    renumbered ('Deck_00_00' as 'Deck_00_08'), and docs/STATION_EDITING.md promises that recipe names
    are the component names. The editor's own delete frees a name properly. Its undo record is dropped:
    undoing half of a rebuild would put the old components back beside the new ones.
    """
    subobjects = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    about = u.SubobjectDataBlueprintFunctionLibrary
    handles = subobjects.k2_gather_subobject_data_for_blueprint(blueprint)
    doomed = []
    for handle in handles:
        data = subobjects.k2_find_subobject_data_from_handle(handle)
        data = data[-1] if isinstance(data, tuple) else data
        if about.can_delete(data) and not about.is_inherited_component(data):
            doomed.append(handle)
    if not doomed:
        return 0
    index = u.SystemLibrary.begin_transaction('SSScenes', 'Rebuild station layout', None)
    try:
        return subobjects.delete_subobjects(handles[0], doomed, blueprint)
    finally:
        if index >= 0:
            u.SystemLibrary.cancel_transaction(index)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _disk(package):
    return ROOT / 'Content' / (package[len('/Game/'):] + '.uasset')


def last_authored_sha(package=PACKAGE, receipts=None):
    """The sha256 the newest receipt about package recorded for its saved file; None when no receipt is about it.

    Every build of the layout from a recipe, here or in Scripts/AuthorStationEditableLayout.py, leaves
    EditableLayout-<id>/Authoring.json with the 'sha256' of the file it saved.
    """
    newest = None
    for path in (receipts or RECEIPTS).glob('EditableLayout-*/Authoring.json'):
        try:
            when, data = path.stat().st_mtime, json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and str(data.get('blueprint', '')).lower() == package.lower() and data.get('sha256') \
                and (newest is None or when > newest[0]):
            newest = (when, data['sha256'])
    return newest[1] if newest else None


def changed_outside_recipe(package=PACKAGE, receipts=None):
    """'' while the saved layout is the file the last recipe build left, else the refusal, which begins with STALE."""
    disk = _disk(package)
    if not disk.is_file():
        return ''
    name = package.rsplit('/', 1)[-1]
    if _dirty(package):
        return (f'{STALE}: {name} has unsaved changes in the open editor, which a rebuild would discard. Save or close the Blueprint '
                f'first; or apply anyway (Apply Anyway in Blender, force=True here) to replace them with the recipe')
    known = last_authored_sha(package, receipts)
    if known is not None and known == _sha256(disk):
        return ''
    how = ('no receipt says a recipe built it' if known is None else
           'its saved file is not the one the last recipe build left: the Station Workshop\'s Save + Apply, or a save in the Blueprint '
           'editor, has changed it since')
    return (f'{STALE}: {name}: {how}. Those changes are not in the recipe, and rebuilding replaces them. Apply anyway (Apply Anyway in '
            f'Blender, force=True here) to do that; the Blueprint as it is now is backed up first')


def _dirty(package):
    try:
        return any(str(pkg.get_name()) == package for pkg in u.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    except Exception:
        return False


def _layout_blueprint(package):
    """True when the asset at package is a Blueprint of the station layout class: the only thing a copy may replace."""
    try:
        asset = u.EditorAssetLibrary.load_asset(package)
        if not isinstance(asset, u.Blueprint):
            return False
        audit = json.loads(u.SSStationLayoutAuthoringLibrary.describe_station_visual_layout(asset))
        return str(audit.get('parent', '')).endswith(LAYOUT_PARENT)
    except Exception:
        return False


# ---------------------------------------------------------------- apply
def apply_station_recipe(path, target=None, force=False):
    """Rebuild BP_StationVisualLayout from the recipe at path, save it, and write a receipt.

    Returns {'components': n, 'blueprint': package, ...}; raises RuntimeError saying why when the recipe
    is refused. The previous saved Blueprint is copied into the receipt folder first, as the author
    script does for --reset-layout.

    force rebuilds a layout that something other than a recipe has changed since the last build (see
    changed_outside_recipe); without it that is refused, because the rebuild discards those changes.

    target, a /Game package other than the layout's own, builds a copy there and leaves the owner's
    Blueprint file as it is: for a look at a recipe before it replaces the layout, and for
    Scripts/TestSendScenes.py. The layout library knows one package only (LayoutPackage, compiled in), so
    the recipe is still built into BP_StationVisualLayout in memory; that is duplicated to target, the
    duplicate is saved, and the layout is reloaded from its untouched file and never saved. The result's
    'layout_reloaded' says whether that reload took. A copy may only go to a path that is free, or over an
    earlier copy (a Blueprint of the layout class): never over any other asset.
    """
    target = str(target or PACKAGE).split('.')[0]
    if target.lower() == PACKAGE.lower():
        target = PACKAGE   # Unreal's paths ignore case: '.../bp_stationvisuallayout' is the owner's layout, not a copy of it
    scratch = target != PACKAGE
    if not target.startswith('/Game/') or target.endswith('/'):
        raise RuntimeError(f'not a /Game package: {target}')
    recipe_path = Path(path)
    if not recipe_path.is_file():
        raise RuntimeError(f'no recipe at {recipe_path}')
    recipe_text = recipe_path.read_text(encoding='utf-8-sig')
    try:
        recipe = json.loads(recipe_text)
    except ValueError as e:
        raise RuntimeError(f'{recipe_path.name} is not JSON ({e}); Blueprint untouched')
    try:
        if u.get_editor_subsystem(u.LevelEditorSubsystem).is_in_play_in_editor():
            raise RuntimeError('stop Play before applying: the station in the running game is built from this Blueprint')
    except AttributeError:
        pass   # no level editor in a commandlet, and so no Play
    filled, disagree = fill_transforms(recipe)
    if filled:
        # Only then is the text changed; an untouched recipe is handed over byte for byte, so its hash is the file's.
        recipe_text = json.dumps(recipe)
        _log(f'{filled} matrix-only parts given location/rotation/scale for the layout library')
    if disagree:
        u.log_warning(f'SSScenes: {len(disagree)} parts carry a matrix that disagrees with their location/rotation/scale; '
                      f'the layout uses the latter: {", ".join(disagree[:8])}')
    problems = check_recipe(recipe)
    if problems:
        more = f' (and {len(problems) - 12} more)' if len(problems) > 12 else ''
        raise RuntimeError('recipe refused, Blueprint untouched: ' + '; '.join(problems[:12]) + more)

    lib = u.EditorAssetLibrary
    bridge = u.SSStationLayoutAuthoringLibrary
    layout_disk = _disk(PACKAGE)
    layout_before = _sha256(layout_disk) if layout_disk.is_file() else None
    existed = lib.does_asset_exist(target)
    disk = _disk(target)
    if existed and not disk.is_file():
        raise RuntimeError(f'save {target} before it is rebuilt: there is no saved file to back up')
    if scratch:
        if disk == layout_disk:   # path equality ignores case on Windows, as Unreal does: whatever the spelling, this is the owner's file
            raise RuntimeError(f'{target} is the owner layout itself, not a copy of it')
        if lib.does_asset_exist(PACKAGE) and not layout_disk.is_file():
            raise RuntimeError('save the owner layout first: building a copy goes through it in memory, and it is put back from its file')
        if _dirty(PACKAGE):
            raise RuntimeError('the owner layout has unsaved changes in the open editor: building a copy goes through it in memory and puts '
                               'it back from its file, which would discard them. Save or close the Blueprint first')
        if disk.is_file() and not existed:
            raise RuntimeError(f'{disk} exists but the editor does not know it yet: restart the editor, or choose another target')
        if existed and not _layout_blueprint(target):
            # The copy replaces what is at target (delete, then duplicate): only an earlier copy may be what is there.
            raise RuntimeError(f'{target} exists and is not a copy of the station layout: a copy is only built at a free path, '
                               f'or over an earlier copy')
    else:
        stale = changed_outside_recipe()
        if stale and not force:
            raise RuntimeError(stale)
        if stale:
            u.log_warning(f'SSScenes: applying anyway: {stale}')
    output = RECEIPTS / ('EditableLayout-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    # Said before anything is built, so whoever tidies receipts (Scripts/TestSendScenes.py) can tell whose a folder is
    # even when the build fails and no Authoring.json is written.
    (output / 'Request.json').write_text(json.dumps({'target': target, 'recipe': str(recipe_path), 'copy': scratch, 'forced': bool(force),
                                                     'started': time.strftime('%Y-%m-%d %H:%M:%S')}, indent=2) + '\n', encoding='utf-8')
    before = _sha256(disk) if disk.is_file() else None
    backup = None
    if disk.is_file():   # the file, not the registry's word for it: the layout library finds a package by its file, and so must the backup
        backup = output / disk.name
        shutil.copy2(disk, backup)
        if _sha256(backup) != before:
            raise RuntimeError(f'the backup at {backup} does not match the saved Blueprint; nothing was changed')
    layout_kept = None
    if scratch and layout_disk.is_file():
        # The copy is built through the owner's layout in memory, which is then put back from its file. Should that
        # reload fail and someone press Save All, this is the layout as it was.
        layout_kept = output / ('OwnerLayout-' + layout_disk.name)
        shutil.copy2(layout_disk, layout_kept)
        if _sha256(layout_kept) != layout_before:
            raise RuntimeError(f'the safety copy at {layout_kept} does not match the saved layout; nothing was changed')
    if lib.does_asset_exist(PACKAGE):
        old = lib.load_asset(PACKAGE)
        try:   # an open Blueprint editor would go on showing, and could save, the components about to be replaced
            u.get_editor_subsystem(u.AssetEditorSubsystem).close_all_editors_for_asset(old)
        except Exception:
            pass
        try:
            _clear_components(old)
        except Exception as e:  # the library clears the nodes itself; all that is lost is the names staying as written
            u.log_warning(f'SSScenes: old components not deleted first ({e}); parts that kept their name may come back renumbered')
        old = None
    sizes = _log_sizes()
    blueprint = bridge.create_station_visual_layout(recipe_text, True)
    audit = json.loads(bridge.describe_station_visual_layout(blueprint)) if blueprint else {}
    if not blueprint or not audit.get('compiled') or not audit.get('components'):
        reasons = _logged_reasons(sizes) or ['the layout library gave no reason; look for "Station layout" in the editor log']
        reloaded = layout_disk.is_file() and _reload_from_disk()
        state = ('The Blueprint was reloaded from disk.' if reloaded else
                 'The Blueprint in memory is half built: do not save it, and restart the editor.' if layout_disk.is_file() else '')
        raise RuntimeError('native station layout authoring failed: ' + '; '.join(r.rstrip('.') for r in reasons) + '. ' + state
                           + (f' The previous Blueprint is kept at {backup}.' if backup else ''))
    recipe_sha = hashlib.sha256(recipe_text.encode()).hexdigest()
    reloaded = None
    if scratch:
        try:
            if existed and not lib.delete_asset(target):
                raise RuntimeError(f'{target} could not be replaced; its previous file is kept at {backup}')
            built = lib.duplicate_loaded_asset(blueprint, target)
            if not built:
                raise RuntimeError(f'the layout was built but could not be duplicated to {target}')
            audit = json.loads(bridge.describe_station_visual_layout(built))
            if not audit.get('compiled') or not audit.get('components'):
                raise RuntimeError(f'the copy at {target} did not compile')
        finally:
            # Whatever happened to the copy, the layout itself goes back to what its file holds.
            blueprint = None
            reloaded = layout_disk.is_file() and _reload_from_disk()
            if not reloaded:
                u.log_warning(f'SSScenes: {PACKAGE} holds the rebuilt layout in memory, unsaved: do not save it; '
                              f'restart the editor to get the saved one back (the saved one is also kept at {layout_kept})')
        blueprint = built
    lib.set_metadata_tag(blueprint, 'SSStationLayoutInitialRecipeSHA256', recipe_sha)
    if not lib.save_loaded_asset(blueprint, only_if_is_dirty=False) or not disk.is_file():
        raise RuntimeError(f'the layout was rebuilt but {disk} did not save; the previous one is kept at {backup}')
    if scratch and layout_before != (_sha256(layout_disk) if layout_disk.is_file() else None):
        raise RuntimeError(f'{layout_disk} changed while a copy was built at {target}: that must never happen; '
                           f'compare it with the newest backup under {RECEIPTS}')
    components = len(audit.get('components', []))
    status = 'EDITABLE_LAYOUT_COPY_AUTHORED' if scratch else 'EDITABLE_LAYOUT_AUTHORED_RUNTIME_REVIEW_PENDING'
    result = dict(status=status, blueprint=target, file=str(disk), sha256=_sha256(disk), previous_sha256=before,
                  backup=str(backup) if backup else None, owner_layout_kept=str(layout_kept) if layout_kept else None,
                  forced=bool(force), recipe=str(recipe_path), recipe_sha256=recipe_sha,
                  native_audit=audit, engine=u.SystemLibrary.get_engine_version(), applied_by='ss_scenes.apply_station_recipe',
                  scope='Editable visual components; ASSStation retains collision, services and docking.')
    receipt = output / 'Authoring.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    u.log('STATION_EDITABLE_LAYOUT ' + json.dumps(dict(status=status, receipt=str(receipt), components=components)))
    out = {'components': components, 'blueprint': target, 'receipt': str(receipt), 'backup': str(backup) if backup else None}
    if scratch:
        out['layout_reloaded'] = bool(reloaded)
        out['owner_layout_kept'] = str(layout_kept) if layout_kept else None
    return out


def register():
    """Called by init_unreal.py at editor start, commandlets included. Nothing to set up: Blender calls
    apply_station_recipe over the live link, so this only says the module is there."""
    _log('ready: apply_station_recipe(path) rebuilds the station layout from a recipe Blender wrote')
