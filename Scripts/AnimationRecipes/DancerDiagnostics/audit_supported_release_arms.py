import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Owner reach/reversal screen on the saved release candidate's actual poses."""
from pathlib import Path
exec(compile((_recipe_dir/'review_supported_release.py').read_text().split('for i in range(round((end-start)/60/rate*fps)+1):')[0],__file__,'exec'))
hinge={}
for side in ['l','r']:
 a,b,c=[rest[n+'_'+side] for n in ['upperarm','lowerarm','hand']]
 hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(c.translation-b.translation).normalized()
rows=[]
for i in range(1101):
 source=780+i*.2;p,_=sample_release(source)
 chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();up=chest@Vector((0,0,1));forward=chest@Vector((0,-1,0))
 for side in ['l','r']:
  a,b,c=[p[n+'_'+side] for n in ['upperarm','lowerarm','hand']]
  upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized();h=upper.cross(lower);flex=math.degrees(upper.angle(lower));alignment=1.
  if h.length>.1:alignment=(a.to_quaternion().inverted()@h.normalized()).dot(hinge[side])
  back=math.degrees(math.asin(max(-1,min(1,-upper.dot(forward)))));limit=10 if upper.dot(up)>0 else 0
  rows.append({'source_frame':source,'time':i/60,'side':side,'elbow_flex':flex,'hinge_alignment':alignment,'rear_degrees':back,'rear_limit':limit,'reversal':alignment<0 and flex>10,'rear_flag':back>limit+2})
summary={'samples':len(rows),'reversal_samples':sum(x['reversal'] for x in rows),'rear_flag_samples':sum(x['rear_flag'] for x in rows),'max_rear_degrees':max(x['rear_degrees'] for x in rows),'worst_rear':sorted(rows,key=lambda x:x['rear_degrees']-x['rear_limit'],reverse=True)[:8]}
(O/'ArmScreen.json').write_text(json.dumps({'summary':summary,'samples':rows,'scope':'Chest-relative owner reach screen; not a clinical or complete visual acceptance.'},indent=2))
print('RELEASE_ARM_SCREEN',json.dumps(summary),flush=True)
