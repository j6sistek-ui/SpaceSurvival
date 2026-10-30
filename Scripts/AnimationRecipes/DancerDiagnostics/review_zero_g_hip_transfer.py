import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only posed hip-volume controls for five segment transfer.

Static render copies blend DQ-vs-linear coordinates with the established local
hip mask. This demonstrates the target, not a baked/native/runtime solution.
"""
from pathlib import Path
code=(Path(__file__).resolve().parent/'review_zero_g_joint_transfer.py').read_text()
code=code.replace("O=R/'ZeroGJointTransferLocalBasis'","O=R/'ZeroGHipTransfer'")
anchor="rows=[];ends={}"
setup='''
import numpy as np
original_meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render and not o.hide_get()]
targets={};centers=np.array([tuple(rest['thigh_'+side].translation) for side in ('l','r')])
for ob in original_meshes:
 arm=next((m for m in ob.modifiers if m.type=='ARMATURE'),None)
 if not arm:continue
 points=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices])
 dist=np.linalg.norm(points[:,None,:]-centers[None,:,:],axis=2).min(axis=1)
 mask=np.clip((.42-dist)/.22,0,1);mask=mask*mask*(3-2*mask)
 if mask.max()<1e-6:continue
 arm.use_deform_preserve_volume=False
 targets[ob.name]=(ob,arm,mask)
copies=[]
def make_target_copies():
 for cp,orig in copies:bpy.data.objects.remove(cp,do_unlink=True);orig.hide_render=False
 copies.clear()
 for ob,arm,mask in targets.values():
  arm.use_deform_preserve_volume=False;bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());lin=np.array([tuple(v.co) for v in ev.data.vertices]);me=bpy.data.meshes.new_from_object(ev)
  arm.use_deform_preserve_volume=True;bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());vol=np.array([tuple(v.co) for v in ev.data.vertices]);arm.use_deform_preserve_volume=False;bpy.context.view_layer.update()
  assert len(lin)==len(mask)==len(vol)
  target=lin+(vol-lin)*mask[:,None];me.vertices.foreach_set('co',target.ravel());me.update()
  cp=bpy.data.objects.new(ob.name+'_PosedHipControl',me);s.collection.objects.link(cp);cp.matrix_world=ob.matrix_world.copy();ob.hide_render=True;copies.append((cp,ob))
'''
assert anchor in code;code=code.replace(anchor,setup+'\n'+anchor)
code=code.replace("chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();center=p['pelvis'].translation+chest@Vector((0,0,.15))","make_target_copies()\n  chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();center=p['pelvis'].translation+chest@Vector((0,0,.15))")
exec(compile(code,__file__,'exec'))
