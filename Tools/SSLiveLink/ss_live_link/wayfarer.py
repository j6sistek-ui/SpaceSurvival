"""Current Wayfarer map snapshots: new Blender scene, guarded selected-placement edits."""
import json
from pathlib import Path
import uuid
from collections import defaultdict

import bpy
from mathutils import Vector

from . import core
from .proxy_cache import snapshot_mesh_key

SNAPSHOT = 'ss_wayfarer_snapshot'
GUID = 'ss_wayfarer_guid'
BASE = 'ss_wayfarer_base'
OWNER = 'ss_wayfarer_owner'


def open_snapshot(path=None):
    root = core.project_root()
    if not root:
        raise RuntimeError('Set the SS Link project root first')
    if path is None:
        latest = root / 'Artifacts/WayfarerBlender/latest.json'
        if not latest.is_file():
            raise RuntimeError('Export the current Wayfarer map from Unreal first')
        path = json.loads(latest.read_text(encoding='utf-8'))['scene']
    path = Path(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not data.get('snapshot_id') or not data.get('objects'):
        raise ValueError('Invalid or empty Wayfarer snapshot')
    if Path(data['project_root']).resolve() != root.resolve():
        raise ValueError('This snapshot belongs to another project; export it from the selected Unreal project')
    for row in data['objects']:
        proxy = data['proxies'].get(row['asset'])
        if not proxy or not Path(proxy).is_file():
            raise RuntimeError(f'Missing real geometry for {row["asset"]}; refresh/export before opening')
    previous = bpy.context.window.scene
    scene = bpy.data.scenes.new('Wayfarer station')
    bpy.context.window.scene = scene
    scene.unit_settings.system = 'METRIC'
    scene[SNAPSHOT] = data['snapshot_id']
    scene['ss_target_map'] = data['target_map']
    scene['ss_wayfarer_project'] = data['project_root']
    scene['ss_wayfarer_source'] = str(path.resolve())
    scene['ss_wayfarer_non_mesh_actors'] = data['non_mesh_actors']
    editable = bpy.data.collections.new('Wayfarer - editable placements')
    locked = bpy.data.collections.new('Wayfarer - Unreal context (locked)')
    scene.collection.children.link(editable)
    scene.collection.children.link(locked)
    locked.hide_select = True
    try:
        meshes = {}
        for asset in sorted({row['asset'] for row in data['objects']}):
            entry = {'asset': asset, 'name': asset.split('.')[-1], 'proxy': data['proxies'][asset]}
            key = snapshot_mesh_key(asset, entry['proxy'])
            meshes[asset] = core.proxy_mesh(entry, cache_key=key, require_geometry=True)
        centers = []
        for row in data['objects']:
            obj = bpy.data.objects.new(row['name'], meshes[row['asset']])
            obj.matrix_world = core.from_ue_rows(row['matrix'])
            obj['ss_source_actor'] = row['source_actor']
            obj['ss_source_component'] = row['source_component']
            obj['ss_unreal_label'] = row['name']
            obj['ss_loaded_blender_name'] = obj.name
            obj[OWNER] = data['snapshot_id']
            if row['editable']:
                obj[core.PROP_ASSET] = row['asset']
                obj[core.PROP_LINK] = row['guid']
                obj[core.PROP_MATERIALS] = json.dumps(row.get('materials', []))
                obj[GUID] = row['guid']
                obj[BASE] = row['base']
                editable.objects.link(obj)
            else:
                obj['ss_context_asset'] = row['asset']
                obj['ss_context_reason'] = row.get('context_reason', 'Unreal context')
                obj.hide_select = True
                locked.objects.link(obj)
            if row.get('hide_in_blender'):
                obj['ss_hidden_reason'] = row.get('blender_hidden_reason', 'hidden in Unreal')
                obj.hide_viewport = True
                obj.hide_render = True
            else:
                centers.append(obj.matrix_world.translation.copy())
        if hasattr(scene, 'ss_link'):
            scene.ss_link.live = False
            scene.ss_link.status = f'Wayfarer: {data["editable"]} editable placements; {data["locked"]} locked context meshes'
            bpy.ops.ss_link.load_catalog()
        core.pushed_links.clear()
        note = bpy.data.texts.new('Wayfarer - START HERE')
        note.write('Current Unreal map: ' + data['target_map'] + '\n'
                   'Move editable placements, then SS Link > Push Selected. Save the Unreal level after review.\n'
                   'Add at Cursor creates new mesh placements. Delete actors and edit Blueprint logic directly in Unreal.\n'
                   'Push checks the original actor state and refuses stale edits. Export/open a fresh snapshot after Unreal edits.\n'
                   'Locked context includes Blueprint meshes, instances, streamed children and skeletal reference poses.\n'
                   'Lights, effects, animation and original material graphs remain authoritative in Unreal.\n'
                   'The existing Blender scenes remain intact. Save this working file explicitly.\n')
        center = sum(centers, Vector()) / len(centers) if centers else Vector()
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.clip_end = 10000
                area.spaces.active.region_3d.view_location = center
                area.spaces.active.region_3d.view_distance = 180
        return {'scene': scene.name, 'objects': len(data['objects']), 'editable': data['editable'], 'locked': data['locked']}
    except Exception:
        # Preserve the prior working scene; leave the failed import visible for diagnosis.
        bpy.context.window.scene = previous
        scene.name = 'Wayfarer import incomplete'
        raise


def push(objects, remove=()):
    from . import editor_link, surfaces
    scene = bpy.context.scene
    if remove:
        raise RuntimeError('Delete Wayfarer actors directly in Unreal; Live removal is disabled')
    objects = list(objects)
    rows = []
    identities = defaultdict(list)
    for obj in scene.objects:
        if obj.get(GUID):
            identities[obj[GUID]].append(obj)
    seen_links = set()
    for obj in objects:
        if obj.name not in scene.objects:
            raise RuntimeError('A selected part belongs to another scene')
        if obj.get(OWNER) and obj[OWNER] != scene[SNAPSHOT]:
            raise RuntimeError('A part belongs to a different Wayfarer snapshot')
        guid = obj.get(GUID)
        duplicate = False
        if guid:
            matches = identities[guid]
            if len(matches) > 1:
                originals = [candidate for candidate in matches if candidate.name == candidate.get('ss_loaded_blender_name')]
                if len(originals) != 1:
                    raise RuntimeError('Original of these duplicated/renamed parts is ambiguous; use Add at Cursor for a new placement')
                duplicate = obj != originals[0]
                if duplicate:
                    guid = None
                    obj[core.PROP_LINK] = uuid.uuid4().hex
        else:
            if obj.get('ss_source_actor'):
                raise RuntimeError('Original actor identity was removed; open a fresh snapshot')
            obj[core.PROP_LINK] = obj.get(core.PROP_LINK) or uuid.uuid4().hex
        if obj[core.PROP_LINK] in seen_links:
            if guid:
                raise RuntimeError('Two original placements share a link identity; open a fresh snapshot')
            obj[core.PROP_LINK] = uuid.uuid4().hex
        seen_links.add(obj[core.PROP_LINK])
        label = obj.get('ss_unreal_label', obj.name) if obj.name == obj.get('ss_loaded_blender_name') else obj.name
        row = {'link': obj[core.PROP_LINK], 'asset': obj[core.PROP_ASSET], 'name': label,
               'matrix': core.to_ue_rows(obj.matrix_world), 'guid': guid, 'base': obj.get(BASE) if guid else None,
               'new': not bool(guid)}
        if obj.get(core.PROP_MATERIALS):
            row['materials'] = json.loads(obj[core.PROP_MATERIALS])
        surfaces.add_to_record(obj, row)
        rows.append(row)
    payload = {'objects': rows, 'snapshot_id': scene[SNAPSHOT], 'project_root': scene['ss_wayfarer_project'],
               'target_map': scene['ss_target_map']}
    call = "__import__('ss_wayfarer').apply_edits(" + repr(json.dumps(payload))
    editor_link.link.call(call + ', dry_run=True)')
    result = editor_link.link.call(call + ', dry_run=False)')
    by_link = {obj[core.PROP_LINK]: obj for obj in objects}
    rows_by_link = {row['link']: row for row in rows}
    for receipt in result.get('placements', []):
        obj = by_link[receipt['link']]
        obj[GUID], obj[BASE], obj[OWNER] = receipt['guid'], receipt['base'], scene[SNAPSHOT]
        obj[core.PROP_MATERIALS] = json.dumps(receipt['materials'])
        obj['ss_loaded_blender_name'] = obj.name
        obj['ss_unreal_label'] = rows_by_link[receipt['link']]['name']
        obj['ss_source_actor'] = receipt['source_actor']
    return result
