import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""CPU-only fresh saved full-weight seam and protected-front verification."""
import bpy,json,hashlib
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaNape'
names=('Vexa_Nude_Torso','Eden_Pink_CharacterMesh0.001');pairs=json.loads((R/'VexaShoulderFoundation/Report.json').read_text())['neck_pairs']
base=D/'Vexa_CoordinatedSymmetry_Proof.blend';path=D/'Vexa_ShoulderBalanced_Proof.blend';before=hashlib.sha256(path.read_bytes()).hexdigest()
def weights(ob,v):return {ob.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0}
bpy.ops.wm.open_mainfile(filepath=str(base),load_ui=False);original={n:[(tuple(v.co),weights(bpy.data.objects[n],v),(bpy.data.objects[n].matrix_world@v.co).y) for v in bpy.data.objects[n].data.vertices] for n in names}
bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');objects=[bpy.data.objects[n] for n in names]
maxsum=0.;maxcount=0;front_count=0
for ob in objects:
 for v,(co,w,y) in zip(ob.data.vertices,original[ob.name]):
  assert tuple(v.co)==co
  current=weights(ob,v);maxsum=max(maxsum,abs(sum(current.values())-1));maxcount=max(maxcount,len(current))
  if y<=.025:assert current==w;front_count+=1
assert maxsum<1e-5,maxsum
maxgap=0.;worst=None
for frame in range(1,962):
 s.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();a,b=[ob.evaluated_get(dg) for ob in objects]
 for i,j,*_ in pairs:
  gap=((a.matrix_world@a.data.vertices[i].co)-(b.matrix_world@b.data.vertices[j].co)).length
  if gap>maxgap:maxgap=gap;worst={'frame':frame,'pair':[i,j]}
assert maxgap<1e-5,maxgap
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
report={'sha256':before,'frames':961,'pairs':len(pairs),'max_saved_seam_m':maxgap,'worst':worst,'rest_geometry_unchanged':True,'front_weight_vertices_unchanged':front_count,'weight_sum_error':maxsum,'max_influences':maxcount,'bones':len(rig.data.bones),'source_file_unchanged':True,'status':'CPU STRUCTURE/SEAM PASS; visual/native/owner acceptance open'}
(O/'SavedVerification.json').write_text(json.dumps(report,indent=2));print('BALANCED_SAVED_VERIFIED',json.dumps(report),flush=True)
