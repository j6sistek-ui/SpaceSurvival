import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Measure native importer pruning against the saved source; no source writes."""
import bpy,json,numpy as np
from pathlib import Path
P=R.parents[2]
native=json.loads((R/'NativeHipProof.json').read_text())
names={n for row in native['assets'] for n in row.get('morphs',[])}
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene;rows=[]
for ob in s.objects:
 if ob.type!='MESH' or not ob.data.shape_keys:continue
 keys=ob.data.shape_keys.key_blocks;missing=[k for k in keys if k.name.startswith('REVIEW_') and k.name not in names]
 base=np.array([tuple(v.co) for v in keys[0].data]);deltas=[np.array([tuple(v.co) for v in k.data])-base for k in missing]
 maximum=0.;when=0
 for frame in range(s.frame_start,s.frame_end+1):
  s.frame_set(frame)
  if not missing:continue
  combined=sum(k.value*d for k,d in zip(missing,deltas))
  error=float(np.linalg.norm(combined,axis=1).max()*max(ob.matrix_world.to_scale()))
  if error>maximum:maximum=error;when=frame
 rows.append({'mesh':ob.name,'missing':[k.name for k in missing],'max_combined_rest_error_m':maximum,'frame':when,'individual_max_delta_m':{k.name:float(np.linalg.norm(d,axis=1).max()*max(ob.matrix_world.to_scale())) for k,d in zip(missing,deltas)}})
report={'samples':s.frame_end-s.frame_start+1,'meshes':rows,'note':'Rest-space curve-weighted error only; not native pose parity or visual acceptance'}
(R/'HipMorphPruning.json').write_text(json.dumps(report,indent=2));print('HIP_PRUNING',report,flush=True)
