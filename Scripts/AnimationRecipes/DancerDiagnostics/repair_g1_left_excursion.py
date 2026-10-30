import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Bounded trial removes inspected behind-torso arm loop; no pole adoption."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'repair_g2_arm_excursion.py').read_text()
code=code.replace("D/'GB_ShoulderResponse_ActionLibrary.blend'","D/'G2_TwoPassages_ActionLibrary.blend'").replace("D/'G2_ArmPassage_ActionLibrary.blend';assert", "D/'GB_SelectedPassages_ActionLibrary.blend';assert")
code=code.replace('4d72c70e5410b55847c81943c4ab7c6a3e4d2baa5b151611673dbec6216f4679','fa3967d2d67d8743ba42e94b04aa8f102bd8a21b8360a48ef91f0797e26e36b3')
code=code.replace("old=bpy.data.actions['A_F3_ShoulderResponse_g2']","old=bpy.data.actions['A_F3_ShoulderResponse_g1']").replace("new.name='A_F3_ArmPassage_g2'","new.name='A_F3_SelectedPassages_g1'")
code=code.replace("n.endswith('_r')","n.endswith('_l')").replace("{'clavicle_r'};a,z=59,109","{'clavicle_l'};a,z=192,270").replace("['hand_r']","['hand_l']")
code=code.replace("O/'Repair.json'","O/'G1Repair.json'")
exec(compile(code,__file__,'exec'))
