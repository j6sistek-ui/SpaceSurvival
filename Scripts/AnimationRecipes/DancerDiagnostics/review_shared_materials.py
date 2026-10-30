import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Restore source material assignments by exact rest triangles on a private copy.

Material/lighting review supplements, rather than replaces, clay anatomy checks.
The current source and vendor options remain unchanged.
"""
import bpy,json,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/MaterialReview';O.mkdir(exist_ok=True)
proof=D/'Vexa_ZeroG_SharedHip_Proof.blend';source=R.parents[2]/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (proof,source)}
bpy.ops.wm.open_mainfile(filepath=str(proof),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs'])
mapping={'Vexa_Continuous_Hands':['Vexa_Nude_Torso','Eden_Pink_Hands.001'],'Vexa_Continuous_Feet':['Vexa_Nude_Legs','Eden_Pink_Feet.001'],'Vexa_Top':['Vexa_Top'],'Vexa_Bottom':['Vexa_Bottom'],'Eden_Pink_CharacterMesh0.001':['Eden_Pink_CharacterMesh0.001']}
targets={n:bpy.data.objects[n] for n in mapping};names=tuple(sorted({n for ns in mapping.values() for n in ns}))
with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=list(names)
loaded=dict(zip(names,b.objects));report={'source_hashes':before,'face_assignment':[],'views':[],'acceptance':'Private Blender material approximation, no native shader or full-motion acceptance'}
for name,source_names in mapping.items():
 ob=targets[name];ob.data.materials.clear();entries=[];materials=[]
 for n in source_names:
  original=loaded[n];offset=len(materials);materials.extend(list(original.data.materials))
  for face in original.data.polygons:
   coords=[original.matrix_world@original.data.vertices[i].co for i in face.vertices];assert len(coords)==3
   entries.append((sum(coords,Vector())/3,coords,offset+face.material_index))
 for mat in materials:ob.data.materials.append(mat)
 tree=kdtree.KDTree(len(entries))
 for i,(center,_,_) in enumerate(entries):tree.insert(center,i)
 tree.balance();max_error=0;used=set()
 for face in ob.data.polygons:
  coords=[ob.matrix_world@ob.data.vertices[i].co for i in face.vertices];center=sum(coords,Vector())/3;_,i,d=tree.find(center)
  assert d<1e-5,(name,face.index,d)
  err=max(min((v-w).length for w in entries[i][1]) for v in coords);assert err<1e-5,(name,face.index,err)
  face.material_index=entries[i][2];max_error=max(max_error,err);used.add(i)
 assert len(used)==len(entries)==len(ob.data.polygons),(name,len(used),len(entries))
 report['face_assignment'].append({'mesh':name,'triangles':len(used),'max_rest_match_m':max_error,'materials':[m.name for m in materials]})
for original in loaded.values():bpy.data.objects.remove(original,do_unlink=True)
for ob in list(s.objects):
 if ob.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(ob,do_unlink=True)
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=48;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices();assert any(d.type=='OPTIX' for d in prefs.devices)
for d in prefs.devices:d.use=d.type=='OPTIX'
s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.world=bpy.data.worlds.new('SharedMaterialWorld');s.world.use_nodes=True;bg=s.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.07,.08,.10,1);bg.inputs[1].default_value=.3
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.05
lights=[]
for energy,size in ((180,2.0),(85,2.4),(65,1.0)):
 bpy.ops.object.light_add(type='AREA');li=bpy.context.object;li.data.energy=energy;li.data.shape='DISK';li.data.size=size;lights.append(li)
def assign(suffix,f):
 name='A_F3_Coordinated_ZeroG_'+suffix;a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
for suffix,f in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474),('05_LateralArc',421)]:
 assign(suffix,f)
 up=((rig.matrix_world@rig.pose.bones['neck_01'].matrix).translation-(rig.matrix_world@rig.pose.bones['spine_03'].matrix).translation).normalized()
 side=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation-(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation).normalized();front=up.cross(side).normalized()
 center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation+up*.1
 for view,delta in [('front',front*4),('rear_oblique',-front*3.5+side*2)]:
  cam.location=center+delta+up*.1;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  for li,(x,y,z),color in zip(lights,[(-1,-1.5,1.7),(1,-1,1),(0,1,.8)],[(1,.96,.9),(.9,.95,1),(1,1,1)]):
   li.location=center+side*x-front*y+up*z;li.rotation_euler=(center-li.location).to_track_quat('-Z','Y').to_euler();li.data.color=color
  s.render.filepath=str(O/f'{suffix}_{view}.png');bpy.ops.render.render(write_still=True);report['views'].append({'action':suffix,'frame':f,'view':view,'file':s.render.filepath})
assign('01_Drift',1)
# One retained material assembly; no source iterations or duplicate snapshots.
output=D/'Vexa_ZeroG_MaterialReview.blend';assert not output.exists();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
report['output']=str(output);report['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
(O/'Report.json').write_text(json.dumps(report,indent=2));print('SHARED_MATERIAL_REVIEW_DONE',flush=True)
