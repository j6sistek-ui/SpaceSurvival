"""Use connected surface distance to follow the hooked tail through its actual tip."""
import bpy,json,heapq,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
rig=bpy.data.objects['Armature'];mesh=bpy.data.objects['SquirrelHero_Replacement'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.rotation_quaternion=(1,0,0,0)
tail=set(json.loads((OUT/'repair_vertices.json').read_text())['tail'])
points={i:mesh.matrix_world@mesh.data.vertices[i].co for i in tail}
lookup={};members=[];index={};p=[]
for i,v in points.items():
    key=tuple(round(x,5) for x in v)
    if key not in lookup:lookup[key]=len(p);p.append(v);members.append([])
    k=lookup[key];index[i]=k;members[k].append(i)
adj=[{} for _ in p]
for e in mesh.data.edges:
    a,b=e.vertices
    if a in tail and b in tail:
        a,b=index[a],index[b]
        if a!=b:adj[a][b]=adj[b][a]=(p[a]-p[b]).length
seeds=[i for i,v in enumerate(p) if v.y<-.085]
assert seeds
dist=[float('inf')]*len(p);queue=[]
for i in seeds:dist[i]=0;heapq.heappush(queue,(0,i))
while queue:
    value,i=heapq.heappop(queue)
    if value!=dist[i]:continue
    for j,length in adj[i].items():
        candidate=value+length
        if candidate<dist[j]:dist[j]=candidate;heapq.heappush(queue,(candidate,j))
assert all(math.isfinite(d) for d in dist), 'Disconnected tail component requires explicit classification'
ordered=sorted(dist);length=ordered[int(len(ordered)*.995)]
centers=[Vector((0,-.14,.397))]
for n in range(1,8):
    target=length*n/7
    selected=[v for v,d in zip(p,dist) if abs(d-target)<length*.035] if n<7 else [v for v,d in zip(p,dist) if d>length*.96]
    assert selected;centers.append(sum(selected,Vector())/len(selected))
print('CENTERLINE',json.dumps([list(v) for v in centers]),flush=True)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for i in range(7):
    b=rig.data.edit_bones['tail_%02d'%(i+1)];b.use_connect=False;b.head=rig.matrix_world.inverted()@centers[i];b.tail=rig.matrix_world.inverted()@centers[i+1]
bpy.ops.object.mode_set(mode='OBJECT')
for i in tail:
    q=max(0,min(6,dist[index[i]]/length*7-.5));a=int(q);f=q-a
    blend=max(0,min(1,(points[i].y+.10)/.03)) if points[i].y<-.07 else 1
    weights={'tail_%02d'%(a+1):(1-f)*blend,'pelvis':1-blend}
    if f:weights['tail_%02d'%(a+2)]=f*blend
    for g in list(mesh.data.vertices[i].groups):mesh.vertex_groups[g.group].remove([i])
    for name,w in weights.items():
        if w>1e-7:mesh.vertex_groups[name].add([i],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
report={'tail_centerline':[list(v) for v in centers],'surface_path_length_m':length,'tail_vertices':len(tail),'all_tail_vertices_connected':True,'assignment':'continuous root-to-tip geodesic distance; no nearest-segment ambiguity at hook'}
(OUT/'tail_weight_revision.json').write_text(json.dumps(report,indent=2));print('TAIL_REWEIGHT_OK')
