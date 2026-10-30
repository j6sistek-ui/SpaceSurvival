import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Inspect actual intermediate knee bends, not just the closed curl.
The localized corrective-smooth candidate follows Blender's documented
post-armature workflow and does not alter the saved proof or original rig.
"""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=R.parents[2];O=R/'KneeRangeReview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');legs=bpy.data.objects['Roxie_Nude_Legs'];arm=next(m for m in legs.modifiers if m.type=='ARMATURE')
rest=np.array([tuple(legs.matrix_world@v.co) for v in legs.data.vertices]);knees=np.array([tuple(rig.matrix_world@rig.data.bones['calf_'+side].head_local) for side in ('l','r')]);dist=np.linalg.norm(rest[:,None,:]-knees[None,:,:],axis=2).min(axis=1);mask=np.clip((.18-dist)/.12,0,1);mask=mask*mask*(3-2*mask)
group=legs.vertex_groups.new(name='REVIEW_KneeOnly')
for i,w in enumerate(mask):
 if w>0:group.add([i],float(w),'REPLACE')
smooth=legs.modifiers.new('REVIEW_KneeCorrective','CORRECTIVE_SMOOTH');smooth.factor=.5;smooth.iterations=5;smooth.smooth_type='LENGTH_WEIGHTED';smooth.vertex_group=group.name;smooth.use_pin_boundary=True;smooth.show_viewport=False;smooth.show_render=False
report={'poses':[],'candidate':'knee-only corrective smoothing, factor0.5 / 5iterations / length-weighted','source':'https://docs.blender.org/manual/pt/5.2/modeling/modifiers/deform/corrective_smooth.html'};samples=[]
for frame in range(1,962,2):
 s.frame_set(frame);points=[(rig.matrix_world@rig.pose.bones[n].matrix).translation for n in ('thigh_l','calf_l','foot_l')]
 bend=180-math.degrees((points[0]-points[1]).angle(points[2]-points[1]));samples.append((frame,bend))
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('KneeRange');s.world.color=(.035,.045,.055);s.render.resolution_x=600;s.render.resolution_y=600;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.58
for desired in (30,60,90,110):
 frame,bend=min(samples,key=lambda x:abs(x[1]-desired));s.frame_set(frame);p=[(rig.matrix_world@rig.pose.bones[n].matrix).translation for n in ('thigh_l','calf_l','foot_l')];center=p[1];normal=(p[0]-p[1]).cross(p[2]-p[1]).normalized()
 for side in (-1,1):
  cam.location=center+normal*(3*side);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  for mode in ('linear','smooth'):
   smooth.show_viewport=(mode=='smooth');smooth.show_render=(mode=='smooth');bpy.context.view_layer.update()
   s.render.filepath=str(O/f'{desired}_{side}_{mode}.png');bpy.ops.render.render(write_still=True)
 report['poses'].append({'desired_degrees':desired,'actual_degrees':bend,'seconds':(frame-1)/60})
(O/'Report.json').write_text(json.dumps(report,indent=2));print('KNEE_RANGE_DONE',report['poses'],flush=True)
