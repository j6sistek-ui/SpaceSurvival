import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';OUT=R/'RefinementReview';OUT.mkdir(exist_ok=True)
import forearm_markers
manifest=json.loads((D/'Manifest.json').read_text());report={'clips':[],'images':[]}
bpy.ops.wm.open_mainfile(filepath=str(D/'Refined_ActionLibrary.blend'),load_ui=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
rest={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones};ends={}
for row in manifest['clips']:
 key=row['clip'];act=bpy.data.actions['A_F3_Refined_'+key];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 names=['pelvis','head','spine_05','upperarm_l','upperarm_r','lowerarm_l','lowerarm_r','hand_l','hand_r','foot_l','foot_r']
 item={'clip':key,'elbow_reversals':0,'rear_reach_frames':0,'max_rear_degrees':0,'max_hand_step_m':0,'worst_jump_time':0};previous=None
 for frame in range(1,row['frames']+1):
  scene.frame_set(frame);p={n:rig.matrix_world@rig.pose.bones[n].matrix for n in names}
  chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();f=chest@Vector((0,-1,0));up=chest@Vector((0,0,1))
  reversal=False;rear=False
  for side in ('l','r'):
   ns=['upperarm_'+side,'lowerarm_'+side,'hand_'+side];a,b,c=[p[n] for n in ns];a0,b0,c0=[rest[n] for n in ns]
   u=(b.translation-a.translation).normalized();v=(c.translation-b.translation).normalized();h=u.cross(v)
   h0=a0.to_quaternion().inverted()@(b0.translation-a0.translation).cross(c0.translation-b0.translation).normalized()
   if h.length>.1:reversal|=(a.to_quaternion().inverted()@h.normalized()).dot(h0)<0
   back=math.degrees(math.asin(max(-1,min(1,-u.dot(f)))));rear|=back>(12 if u.dot(up)>0 else 2)
   item['max_rear_degrees']=max(item['max_rear_degrees'],back)
   if previous:
    step=(c.translation-previous[ns[-1]].translation).length
    if step>item['max_hand_step_m']:item['max_hand_step_m']=step;item['worst_jump_time']=(frame-1)/60
  item['elbow_reversals']+=reversal;item['rear_reach_frames']+=rear;previous=p
  if frame in (1,row['frames']):ends.setdefault(key,[]).append({n:list(m.translation) for n,m in p.items()})
 report['clips'].append(item);print('SCREEN',item,flush=True)
zero=[key for key in ends if key.startswith('ZeroG')]
report['zero_g_endpoint_max_m']=max((Vector(ends[a][1][n])-Vector(ends[b][0][n])).length for a in zero for b in zero for n in ends[a][0])
(OUT/'Report.json').write_text(json.dumps(report,indent=2))
shots=[('Vexa','g1',16.233333,angle) for angle in ('front','back','side')]+[('Vexa','g1',t,'front') for t in (15.8,16.0,16.5,16.7)]
shots += [('Vexa',key,t,'front') for key,t in [('g2',1.266666),('b1',3.4),('b2',4.0)]]
shots += [(who,key,t,angle) for who,key,t in [('Vexa','ZeroG_01_Drift',8),('Roxie','ZeroG_02_Spiral',8),('Jinx','ZeroG_03_Butterfly',7),('Vesper','ZeroG_04_Inversion',8),('Vexa','ZeroG_05_LateralArc',7)] for angle in ('front','back')]
for ix,(who,key,t,angle) in enumerate(shots):
 bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021'/(who+'_Character_Options.blend')),load_ui=False)
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear()
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();forearm_markers.add(rig)
 with bpy.data.libraries.load(str(D/'Refined_ActionLibrary.blend'),link=False) as (a,b):b.actions=['A_F3_Refined_'+key]
 act=b.actions[0];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 scene=bpy.context.scene;scene.render.fps=60;scene.frame_set(round(t*60)+1)
 scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
 scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('ReviewWorld');scene.world.color=(.035,.045,.055)
 scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation+Vector((0,0,.15))
 delta={'front':Vector((0,-6,1)),'back':Vector((0,6,1)),'side':Vector((6,0,1))}[angle]
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.7
 cam.location=center+delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/f'{ix:02}_{who}_{key}_{angle}.png');bpy.ops.render.render(write_still=True)
 report['images'].append({'who':who,'clip':key,'time':t,'angle':angle,'path':scene.render.filepath})
 print('RENDERED',ix,flush=True)
(OUT/'Report.json').write_text(json.dumps(report,indent=2));print('REVIEW_DONE',flush=True)
