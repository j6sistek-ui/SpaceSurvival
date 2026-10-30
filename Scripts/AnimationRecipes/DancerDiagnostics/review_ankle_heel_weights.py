import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare posterior ankle influence transition, retaining the complete original."""
from pathlib import Path
code=(_recipe_dir/'review_distal_unoccluded.py').read_text()
exec(compile(code.split("report={'source_sha256'")[0],__file__,'exec'))
O=R/'VexaDistalRepair/HeelWeightControl';O.mkdir(exist_ok=True)
ob=bpy.data.objects['Vexa_Continuous_Feet']
original=[{g.group:g.weight for g in v.groups} for v in ob.data.vertices]
points=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])
arm=next(m for m in ob.modifiers if m.type=='ARMATURE')
report={'source_sha256':digest,'scope':'Weight and preserve-volume controls only, no saved mesh adoption','cases':[],'weight_changes':{}}
patch=None
loop=code[code.index("for side in ('l','r'):"):code.index('assert hashlib.sha256(src.read_bytes())')]
loop=loop.replace("source=bpy.data.objects[on]; bone=bn+'_'+side","if kind!='ankle':continue\n  source=bpy.data.objects[on]; bone=bn+'_'+side")
loop=loop.replace("f'{kind}_{side}_{label}_{angle:+d}_{view}.png'","f'{variant}_{kind}_{side}_{label}_{angle:+d}_{view}.png'")
loop=loop.replace("{'side':side,'joint':kind","{'variant':variant,'side':side,'joint':kind")
for variant in ['original','posterior_transition','preserve_volume']:
 for v,weights in zip(ob.data.vertices,original):
  for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
  for i,w in weights.items():ob.vertex_groups[i].add([v.index],w,'REPLACE')
 arm.use_deform_preserve_volume=variant=='preserve_volume';changed=0
 if variant=='posterior_transition':
  for side in ['l','r']:
   j=np.array(rig.matrix_world@rig.data.bones['foot_'+side].head_local);b=np.array(rig.matrix_world@rig.data.bones['ball_'+side].head_local)
   forward=b-j;forward[2]=0;forward/=np.linalg.norm(forward)
   d=points-j;y=d@forward;z=d[:,2];dist=np.linalg.norm(d,axis=1)
   foot=ob.vertex_groups['foot_'+side].index
   calves=[ob.vertex_groups['calf_'+side].index,ob.vertex_groups['calf_twist_01_'+side].index]
   for v in ob.data.vertices:
    i=v.index;weights=original[i];oldfoot=weights.get(foot,0);oldcalf=sum(weights.get(g,0) for g in calves);mass=oldfoot+oldcalf
    if mass<.5 or dist[i]>.18 or z[i]<-.04 or z[i]>.14:continue
    t=float(np.clip((z[i]+.005)/.12,0,1));desired=1-t*t*(3-2*t)
    mask=float(np.clip((.02-y[i])/.04,0,1));mask=mask*mask*(3-2*mask)
    newfoot=oldfoot+(desired*mass-oldfoot)*mask
    if abs(newfoot-oldfoot)<1e-6:continue
    ob.vertex_groups[foot].add([i],newfoot,'REPLACE')
    if oldcalf>1e-8:
     for g in calves:ob.vertex_groups[g].add([i],weights.get(g,0)*(mass-newfoot)/oldcalf,'REPLACE')
    else:ob.vertex_groups[calves[1]].add([i],mass-newfoot,'REPLACE')
    changed+=1
 report['weight_changes'][variant]=changed
 exec(compile(loop,__file__,'exec'))
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps(report,indent=2));print('HEEL_WEIGHT_CONTROLS_DONE',report['weight_changes'],flush=True)
