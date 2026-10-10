"""Make a color-only Joy derivative and a CPU-rendered head preview."""
import bpy
import hashlib
import json
from array import array
from pathlib import Path

SOURCE = Path('M:/Local AI/Projects/JoySkinPreview_20261008/selected_deep_purple/Joy_Purple_HairFitted.blend')
OUT = Path(__file__).resolve().parents[3] / '.agent/local/StationRefinement/CpuJoy121/JoyBlue114'
TARGET = OUT / 'Joy_LightBlue_HairFitted.blend'
EXPECTED = 'ea6f4be979d1381b15899b16cded8059578d8529c9d2deed962fc6f09b5576a6'
BLUE = (.46, .66, .84, 1.)
DARK = (.008, .009, .012, 1.)

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def geometry():
    h = hashlib.sha256()
    for obj in sorted(bpy.context.scene.objects, key=lambda o:o.name):
        if obj.type == 'MESH':
            h.update(obj.name.encode())
            coords = array('f', [0.]) * (len(obj.data.vertices)*3)
            obj.data.vertices.foreach_get('co', coords)
            h.update(coords.tobytes())
            h.update(str([(m.type, m.object.name if m.type=='ARMATURE' and m.object else None) for m in obj.modifiers]).encode())
            if obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks:
                    key.data.foreach_get('co', coords)
                    h.update(coords.tobytes())
        elif obj.type == 'ARMATURE':
            h.update(str([(b.name, [list(v) for v in b.matrix_local]) for b in obj.data.bones]).encode())
    return h.hexdigest()

assert not TARGET.exists()
assert sha(SOURCE) == EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
before = geometry()
changed = []
for part in ('Head', 'Body', 'Arm', 'Leg'):
    mat = bpy.data.materials['Joy_Purple_Std_Skin_'+part]
    nodes = [n for n in mat.node_tree.nodes if 'SkinTint' in n.name]
    assert len(nodes)==1 and nodes[0].type=='MIX_RGB'
    node = nodes[0]
    assert not node.inputs[2].is_linked
    changed.append({'material': mat.name, 'node': node.name, 'before': list(node.inputs[2].default_value), 'after': list(BLUE)})
    node.inputs[2].default_value = BLUE
    mat.diffuse_color = BLUE
streak = bpy.data.materials['Joy_Purple_Hair_streak']
for node in streak.node_tree.nodes:
    if node.type == 'BSDF_HAIR_PRINCIPLED':
        assert not node.inputs['Color'].is_linked
        changed.append({'material': streak.name, 'node': node.name, 'before': list(node.inputs['Color'].default_value), 'after': list(DARK)})
        node.inputs['Color'].default_value = DARK
assert geometry() == before
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
camera = scene.camera
assert camera and camera.name == 'JoyPreview_Camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .56
camera.location.z = 1.60
scene.render.resolution_x = 512
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT/'Joy-light-blue-head.png')
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET), check_existing=False)
assert sha(SOURCE) == EXPECTED
report = {'source': str(SOURCE), 'source_sha256': EXPECTED, 'source_preserved': True,
          'derivative': str(TARGET), 'derivative_sha256': sha(TARGET),
          'geometry_and_shape_keys_preserved': geometry()==before, 'geometry_sha256': before,
          'changes': changed, 'render_engine': 'Cycles CPU', 'gpu_rendering': False,
          'preview': scene.render.filepath, 'native_adoption': 'PENDING', 'animation_transfer': 'PENDING'}
(OUT/'ColorReceipt.json').write_text(json.dumps(report, indent=2)+'\n')
print('JOY_BLUE_SAVED', str(TARGET), flush=True)
bpy.ops.render.render(write_still=True)
report['preview_sha256'] = sha(Path(scene.render.filepath))
report['render_finished'] = True
(OUT/'ColorReceipt.json').write_text(json.dumps(report, indent=2)+'\n')
print('JOY_BLUE_CPU_RENDER_FINISHED', flush=True)
