import bpy, sys, re
act,frame=sys.argv[-2],int(sys.argv[-1]); sc=bpy.context.scene; arm=[o for o in sc.objects if o.type=='ARMATURE'][0]; m=[o for o in sc.objects if o.type=='MESH'][0]
gname={g.index:g.name for g in m.vertex_groups}
def lab(i):
    v=m.data.vertices[i]; d={}
    for g in v.groups:
        mm=re.match(r'(.+)_\d+$',gname[g.group]); k=mm.group(1) if mm and ('Tent' in gname[g.group]) else gname[g.group]
        d[k]=d.get(k,0)+g.weight
    return sorted(d.items(),key=lambda x:-x[1])[:2]
arm.data.pose_position='REST'; bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); e=m.evaluated_get(dg); me=e.to_mesh(); R=[e.matrix_world@v.co for v in me.vertices]; e.to_mesh_clear()
arm.data.pose_position='POSE'; arm.animation_data.action=bpy.data.actions[act]; sc.frame_set(frame)
dg=bpy.context.evaluated_depsgraph_get(); e=m.evaluated_get(dg); me=e.to_mesh(); Q=[e.matrix_world@v.co for v in me.vertices]; e.to_mesh_clear()
st=[]
for ed in m.data.edges:
    a,b=ed.vertices; r=(R[a]-R[b]).length
    if r>1e-5: st.append(((Q[a]-Q[b]).length/r,a,b))
st.sort(reverse=True)
print("NEDGES>3x",sum(1 for s in st if s[0]>3),"of",len(st))
for s,a,b in st[:12]: print("ST",round(s,1),[round(c,2) for c in R[a]],lab(a),lab(b))
