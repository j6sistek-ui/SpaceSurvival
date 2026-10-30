import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Isolated distal surfaces with landmark-aligned cameras; no source writes.

Earlier full-character ankle closeups could be occluded by the arm. Extract
only the requested limb patch from the evaluated mesh, without changing its
skin or topology. Test angles remain diagnostic, not an anatomical standard.
"""
import bpy, json, hashlib, math, numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
O=R/'VexaDistalRepair/UnoccludedFinal'; O.mkdir(exist_ok=True)
src=D/'Vexa_HandIsolation_Proof.blend'; digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene; rig=next(o for o in s.objects if o.type=='ARMATURE'); rig.animation_data_clear()
for ob in s.objects:
 if ob.type=='MESH':
  ob.hide_render=True
  if ob.data.shape_keys:
   ob.data.shape_keys.animation_data_clear()
   for key in ob.data.shape_keys.key_blocks:
    if key.name.startswith('REVIEW_'): key.value=0
for b in rig.pose.bones: b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update(); rest={b.name:b.matrix.copy() for b in rig.pose.bones}
s.render.engine='BLENDER_WORKBENCH'; s.display.shading.light='STUDIO'
s.display.shading.color_type='SINGLE'; s.display.shading.single_color=(.55,.55,.55)
s.display.shading.show_cavity=False; s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('DistalUnoccludedWorld'); s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=700; s.render.resolution_percentage=100
bpy.ops.object.camera_add(); cam=bpy.context.object; s.camera=cam; cam.data.type='ORTHO'
report={'source_sha256':digest,'scope':'isolated patches, open cut at proximal boundary, no repair or anatomical acceptance','cases':[]}
patch=None
for side in ('l','r'):
 for kind,on,bn,prox,tip,angles in [
  ('wrist','Vexa_Continuous_Hands','hand','lowerarm','middle_01',(-30,0,30)),
  ('ankle','Vexa_Continuous_Feet','foot','calf','ball',(-30,0,30))]:
  source=bpy.data.objects[on]; bone=bn+'_'+side
  joint=rest[bone].translation; end=rest[tip+'_'+side].translation
  along=(end-joint).normalized()
  across=(rest['index_01_'+side].translation-rest['pinky_01_'+side].translation).normalized() if kind=='wrist' else (rest['foot_l'].translation-rest['foot_r'].translation).normalized()
  across=(across-along*across.dot(along)).normalized(); normal=along.cross(across).normalized()
  # Keep every face in the side's distal cluster and 16/22 cm proximally.
  worldrest=np.array([tuple(source.matrix_world@v.co) for v in source.data.vertices])
  center=np.array(rig.matrix_world@joint); toward=(rig.matrix_world.to_3x3()@(rest[prox+'_'+side].translation-joint)).normalized()
  dist=np.linalg.norm(worldrest-center,axis=1); proximal=(worldrest-center)@np.array(toward)
  selected=(dist<(.31 if kind=='wrist' else .43))&(proximal<(.16 if kind=='wrist' else .22))
  own=np.array([sum(g.weight for g in v.groups if source.vertex_groups[g.group].name.endswith('_'+side)) for v in source.data.vertices])
  selected &= own>.5
  faces=[tuple(p.vertices) for p in source.data.polygons if all(selected[i] for i in p.vertices)]
  used=sorted({i for f in faces for i in f}); remap={v:i for i,v in enumerate(used)}
  if patch: bpy.data.objects.remove(patch,do_unlink=True)
  mesh=bpy.data.meshes.new('IsolatedDistalPatch'); mesh.from_pydata(worldrest[used],[],[tuple(remap[i] for i in f) for f in faces]); mesh.update()
  patch=bpy.data.objects.new('IsolatedDistalPatch',mesh); s.collection.objects.link(patch)
  for p in mesh.polygons: p.use_smooth=True
  for label,axis,values in [('flex' if kind=='wrist' else 'pitch',across,angles),('deviation' if kind=='wrist' else 'roll',normal if kind=='wrist' else along,(-15,15))]:
   for angle in values:
    for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    delta=Matrix.Translation(joint)@Quaternion(axis,math.radians(angle)).to_matrix().to_4x4()@Matrix.Translation(-joint)
    rig.pose.bones[bone].matrix_basis=rest[bone].inverted()@delta@rest[bone]; bpy.context.view_layer.update()
    matrix_error=max(abs(rig.pose.bones[bone].matrix[i][j]-(delta@rest[bone])[i][j]) for i in range(4) for j in range(4))
    assert matrix_error<.0001,(bone,label,angle,matrix_error)
    ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get())
    coords=[tuple(source.matrix_world@ev.data.vertices[i].co) for i in used]
    mesh.vertices.foreach_set('co',np.array(coords).ravel()); mesh.update(); bpy.context.view_layer.update()
    focus=rig.matrix_world@joint+(rig.matrix_world.to_3x3()@along).normalized()*(.035 if kind=='wrist' else .06)
    cam.data.ortho_scale=.4 if kind=='wrist' else .56
    for view,direction in [('edge',across),('surface',normal)]:
     cam.location=focus+(rig.matrix_world.to_3x3()@direction).normalized()*3
     assert (cam.location-focus).length>2.9
     cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler()
     path=O/f'{kind}_{side}_{label}_{angle:+d}_{view}.png'
     s.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    report['cases'].append({'side':side,'joint':kind,'test':label,'degrees':angle,'vertices':len(used),'faces':len(faces),'matrix_error':matrix_error,'bounds':[np.array(coords).min(axis=0).tolist(),np.array(coords).max(axis=0).tolist()],'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in source.modifiers]})
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps(report,indent=2)); print('DISTAL_UNOCCLUDED_DONE',flush=True)
