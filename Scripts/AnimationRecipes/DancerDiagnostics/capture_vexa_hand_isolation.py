import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh native mesh and matching hand controls; existing proof stays intact."""
import unreal as u,json,hashlib
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
OLD='/Game/SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025';NEW='/Game/SpaceSurvival/Licensed/VexaHandIsolationProof_20261026'
assert 'WorkbenchNative/CharacterWorkbench' in u.Paths.get_project_file_path().replace('\\','/')
protected=Path(u.Paths.project_content_dir())/'SpaceSurvival/Licensed/VexaContinuousDistalProof_20261025'
hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected.rglob('*') if p.is_file()}
old=u.load_asset(OLD+'/SK_VexaContinuousDistalProof');assert old
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
task=u.AssetImportTask();task.filename=str(D/'Vexa_HandIsolation_Rest.fbx');task.destination_path=NEW;task.destination_name='SK_VexaHandIsolationProof';task.automated=True;task.save=True;task.replace_existing=False
assert not u.EditorAssetLibrary.does_asset_exist(NEW+'/'+task.destination_name)
opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=True;opt.import_as_skeletal=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.skeleton=old.skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH
opt.skeletal_mesh_import_data.set_editor_property('import_morph_targets',True);opt.skeletal_mesh_import_data.set_editor_property('morph_threshold_position',.00001);task.options=opt
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);new=u.load_asset(NEW+'/'+task.destination_name);assert new and new.skeleton==old.skeleton
lods=new.get_editor_property('source_models')
for lod in lods:
 settings=lod.get_editor_property('build_settings');settings.set_editor_property('bone_influence_limit',12);lod.set_editor_property('build_settings',settings)
new.set_editor_property('source_models',lods)
editor=u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
settings=editor.get_lod_build_settings(new,0);settings.set_editor_property('bone_influence_limit',12);editor.set_lod_build_settings(new,0,settings)
assert u.EditorAssetLibrary.save_loaded_asset(new,False)
assert {m.get_name().casefold() for m in new.get_editor_property('morph_targets')}=={m.get_name().casefold() for m in old.get_editor_property('morph_targets')}
meshes={'before':old,'after':new};clips={'g1':u.load_asset(OLD+'/A_ShoulderResponse_g1_shoulder')};assert clips['g1']
code=(Path(__file__).resolve().parent/'capture_balanced_motion.py').read_text().replace('VexaBalancedProof_20261025','VexaHandIsolationProof_20261026').replace('SK_VexaBalancedProof','SK_VexaHandIsolationProof')
code=code.replace("clip=u.load_asset(BASE+'/'+asset+'_Anim')","clip=clips['g1']")
code=code[:code.index("state={'start':time.monotonic()")]
wrapper=(Path(__file__).resolve().parent/'capture_gb_wrist_comparison.py').read_text();tail=wrapper.split("code=code[:start]+'''",1)[1].split("'''\nexec",1)[0]
start=tail.index('events=');end=tail.index("OUT=R/'NativeGBWristComparison'",start)
segments="""segments=[]
for frame in (220,881):
 for side in ('l','r'):
  for mode in ('before','after'):
   for view in ('palm','oblique'):
    segments.append({'name':f'g1_{frame}_{side}_{mode}_{view}','key':'g1','mesh':mode,'start':(frame-1)/60,'frames':1,'fps':30,'side':side,'camera':view})
"""
tail=tail[:start]+segments+tail[end:]
tail=tail.replace('NativeGBWristComparison','NativeVexaHandIsolation')
tail=tail.replace("if frame==0:c.play_animation(clips[seg['key']],False);c.set_play_rate(0)","if frame==0:\n    c.set_skeletal_mesh_asset(meshes[seg['mesh']]);c.play_animation(clips[seg['key']],False);c.set_play_rate(0)\n    for i in range(c.get_num_materials()):c.set_material(i,mat)")
a=tail.index("   if seg['camera']=='wrist':");b=tail.index("   state['cap'].set_actor_location",a)
tail=tail[:a]+"""   hand=c.get_socket_location('hand_'+seg['side']);middle=c.get_socket_location('middle_01_'+seg['side']);index=c.get_socket_location('index_01_'+seg['side']);pinky=c.get_socket_location('pinky_01_'+seg['side'])
   along=unit(middle-hand);across=unit(index-pinky);normal=unit(cross(along,across));center=hand+along*7.5
   direction=normal if seg['camera']=='palm' else unit(normal*-1+across*.7)
   loc=center+direction*23
"""+tail[b:]
tail=tail.replace("report['ok']=not report['errors']", "report['original_proof_unchanged']=all(Path(p).is_file() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())\n report['ok']=report['original_proof_unchanged'] and not report['errors']")
tail=tail.replace("'status':'Private unconstrained clips on Vexa. Spiral morph curves absent; no contact or anatomy acceptance.'","'status':'Private one-vertex opposite-hand weight repair. Same preserved G1 action; no pose edits or contact acceptance.'")
exec(compile(code+tail,__file__,'exec'))
