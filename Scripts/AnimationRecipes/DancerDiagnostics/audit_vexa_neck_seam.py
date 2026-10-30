import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare paired modular neck vertices and original left/right weights."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaShoulderFoundation'
from coordinated_girdle import coordinate
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');torso=bpy.data.objects['Vexa_Nude_Torso'];head=bpy.data.objects['Eden_Pink_CharacterMesh0.001'];r=json.loads((O/'Report.json').read_text());pairs=r['neck_pairs']
def weights(o,i):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups if g.weight>1e-8}
report={'pairs':[],'poses':[],'mirror_details':[]}
for i,j,d in pairs:
 a=weights(torso,i);b=weights(head,j)
 report['pairs'].append({'torso':i,'head':j,'position':list(torso.matrix_world@torso.data.vertices[i].co),'weight_L1':sum(abs(a.get(n,0)-b.get(n,0)) for n in set(a)|set(b)),'torso_weights':a,'head_weights':b})
for row in r['mirror']['largest_weight_mismatches']:
 i,j=row['left'],row['right'];report['mirror_details'].append(dict(row,position=list(torso.matrix_world@torso.data.vertices[i].co),left_weights=weights(torso,i),right_weights=weights(torso,j)))
with bpy.data.libraries.load(str(D/'Vexa_LegPlane_Proof.blend'),link=False) as (a,b):b.actions=['A_F3_LegPlane_ZeroG_02_Spiral']
act=b.actions[0];ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:(rig.matrix_world@b.bone.matrix_local).copy() for b in ordered};parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered}
for mode in ('baseline','coordinated'):
 for f in (1,241,543,733,961):
  rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];s.frame_set(f);bpy.context.view_layer.update()
  if mode=='coordinated':
   pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};rig.animation_data_clear();coordinate(pose,rest,parent,desc,True);local={n:rig.matrix_world.inverted()@m for n,m in pose.items()}
   for pb in ordered:
    base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local;pb.matrix_basis=base.inverted()@local[pb.name]
   bpy.context.view_layer.update()
  dg=bpy.context.evaluated_depsgraph_get();a=torso.evaluated_get(dg);b=head.evaluated_get(dg)
  gaps=[((a.matrix_world@a.data.vertices[i].co)-(b.matrix_world@b.data.vertices[j].co)).length for i,j,_ in pairs]
  report['poses'].append({'mode':mode,'frame':f,'max_gap_m':max(gaps),'worst_pair':pairs[int(np.argmax(gaps))]})
(O/'NeckSeam.json').write_text(json.dumps(report,indent=2));print('NECK_SEAM',json.dumps({'max_pair_weight_difference':max(v['weight_L1'] for v in report['pairs']),'poses':report['poses'],'mirror_details':report['mirror_details'][:3]}),flush=True)
