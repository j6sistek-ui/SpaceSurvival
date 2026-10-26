import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Native matching before/after G2 on the repaired private hand mesh."""
import unreal as u,json,hashlib
from pathlib import Path
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
OLD='/Game/SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
guard=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in guard.rglob('*') if p.is_file()}
code=(Path(__file__).resolve().parent/'capture_gb_wrist_comparison.py').read_text().replace("code=source('capture_balanced_motion.py')","code=source('capture_balanced_motion.py').replace('VexaContinuousDistalProof_20261025','VexaHandIsolationProof_20261026').replace('SK_VexaContinuousDistalProof','SK_VexaHandIsolationProof').replace(\"clip=u.load_asset(BASE+'/'+asset+'_Anim')\",\"clip=u.load_asset(OLD+'/A_ShoulderResponse_g2_shoulder')\")")
code=code.replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBFastPassage/Export.json'").replace("'A_Wrist_'","'A_ArmPassage_'").replace("clip=clips['g1_after']","clips['g2_before']=u.load_asset(OLD+'/A_ShoulderResponse_g2_shoulder');clip=clips['g2_passage']")
a=code.index("events=[('g1',220,");b=code.index("OUT=R/'NativeGBWristComparison'",a)
code=code[:a]+"""segments=[]
for mode in ('before','passage'):
 for view in ('front','back'):
  segments.append({'name':mode+'_'+view,'key':'g2_'+mode,'start':.4,'frames':144,'fps':60,'camera':view})
"""+code[b:]
code=code.replace('NativeGBWristComparison','NativeG2ArmPassage')
code=code.replace("else:center=c.get_socket_location('pelvis')+up*15;loc=center+front*230+side*65+up*20","else:center=c.get_socket_location('pelvis')+up*10;loc=center+front*(235 if seg['camera']=='front' else -235)+side*45+up*15")
code=code.replace("report['ok']=not report['errors'] and len(report['captured'])==sum(x['frames'] for x in segments)","report['old_proof_unchanged']=all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())\n report['ok']=report['old_proof_unchanged'] and not report['errors'] and len(report['captured'])==sum(x['frames'] for x in segments)")
code=code.replace("'status':'Private unconstrained clips on Vexa. Spiral morph curves absent; no contact or anatomy acceptance.'","'status':'Private local G2 rephrasing, frames59-109 only. New one-vertex hand repair; Spiral corrections disabled. No pole or whole-routine acceptance.'")
exec(compile(code,__file__,'exec'))
