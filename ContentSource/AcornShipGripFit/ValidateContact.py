"""Validate full terminal-ring clearance, not only palm proxies or tip centers."""
from pathlib import Path
import importlib.util,json,math
import numpy as np
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ss_hand_surface',OUT/'MeasureContact.py');surface=importlib.util.module_from_spec(spec);spec.loader.exec_module(surface)

def main():
 mesh,skin,inverse,selections=surface.data();pilot,binary=surface.read(surface.ROOT/'ContentSource/Animation/Pilot.glb');report=json.loads((OUT/'Report.json').read_text());result={'status':'SOURCE_TERMINAL_RING_CONTACT_ENVELOPE_MEASURED_NOT_GRASP_ACCEPTANCE','radius_cm':1.8,'ring_samples':64,'pilot_frames':121,'hands':{},'limits':['Vertical surface rays sample the actual posed hand triangles at the terminal ring XY; negative signed gaps indicate ring-plane penetration.','This is a sampled ring check, not a complete solid-to-solid intersection solver.','Open/upturned anatomicalLhand remains; geometry fit does not create a grasp.']}
 rings={}
 for row in report['grips']:
  side=row['side'];tip=np.array(row['new_tip_cm']);normal=np.array(row['tip_up_normal']);normal/=np.linalg.norm(normal);direction=np.array(row['centerline_cm'][-1])-np.array(row['centerline_cm'][-2]);direction/=np.linalg.norm(direction);assert direction@normal>1-1e-8
  axis=np.cross(normal,[0,1,0]);axis/=np.linalg.norm(axis);other=np.cross(normal,axis);rings[side]=np.array([tip+1.8*(axis*math.cos(i*math.tau/64)+other*math.sin(i*math.tau/64))for i in range(64)])
  result['hands'][side]={'tip_cm':tip.tolist(),'ring_plane_normal':normal.tolist(),'gap_envelopes_per_pilot_frame':[],'exit_release_envelopes':[]}
 for frame in range(121):
  posed=surface.pose(skin,inverse,selections,pilot,binary,frame/30)
  for side,ring in rings.items():
   gaps=[]
   for point in ring:
    hits=surface.vertical_hits(posed[side],selections[side]['faces'],*point[:2]);assert hits;gaps.append(hits[0]['z_cm']-point[2])
   result['hands'][side]['gap_envelopes_per_pilot_frame'].append({'seconds':frame/30,'min_cm':min(gaps),'max_cm':max(gaps)})
 exit_clip,exit_binary=surface.read(surface.ROOT/'ContentSource/Animation/Disembark.glb')
 for frame in range(13):
  posed=surface.pose(skin,inverse,selections,exit_clip,exit_binary,frame/30)
  for side,ring in rings.items():
   gaps=[];misses=0
   for point in ring:
    hits=surface.vertical_hits(posed[side],selections[side]['faces'],*point[:2])
    if hits:gaps.append(hits[0]['z_cm']-point[2])
    else:misses+=1
   result['hands'][side]['exit_release_envelopes'].append({'seconds':frame/30,'ray_misses':misses,'min_cm':min(gaps)if gaps else None,'max_cm':max(gaps)if gaps else None})
 posed=surface.pose(skin,inverse,selections,pilot,binary,0)
 for check in report['blender_surface_checks']:
  side=check['side'];point=check['blender_under_glove_ray_hit_cm'];hits=surface.vertical_hits(posed[side],selections[side]['faces'],*point[:2]);error=abs(hits[0]['z_cm']-point[2]);assert error<.002;result['hands'][side]['blender_vs_direct_skinning_vertical_hit_error_cm']=error
 for side,row in result['hands'].items():
  frames=row['gap_envelopes_per_pilot_frame'];row['pilot_worst_signed_gap_cm']=[min(item['min_cm']for item in frames),max(item['max_cm']for item in frames)]
 (OUT/'ContactValidation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({side:{key:value for key,value in row.items()if key not in ['gap_envelopes_per_pilot_frame','exit_release_envelopes']}for side,row in result['hands'].items()},indent=2))
if __name__=='__main__':main()
