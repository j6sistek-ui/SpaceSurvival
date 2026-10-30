import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Opposing lit views of the local axilla candidate, source files unchanged."""
from pathlib import Path
exec((Path(__file__).resolve().parent/'review_axilla_color.py').read_text().split('for sec in (4,9.033333):')[0])
out=R/'VexaAxillaOpposing';out.mkdir(exist_ok=True);report['views']=[]
appearance(True)
for li in lights:li.data.color=(1,1,1)
for sec in (4,8,9.033333,12.2):
 s.frame_set(round(1+sec*60));bpy.context.view_layer.update()
 chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
 center=((rig.matrix_world@rig.pose.bones['upperarm_l'].matrix).translation+(rig.matrix_world@rig.pose.bones['upperarm_r'].matrix).translation)*.5
 for view,off in [('back',Vector((0,3,.15))),('opposite',Vector((2,-2,.15)))]:
  cam.location=center+chest@off;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  for li,delta in zip(lights,(off*.5+Vector((-.4,0,1.3)),off*.4+Vector((1,0,.6)),-off*.4+Vector((0,0,1)))):
   li.location=center+chest@delta;li.rotation_euler=(center-li.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(out/f'{sec:g}_{view}.png');bpy.ops.render.render(write_still=True);report['views'].append(s.render.filepath)
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in before.items())
(out/'Report.json').write_text(json.dumps(report,indent=2));print('AXILLA_OPPOSING_DONE')
