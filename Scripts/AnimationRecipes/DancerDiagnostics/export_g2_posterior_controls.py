import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Saved source bone and surface samples, independent of FBX and Unreal."""
import bpy, hashlib, json, math, numpy as np
from pathlib import Path
O=R/'G2PosteriorHip'
contract=json.loads((O/'Export.json').read_text());source=Path(contract['source'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==contract['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rows=[];surfaces={}
for seconds in (0.,2.5,7.1,10.6,12.4,14.5,22.6666666667,30.6666666667):
    frame=min(s.frame_end,1+seconds*60);s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
    label=f'{seconds:06.2f}'
    rows.append({'label':label,'seconds':(frame-1)/60,'bones_m':{b.name:list((rig.matrix_world@b.matrix).translation) for b in rig.pose.bones}})
    for ob in s.objects:
        if ob.type=='MESH' and not ob.hide_render:
            ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            surfaces[label+'__'+ob.name]=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices],dtype=np.float32)
(O/'SourceControls.json').write_text(json.dumps({'source_sha256':contract['source_sha256'],'rows':rows},indent=2))
np.savez_compressed(O/'SourceSurfaces.npz',**surfaces)
assert hashlib.sha256(source.read_bytes()).hexdigest()==contract['source_sha256']
print('G2_POSTERIOR_SOURCE_CONTROLS',len(rows),flush=True)
