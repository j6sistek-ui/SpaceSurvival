import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh native sweep: wrist/ankle diagnostic poses plus preserved shoulder."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(R))
from distal_native_common import source
code=source('capture_balanced_clean.py')
code=code.replace("RECOMPUTE=os.environ.get('SS_REVIEW_RECOMPUTE')=='1'","RECOMPUTE=False")
code=code.replace("if now-state['start']>150:","if now-state['start']>240:")
code=code.replace("shots=[(9.033333,a) for a in ('front','back','side')]+[(12.2,'side')]", "shots=[(x['seconds'],x['focus']+'_'+view) for x in json.loads((R/'VexaDistalRepair/NativeStress/Cases.json').read_text())['cases'] if x['test'] in ('flex','pitch') for view in ('front','side')]")
old="clip=u.load_asset(BASE+'/'+asset+'_Anim');assert sk and clip and sk.skeleton and clip.get_editor_property('skeleton'), 'Proof dependencies must survive fresh load'"
new="""clip=u.load_asset(BASE+'/'+asset+'_DistalStress')
assert sk and sk.skeleton
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
task=u.AssetImportTask();task.filename=str(R.parents[2]/'SourceAssets/DanceRefinement_20261025/Vexa_DistalStress_48s.fbx');task.destination_path=BASE;task.destination_name=asset+'_DistalStress';task.automated=True;task.save=True;task.replace_existing=True
opt=u.FbxImportUI();opt.automated_import_should_detect_type=False;opt.import_mesh=False;opt.import_animations=True;opt.import_materials=False;opt.import_textures=False;opt.skeleton=sk.skeleton;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',60);opt.anim_sequence_import_data.set_editor_property('preserve_local_transform',True);task.options=opt
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
clip=u.load_asset(BASE+'/'+asset+'_DistalStress');assert clip and abs(clip.sequence_length-48)<.05
assert u.EditorAssetLibrary.save_loaded_asset(clip,False)
assert u.SystemLibrary.get_console_variable_int_value('r.SkinCache.CompileShaders')==1
"""
assert old in code;code=code.replace(old,new)
code=code.replace("if RECOMPUTE:\n    u.SystemLibrary.execute_console_command(world,'r.SkinCache.Mode 1',pc)","if True:\n    u.SystemLibrary.execute_console_command(world,'r.SkinCache.Mode 1',pc)")
start=code.index("  left=c.get_socket_location('upperarm_l')")
end=code.index("  label=f'{sec}_{angle}'",start)
replacement="""  joint,side,view=angle.split('_');bone=joint+'_'+side
  center=c.get_socket_location(bone)
  def unit(v):return v/max(math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),1e-8)
  def cross(a,b):return u.Vector(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x)
  if joint=='hand':
   along=unit(c.get_socket_location('middle_01_'+side)-center)
   across=unit(c.get_socket_location('index_01_'+side)-c.get_socket_location('pinky_01_'+side))
   normal=unit(cross(along,across));center=center+along*4
   direction=normal if view=='front' else across
   distance=32
  else:
   along=unit(c.get_socket_location('ball_'+side)-center)
   up=unit(c.get_socket_location('calf_'+side)-center)
   across=unit(cross(up,along));center=center+along*5
   direction=along*-1+up*.4 if view=='front' else across
   distance=45
  loc=center+unit(direction)*distance;cam=state['camera'];cam.set_actor_location(loc,False,True);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,center),False);cam.camera_component.set_field_of_view(60)
"""
code=code[:start]+replacement+code[end:]
exec(compile(code,__file__,'exec'))
