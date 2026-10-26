import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Remove proven pelvis contamination from Vexa hands; preserve other weights."""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector
P = R.parents[2]
D = P/'SourceAssets/DanceRefinement_20261025'
source = D/'Vexa_AxillaLocal_Proof.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == '1f677227824704fb3741f3dbbc3db3c30f6458e6cd8a9b30148896be0f40a680'
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
s = bpy.context.scene
rig = next(o for o in s.objects if o.type == 'ARMATURE')
hand = next(o for o in s.objects if o.type == 'MESH' and 'Hands' in o.name)
report = {'source_sha256': digest, 'changed': [], 'views': []}
out = R/'VexaDistalRepair'
out.mkdir(exist_ok=True)
original = [{hand.vertex_groups[g.group].name: g.weight for g in v.groups} for v in hand.data.vertices]
def capture(label):
    s.render.engine = 'BLENDER_WORKBENCH'
    s.display.shading.light = 'STUDIO'
    s.display.shading.color_type = 'SINGLE'
    s.display.shading.single_color = (.55,.55,.55)
    s.display.shading.show_cavity = True
    s.display.shading.background_type = 'WORLD'
    s.world.color = (.035,.045,.055)
    s.render.resolution_x = s.render.resolution_y = 640
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    cam = s.camera
    if cam is None:
        bpy.ops.object.camera_add()
        cam = bpy.context.object
        s.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = .3
    s.frame_set(241)
    bpy.context.view_layer.update()
    for side in ('r','l'):
        bone = rig.pose.bones['hand_'+side]
        center = rig.matrix_world @ bone.head
        orientation = (rig.matrix_world @ bone.parent.matrix).to_quaternion()
        for view, direction in [('front',Vector((0,-2,.8))),('side',Vector((2,0,.8)))]:
            cam.location = center + orientation @ direction
            cam.rotation_euler = (center-cam.location).to_track_quat('-Z','Y').to_euler()
            file = out/f'thumb_{side}_{label}_{view}.png'
            s.render.filepath = str(file)
            bpy.ops.render.render(write_still=True)
            report['views'].append(str(file))
capture('before')
group = hand.vertex_groups.get('pelvis')
assert group
for v in hand.data.vertices:
    old = original[v.index]
    if old.get('pelvis',0) <= 0:
        continue
    clean = {k:w for k,w in old.items() if k != 'pelvis' and w > 0}
    total = sum(clean.values())
    assert total > .5, (v.index,old)
    group.remove([v.index])
    for k,w in clean.items():
        hand.vertex_groups[k].add([v.index],w/total,'REPLACE')
    report['changed'].append({'vertex':v.index,'pelvis_weight':old['pelvis'],'old':old,'new':{k:w/total for k,w in clean.items()}})
assert report['changed']
for v in hand.data.vertices:
    current = {hand.vertex_groups[g.group].name:g.weight for g in v.groups}
    assert current.get('pelvis',0) == 0
    if original[v.index].get('pelvis',0) == 0:
        assert current == original[v.index]
    else:
        assert abs(sum(current.values())-1) < 1e-6
capture('after')
s.frame_set(1)
output = D/'Vexa_HandWeights_Proof.blend'
assert not output.exists(), 'Keep earlier candidate intact'
bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
report['output'] = str(output)
report['output_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
report['source_unchanged'] = True
(out/'HandRepair.json').write_text(json.dumps(report,indent=2))
print('HAND_REPAIR', len(report['changed']), report['output_sha256'], flush=True)
