import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Native G1 front/back motion, approved pose, and bounded G2/B controls."""
from pathlib import Path
code=(Path(__file__).resolve().parent/'capture_gb_wrist_comparison.py').read_text()
code=code.replace("R/'VexaDistalRepair/GBWristExport.json'","R/'GBShoulderResponse/Export.json'")
code=code.replace("'A_Wrist_'","'A_ShoulderResponse_'").replace("clips['g1_after']","clips['g1_shoulder']")
start=code.index("events=[('g1',220,'l')]") if "events=[('g1',220,'l')]" in code else code.index("events=[('g1',220,'l'),")
end=code.index("OUT=R/'NativeGBWristComparison'",start)
segments="""segments=[]
for view in ('front','back'):
 segments.append({'name':'g1_'+view,'key':'g1_shoulder','start':0,'frames':405,'fps':24,'camera':view})
for key,frame in [('g1',881),('g1',84),('g2',1),('g2',543),('b1',978),('b2',543)]:
 for view in ('front','back'):
  segments.append({'name':key+'_'+str(frame)+'_'+view,'key':key+'_shoulder','start':(frame-1)/60,'frames':1,'fps':24,'camera':view})
"""
code=code[:start]+segments+code[end:]
code=code.replace("R/'NativeGBWristComparison'","R/'NativeGBShoulderResponse'").replace("R/'NativeGBWristComparison.json'","R/'NativeGBShoulderResponse.json'")
code=code.replace("if now-state['start']>360:","if now-state['start']>420:")
code=code.replace("else:center=c.get_socket_location('pelvis')+up*15;loc=center+front*230+side*65+up*20","else:center=(l+rr)*.5-up*13;loc=center+front*(115 if seg['camera']=='front' else -115)+up*10")
code=code.replace("'status':'Private unconstrained clips on Vexa. Spiral morph curves absent; no contact or anatomy acceptance.'","'status':'Private shoulder response. Owner approves G1 frame881 front only; full motion and other views are not accepted. No pole contact.'")
exec(compile(code,__file__,'exec'))
