import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Full character and opposing close-ups of the isolated leg-plane proof."""
import bpy,sys,math,json,os
from pathlib import Path
from mathutils import Vector,Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
CHARACTER='Vexa';assert CHARACTER in ('Roxie','Vexa','Jinx','Vesper')
SHOULDER=True
assert not SHOULDER or CHARACTER=='Vexa', 'One repair target: Vexa'
stem='Vexa_Shoulder' if SHOULDER else CHARACTER+'_LegPlane'
O=R/'VexaUnderarmReview';O.mkdir(exist_ok=True)
import forearm_markers
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021'/(CHARACTER+'_Character_Options.blend')),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
replacement=tuple(CHARACTER+x for x in ('_Nude_Legs','_Nude_Torso','_Bottom'))
for n in replacement:
 ob=bpy.data.objects.get(n)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
with bpy.data.libraries.load(str(D/(stem+'_Proof.blend')),link=False) as (a,b):
 b.objects=list(replacement);b.actions=['A_F3_Vexa_Shoulder_ZeroG_02_Spiral' if SHOULDER else 'A_F3_LegPlane_ZeroG_02_Spiral']
for ob in b.objects:
 s.collection.objects.link(ob);world=ob.matrix_world.copy();ob.parent=rig;ob.matrix_world=world
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig;mod.use_deform_preserve_volume=False
act=b.actions[0];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
bpy.context.view_layer.update();forearm_markers.add(rig)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True
s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('LegMotionReview');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.fps=60
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'

import numpy as np
from shoulder_support import shoulder_mask
torso=bpy.data.objects['Vexa_Nude_Torso'];center_rest=rig.matrix_world@rig.data.bones['upperarm_l'].head_local
mask,boundary=shoulder_mask(torso,[center_rest]);group=torso.vertex_groups.new(name='REVIEW_LeftUnderarmOnly')
for i,w in enumerate(mask):
 if w>0:group.add([i],float(w),'REPLACE')
mod=torso.modifiers.new('REVIEW_LeftUnderarmCorrective','CORRECTIVE_SMOOTH');mod.vertex_group=group.name;mod.factor=1.;mod.iterations=5;mod.rest_source='ORCO';mod.use_pin_boundary=True
report={'scope':'Vexa left shoulder only, private comparison; no source writes','poses':[]}
def coords():
 ev=torso.evaluated_get(bpy.context.evaluated_depsgraph_get());return np.array([tuple(ev.matrix_world@v.co) for v in ev.data.vertices])
for t in (8,9.033333,12.2):
 s.frame_set(round(1+t*60));mod.show_viewport=False;mod.show_render=False;bpy.context.view_layer.update();before=coords()
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
 center=(rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation
 for count in (0,5,20):
  mod.show_viewport=count>0;mod.show_render=count>0;mod.iterations=max(count,1);bpy.context.view_layer.update();after=coords();delta=np.linalg.norm(after-before,axis=1)
  report['poses'].append({'seconds':t,'iterations':count,'max_delta_m':float(delta.max()),'outside_mask_delta_m':float(delta[mask==0].max()),'boundary_delta_m':float(delta[list(boundary)].max())})
  for view,offset in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15)))]:
   cam.data.ortho_scale=.72;cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{count}_{view}.png');bpy.ops.render.render(write_still=True)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('VEXA_UNDERARM_REVIEW_DONE',flush=True)
