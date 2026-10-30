import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Inspect symmetry, modular neck contact and matched shoulder poses; never save sources."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaShoulderFoundation';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
torso=bpy.data.objects['Vexa_Nude_Torso'];head=bpy.data.objects['Eden_Pink_CharacterMesh0.001']
report={'source':'Vexa_Character_Options.blend','status':'READ-ONLY DIAGNOSTIC','meshes':{},'poses':[]}
def points(o,evaluated=False):
    ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o
    return [ob.matrix_world@v.co for v in ob.data.vertices]
def weights(o,index):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[index].groups if g.weight>1e-8}
def boundary(o):
    edges={}
    for p in o.data.polygons:
        for e in p.edge_keys:edges[e]=edges.get(e,0)+1
    return sorted({v for e,n in edges.items() if n==1 for v in e})
def swap(n):return n[:-2]+('_r' if n.endswith('_l') else '_l') if n.endswith(('_l','_r')) else n
tp=points(torso);hp=points(head);kd=KDTree(len(tp))
for i,p in enumerate(tp):kd.insert(p,i)
kd.balance();mirror=[]
for i,p in enumerate(tp):
    if p.x<.015:continue
    q,j,dist=kd.find(Vector((-p.x,p.y,p.z)))
    a={swap(n):w for n,w in weights(torso,i).items()};b=weights(torso,j)
    mirror.append({'left':i,'right':j,'distance_m':dist,'weight_L1':sum(abs(a.get(n,0)-b.get(n,0)) for n in set(a)|set(b))})
report['mirror']={'max_nearest_m':max(x['distance_m'] for x in mirror),'max_weight_L1':max(x['weight_L1'] for x in mirror),'largest_weight_mismatches':sorted(mirror,key=lambda x:x['weight_L1'],reverse=True)[:12]}
hk=KDTree(len(hp))
for i,p in enumerate(hp):hk.insert(p,i)
hk.balance();pairs=[]
for i in boundary(torso):
    if tp[i].z<1.4:continue
    q,j,dist=hk.find(tp[i])
    if dist<.005:pairs.append((i,j,dist))
report['neck_pairs']=pairs
for o in (torso,head,bpy.data.objects['Vexa_Top']):
    report['meshes'][o.name]={'boundary_vertices':len(boundary(o)),'active_shapes':{k.name:k.value for k in o.data.shape_keys.key_blocks if abs(k.value)>1e-5} if o.data.shape_keys else {},'collections':[{ 'name':c.name,'hide_render':c.hide_render,'hide_viewport':c.hide_viewport} for c in o.users_collection]}
rest={b.name:(rig.matrix_world@b.matrix_local).copy() for b in rig.data.bones};ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));inv=rig.matrix_world.inverted()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.65,.65,.65);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Foundation');s.world.color=(.035,.045,.055)
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
for o in s.objects:
    if o.type=='MESH' and 'hair' in o.name.lower():o.hide_render=True
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
for label,elevation in [('rest',None),('T',0),('up',70)]:
    pose={n:m.copy() for n,m in rest.items()}
    if elevation is not None:
        for side,sign in [('l',1),('r',-1)]:
            upper='upperarm_'+side;lower='lowerarm_'+side
            direction=(rest[lower].translation-rest[upper].translation).normalized();angle=math.radians(elevation)
            goal=Vector((sign*math.cos(angle),0,math.sin(angle)));q=direction.rotation_difference(goal);pivot=rest[upper].translation
            for b in [rig.pose.bones[upper]]+list(rig.pose.bones[upper].children_recursive):
                m=rest[b.name];pose[b.name]=Matrix.LocRotScale(pivot+q@(m.translation-pivot),q@m.to_quaternion(),m.to_scale())
    local={n:inv@m for n,m in pose.items()}
    for pb in ordered:
        base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
        pb.matrix_basis=base.inverted()@local[pb.name]
    bpy.context.view_layer.update();a=points(torso,True);b=points(head,True)
    report['poses'].append({'label':label,'max_neck_pair_gap_m':max(((a[i]-b[j]).length for i,j,_ in pairs),default=None)})
    center=Vector((0,0,1.46))
    for view,offset in [('front',Vector((0,-3,.12))),('back',Vector((0,3,.12)))]:
        cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{label}_{view}.png');bpy.ops.render.render(write_still=True)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('FOUNDATION',json.dumps({'mirror':report['mirror'],'poses':report['poses'],'neck_pair_count':len(pairs)}),flush=True)
