"""Prefab recipes: save a selection of tagged parts as Prefabs/<Category>/<Name>.json, load one back as proxies.

The recipe is the same file the editor reads and writes (Content/Python/ss_prefabs.py), in Unreal's frame.
"""
from pathlib import Path
import json
import math

import bpy
from mathutils import Matrix, Vector

from . import core, library, surfaces


def save_prefab(objects, category, name, purpose=''):
    """Write objects as a recipe relative to their bounds centre XY / bottom Z, in Unreal's frame."""
    objects = [o for o in objects if o.get(core.PROP_ASSET)]
    if not objects:
        raise RuntimeError('select at least one tagged part')
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for o in objects:
        for c in o.bound_box:
            p = core.ue_point(o.matrix_world @ Vector(c))
            for i in range(3):
                lo[i] = min(lo[i], p[i]); hi[i] = max(hi[i], p[i])
    pivot = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]
    parts = []
    for o in objects:
        rows = core.to_ue_rows(o.matrix_world)
        rows[3] = [rows[3][0] - pivot[0], rows[3][1] - pivot[1], rows[3][2] - pivot[2], 1.0]
        part = {'name': o.name, 'asset': o[core.PROP_ASSET], 'matrix': [[round(v, 6) for v in r] for r in rows]}
        if o.get(core.PROP_MATERIALS):
            part['materials'] = json.loads(o[core.PROP_MATERIALS])
        parts.append(surfaces.add_to_record(o, part))
    lights = []
    for o in bpy.context.selected_objects:
        if o.type == 'LIGHT' and o.data.type == 'POINT':
            p = core.ue_point(o.matrix_world.translation)
            lights.append({'name': o.name, 'location': [p[i] - pivot[i] for i in range(3)], 'color': list(o.data.color)[:3],
                           'intensity': o.data.energy * 8.0, 'attenuation_radius': (o.data.cutoff_distance if o.data.use_custom_distance else 10.0) * 100.0,
                           'cast_shadows': bool(o.data.use_shadow)})
    recipe = {'schema_version': 1, 'purpose': purpose or f'{name}: {len(parts)} parts, {len(lights)} lights (authored in Blender)',
              'origin': 'bounds centre XY, bounds bottom Z of the parts when saved; place_prefab puts this point at the requested location',
              'static_meshes': parts, 'point_lights': lights, 'notes': []}
    path = core.prefabs_dir() / category / f'{name}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(recipe, indent=1), encoding='utf-8')
    return path


def load_prefab(ref, at=None):
    """Proxies for a recipe, in a collection named after it, with the origin at the 3D cursor (or at)."""
    path = core.prefabs_dir() / (ref + '.json') if not str(ref).lower().endswith('.json') else Path(ref)
    recipe = json.loads(path.read_text(encoding='utf-8'))
    origin = Matrix.Translation(at if at is not None else bpy.context.scene.cursor.location)
    col = core.ensure_collection(f'SS Prefab {path.stem}')
    made = []
    for part in recipe.get('static_meshes', []):
        if 'matrix' in part:
            local = core.from_ue_rows(part['matrix'])
        else:
            scl = part.get('scale', [1, 1, 1])
            scl = scl if isinstance(scl, (list, tuple)) else [scl] * 3
            local = core.from_ue_rows(core.rows_from_rotator(part.get('location', [0, 0, 0]), part.get('rotation', [0, 0, 0]), scl))
        obj = core.add_part(part['asset'], origin @ local, col, name=part.get('name'), materials=part.get('materials'))
        surfaces.restore(obj, part.get('surface_overrides'))
        made.append(obj)
    for light in recipe.get('point_lights', []):
        data = bpy.data.lights.new(light.get('name', 'Light'), 'POINT')
        c = light.get('color', [1, 1, 1])
        data.color = (c[0], c[1], c[2])
        data.energy = float(light.get('intensity', 5000)) / 8.0
        obj = bpy.data.objects.new(light.get('name', 'Light'), data)
        p = light['location']
        obj.matrix_world = origin @ Matrix.Translation(Vector((p[0], -p[1], p[2])) / 100.0)
        col.objects.link(obj)
        made.append(obj)
    return made


# ---------------------------------------------------------------- operators
class SSLINK_OT_save_prefab(bpy.types.Operator):
    bl_idname = 'ss_link.save_prefab'
    bl_label = 'Save Selection as Prefab'
    bl_description = 'Write Prefabs/<Category>/<Name>.json from the selected tagged parts'

    def execute(self, context):
        st = context.scene.ss_link
        try:
            path = save_prefab(context.selected_objects, st.save_category.strip() or 'Unsorted', st.save_name.strip() or 'Prefab')
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        library.refresh_prefab_items()
        st.status = f'saved {path.relative_to(core.prefabs_dir())}'
        return {'FINISHED'}


class SSLINK_OT_load_prefab(bpy.types.Operator):
    bl_idname = 'ss_link.load_prefab'
    bl_label = 'Load Prefab at Cursor'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        st = context.scene.ss_link
        if not st.prefab:
            self.report({'ERROR'}, 'no prefab chosen')
            return {'CANCELLED'}
        try:
            made = load_prefab(st.prefab)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        core.deselect_all(context)
        for o in made:
            o.select_set(True)
        st.status = f'loaded {st.prefab}: {len(made)} objects'
        return {'FINISHED'}


class SSLINK_OT_refresh_prefabs(bpy.types.Operator):
    bl_idname = 'ss_link.refresh_prefabs'
    bl_label = 'Refresh'

    def execute(self, context):
        library.refresh_prefab_items()
        return {'FINISHED'}


classes = (SSLINK_OT_save_prefab, SSLINK_OT_load_prefab, SSLINK_OT_refresh_prefabs)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
