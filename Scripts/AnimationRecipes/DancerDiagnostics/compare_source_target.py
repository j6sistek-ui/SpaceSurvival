import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Matched source/retarget poses; never saves original characters or motions."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
P=R.parents[2]
import forearm_markers
out=R/'SourceComparison';out.mkdir(exist_ok=True)
audit=json.loads((R/'BaselineArmScreen.json').read_text())
report=[]
for row in audit['clips']:
 clip=row['clip'];times=[row['worst'][0]['time'],4.0]
 for ix,t in enumerate(times):
  bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
  scene=bpy.context.scene;scene.render.fps=60
  target=next(o for o in scene.objects if o.type=='ARMATURE')
  before=set(bpy.data.objects)
  bpy.ops.import_scene.fbx(filepath=str(R/'SourceBaseline'/f'A_F3_Baseline_{clip}_Source_Anim.fbx'))
  imported=set(bpy.data.objects)-before;rt=next(o for o in imported if o.type=='ARMATURE')
  action=rt.animation_data.action
  target.animation_data_create();target.animation_data.action=action;target.animation_data.action_slot=action.slots[0]
  for ob in imported:bpy.data.objects.remove(ob,do_unlink=True)
  forearm_markers.add(target)
  before=set(bpy.data.objects)
  bpy.ops.import_scene.gltf(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/MotionSources'/f'{clip}_default.glb'))
  imported=set(bpy.data.objects)-before;source=next(o for o in imported if o.type=='ARMATURE')
  # Match character roots in two columns without altering their animation keys.
  roots=[ob for ob in imported if ob.parent not in imported]
  for ob in roots:ob.location.x-=2.2
  target.location.x+=.6
  scene.frame_set(round(t*60)+int(action.frame_range[0]))
  scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO'
  scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
  scene.display.shading.show_cavity=True;scene.display.shading.show_specular_highlight=False
  scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('ComparisonWorld');scene.world.color=(.035,.045,.055)
  scene.render.resolution_x=1100;scene.render.resolution_y=700;scene.render.resolution_percentage=100
  center=(target.matrix_world@target.pose.bones['pelvis'].matrix).translation
  center.x-=1.4
  for angle,delta in [('front',Vector((0,-6,1))),('back',Vector((0,6,1)))]:
   bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=5
   cam.location=center+delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
   scene.render.filepath=str(out/f'{clip}_{ix}_{angle}.png');bpy.ops.render.render(write_still=True)
   report.append({'clip':clip,'time':t,'angle':angle,'path':scene.render.filepath,'source_world':list(source.matrix_world.translation),'target_world':list(target.matrix_world.translation)})
  print('COMPARE_DONE',clip,t,flush=True)
(out/'Report.json').write_text(json.dumps(report,indent=2))
