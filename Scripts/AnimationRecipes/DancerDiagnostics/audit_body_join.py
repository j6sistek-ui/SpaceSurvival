import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Distinguish modular skin joins from the separate clothing overlay."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,kdtree
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'BodyJoinReview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'Roxie_LegPlane_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
torso=bpy.data.objects['Roxie_Nude_Torso'];legs=bpy.data.objects['Roxie_Nude_Legs'];bottom=bpy.data.objects['Roxie_Bottom']
def boundary(ob):
 uses={}
 for poly in ob.data.polygons:
  for edge in poly.edge_keys:uses[edge]=uses.get(edge,0)+1
 return sorted({i for edge,n in uses.items() if n==1 for i in edge})
def positions(ob,evaluated=False):
 obj=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else ob
 return [ob.matrix_world@v.co for v in obj.data.vertices]
rest_t=positions(torso);rest_l=positions(legs);tb=boundary(torso);lb=boundary(legs)
kd=kdtree.KDTree(len(tb))
for i in tb:kd.insert(rest_t[i],i)
kd.balance();pairs=[]
for i in lb:
 p,j,d=kd.find(rest_l[i])
 if d<.002:pairs.append((j,i,d))
report={'source_boundary_pairs_within_2mm':len(pairs),'rest_max_gap_m':max((x[2] for x in pairs),default=None),'poses':[]}
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('BodyJoin');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
for ob,color in ((torso,(.28,.6,.9,1)),(legs,(.9,.55,.2,1)),(bottom,(.3,.85,.4,1))):
 m=bpy.data.materials.new(ob.name+'_Diagnostic');m.diffuse_color=color;ob.data.materials.clear();ob.data.materials.append(m)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.05
for t in (8,9.033333,9.5):
 s.frame_set(round(1+t*60));bpy.context.view_layer.update();a=positions(torso,True);b=positions(legs,True)
 report['poses'].append({'seconds':t,'max_paired_skin_gap_m':max(((a[i]-b[j]).length for i,j,d in pairs),default=None)})
 center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation
 for mode in ('parts','skin_only'):
  bottom.hide_render=mode=='skin_only'
  for view,delta in (('front',Vector((0,-5,.6))),('back',Vector((0,5,.6)))):
   cam.location=center+delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t:g}_{view}_{mode}.png');bpy.ops.render.render(write_still=True)
bottom.hide_render=False
(O/'Report.json').write_text(json.dumps(report,indent=2));print('BODY_JOIN_AUDIT',json.dumps(report),flush=True)
