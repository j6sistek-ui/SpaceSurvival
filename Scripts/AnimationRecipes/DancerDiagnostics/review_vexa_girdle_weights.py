import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Actual saved Vexa shoulder weights, rendered in an unsaved diagnostic scene."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
O=R/'VexaGirdleStudy/Weights';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_ShoulderGirdle_Study.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
torso=bpy.data.objects['Vexa_Nude_Torso']
for obj in s.objects:
 if obj.type=='MESH':obj.hide_render=obj!=torso
if torso.data.shape_keys:
 torso.data.shape_keys.animation_data_clear()
 for key in torso.data.shape_keys.key_blocks:key.value=0
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='FLAT';s.display.shading.color_type='VERTEX';s.display.shading.show_shadows=False
s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('WeightReview');s.world.color=(.035,.045,.055)
s.render.resolution_x=700;s.render.resolution_y=600;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
center=Vector((0,0,1.28));cam.location=center+Vector((0,3,.08));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
attribute=torso.data.color_attributes.new(name='REVIEW_Weights',type='FLOAT_COLOR',domain='POINT');torso.data.color_attributes.active_color=attribute
def color(weight):
 # Blue -> cyan -> green -> yellow -> red; exact raw influence, no rescaling.
 w=max(0,min(1,weight))*4;i=min(3,int(w));t=w-i
 stops=((0,0,.65),(0,.7,1),(0,1,0),(1,1,0),(1,0,0))
 return tuple(stops[i][axis]*(1-t)+stops[i+1][axis]*t for axis in range(3))+(1,)
records=[]
for name in ('clavicle_l','REVIEW_scapula_l','spine_05','upperarm_l'):
 group=torso.vertex_groups[name];weights=[]
 for vertex in torso.data.vertices:
  weight=next((g.weight for g in vertex.groups if g.group==group.index),0)
  weights.append(weight);attribute.data[vertex.index].color=color(weight)
 s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
 records.append({'group':name,'nonzero':sum(w>0 for w in weights),'max':max(weights)})
(O/'Report.json').write_text(json.dumps(records,indent=2));print('VEXA_WEIGHT_VIEWS_DONE',flush=True)
