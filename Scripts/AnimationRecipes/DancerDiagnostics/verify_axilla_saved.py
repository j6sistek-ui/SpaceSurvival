import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Fresh reload: preserve bones/weights/baseline keys; inspect all neck seam frames."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_ShoulderBalanced_Proof.blend';candidate=D/'Vexa_AxillaLocal_Proof.blend'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,candidate)}
def snapshot():
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 bones={b.name:tuple(tuple(row) for row in b.matrix_local) for b in rig.data.bones}
 objects={o.name:{'co':[tuple(v.co) for v in o.data.vertices],'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0} for v in o.data.vertices],'keys':{k.name:[tuple(v.co) for v in k.data] for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}} for o in bpy.context.scene.objects if o.type=='MESH'}
 return bones,objects
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);bones,objects=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False);newbones,newobjects=snapshot();assert newbones==bones
newkeys=[]
for name,row in objects.items():
 current=newobjects[name];assert current['co']==row['co'] and current['weights']==row['weights'],name
 for key,coords in row['keys'].items():assert current['keys'][key]==coords,(name,key)
 newkeys.extend((name,key) for key in current['keys'] if key not in row['keys'])
assert len(newkeys)==24 and all(n=='Vexa_Nude_Torso' and k.startswith('REVIEW_Vexa_Axilla_') for n,k in newkeys)
body=bpy.data.objects['Vexa_Nude_Torso'];head=bpy.data.objects['Eden_Pink_CharacterMesh0.001'];s=bpy.context.scene
pairs=json.loads((R/'VexaShoulderFoundation/Report.json').read_text())['neck_pairs'];maxgap=0
for f in range(1,962):
 s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();a,b=body.evaluated_get(dg),head.evaluated_get(dg)
 maxgap=max(maxgap,max(((a.matrix_world@a.data.vertices[i].co)-(b.matrix_world@b.data.vertices[j].co)).length for i,j,*_ in pairs))
assert maxgap<1e-5,maxgap
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
report={'hashes':hashes,'original_bones':len(bones),'original_weights_geometry_and_keys_unchanged':True,'new_local_torso_keys':len(newkeys),'neck_seam_frames':961,'neck_seam_pairs':len(pairs),'max_neck_seam_m':maxgap,'status':'Structural and seam checks pass; native and full artistic motion review open'}
(R/'VexaAxillaProof/SavedVerification.json').write_text(json.dumps(report,indent=2));print('AXILLA_SAVED_VERIFIED',json.dumps(report))
