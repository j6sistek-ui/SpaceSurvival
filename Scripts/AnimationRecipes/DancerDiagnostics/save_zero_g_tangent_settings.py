import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Retain the black-mask experiment; this is not a verified normal fix."""
import unreal as u,json,hashlib,traceback
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/VexaZeroGSharedHipProof_20261026';report={'errors':[]}
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
root=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed'
protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for sub in ('VexaHandIsolationProof_20261026','VexaContinuousDistalProof_20261025') for p in (root/sub).rglob('*') if p.is_file()}
try:
 mesh=u.load_asset(B+'/SK_VexaZeroGShared');editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem);assert mesh
 report['before']=[{'section':i,'recompute':editor.get_section_recompute_tangent(mesh,0,i),'mask':editor.get_section_recompute_tangents_vertex_mask_channel(mesh,0,i)} for i in range(editor.get_num_sections(mesh,0))]
 for i in range(editor.get_num_sections(mesh,0)):
  assert editor.set_section_recompute_tangent(mesh,0,i,True)
  assert editor.set_section_recompute_tangents_vertex_mask_channel(mesh,0,i,1)
 assert u.EditorAssetLibrary.save_loaded_asset(mesh,False)
 report['after']=[{'section':i,'recompute':editor.get_section_recompute_tangent(mesh,0,i),'mask':editor.get_section_recompute_tangents_vertex_mask_channel(mesh,0,i)} for i in range(editor.get_num_sections(mesh,0))]
 assert all(x['recompute'] and x['mask']==1 for x in report['after'])
 report['old_proofs_unchanged']=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items());assert report['old_proofs_unchanged']
 report['mesh_sha256']=hashlib.sha256((root/'VexaZeroGSharedHipProof_20261026/SK_VexaZeroGShared.uasset').read_bytes()).hexdigest();report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'ZeroGSharedHip/SavedTangents.json').write_text(json.dumps(report,indent=2));print('ZERO_G_SAVED_TANGENTS',report,flush=True)
