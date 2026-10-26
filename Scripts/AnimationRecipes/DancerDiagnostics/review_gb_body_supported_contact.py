import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Feasibility control: support the whole body from an unchanged arm chain.

This is not the rejected V8 arm IK. No upper-arm/elbow/wrist local transform
changes. A rigid whole-character transform fixes the selected hand, then only
finger curls change. Collision/jerk may reject a passage; never hide failure
by twisting the arm. Original root trajectory is intentionally not retained.
"""
import bpy, json, math, hashlib, os, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
close=bool(os.environ.get('SS_CONTACT_CLOSEUP'))
O=R/('GBSupportedContactGripInward' if close else 'GBSupportedContactInward'); O.mkdir(exist_ok=True)
files=[D/'Vexa_HandIsolation_Proof.blend',D/'GB_SelectedPassages_ActionLibrary.blend']
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
bpy.ops.wm.open_mainfile(filepath=str(files[0]),load_ui=False)
s=bpy.context.scene; rig=next(o for o in s.objects if o.type=='ARMATURE')
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for k in ob.data.shape_keys.key_blocks:
   if k.name.startswith('REVIEW_'):k.value=0
with bpy.data.libraries.load(str(files[1]),link=False) as(a,b):
 b.actions=['A_F3_SelectedPassages_g1','A_F3_TwoPassages_g2']
acts={k:a for k,a in zip(('g1','g2'),b.actions)}
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
rest={b.name:rig.matrix_world@b.bone.matrix_local for b in ordered}
parent={b.name:b.parent.name if b.parent else None for b in ordered}
rel={n:rest[parent[n]].inverted()@m if parent[n] else m.copy() for n,m in rest.items()}
desc={b.name:[b.name]+[x.name for x in b.children_recursive] for b in ordered}
side='r'; hn='hand_'+side; inv=rest[hn].inverted()
along=(inv@rest['middle_01_'+side].translation).normalized()
across=inv.to_3x3()@(rest['index_01_'+side].translation-rest['pinky_01_'+side].translation)
across=(across-along*across.dot(along)).normalized(); normal=along.cross(across).normalized()
local=Matrix((along,across,normal)).transposed()
forward=Vector((-1,0,0)); width=Vector((0,0,1))
desired=Matrix((forward,width,forward.cross(width))).transposed()
target=Matrix.LocRotScale(Vector((.105,-.025,3)),(desired@local.inverted()).to_quaternion(),rest[hn].to_scale())
def apply_pose(p):
 invrig=rig.matrix_world.inverted(); localpose={n:invrig@m for n,m in p.items()}
 for pb in ordered:
  base=localpose[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
  pb.matrix_basis=base.inverted()@localpose[pb.name]
 bpy.context.view_layer.update()
def rotate(p,n,q):
 pivot=p[n].translation.copy(); xf=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)
 for child in desc[n]:p[child]=xf@p[child]
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
pole=bpy.context.object; pole.name='Diagnostic_OrangePole'; pole.color=(1,.12,0,1)
for ob in s.objects:
 if ob.type=='MESH' and ob!=pole:ob.color=(.55,.55,.55,1)
s.render.engine='BLENDER_WORKBENCH'; s.display.shading.light='STUDIO'; s.display.shading.color_type='OBJECT'
s.display.shading.show_cavity=False; s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('SupportedContactWorld'); s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=800; s.render.resolution_percentage=100
bpy.ops.object.camera_add(); cam=bpy.context.object; s.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=2.65
report={'sources':hashes,'scope':'right support feasibility; root transform changes; no arm-chain IK; no adoption','poses':[]}
cases=[('g1',881)] if close else [('g1',600),('g1',700),('g1',800),('g1',881),('g1',950),('g2',200),('g2',300),('g2',400),('g2',500),('g2',600)]
for clip,frame in cases:
 rig.animation_data_create(); rig.animation_data.action=acts[clip]; rig.animation_data.action_slot=acts[clip].slots[0]
 s.frame_set(frame); bpy.context.view_layer.update()
 original={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered}
 original_local={b.name:b.matrix_basis.copy() for b in ordered}
 root_delta=target@original[hn].inverted()
 assert max(abs(v-1) for v in root_delta.to_scale())<.0001
 p={n:root_delta@m for n,m in original.items()}
 rig.animation_data_clear()
 for finger in ('index','middle','ring','pinky'):
  for i in (1,2,3):
   n=f'{finger}_{i:02}_{side}'; base=p[parent[n]]@rel[n]
   rotate(p,n,base.to_quaternion()@p[n].to_quaternion().inverted())
   # Flex toward the palm normal. With forward=-X and width=+Z,
   # forward.cross(palm_normal)=-Z: positive-width curl bends outward.
   rotate(p,n,Quaternion(-width,.35 if i==1 else 1.05))
 apply_pose(p)
 arm_names=['clavicle_r','upperarm_r','lowerarm_r','hand_r','clavicle_l','upperarm_l','lowerarm_l','hand_l']
 localerr=max(abs(rig.pose.bones[n].matrix_basis[i][j]-original_local[n][i][j]) for n in arm_names for i in range(4) for j in range(4))
 assert localerr<.0001,(clip,frame,localerr)
 bounds=[];penetrating={}
 deps=bpy.context.evaluated_depsgraph_get()
 for ob in s.objects:
  if ob.type!='MESH' or ob==pole or ob.hide_render:continue
  ev=ob.evaluated_get(deps); points=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices])
  radius=np.linalg.norm(points[:,:2],axis=1)
  bounds.append(points)
  ids=np.flatnonzero((radius<.025)&(points[:,2]>0)&(points[:,2]<5))
  if len(ids):penetrating[ob.name]={'vertices':len(ids),'max_penetration_mm':float((.025-radius[ids]).max()*1000)}
 allp=np.concatenate(bounds);center=(Vector(allp.min(axis=0))+Vector(allp.max(axis=0)))*.5
 row={'clip':clip,'frame':frame,'arm_local_max_error':localerr,'pole_intersections':penetrating,'bounds_m':[allp.min(axis=0).tolist(),allp.max(axis=0).tolist()]}
 if close:
  center=Vector((0,0,3));cam.data.ortho_scale=.32
  hands=bpy.data.objects['Vexa_Continuous_Hands'];ev=hands.evaluated_get(deps)
  pts=np.array([tuple(hands.matrix_world@v.co) for v in ev.data.vertices])
  group=[]
  for v in hands.data.vertices:
   masses={f:sum(g.weight for g in v.groups if hands.vertex_groups[g.group].name.startswith(f+'_') and hands.vertex_groups[g.group].name.endswith('_r')) for f in ['hand','thumb','index','middle','ring','pinky']}
   name=max(masses,key=masses.get);group.append(name if masses[name]>.5 else 'other')
  np.savez_compressed(O/'GripSurface.npz',points=pts,groups=np.array(group))
 for view,offset in [('front',Vector((3,-5,.4))),('back',Vector((-3,5,.4))),('side',Vector((4,2,0)))]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(O/f'{clip}_{frame}_{view}.png');bpy.ops.render.render(write_still=True)
 report['poses'].append(row)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(O/'Feasibility.json').write_text(json.dumps(report,indent=2));print('BODY_SUPPORTED_CONTACT_DONE',flush=True)
