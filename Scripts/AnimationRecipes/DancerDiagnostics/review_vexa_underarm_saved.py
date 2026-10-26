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
stem='Vexa_Underarm'
O=R/'VexaUnderarmProof';O.mkdir(exist_ok=True)
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

# Hide hair only in this diagnostic session, preserving the saved character.
hidden=[]
for ob in s.objects:
 if ob.type=='MESH' and 'hair' in ob.name.casefold():ob.hide_render=True;hidden.append(ob.name)
report={'hidden_for_inspection':hidden,'captures':[]}
for t in (0,4,8,9.033333,9.5,12.2,14,16):
 s.frame_set(round(1+t*60));bpy.context.view_layer.update()
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
 center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 for view,offset in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15))),('side',Vector((3,0,.15)))]:
  cam.data.ortho_scale=.9;cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{view}.png');bpy.ops.render.render(write_still=True);report['captures'].append(s.render.filepath)
(O/'ReloadViews.json').write_text(json.dumps(report,indent=2));print('VEXA_UNDERARM_RELOAD_DONE',flush=True)
