import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Separate late left-arm trial; preserve the early G2 candidate and source."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'repair_g2_arm_excursion.py').read_text()
code=code.replace("D/'GB_ShoulderResponse_ActionLibrary.blend'","D/'G2_ArmPassage_ActionLibrary.blend'").replace("D/'G2_ArmPassage_ActionLibrary.blend';assert", "D/'G2_TwoPassages_ActionLibrary.blend';assert")
code=code.replace('4d72c70e5410b55847c81943c4ab7c6a3e4d2baa5b151611673dbec6216f4679','ac64f03842453cb6b803e62fcc4c0ffc54df9213408a07c81f48affa5de00f39')
code=code.replace("old=bpy.data.actions['A_F3_ShoulderResponse_g2']","old=bpy.data.actions['A_F3_ArmPassage_g2']").replace("new.name='A_F3_ArmPassage_g2'","new.name='A_F3_TwoPassages_g2'")
code=code.replace("n.endswith('_r')","n.endswith('_l')").replace("{'clavicle_r'};a,z=59,109","{'clavicle_l'};a,z=787,830").replace("['hand_r']","['hand_l']")
code=code.replace("O/'Repair.json'","O/'LateRepair.json'")
exec(compile(code,__file__,'exec'))
