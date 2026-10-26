import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Inspect stretched hand edges and exact influences, without writes to art."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_ContinuousDistal_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');ob=bpy.data.objects['Vexa_Continuous_Hands']
for obj in s.objects:
 if obj.type=='MESH' and obj.data.shape_keys:
  obj.data.shape_keys.animation_data_clear()
  for key in obj.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
with bpy.data.libraries.load(str(D/'GB_ShoulderResponse_ActionLibrary.blend'),link=False) as(a,b):b.actions=['A_F3_ShoulderResponse_g1']
report={'object':ob.name,'modifiers':[(m.name,m.type) for m in ob.modifiers],'nonzero_shapes':[(k.name,k.value) for k in ob.data.shape_keys.key_blocks if k.value],'cases':[]}
for frame,mode in [(881,'animated'),(881,'neutral_fingers'),(1,'rest')]:
 rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0];s.frame_set(frame)
 bases={p.name:p.matrix_basis.copy() for p in rig.pose.bones};rig.animation_data_clear()
 for p in rig.pose.bones:p.matrix_basis=bases[p.name]
 if mode!='animated':
  for p in rig.pose.bones:
   if mode=='rest' or p.name.startswith(('thumb_','index_','middle_','ring_','pinky_')):p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(ob.data.vertices)
 rows=[]
 weights=lambda v:{ob.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-6}
 for edge in ob.data.edges:
  a,c=[ob.data.vertices[i] for i in edge.vertices];wa,wc=weights(a),weights(c)
  if max(sum(v for k,v in w.items() if k.startswith(('hand_','thumb_','index_','middle_','ring_','pinky_'))) for w in (wa,wc))<.5:continue
  before=(a.co-c.co).length;after=(me.vertices[a.index].co-me.vertices[c.index].co).length
  if before>.0005 and after/before>1.5:
   rows.append({'edge':edge.index,'ratio':after/before,'length_cm':after*100,'vertices':[{'i':v.index,'rest':list(v.co),'weights':w} for v,w in ((a,wa),(c,wc))]})
 rows.sort(key=lambda x:x['ratio'],reverse=True);report['cases'].append({'frame':frame,'mode':mode,'stretched_count':len(rows),'worst':rows[:14]});ev.to_mesh_clear()
(R/'GBFingerShape/EdgeAudit.json').write_text(json.dumps(report,indent=2));print('HAND_EDGE_AUDIT',[(c['mode'],c['stretched_count'],c['worst'][0]['ratio'] if c['worst'] else 1) for c in report['cases']],flush=True)
