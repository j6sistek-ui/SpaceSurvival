import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""CPU full-motion seam/protection checks and bounded eight-influence candidate."""
import bpy,json,hashlib,math,sys
from pathlib import Path
import numpy as np
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaNape'
source=D/'Vexa_CoordinatedSymmetry_Proof.blend';trial=D/'Vexa_NapeWeights_Trial.blend'
hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (source,trial)}
pairs=json.loads((R/'VexaShoulderFoundation/Report.json').read_text())['neck_pairs'];names=('Vexa_Nude_Torso','Eden_Pink_CharacterMesh0.001')
def get_weights(ob):return [{ob.vertex_groups[g.group].name:g.weight for g in v.groups} for v in ob.data.vertices]
def points(ob,dg):
    ev=ob.evaluated_get(dg);return np.array([list(ev.matrix_world@v.co) for v in ev.data.vertices])
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
original={n:{'vertices':np.array([list(v.co) for v in bpy.data.objects[n].data.vertices]),'weights':get_weights(bpy.data.objects[n])} for n in names}
bpy.ops.wm.open_mainfile(filepath=str(trial),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');objects=[bpy.data.objects[n] for n in names];full_weights={ob.name:get_weights(ob) for ob in objects};changed={};protected={};rest_same=True
for ob in objects:
    rest_same &= np.array_equal(original[ob.name]['vertices'],np.array([list(v.co) for v in ob.data.vertices]))
    changed[ob.name]=[i for i,(a,b) in enumerate(zip(original[ob.name]['weights'],full_weights[ob.name])) if sum(abs(a.get(n,0)-b.get(n,0)) for n in set(a)|set(b))>1e-6]
    protected[ob.name]=sorted(set(range(len(ob.data.vertices)))-set(changed[ob.name]))
assert rest_same
# Preserve the original action and morph animation, compare saved eight-influence
# representation with the full localized result at every fourth frame.
frames=list(range(1,962,4));before={}
for f in frames:
    s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();before[f]={ob.name:points(ob,dg) for ob in objects}
pruned=[]
for ob in objects:
    for v in ob.data.vertices:
        w=full_weights[ob.name][v.index];items=sorted(((n,x) for n,x in w.items() if x>0),key=lambda z:z[1],reverse=True)
        if len(items)<=8:continue
        kept=items[:8];total=sum(x for n,x in kept)
        for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
        for n,x in kept:ob.vertex_groups[n].add([v.index],x/total,'REPLACE')
        pruned.append({'object':ob.name,'vertex':v.index,'removed_weight':sum(x for n,x in items[8:])})
max_prune=0.;max_seam=0.;max_protected=0.;frame_rows=[]
for f in range(1,962):
    s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();pp={ob.name:points(ob,dg) for ob in objects};gap=max(np.linalg.norm(pp[names[0]][i]-pp[names[1]][j]) for i,j,*_ in pairs);max_seam=max(max_seam,float(gap))
    if f in before:
        max_prune=max(max_prune,max(float(np.linalg.norm(pp[n]-before[f][n],axis=1).max()) for n in names))
        max_protected=max(max_protected,max(float(np.linalg.norm(pp[n][protected[n]]-before[f][n][protected[n]],axis=1).max()) for n in names))
    if f in (1,241,543,733,961):frame_rows.append({'frame':f,'neck_seam_m':float(gap)})
assert max_seam<.00001,max_seam
assert max_protected<.00001,max_protected
prune_accepted=max_prune<.00005
restore_error=0.
if not prune_accepted:
    # Do not widen the gate to disguise a failed compression trial. Preserve the
    # full ten-influence candidate; native influence budget remains a follow-up.
    for row in pruned:
        ob=bpy.data.objects[row['object']];i=row['vertex']
        for g in list(ob.data.vertices[i].groups):ob.vertex_groups[g.group].remove([i])
        for n,w in full_weights[ob.name][i].items():ob.vertex_groups[n].add([i],w,'REPLACE')
    for f in frames:
        s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
        restore_error=max(restore_error,max(float(np.linalg.norm(points(ob,dg)-before[f][ob.name],axis=1).max()) for ob in objects))
    assert restore_error<1e-6,restore_error
s.frame_set(543);bpy.context.view_layer.update();rig['Proof_Status']='PRIVATE: symmetric shoulder weights, coordinated clavicles, paired nape smoothing. Not Unreal adopted; visual/full-motion review open.'
target=D/'Vexa_ShoulderBalanced_Proof.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in hashes.items())
report={'status':rig['Proof_Status'],'source_hashes':hashes,'original_rest_geometry_unchanged':bool(rest_same),'changed_counts':{n:len(v) for n,v in changed.items()},'frames_checked':961,'prune_comparison_frames':len(frames),'max_neck_seam_m':max_seam,'max_prune_surface_error_m':max_prune,'prune_accepted':prune_accepted,'restore_error_m':restore_error,'saved_influence_limit':8 if prune_accepted else 10,'max_unmodified_vertex_prune_error_m':max_protected,'pruning_trial':pruned,'sample_frames':frame_rows,'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(O/'BalancedAudit.json').write_text(json.dumps(report,indent=2));print('BALANCED_PROOF_DONE',json.dumps({k:v for k,v in report.items() if k not in ('source_hashes','pruning_trial')}),flush=True)
