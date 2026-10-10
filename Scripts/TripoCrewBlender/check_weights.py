import bpy, sys, re
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
# 'tent': Kraken/Abyss have tentacle chains at every extremity; no biped bone name contains it
ok={"+x":r"(?i)(hand|index|middle|ring|pinky|thumb|mid|lowerarm|forearm|tent)","-x":r"(?i)(hand|index|middle|ring|pinky|thumb|mid|lowerarm|forearm|tent)","top":r"(?i)(head|neck)","low":r"(?i)(foot|ball|toe|calf|tent)"}
allv=[]
for m in [o for o in bpy.data.objects if o.type=='MESH']:
    names={g.index:g.name for g in m.vertex_groups}
    for v in m.data.vertices: allv.append((m.matrix_world@v.co, v, names))
bad=0; tot=0; ex={}
for tag,key in (("+x",lambda t:t[0].x),("-x",lambda t:-t[0].x),("top",lambda t:t[0].z),("low",lambda t:-t[0].z)):
    for p,v,names in sorted(allv,key=key,reverse=True)[:60]:
        g=max(v.groups,key=lambda g:g.weight,default=None); tot+=1
        n=names[g.group] if g else None
        if n is None or not re.search(ok[tag],n): bad+=1; ex.setdefault(tag,n)
# the floor root is not skin: a vertex on it stays on the floor when the body leaves (see strip_root_weights.py)
on_root=sum(1 for _,v,names in allv if any(names[g.group].lower() in ("root","armature") and g.weight>0.001 for g in v.groups))
print("SANITY",sys.argv[-1].split('/')[-1][:-4][-12:],"meshes",len([o for o in bpy.data.objects if o.type=='MESH']),"bad",bad,"of",tot,ex,"on_root",on_root)
