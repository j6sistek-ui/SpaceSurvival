import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Inspect the shared proof's knee geometry and weights without saving it."""
import bpy, json, math, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector

D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
O=R/'ZeroGSharedHip/KneeSourceControl'; O.mkdir(exist_ok=True)
src=D/'Vexa_ZeroG_SharedHip_Proof.blend'; digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene; rig=next(o for o in s.objects if o.type=='ARMATURE')
name='A_F3_Coordinated_ZeroG_01_Drift'; act=bpy.data.actions[name]
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for on,an in json.loads(s['zero_g_curve_pairs'])[name].items():
    keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
s.frame_set(563,subframe=.5);bpy.context.view_layer.update()
legs=next(o for o in s.objects if o.type=='MESH' and not o.hide_render and 'Feet' in o.name)
ev=legs.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh()
points=np.array([tuple(legs.matrix_world@v.co) for v in mesh.vertices]);rest=np.array([tuple(legs.matrix_world@v.co) for v in legs.data.vertices])
weights=[]
for v in legs.data.vertices:
    weights.append({legs.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-6})
report={'source':str(src),'sha256':digest,'mesh':legs.name,'frame':563.5,'bones':{},'near_knee':{},'mesh_modifiers':[m.name+':'+m.type for m in legs.modifiers]}
for side in ('l','r'):
    for bn in ('thigh_'+side,'thigh_twist_01_'+side,'thigh_twist_02_'+side,'calf_'+side,'calf_twist_01_'+side,'calf_twist_02_'+side,'foot_'+side):
        b=rig.data.bones[bn];pb=rig.pose.bones[bn]
        report['bones'][bn]={'parent':b.parent.name,'rest_head':list(rig.matrix_world@b.head_local),'rest_tail':list(rig.matrix_world@b.tail_local),'pose_head':list((rig.matrix_world@pb.matrix).translation),'local_quat':list(pb.matrix_basis.to_quaternion())}
    c=np.array(rig.matrix_world@rig.data.bones['calf_'+side].head_local)
    indices=np.flatnonzero(np.linalg.norm(rest-c,axis=1)<.13)
    report['near_knee'][side]=[{'id':int(i),'rest':rest[i].tolist(),'posed':points[i].tolist(),'weights':weights[i]} for i in indices]
mesh2=bpy.data.meshes.new('KneeFreshNormals');mesh2.from_pydata(points,[],[list(p.vertices) for p in mesh.polygons]);mesh2.update()
obj=bpy.data.objects.new('KneeFreshNormals',mesh2);s.collection.objects.link(obj)
for ob in s.objects:
    if ob.type=='MESH' and ob!=obj:ob.hide_render=True
for p in mesh2.polygons:p.use_smooth=True
colors=mesh2.color_attributes.new(name='KneeWeights',type='FLOAT_COLOR',domain='POINT')
for i,w in enumerate(weights):
    thigh=sum(v for n,v in w.items() if n.startswith('thigh'))
    calf=sum(v for n,v in w.items() if n.startswith('calf'))
    colors.data[i].color=(thigh,.05,calf,1)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.50
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=False;s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('KneeInspectWorld');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=600;s.render.resolution_percentage=100
for side in ('l','r'):
    h,k,a=[(rig.matrix_world@rig.pose.bones[n+'_'+side].matrix).translation for n in ('thigh','calf','foot')]
    normal=(h-k).cross(a-k).normalized();up=(h-k).normalized();front=normal.cross(up).normalized()
    for view,delta in [('hinge',normal*3),('opposite',-normal*3),('front',front*3)]:
        cam.location=k+delta;cam.rotation_euler=(k-cam.location).to_track_quat('-Z','Y').to_euler()
        for mode in ('smooth','weights'):
            s.display.shading.color_type='VERTEX' if mode=='weights' else 'SINGLE'
            s.render.filepath=str(O/f'{side}_{view}_{mode}.png');bpy.ops.render.render(write_still=True)
(O/'Report.json').write_text(json.dumps(report,indent=2))
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
print('KNEE_SOURCE_CONTROL_DONE',legs.name,flush=True)
