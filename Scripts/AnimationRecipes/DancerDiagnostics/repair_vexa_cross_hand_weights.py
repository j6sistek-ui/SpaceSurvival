import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Remove demonstrated opposite-hand influences, preserving all other data."""
import bpy,json,hashlib
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_ContinuousDistal_Proof.blend';output=D/'Vexa_HandIsolation_Proof.blend';assert not output.exists()
digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest=='d70f17f7f766e6eb44a41c407703066b4d9bece496fad0c8a8112cd3427c2500'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
ob=bpy.data.objects['Vexa_Continuous_Hands'];rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
weights=lambda v:{ob.vertex_groups[g.group].name:g.weight for g in v.groups}
before=[weights(v) for v in ob.data.vertices];prefix=('hand_','thumb_','index_','middle_','ring_','pinky_')
report={'source_sha256':digest,'method':'Only demonstrated opposite-hand influence removed, remaining influences renormalized; no finger animation edit','changed':[]}
for v in ob.data.vertices:
 old=before[v.index];totals={side:sum(w for n,w in old.items() if n.startswith(prefix) and n.endswith('_'+side)) for side in ('l','r')}
 side=max(totals,key=totals.get);other='r' if side=='l' else 'l'
 if totals[side]<.5:continue
 bad={n:w for n,w in old.items() if n.startswith(prefix) and n.endswith('_'+other) and w>0}
 if not bad:continue
 # Confirm region independently from bone labels: each touched point must be
 # much closer to its owning wrist than the opposite wrist in the rest pose.
 p=ob.matrix_world@v.co
 own=(p-rig.matrix_world@rig.data.bones['hand_'+side].head_local).length
 opposite=(p-rig.matrix_world@rig.data.bones['hand_'+other].head_local).length
 assert own<opposite*.25,(v.index,own,opposite)
 clean={n:w for n,w in old.items() if n not in bad};total=sum(clean.values());assert total>.85
 for n in bad:ob.vertex_groups[n].remove([v.index])
 for n,w in clean.items():ob.vertex_groups[n].add([v.index],w/total,'REPLACE')
 report['changed'].append({'vertex':v.index,'side':side,'removed':bad,'before':old,'after':weights(v),'rest_distance_own_m':own,'rest_distance_opposite_m':opposite})
assert report['changed']
changed={row['vertex'] for row in report['changed']}
for v in ob.data.vertices:
 if v.index not in changed:assert weights(v)==before[v.index]
 else:assert abs(sum(weights(v).values())-1)<1e-6
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
report['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest();report['untouched_vertices']=len(before)-len(changed)
(R/'GBFingerShape/Repair.json').write_text(json.dumps(report,indent=2));print('CROSS_HAND_REPAIR',len(changed),report['output_sha256'],flush=True)
# Matched controls use the same preserved action library and camera recipes.
code=(Path(__file__).resolve().parent/'probe_gb_finger_shape.py').read_text().replace('Vexa_ContinuousDistal_Proof.blend','Vexa_HandIsolation_Proof.blend').replace("O=R/'GBFingerShape'","O=R/'GBFingerShape/After'")
exec(compile(code,str(R/'probe_gb_finger_shape.py'),'exec'),{'__file__':str(R/'probe_gb_finger_shape.py'),'__name__':'__main__'})
code=(Path(__file__).resolve().parent/'audit_gb_hand_spikes.py').read_text().replace('Vexa_ContinuousDistal_Proof.blend','Vexa_HandIsolation_Proof.blend').replace("R/'GBFingerShape/EdgeAudit.json'","R/'GBFingerShape/After/EdgeAudit.json'")
exec(compile(code,str(R/'audit_gb_hand_spikes.py'),'exec'),{'__file__':str(R/'audit_gb_hand_spikes.py'),'__name__':'__main__'})
