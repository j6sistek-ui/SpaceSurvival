"""Opt-in, per-object simple surfaces. JSON carries values, never Blender node code."""
import json
import math
from pathlib import Path

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from . import core

MARKER = 'ss_simple_surface'
INPUTS = {'base_color': 'Base Color', 'metallic': 'Metallic', 'roughness': 'Roughness',
          'opacity': 'Alpha', 'transmission': 'Transmission Weight', 'ior': 'IOR'}


def describe(obj):
    """Export only explicitly created SS surfaces; reject unsupported edits instead of losing them."""
    result = {}
    for index, slot in enumerate(obj.material_slots):
        mat = slot.material
        if not mat or not mat.get(MARKER):
            continue
        nodes = mat.node_tree.nodes if mat.use_nodes else []
        shader = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        outputs = [n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
        if (not shader or len(outputs) != 1 or len(nodes) != 2
                or not outputs[0].inputs['Surface'].is_linked
                or outputs[0].inputs['Surface'].links[0].from_node != shader):
            raise RuntimeError(f'{obj.name}: use the simple Principled surface; custom shader graphs cannot be transferred')
        if any(socket.is_linked for socket in shader.inputs):
            raise RuntimeError(f'{obj.name}: connected shader inputs need a separate material export')
        values = {}
        for key, socket in INPUTS.items():
            value = shader.inputs[socket].default_value
            values[key] = list(value)[:3] if key == 'base_color' else float(value)
        flat = values['base_color'] + [v for k, v in values.items() if k != 'base_color']
        if not all(math.isfinite(v) for v in flat):
            raise RuntimeError(f'{obj.name}: surface values must be finite')
        result[str(index)] = values
    return result


def assign(obj, index, values):
    # Mesh data may be shared by hundreds of placements. Slot assignments belong to this object.
    if len(obj.material_slots) <= index:
        obj.data = obj.data.copy()
        while len(obj.data.materials) <= index:
            obj.data.materials.append(None)
    mat = bpy.data.materials.new('SS Surface - ' + obj.name)
    mat.use_nodes = True
    mat[MARKER] = True
    shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, socket in INPUTS.items():
        if key in values:
            shader.inputs[socket].default_value = (*values[key], 1.0) if key == 'base_color' else values[key]
    mat.diffuse_color = (*values.get('base_color', [0.65, 0.7, 0.75]), values.get('opacity', 1.0))
    obj.material_slots[index].link = 'OBJECT'
    obj.material_slots[index].material = mat
    return mat


def restore(obj, overrides):
    for slot, values in (overrides or {}).items():
        assign(obj, int(slot), values)


def add_to_record(obj, record):
    record.pop('surface_overrides', None)
    values = describe(obj)
    if values:
        record['surface_overrides'] = values
    return record


class SSLINK_OT_edit_surface(bpy.types.Operator):
    bl_idname = 'ss_link.edit_surface'
    bl_label = 'Make Editable Surface'
    bl_options = {'REGISTER', 'UNDO'}
    style: EnumProperty(items=[('SURFACE', 'Surface', ''), ('GLASS', 'Glass', ''), ('MIRROR', 'Mirror finish', '')])

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH' and bool(obj.get(core.PROP_ASSET))

    def execute(self, context):
        obj = context.active_object
        values = {'base_color': [0.65, 0.7, 0.75], 'metallic': 0.0, 'roughness': 0.4,
                  'opacity': 1.0, 'transmission': 0.0, 'ior': 1.45}
        if self.style == 'GLASS':
            values.update(roughness=0.05, opacity=0.18, transmission=1.0)
        elif self.style == 'MIRROR':
            values.update(base_color=[1.0, 1.0, 1.0], roughness=0.02, metallic=1.0)
        assign(obj, obj.active_material_index, values)
        context.scene.ss_link.status = 'Surface is private to this object. Edit below or in Material Properties.'
        return {'FINISHED'}


class SSLINK_OT_export_material_scene(bpy.types.Operator, ExportHelper):
    bl_idname = 'ss_link.export_material_scene'
    bl_label = 'Export Placement + Materials JSON'
    bl_description = 'Export this scene for desktop handoff, including per-object surface changes; no Unreal connection needed'
    filename_ext = '.json'
    filter_glob: StringProperty(default='*.json', options={'HIDDEN'})

    def execute(self, context):
        from .editor_link import link_payload
        try:
            objects = [o for o in context.scene.objects if o.type == 'MESH' and o.get(core.PROP_ASSET) and not o.get(core.PROP_EDIT)]
            if not objects:
                raise RuntimeError('There are no library parts in this scene')
            data = {'schema_version': 1, 'purpose': 'Blender placement and simple surface handoff',
                    'static_meshes': link_payload(objects), 'point_lights': []}
            Path(self.filepath).write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


def draw(layout, context):
    obj = context.active_object
    layout.label(text='Selected part surface')
    if obj and obj.type == 'MESH' and obj.get(core.PROP_ASSET):
        layout.label(text=f'{obj.name} / slot {obj.active_material_index + 1}')
        row = layout.row(align=True)
        for style, label in [('SURFACE', 'Surface'), ('GLASS', 'Glass'), ('MIRROR', 'Mirror finish')]:
            row.operator('ss_link.edit_surface', text=label).style = style
        mat = obj.active_material
        if mat and mat.get(MARKER) and mat.use_nodes:
            shader = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if shader:
                for socket in INPUTS.values():
                    layout.prop(shader.inputs[socket], 'default_value', text=socket)
    else:
        layout.label(text='Select a placed library mesh')
    layout.operator('ss_link.export_material_scene', icon='EXPORT')


classes = (SSLINK_OT_edit_surface, SSLINK_OT_export_material_scene)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
