import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Compare complete posed surfaces before/after one weight edit, no imports."""
import unreal as u,json,hashlib
from pathlib import Path
OLD='/Game/SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025';NEW='/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026'
protected=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected.rglob('*') if p.is_file()}
old=u.load_asset(OLD+'/SK_VexaContinuousDistalProof');new=u.load_asset(NEW+'/SK_VexaHandIsolationProof');assert old and new and old.skeleton==new.skeleton
meshes={'before':old,'after':new};clips={'g1':u.load_asset(OLD+'/SK_VexaContinuousDistalProof_Anim')};assert clips['g1']
# Read the documented LOD accessor rather than source-model initialization data.
lods={name:u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem).get_lod_build_settings(mesh,0).get_editor_property('bone_influence_limit') for name,mesh in meshes.items()}
wrapper=(Path(__file__).resolve().parent/'capture_vexa_hand_isolation.py').read_text();wrapper=wrapper[wrapper.index("code=(R/'capture_balanced_motion.py')"):]
wrapper=wrapper.replace("for frame in (220,881):","for frame in (481,733):").replace("for side in ('l','r'):","for side in ('l',):").replace("for view in ('palm','oblique'):","for view in ('palm',):")
wrapper=wrapper.replace("exec(compile(code+tail,__file__,'exec'))",'')
exec(compile(wrapper,__file__,'exec'))
tail=tail.replace('NativeVexaHandIsolation','NativeVexaHandIsolationSkin')
needle="   state['component'].capture_scene();state['stage']='export';return"
insert="""   dynamic=u.DynamicMesh();result=u.GeometryScript_SceneUtils.copy_mesh_from_component(c,dynamic,u.GeometryScriptCopyMeshFromComponentOptions(),False)
   query=u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic,False);vectors=u.GeometryScript_List.convert_vector_list_to_array(query[1])
   report.setdefault('surfaces',[]).append({'segment':seg['name'],'seconds':sec,'vertices_cm':[v.to_tuple() for v in vectors],'outcome':str(result[-1])})
"""
assert needle in tail;tail=tail.replace(needle,insert+needle)
tail=tail.replace("report['original_proof_unchanged']=", "report['actual_lod_influence_limits']=lods\n report['original_proof_unchanged']=")
exec(compile(code+tail,__file__,'exec'))
