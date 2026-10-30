import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Export only the new private mesh; retained sources and actions unchanged."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'export_balanced_proof.py').read_text().replace('Vexa_ShoulderBalanced','Vexa_HandIsolation').replace('VexaBalanced','VexaHandIsolation')
code=code.replace("if ob.type!='MESH' or not ob.data.shape_keys:continue","if ob.type!='MESH' or ob.hide_render or not ob.data.shape_keys:continue")
code=code.replace("bpy.ops.export_scene.fbx(filepath=str(D/(stem+'_Proof.fbx')),bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,**options)","# No duplicate animation export: the retained library is unchanged.")
exec(compile(code,__file__,'exec'))
