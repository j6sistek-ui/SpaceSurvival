import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Matched bilateral pose comparison with and without original-right weight transfer."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaSymmetry';O.mkdir(exist_ok=True)
from coordinated_girdle import coordinate
from mirror_vexa_shoulder_weights import apply
report=[];F=Matrix.Diagonal(Vector((-1,1,1,1)))
for side in ('l','r'):
 for variant in ('original','right_weights'):
  bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
  s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');torso=bpy.data.objects['Vexa_Nude_Torso'];rig.animation_data_clear()
  with bpy.data.libraries.load(str(D/'Vexa_LegPlane_Proof.blend'),link=False) as (a,b):b.actions=['A_F3_LegPlane_ZeroG_02_Spiral']
  rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0];s.frame_set(733);bpy.context.view_layer.update()
  rest={b.name:(rig.matrix_world@b.matrix_local).copy() for b in rig.data.bones};source={b.name:(rig.matrix_world@b.matrix).copy() for b in rig.pose.bones};ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
  parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered};rig.animation_data_clear();coordinate(source,rest,parent,desc,False)
  chest=source['spine_05']@rest['spine_05'].inverted();pose={n:m.copy() for n,m in rest.items()};other='r' if side=='l' else 'l'
  for n in desc['clavicle_'+side]:
   pose[n]=chest.inverted()@source[n]
   target=n[:-2]+'_'+other
   if target in rest:pose[target]=F@(pose[n]@rest[n].inverted())@F@rest[target]
  inv=rig.matrix_world.inverted();local={n:inv@m for n,m in pose.items()}
  for pb in ordered:
   base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local;pb.matrix_basis=base.inverted()@local[pb.name]
  row={'source_side':side,'variant':variant}
  if variant=='right_weights':row['weights']=apply(torso)
  bpy.context.view_layer.update()
  points=[torso.matrix_world@v.co for v in torso.data.vertices];tree=KDTree(len(points))
  for i,p in enumerate(points):tree.insert(p,i)
  tree.balance();ob=torso.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=[ob.matrix_world@v.co for v in ob.data.vertices];errors=[]
  for i,p in enumerate(points):
   if .05<p.x<.25 and 1.32<p.z<1.53:
    q,j,dist=tree.find(Vector((-p.x,p.y,p.z)))
    errors.append((posed[i]-Vector((-posed[j].x,posed[j].y,posed[j].z))).length)
  row['mirror_surface_error_m']={'p95':float(np.percentile(errors,95)),'max':max(errors)}
  for ob in s.objects:
   if ob.type=='MESH' and 'hair' in ob.name.lower():ob.hide_render=True
  s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.65,.65,.65);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Symmetry');s.world.color=(.035,.045,.055);s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
  bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.85;center=Vector((0,0,1.47))
  for view,offset in [('front',Vector((0,-3,.12))),('back',Vector((0,3,.12)))]:
   cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{side}_{variant}_{view}.png');bpy.ops.render.render(write_still=True)
   assert max(abs(rig.pose.bones[n].matrix[i][j]-m[i][j]) for n,m in local.items() for i in range(4) for j in range(4))<.001
  report.append(row)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('SYMMETRY_REVIEW',json.dumps([{k:v for k,v in r.items() if k!='weights'} for r in report]),flush=True)
