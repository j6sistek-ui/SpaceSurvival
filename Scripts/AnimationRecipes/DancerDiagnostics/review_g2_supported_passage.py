import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Dense G2 contact feasibility; keep local arms, move the body about its grip."""
from pathlib import Path
exec(compile((_recipe_dir/'audit_supported_contact_motion.py').read_text().split("report={'sources':hashes,'grip_source'")[0],__file__,'exec'))
O=R/'G2SupportedPassage';O.mkdir(exist_ok=True)
act=acts['g2'];rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
start,end=525,770;rate=.2;fps=60;originals=[]
for frame in range(start,end+1):
 s.frame_set(frame);bpy.context.view_layer.update();originals.append({b.name:(rig.matrix_world@b.matrix).copy() for b in ordered})
rig.animation_data_clear()
local_frames=[{n:((p[parent[n]]@rel[n]) if parent[n] else rel[n]).inverted()@p[n] for n in names} for p in originals]
def sample_passage(source):
 lo=min(int(source)-start,end-start);hi=min(lo+1,end-start);f=source-start-lo;original={}
 for n in names:
  base=original[parent[n]]@rel[n] if parent[n] else rel[n];original[n]=base@local_frames[lo][n].lerp(local_frames[hi][n],f)
 return supported(original)
hinge={}
for side in ['l','r']:
 a,b,c=[rest[n+'_'+side] for n in ['upperarm','lowerarm','hand']];hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(c.translation-b.translation).normalized()
rows=[];last=None
for i in range(round((end-start)/60/rate*fps)+1):
 source=start+i/fps*60*rate;p=sample_passage(source);collisions={};minimum=1e3;bounds=[]
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
 pelvis=p['pelvis'];speed=angular=0
 if last:speed=(pelvis.translation-last.translation).length*fps;angular=math.degrees(2*math.acos(min(1,abs(pelvis.to_quaternion().dot(last.to_quaternion())))))*fps
 last=pelvis.copy();pts=np.concatenate(bounds)
 rows.append({'source_frame':source,'time':i/fps,'collisions':collisions,'gap_mm':minimum*1000,'arms':arms,'speed_mps':speed,'angular_dps':angular,'bounds':[pts.min(axis=0).tolist(),pts.max(axis=0).tolist()]})
summary={'samples':len(rows),'collision_samples':sum(bool(x['collisions']) for x in rows),'reversals':sum(a['reversal'] for x in rows for a in x['arms']),'rear_flags':sum(a['rear_flag'] for x in rows for a in x['arms']),'max_speed_mps':max(x['speed_mps'] for x in rows),'max_angular_dps':max(x['angular_dps'] for x in rows),'minimum_gap_mm':min(x['gap_mm'] for x in rows)}
(O/'Audit.json').write_text(json.dumps({'summary':summary,'sources':hashes,'frames':[start,end],'rate':rate,'samples':rows,'scope':'Feasibility only; no loop, visual, garment or production acceptance'},indent=2));print('G2_SUPPORTED',summary,flush=True)
for source in [525,580,640,700,770]:
 p=sample_passage(source);apply_pose(p);center=Vector((.45,-.20,2.9));cam.data.ortho_scale=4;s.render.resolution_x=s.render.resolution_y=700
 for view,offset in [('front',Vector((3,-5,.6))),('back',Vector((-3,5,.4)))]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{source}_{view}.png');bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
print('G2_SUPPORTED_DONE',flush=True)
