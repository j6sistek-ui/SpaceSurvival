import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read rest-rig compatibility before testing another clip on Vexa."""
import bpy,json
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
bpy.ops.wm.open_mainfile(filepath=str(D/'Vexa_ContinuousDistal_Proof.blend'),load_ui=False)
target=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rest={b.name:target.matrix_world@b.matrix_local for b in target.data.bones}
with bpy.data.libraries.load(str(D/'Refined_ActionLibrary.blend'),link=False) as (src,dst):
 names=list(src.objects);actions=list(src.actions);dst.objects=src.objects
loaded=[o for o in dst.objects if o and o.type=='ARMATURE']
for ob in loaded:bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update()
report={'objects':names,'actions':actions,'target_bones':len(rest),'target_object':target.name,'target_matrix':[list(x) for x in target.matrix_world],'rigs':[]}
for rig in loaded:
 shared=set(rest)&set(b.name for b in rig.data.bones)
 error=max(max(abs(rest[n][r][c]-(rig.matrix_world@rig.data.bones[n].matrix_local)[r][c]) for r in range(4) for c in range(4)) for n in shared)
 local_error=max(max(abs(target.data.bones[n].matrix_local[r][c]-rig.data.bones[n].matrix_local[r][c]) for r in range(4) for c in range(4)) for n in shared)
 report['rigs'].append({'name':rig.name,'shared_bones':len(shared),'total_bones':len(rig.data.bones),'rest_max_element_error':error,'local_rest_error':local_error,'object_matrix':[list(x) for x in rig.matrix_world]})
(R/'VexaDistalRepair/ActionReuse.json').write_text(json.dumps(report,indent=2))
print('ACTION_REUSE',json.dumps(report),flush=True)
