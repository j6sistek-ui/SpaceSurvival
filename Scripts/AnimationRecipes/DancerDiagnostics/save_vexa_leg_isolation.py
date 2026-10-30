import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Preserve the four-vertex weight repair independently of any new motion."""
import bpy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(_recipe_dir))
from isolate_distal_leg_weights import isolate
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_HandIsolation_Proof.blend';out=D/'Vexa_LegIsolation_Proof.blend';assert not out.exists()
sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha=='a9dbcbde4743c2eed97b92c1ab18157d8b903a620206e17cd325031a0e976e6e'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
before={(o.name,v.index):{o.vertex_groups[g.group].name:g.weight for g in v.groups} for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices}
changes=isolate(bpy.context.scene);assert {(r['mesh'],r['vertex']) for r in changes}=={('Vexa_Continuous_Feet',v) for v in (1528,1534,1566,1574)}
changed=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 for v in ob.data.vertices:
  old=before[(ob.name,v.index)];now={ob.vertex_groups[g.group].name:g.weight for g in v.groups}
  if old!=now:
   assert abs(sum(old.values())-sum(now.values()))<1e-7
   changed.append((ob.name,v.index))
assert set(changed)=={(r['mesh'],r['vertex']) for r in changes}
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
report={'source':str(source),'source_sha256':sha,'destination':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'changes':changes,'unchanged_weight_vertices':len(before)-len(changes),'scope':'Four isolated opposite-thigh influences; all other vertex weights unchanged; no pose or topology edit.'}
(R/'G2HipVolume').mkdir(exist_ok=True)
(R/'G2HipVolume/LegIsolation.json').write_text(json.dumps(report,indent=2));assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
print('LEG_ISOLATION_SAVED',report['sha256'],len(before),flush=True)
