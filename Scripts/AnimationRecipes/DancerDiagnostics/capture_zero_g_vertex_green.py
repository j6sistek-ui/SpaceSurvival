import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Render the actual GPU vertex green mask instead of assuming CPU-copy defaults."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_zero_g_explicit_skin.py').read_text().replace('NativeExplicitSkin','NativeVertexGreen')
code=code.replace("events=[(row,view) for row in controls['rows'] if row['label'] in ('01_Drift_563p5','02_Spiral_481p0','01_Drift_1') for view in ('front','back')]", "events=[(row,'front') for row in controls['rows'] if row['label']=='01_Drift_563p5']")
# The nested setup is responsible for map/camera ownership; change its private material only.
code=code.replace("mesh.set_editor_property('skin_cache_usage'", "u.MaterialEditingLibrary.delete_all_material_expressions(mat)\\nvertex=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionVertexColor)\\nassert u.MaterialEditingLibrary.connect_material_property(vertex,'G',u.MaterialProperty.MP_EMISSIVE_COLOR)\\nu.MaterialEditingLibrary.recompile_material(mat)\\nmesh.set_editor_property('skin_cache_usage'",1)
exec(compile(code,__file__,'exec'))
