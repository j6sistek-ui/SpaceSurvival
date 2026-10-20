"""Derive centimeter-native, unit-root FBXs; source Blender/FBX files are never changed."""
import hashlib
import json
from pathlib import Path
import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
MANIFEST = OUT / 'SourceManifest.json'
data = json.loads(MANIFEST.read_text())
dest = OUT / 'UnrealUnits'
dest.mkdir(exist_ok=True)
for hero in data['heroes']:
    source = Path(hero['fbx'])
    assert source.parent != dest, 'Already normalized; never normalize twice'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
    rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    world = rig.matrix_world.copy()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    scale = Matrix.Scale(100, 4)
    bones = [(b.name, b.parent.name if b.parent else None, scale @ world @ b.head_local,
              scale @ world @ b.tail_local, (world @ b.matrix_local).to_3x3().col[2].copy()) for b in rig.data.bones]
    geometry = []
    for obj in meshes:
        mesh = obj.data.copy()
        mesh.transform(scale @ obj.matrix_world)
        groups = [(g.name, [(v.index, next((w.weight for w in v.groups if w.group == g.index), 0))
                            for v in obj.data.vertices]) for g in obj.vertex_groups]
        geometry.append((obj.name, mesh, groups))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    arm = bpy.data.armatures.new('CentimeterRig')
    target = bpy.data.objects.new('Armature', arm)
    bpy.context.collection.objects.link(target)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode='EDIT')
    for name, parent, head, tail, roll in bones:
        bone = arm.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bone.align_roll(roll)
        if parent:
            bone.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    for name, mesh, groups in geometry:
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        for group_name, weights in groups:
            group = obj.vertex_groups.new(name=group_name)
            for i, weight in weights:
                if weight:
                    group.add([i], weight, 'REPLACE')
        obj.modifiers.new('Skin', 'ARMATURE').object = target
        obj.select_set(True)
    bpy.context.scene.unit_settings.scale_length = .01
    bpy.context.view_layer.update()
    path = dest / (hero['key'] + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'ARMATURE', 'MESH'},
                            add_leaf_bones=False, bake_anim=False, axis_forward='-Y', axis_up='Z',
                            apply_scale_options='FBX_SCALE_ALL', use_mesh_modifiers=False, path_mode='RELATIVE')
    hero['pre_units_fbx'] = str(source)
    hero['pre_units_sha256'] = hero['fbx_sha256']
    hero['fbx'] = str(path)
    hero['fbx_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    print('CENTIMETER_EXPORT', hero['key'], len(bones), len(geometry), flush=True)
MANIFEST.write_text(json.dumps(data, indent=2))
print('ALL_CENTIMETER_EXPORTS_READY', flush=True)
