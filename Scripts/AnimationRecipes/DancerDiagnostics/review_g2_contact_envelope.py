import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Reversible G2 approach/release candidate. Body translation, no arm IK.

The clear source570-770 passage is retained. A one-second speed ramp at each
end leaves the source playback at0.2 in the middle. Half the ramp integral is
added to the duration, so endpoints decelerate without a frozen-key snap.
"""
from pathlib import Path
code=(_recipe_dir/'review_g2_supported_passage.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('hinge={}')],__file__,'exec'))
O=R/'G2ContactEnvelope';O.mkdir(exist_ok=True)
approach=release=2.5;ramp=1.;motion=(770-570)/12+ramp;duration=approach+motion+release

def smooth(t):
 t=max(0.,min(1.,t));return t*t*t*(10-15*t+6*t*t)

def distance(t):
 # Integral of smoothstep velocity; its integral on[0,1] is0.5.
 t=max(0.,min(motion,t))
 def integral(x):return 2.5*x**4-3*x**5+x**6
 if t<ramp:return ramp*integral(t/ramp)
 if t>motion-ramp:return motion-ramp-ramp*integral((motion-t)/ramp)
 return t-ramp*.5

def sample_envelope(t):
 source=570+12*distance(t-approach)
 p=sample_passage(source)
 opening=1-smooth(t/approach) if t<approach else smooth((t-approach-motion)/release)
 shift=Matrix.Translation(Vector((0,-.4,0))*opening)
 p={n:shift@m for n,m in p.items()}
 # Recover source-local finger rotations; arm locals and hand frame stay intact.
 lo=min(int(source)-start,end-start);hi=min(lo+1,end-start);f=source-start-lo
 for pb in ordered:
  n=pb.name
  if n in finger_basis:
   neutral=local_frames[lo][n].lerp(local_frames[hi][n],f)
   p[n]=p[parent[n]]@rel[n]@finger_basis[n].lerp(neutral,opening)
 return p,source,opening

rows=[];last=None;last_velocity=None
for i in range(round(duration*60)+1):
 t=i/60;p,source,opening=sample_envelope(t);minimum=1e3;collisions={}
 for mesh in meshes:
  name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);rad=triangle_radii(pts,tri);z=pts[tri,2];active=(z.max(axis=1)>0)&(z.min(axis=1)<5)
  minimum=min(minimum,float((rad[active]-.025).min()));bad=(rad<.025-.00001)&active
  if bad.any():collisions[name]={'triangles':int(bad.sum()),'penetration_mm':float((.025-rad[bad]).max()*1000)}
 pelvis=p['pelvis'];speed=acceleration=angular=0
 if last:
  velocity=(pelvis.translation-last.translation)*60;speed=velocity.length
  angular=math.degrees(2*math.acos(min(1,abs(pelvis.to_quaternion().dot(last.to_quaternion())))))*60
  if last_velocity is not None:acceleration=((velocity-last_velocity)*60).length
  last_velocity=velocity.copy()
 last=pelvis.copy()
 rows.append({'time':t,'source':source,'opening':opening,'collisions':collisions,'gap_mm':minimum*1000,'speed_mps':speed,'angular_dps':angular,'acceleration_mps2':acceleration})
summary={'samples':len(rows),'seconds':duration,'collision_samples':sum(bool(x['collisions']) for x in rows),'minimum_gap_mm':min(x['gap_mm'] for x in rows),'max_speed_mps':max(x['speed_mps'] for x in rows),'max_acceleration_mps2':max(x['acceleration_mps2'] for x in rows),'max_angular_dps':max(x['angular_dps'] for x in rows)}
(O/'Audit.json').write_text(json.dumps({'summary':summary,'sources':hashes,'samples':rows,'scope':'Contact envelope candidate, no loop or artistic/native acceptance'},indent=2),encoding='utf-8')
print('G2_ENVELOPE',summary,flush=True)
for time in [0,1.25,2.5,3,4,approach+motion-1,approach+motion,approach+motion+1.25,duration]:
 p,_,_=sample_envelope(time);apply_pose(p);center=Vector((0,-.15,2.8));cam.data.ortho_scale=3.;s.render.resolution_x=s.render.resolution_y=700
 for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{time:06.2f}_{view}.png');bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
