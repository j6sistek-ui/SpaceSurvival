import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh source-file controls and posed surface samples for native comparison."""
import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/Controls';O.mkdir(exist_ok=True)
source=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs'])
assert len(pairs)==5 and all(n in bpy.data.actions for n in pairs)
rest=rig.matrix_world@rig.data.bones['spine_05'].matrix_local
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('ZeroGSourceReview');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.35
rows=[];surfaces={}
for name,pa in pairs.items():
 action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for n,a in pa.items():
  keys=bpy.data.objects[n].data.shape_keys;keys.animation_data_create();keys.animation_data.action=bpy.data.actions[a];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 first,last=map(round,action.frame_range);want=sorted({first,first+(last-first)*.25,first+(last-first)*.5,first+(last-first)*.75,last}|({563.5} if 'Drift' in name else {461.} if 'Butterfly' in name else set()))
 for f in want:
  s.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update();p={b.name:(rig.matrix_world@b.matrix).copy() for b in rig.pose.bones};chest=p['spine_05'].to_quaternion()@rest.to_quaternion().inverted();center=p['pelvis'].translation+chest@Vector((0,0,.15))
  label=name.split('ZeroG_')[1]+'_'+str(f).replace('.','p')
  for view,off in [('front',Vector((0,-3,.2))),('back',Vector((0,3,.2)))]:
   cam.location=center+chest@off;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/(label+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
  row={'action':name,'label':label,'frame':f,'seconds':(f-1)/60,'bones_m':{n:list(m.translation) for n,m in p.items()}};rows.append(row)
  if abs(f-(first+(last-first)*.5))<1e-5:
   for ob in s.objects:
    if ob.type!='MESH' or ob.hide_render:continue
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());surfaces[label+'__'+ob.name]=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices],dtype=np.float32)
np.savez_compressed(O/'PosedSurfaces.npz',**surfaces)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps({'source_sha256':digest,'rows':rows},indent=2));print('ZERO_G_SOURCE_CONTROLS_DONE',len(rows),flush=True)
