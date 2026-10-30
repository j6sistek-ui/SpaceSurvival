import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Opposing whole-body and hand views of the collision-screened release."""
from pathlib import Path
exec(compile((_recipe_dir/'review_supported_release.py').read_text().split('for i in range(round((end-start)/60/rate*fps)+1):')[0],__file__,'exec'))
for source in [780,830,881,912,920,925,930,935,940,960,1000]:
 p,blend=sample_release(source);apply_pose(p);center=Vector((.45,-.20,2.9));cam.data.ortho_scale=3.2;s.render.resolution_x=s.render.resolution_y=800
 for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{source}_{view}.png');bpy.ops.render.render(write_still=True)
 if 920<=source<=940:
  center=p['hand_r'].translation;cam.data.ortho_scale=.5
  for view,offset in [('hand_front',Vector((3,-5,.6))),('hand_back',Vector((-3,5,.4)))]:
   cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{source}_{view}.png');bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('SUPPORTED_RELEASE_VIEWS_DONE',flush=True)
