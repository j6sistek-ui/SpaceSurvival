import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Add a deliberate floating return outside the pole, preserving arm lengths."""
from pathlib import Path
code=(_recipe_dir/'review_g2_contact_envelope.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('rows=[];last=None;last_velocity=None')],__file__,'exec'))
O=R/'G2ReturnLoop';O.mkdir(exist_ok=True)
envelope_seconds=duration;duration+=8.
initial=sample_envelope(0)[0];final=sample_envelope(envelope_seconds)[0]
park=Matrix.Translation((0,-1.,0))
park_start={n:park@m for n,m in initial.items()};park_end={n:park@m for n,m in final.items()}
def locals_of(p):return {n:((p[parent[n]]@rel[n]) if parent[n] else rel[n]).inverted()@p[n] for n in names}
local_start,local_end=locals_of(park_start),locals_of(park_end)
def sample_loop(t):
 if t<=envelope_seconds:return sample_envelope(t)[0]
 t-=envelope_seconds
 if t<2:
  shift=Matrix.Translation((0,-smooth(t/2),0));return {n:shift@m for n,m in final.items()}
 if t<6:
  a=smooth((t-2)/4);p={}
  for n in names:
   base=p[parent[n]]@rel[n] if parent[n] else rel[n]
   p[n]=base@local_end[n].lerp(local_start[n],a)
  return p
 shift=Matrix.Translation((0,-(1-smooth((t-6)/2)),0))
 return {n:shift@m for n,m in initial.items()}

hinge={}
for side in ['l','r']:
 a,b,c=[rest[n+'_'+side] for n in ['upperarm','lowerarm','hand']];hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(c.translation-b.translation).normalized()
rows=[];last=None
for i in range(round(duration*60)+1):
 t=i/60;p=sample_loop(t);collisions={};minimum=1e3;bounds=[]
 for mesh in meshes:
  name,_,tri,_,_,grip=mesh;pts=surface(p,mesh);bounds.append(pts);rad=triangle_radii(pts,tri);z=pts[tri,2];active=(z.max(axis=1)>0)&(z.min(axis=1)<5)
  minimum=min(minimum,float((rad[active]-.025).min()));bad=(rad<.025-.00001)&active
  if bad.any():collisions[name]={'triangles':int(bad.sum()),'penetration_mm':float((.025-rad[bad]).max()*1000)}
 arms=[];chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();up=chest@Vector((0,0,1));forward=chest@Vector((0,-1,0))
 for side in ['l','r']:
  a,b,c=[p[n+'_'+side] for n in ['upperarm','lowerarm','hand']];upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized();h=upper.cross(lower);flex=math.degrees(upper.angle(lower));alignment=1.
  if h.length>.1:alignment=(a.to_quaternion().inverted()@h.normalized()).dot(hinge[side])
  rear=math.degrees(math.asin(max(-1,min(1,-upper.dot(forward)))));limit=10 if upper.dot(up)>0 else 0
  arms.append({'side':side,'elbow_flex':flex,'hinge_alignment':alignment,'rear':rear,'reversal':alignment<0 and flex>10,'rear_flag':rear>limit+2})
 pts=np.concatenate(bounds);pelvis=p['pelvis'];speed=angular=0
 if last:speed=(pelvis.translation-last.translation).length*60;angular=math.degrees(2*math.acos(min(1,abs(pelvis.to_quaternion().dot(last.to_quaternion())))))*60
 last=pelvis.copy()
 rows.append({'time':t,'collisions':collisions,'gap_mm':minimum*1000,'arms':arms,'speed_mps':speed,'angular_dps':angular,'radial_extent_m':float(np.linalg.norm(pts[:,:2],axis=1).max()),'height_range_m':[float(pts[:,2].min()),float(pts[:,2].max())]})
summary={'samples':len(rows),'seconds':duration,'collision_samples':sum(bool(x['collisions']) for x in rows),'reversals':sum(a['reversal'] for x in rows for a in x['arms']),'rear_flags':sum(a['rear_flag'] for x in rows for a in x['arms']),'max_speed_mps':max(x['speed_mps'] for x in rows),'max_angular_dps':max(x['angular_dps'] for x in rows),'radial_extent_m':max(x['radial_extent_m'] for x in rows),'loop_matrix_error':max(float(np.abs(np.array(initial[n])-np.array(sample_loop(duration)[n])).max()) for n in names)}
(O/'Audit.json').write_text(json.dumps({'summary':summary,'sources':hashes,'samples':rows,'scope':'G2 selected-passage loop candidate; no native/artistic or full-original coverage acceptance'},indent=2),encoding='utf-8')
print('G2_LOOP',summary,flush=True)
for time in [envelope_seconds,envelope_seconds+2,envelope_seconds+3,envelope_seconds+4,envelope_seconds+5,envelope_seconds+6,duration]:
 apply_pose(sample_loop(time));center=Vector((0,-.65,2.8));cam.data.ortho_scale=3.4;s.render.resolution_x=s.render.resolution_y=700
 for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{time:06.2f}_{view}.png');bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
