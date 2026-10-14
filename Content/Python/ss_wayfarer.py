"""Snapshot the current Wayfarer map for Blender, and safely apply selected placements.

Export never tags, rebuilds or saves the Unreal map. Native actor GUIDs identify direct
StaticMeshActors; Blueprint components, instances and streamed children are locked context.
Run export_scene(dry_run=True), inspect it, then export_scene(dry_run=False).
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import uuid

import unreal as u
import ss_prefabs

TARGET = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUTPUT = ROOT / 'Artifacts/WayfarerBlender'
REQUIRED_LEVELS = ('/Game/BuildingLibrary/Home/L_CrewApartment',)


def _guid(actor):
    guid = actor.get_editor_property('actor_guid')
    # UE5.8 KismetGuidLibrary exposes Conv_GuidToString as ScriptMethod ToString;
    # its implementation uses EGuidFormats::Digits. Guid fields are not Python attributes.
    value = guid.to_string().lower()
    if len(value) != 32 or any(character not in '0123456789abcdef' for character in value):
        raise ValueError('Unreal returned an invalid persistent actor GUID')
    return value if value != '0' * 32 else ''


def _world():
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    if levels.is_in_play_in_editor():
        raise RuntimeError('Stop Play before exporting or editing Wayfarer')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    current = world.get_path_name().split('.')[0]
    if current != TARGET:
        raise RuntimeError(f'Open {TARGET} first; current map is {current}')
    return world


def _direct(actor, world):
    return (actor.get_class().get_path_name() == '/Script/Engine.StaticMeshActor'
            and actor.get_outer().get_outer() == world and bool(_guid(actor)))


def _materials(component):
    return [material.get_path_name() if material else '' for material in component.get_materials()]


def _visibility(actor, component):
    actor_hidden = bool(actor.get_editor_property('hidden'))
    component_hidden = bool(component.get_editor_property('hidden_in_game'))
    component_visible = bool(component.get_editor_property('visible'))
    sky = ('OutpostRole:Sky' in [str(tag) for tag in actor.tags]
           or actor.get_actor_label() in ('Environment/Starfield', 'Sandbox stars'))
    reasons = [name for name, value in (('actor hidden in game', actor_hidden),
               ('component hidden in game', component_hidden), ('component not visible', not component_visible),
               ('sky shell', sky)) if value]
    return {'actor_hidden_in_game': actor_hidden, 'component_hidden_in_game': component_hidden,
            'component_visible': component_visible, 'sky_shell': sky,
            'hide_in_blender': bool(reasons), 'blender_hidden_reason': '; '.join(reasons)}


def _level_package(value):
    text = value.get_path_name() if hasattr(value, 'get_path_name') else str(value)
    text = text.split('.')[0]
    if text.startswith('/Temp/Game/'):
        text = text[len('/Temp'):]
    return re.sub(r'_LevelInstance_[0-9a-fA-F]{16}_0$', '', text)


def _streams(world):
    # UWorld.StreamingLevels is protected even through get_editor_property.
    # The public object iterator includes other worlds and class-default objects;
    # retain only actual LevelStreaming instances owned by this exact editor world.
    return [stream for stream in u.ObjectIterator(u.LevelStreaming)
            if isinstance(stream, u.LevelStreaming) and stream.get_outer() == world]


def _stream_package(stream):
    # PackageNameToLoad is protected in the Python wrapper. This public UFUNCTION
    # returns the editor's /Temp/Game/..._LevelInstance_<hash>_0 package instead.
    # Export is editor-only (_world rejects PIE), so normalize that known form.
    package = _level_package(stream.get_world_asset_package_f_name())
    if not package.startswith('/'):
        raise RuntimeError('Streaming level has no source package: ' + stream.get_path_name())
    return package


def level_readiness(instances, streams, required_levels=REQUIRED_LEVELS):
    """Pure gate: no missing/pending instance, and required apartment geometry is present."""
    pending = []
    packages = {row['package'] for row in instances}
    for required in required_levels:
        if required not in packages:
            pending.append(f'Required level instance absent or unresolved: {required}')
    for package in sorted(packages):
        expected = sum(row['package'] == package for row in instances)
        matched = [row for row in streams if row['package'] == package]
        ready = [row for row in matched if row['loaded'] and row['visible'] and not row['pending'] and row['mesh_placements'] > 0]
        if len(ready) < expected:
            pending.append(f'{package}: {len(ready)}/{expected} instances loaded with visible child mesh geometry')
    for row in streams:
        if row['pending']:
            pending.append(f'Streaming state pending: {row["package"]}')
    return pending


def _streaming_status(world, objects):
    # EditorActorSubsystem filters transient/uneditable LevelInstance children.
    actors = list(u.GameplayStatics.get_all_actors_of_class(world, u.Actor))
    instances, streams = [], []
    try:
        for actor in actors:
            if isinstance(actor, u.LevelInstance) and not isinstance(actor, getattr(u, 'PackedLevelActor', type(None))):
                instances.append({'name': actor.get_actor_label(), 'package': _level_package(actor.get_editor_property('world_asset'))})
        geometry = {}
        for row in objects:
            geometry[row['source_actor']] = geometry.get(row['source_actor'], 0) + 1
        for stream in _streams(world):
            level = stream.get_loaded_level()
            package = _stream_package(stream)
            children = [actor for actor in actors if actor.get_outer() == level] if level else []
            streams.append({'package': package, 'loaded': bool(stream.is_level_loaded()),
                            'visible': bool(stream.is_level_visible()), 'pending': bool(stream.is_streaming_state_pending()),
                            'child_actors': len(children), 'mesh_placements': sum(geometry.get(actor.get_path_name(), 0) for actor in children)})
        return {'instances': instances, 'streams': streams, 'pending': level_readiness(instances, streams)}
    except Exception as exc:
        return {'instances': instances, 'streams': streams, 'pending': ['Cannot verify loaded level instances: ' + str(exc)]}


def _state(actor):
    component = actor.static_mesh_component
    return {'guid': _guid(actor), 'asset': component.static_mesh.get_path_name(),
            'matrix': [[round(float(v), 5) for v in row] for row in ss_prefabs.matrix_rows(actor.get_actor_transform())],
            'materials': _materials(component), 'name': actor.get_actor_label(),
            'parent': actor.get_attach_parent_actor().get_path_name() if actor.get_attach_parent_actor() else ''}


def state_digest(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def checked_matrix(rows):
    if not isinstance(rows, list) or len(rows) != 4 or any(not isinstance(r, list) or len(r) != 4 for r in rows):
        raise ValueError('Placement matrix must be 4 by 4')
    values = [[float(v) for v in row] for row in rows]
    if not all(math.isfinite(v) for row in values for v in row):
        raise ValueError('Placement matrix contains non-finite values')
    axes = [row[:3] for row in values[:3]]
    lengths = [math.sqrt(sum(v * v for v in axis)) for axis in axes]
    if min(lengths) < 1e-6 or any(abs(values[i][3]) > 1e-6 for i in range(3)) or abs(values[3][3] - 1) > 1e-6:
        raise ValueError('Placement has a flat scale or invalid affine matrix')
    for a, b in ((0, 1), (0, 2), (1, 2)):
        if abs(sum(x * y for x, y in zip(axes[a], axes[b]))) > lengths[a] * lengths[b] * 1e-4:
            raise ValueError('Placement is skewed; apply its parent/scale before pushing')
    return values


def preflight(payload, snapshot, current, project_root, target_map):
    """Pure validation: reject the entire request before any actor/material mutation."""
    if payload.get('target_map') != target_map or snapshot.get('target_map') != target_map:
        raise ValueError('Wayfarer destination map does not match')
    if Path(payload.get('project_root', '')).resolve() != Path(project_root).resolve() or Path(snapshot['project_root']).resolve() != Path(project_root).resolve():
        raise ValueError('Wayfarer belongs to another project checkout; export it again from this editor')
    if payload.get('snapshot_id') != snapshot.get('snapshot_id'):
        raise ValueError('Wayfarer snapshot identity does not match')
    if payload.get('remove'):
        raise ValueError('Delete Wayfarer actors in Unreal; Blender Push never deletes existing actors')
    seen, links = set(), set()
    for row in payload.get('objects', []):
        checked_matrix(row.get('matrix'))
        link = row.get('link')
        if not link or link in links:
            raise ValueError('Every placement must have a distinct link identity')
        links.add(link)
        guid = row.get('guid')
        if guid:
            if guid in seen:
                raise ValueError('Two placements share an Unreal actor identity; add a new part from the library')
            seen.add(guid)
            live = current.get(guid)
            if live is None:
                raise ValueError(f'Original Unreal actor is missing or no longer editable: {row.get("name", guid)}')
            if row.get('base') != state_digest(live):
                raise ValueError(f'Unreal changed after this placement was loaded: {row.get("name", guid)}; open a fresh snapshot')
            if row.get('asset') != live['asset']:
                raise ValueError('Push cannot replace an existing Wayfarer mesh; edit its asset explicitly in Unreal')
        elif row.get('new') is not True:
            raise ValueError('A placement has no original actor identity and was not marked as new')
    return True


def _collect(world):
    objects, omitted, failures = [], [], []
    actors = list(u.GameplayStatics.get_all_actors_of_class(world, u.Actor))
    for actor in actors:
        direct = _direct(actor, world)
        emitted = 0
        components = list(actor.get_components_by_class(u.StaticMeshComponent))
        for component in components:
            mesh = component.static_mesh
            if not mesh:
                continue
            instance = isinstance(component, u.InstancedStaticMeshComponent)
            count = component.get_instance_count() if instance else 1
            for index in range(count):
                transform = component.get_instance_transform(index, world_space=True) if instance else component.get_world_transform()
                if transform is None:
                    failures.append(component.get_path_name() + ':' + str(index))
                    continue
                editable = direct and component == actor.static_mesh_component and not instance
                row = {'name': actor.get_actor_label() + (f' / {component.get_name()} [{index}]' if instance else ''),
                       'asset': mesh.get_path_name(), 'matrix': ss_prefabs.matrix_rows(transform),
                       'materials': _materials(component), 'editable': editable,
                       'source_actor': actor.get_path_name(), 'source_component': component.get_path_name(),
                       'area': str(actor.get_folder_path()) or 'Wayfarer'}
                row.update(_visibility(actor, component))
                if editable:
                    state = _state(actor)
                    row.update(guid=state['guid'], base=state_digest(state), matrix=state['matrix'], name=state['name'])
                else:
                    row['context_reason'] = 'Unreal Blueprint/component/instance or streamed level'
                objects.append(row)
                emitted += 1
        # Skeletal assets are exported in their reference pose as locked geometry.
        for component in actor.get_components_by_class(u.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            if mesh:
                row = {'name': actor.get_actor_label() + ' (reference pose)', 'asset': mesh.get_path_name(),
                                'matrix': ss_prefabs.matrix_rows(component.get_world_transform()),
                                'materials': _materials(component), 'editable': False,
                                'source_actor': actor.get_path_name(), 'source_component': component.get_path_name(),
                                'area': str(actor.get_folder_path()) or 'Wayfarer', 'context_reason': 'Skeletal reference pose; animation stays in Unreal'}
                row.update(_visibility(actor, component))
                objects.append(row)
                emitted += 1
        if not emitted:
            omitted.append({'name': actor.get_actor_label(), 'class': actor.get_class().get_path_name(), 'path': actor.get_path_name()})
    return objects, omitted, failures, len(actors)


def export_scene(dry_run=True):
    """Export the loaded current map, including loaded LevelInstance children; never load/save a level.

    The caller must let streamed levels finish loading first. Counts and non-mesh actors
    are recorded, so an unloaded level or unsupported presentation is never hidden.
    """
    world = _world()
    objects, omitted, failures, actor_count = _collect(world)
    streaming = _streaming_status(world, objects)
    summary = {'target_map': TARGET, 'actors': actor_count, 'placements': len(objects),
               'editable': sum(row['editable'] for row in objects),
               'locked': sum(not row['editable'] for row in objects), 'non_mesh_actors': len(omitted),
               'geometry_failures': failures, 'streaming': streaming,
               'hidden_in_blender': sum(row['hide_in_blender'] for row in objects), 'dry_run': dry_run}
    if dry_run:
        return summary
    if failures or not objects or streaming['pending']:
        raise RuntimeError('Map geometry is incomplete; inspect export_scene(dry_run=True)')
    snapshot_id = uuid.uuid4().hex
    folder = OUTPUT / 'Snapshots' / snapshot_id
    folder.mkdir(parents=True)
    entries = {row['asset']: dict(row) for row in (ss_prefabs.load_catalog() or {}).get('meshes', [])}
    required = sorted({row['asset'] for row in objects})
    proxies = {}
    for asset in required:
        entry = entries.get(asset, {})
        proxy = ss_prefabs.LIBRARY / entry.get('proxy', '')
        fresh = entry.get('source_stamp') == ss_prefabs._source_stamp(asset) if asset.startswith('/Game/') else False
        if not proxy.is_file() or not fresh:
            mesh = u.load_asset(asset)
            proxy = folder / 'proxies' / (hashlib.sha256(asset.encode()).hexdigest()[:24] + '.glb')
            if not mesh or not ss_prefabs.export_proxy(mesh, proxy):
                raise RuntimeError(f'No real mesh proxy for {asset}; incomplete snapshot kept at {folder}')
        proxies[asset] = str(proxy.resolve())
    result = dict(summary, schema_version=1, snapshot_id=snapshot_id, project_root=str(ROOT),
                  generated=datetime.now(timezone.utc).isoformat(), objects=objects, proxies=proxies, non_mesh=omitted)
    path = folder / 'scene.json'
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    latest = OUTPUT / 'latest.json'
    pending = latest.with_suffix('.pending.json')
    pending.write_text(json.dumps({'scene': str(path), 'snapshot_id': snapshot_id}, indent=2), encoding='utf-8')
    pending.replace(latest)
    return dict(summary, snapshot=str(path), snapshot_id=snapshot_id)


def apply_edits(payload, dry_run=True):
    """Preflight selected transforms/materials, then make one undoable edit; never save the map."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    world = _world()
    ident = payload.get('snapshot_id', '')
    if len(ident) != 32 or any(ch not in '0123456789abcdef' for ch in ident):
        raise ValueError('Invalid Wayfarer snapshot identity')
    path = OUTPUT / 'Snapshots' / ident / 'scene.json'
    snapshot = json.loads(path.read_text(encoding='utf-8'))
    actors = {}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if _direct(actor, world) and actor.static_mesh_component.static_mesh:
            guid = _guid(actor)
            if guid in actors:
                raise RuntimeError('Duplicate native actor GUID; do not apply this snapshot')
            actors[guid] = actor
    current = {guid: _state(actor) for guid, actor in actors.items()}
    preflight(payload, snapshot, current, ROOT, TARGET)
    import ss_surfaces
    plans = []
    for row in payload.get('objects', []):
        mesh = u.load_asset(row['asset'])
        if not isinstance(mesh, u.StaticMesh):
            raise ValueError('Only static meshes can be placed or moved')
        count = len(mesh.static_materials)
        if len(row.get('materials', [])) > count:
            raise ValueError('Too many material slots')
        for material in row.get('materials', []):
            if material and not isinstance(u.load_asset(material), u.MaterialInterface):
                raise ValueError(f'Material cannot be loaded: {material}')
        for slot, values in row.get('surface_overrides', {}).items():
            if not 0 <= int(slot) < count:
                raise ValueError('Invalid surface slot')
            ss_surfaces.checked(values)
        plans.append((row, ss_prefabs.transform_from_rows(row['matrix'])))
    if dry_run:
        return {'dry_run': True, 'moved': sum(bool(row.get('guid')) for row, _ in plans),
                'created': sum(not row.get('guid') for row, _ in plans), 'removed': 0, 'errors': []}
    resolved = ss_surfaces.resolve_rows([row for row, _ in plans])
    receipts, rollback, created = [], [], []
    with u.ScopedEditorTransaction('SS Link: selected Wayfarer placements'):
        try:
            for (original, transform), row in zip(plans, resolved):
                actor = actors.get(row.get('guid'))
                if actor is None:
                    actor = ss_prefabs.spawn_mesh(row['asset'], transform, label=row.get('name'), folder='Blender additions', materials=row.get('materials'))
                    created.append(actor)
                else:
                    rollback.append((actor, actor.get_actor_transform(), list(actor.static_mesh_component.get_materials()), actor.get_actor_label()))
                    actor.modify()
                    actor.static_mesh_component.modify()
                    actor.set_actor_transform(transform, False, False)
                    for slot, material in enumerate(row.get('materials', [])):
                        actor.static_mesh_component.set_material(slot, u.load_asset(material) if material else actor.static_mesh_component.static_mesh.get_material(slot))
                    if row.get('name') and row['name'] != actor.get_actor_label():
                        actor.set_actor_label(row['name'])
                state = _state(actor)
                if not state['guid']:
                    raise RuntimeError('New placement has no persistent actor identity')
                receipts.append({'link': original['link'], 'guid': state['guid'], 'base': state_digest(state),
                                 'materials': state['materials'], 'source_actor': actor.get_path_name()})
        except Exception:
            for actor, transform, materials, label in reversed(rollback):
                actor.set_actor_transform(transform, False, False)
                for slot, material in enumerate(materials):
                    actor.static_mesh_component.set_material(slot, material)
                actor.set_actor_label(label)
            for actor in reversed(created):
                u.get_editor_subsystem(u.EditorActorSubsystem).destroy_actor(actor)
            raise
    return {'created': sum(not row.get('guid') for row, _ in plans), 'moved': sum(bool(row.get('guid')) for row, _ in plans),
            'removed': 0, 'errors': [], 'placements': receipts, 'saved': False}
