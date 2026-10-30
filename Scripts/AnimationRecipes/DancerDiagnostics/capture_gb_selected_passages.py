import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Whole native G1/G2 opposing views after three local passage changes."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_g2_arm_passage.py').read_text()
code=code.replace("R/'GBFastPassage/Export.json'","R/'GBFastPassage/SelectedExport.json'")
code=code.replace("'A_ArmPassage_'","'A_SelectedPassages_'")
code=code.replace("clips['g2_before']=u.load_asset(OLD+'/A_ShoulderResponse_g2_shoulder');clip=clips['g2_passage']","clip=clips['g1_selected']")
start=code.index('for mode in (');end=code.index('"""+code[b:]',start)
code=code[:start]+'''for clip in ('g1','g2'):
 for view in ('front','back'):
  count=int(clips[clip+'_selected'].sequence_length*24)+1
  segments.append({'name':clip+'_'+view,'key':clip+'_selected','start':0,'frames':count,'fps':24,'camera':view})
'''+code[end:]
code=code.replace('NativeG2ArmPassage','NativeGBSelectedPassages').replace('frames59-109 only','G1 frames192-270 and G2 frames59-109/787-830 only')
# Four whole-clip views have more frames than the earlier excerpt comparison.
code=code.replace("exec(compile(code,__file__,'exec'))","code=code.replace(\">360:\",\">600:\")\nexec(compile(code,__file__,'exec'))")
exec(compile(code,__file__,'exec'))
