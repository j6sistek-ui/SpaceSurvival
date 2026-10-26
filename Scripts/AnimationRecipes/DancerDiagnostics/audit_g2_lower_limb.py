import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Read-only pelvis-relative leg directions and posterior hip weights."""
import bpy, json, math, sys, numpy as np
from pathlib import Path
from mathutils import Vector

sys.path.insert(0, str(_recipe_dir))
from g2_contact_recipe import G2ContactRecipe
model = G2ContactRecipe(R.parents[2])
rest = model.rest
def angle(a,b):
    return math.degrees(a.angle(b))
rows=[]
for frame in range(round(model.duration*60)+1):
    t=frame/60; p=model.pose(t)
    pelvis_delta=p['pelvis'].to_quaternion()@rest['pelvis'].to_quaternion().inverted()
    for side in ('l','r'):
        h,k,a,b=[p[n+'_'+side] for n in ('thigh','calf','foot','ball')]
        rh,rk,ra,rb=[rest[n+'_'+side] for n in ('thigh','calf','foot','ball')]
        thigh=(k.translation-h.translation).normalized(); shin=(a.translation-k.translation).normalized(); foot=(b.translation-a.translation).normalized()
        rthigh=(rk.translation-rh.translation).normalized(); rshin=(ra.translation-rk.translation).normalized(); rfoot=(rb.translation-ra.translation).normalized()
        local=pelvis_delta.inverted()@thigh
        outward=1 if rh.translation.x>rest['pelvis'].translation.x else -1
        knee_axis=thigh.cross(shin)
        ref_axis=rh.to_quaternion().inverted()@rthigh.cross(rshin).normalized()
        alignment=(h.to_quaternion().inverted()@knee_axis.normalized()).dot(ref_axis) if knee_axis.length>.01 else 1
        calf_delta=k.to_quaternion()@rk.to_quaternion().inverted()
        foot_local=calf_delta.inverted()@foot
        ankle_swing=angle(foot_local,rfoot)
        rows.append({'time':t,'side':side,'hip_forward_deg':math.degrees(math.atan2(-local.y,-local.z)),
          'hip_outward_deg':math.degrees(math.asin(max(-1,min(1,local.x*outward)))),
          'knee_flex_deg':angle(thigh,shin),'knee_axis_alignment':alignment,
          'ankle_departure_from_rest_deg':ankle_swing})
metrics=['hip_forward_deg','hip_outward_deg','knee_flex_deg','knee_axis_alignment','ankle_departure_from_rest_deg']
extrema={side:{key:{'min':min((r for r in rows if r['side']==side),key=lambda r:r[key]),'max':max((r for r in rows if r['side']==side),key=lambda r:r[key])} for key in metrics} for side in ('l','r')}
weights=[]
for ob in model.scene.objects:
    if ob.type!='MESH' or ob.hide_render or not any(m.type=='ARMATURE' for m in ob.modifiers):continue
    pts=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])
    # Survey raw coordinates, not a claimed anatomical region.
    selected=(pts[:,1]>.015)&(pts[:,2]>.75)&(pts[:,2]<1.15)&(np.abs(pts[:,0])<.25)
    influence={}
    for v in ob.data.vertices:
        if not selected[v.index]:continue
        for g in v.groups:
            n=ob.vertex_groups[g.group].name
            if n in model.names:influence.setdefault(n,[]).append(g.weight)
    weights.append({'mesh':ob.name,'bounds':[pts.min(axis=0).tolist(),pts.max(axis=0).tolist()],
      'selected_vertices':int(selected.sum()),'influences':{n:{'count':len(v),'mean':float(np.mean(v)),'max':max(v)} for n,v in influence.items()}})
report={'sources':model.hashes,'scope':'Diagnostic angles only, not universal anatomical limits or visual acceptance.',
 'rest_joints':{n:list(rest[n].translation) for n in model.names if n.startswith(('pelvis','thigh','calf','foot','ball'))},
 'extrema':extrema,'knee_reversal_flags':[r for r in rows if r['knee_flex_deg']>10 and r['knee_axis_alignment']<0],
 'weights':weights,'samples':rows}
out=R/'G2HipVolume'/'LowerLimbAudit.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
model.assert_inputs_unchanged()
print('LOWER_LIMB_SUMMARY',json.dumps({k:report[k] for k in ('rest_joints','extrema','weights')}),flush=True)
print('KNEE_REVERSALS',len(report['knee_reversal_flags']),flush=True)
