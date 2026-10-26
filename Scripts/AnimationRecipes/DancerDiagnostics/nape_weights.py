import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Private seam-aware nape weight diffusion; geometry and front weights unchanged."""
import numpy as np

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def apply(torso,head,pairs,iterations=8):
    objects=(torso,head);names=sorted({g.name for ob in objects for g in ob.vertex_groups})
    nmap={n:i for i,n in enumerate(names)};keys=[];lookup={};positions=[];original=[]
    # Only explicitly audited modular seam pairs share a logical vertex.
    pairmap={int(j):int(i) for i,j,*_ in pairs}
    for oi,ob in enumerate(objects):
        for v in ob.data.vertices:
            key=(0,pairmap[v.index]) if oi==1 and v.index in pairmap else (oi,v.index)
            if key not in lookup:
                lookup[key]=len(positions);positions.append(list(ob.matrix_world@v.co))
                w=np.zeros(len(names))
                for g in v.groups:w[nmap[ob.vertex_groups[g.group].name]]=g.weight
                original.append(w/max(w.sum(),1e-12))
            keys.append((oi,v.index,lookup[key]))
    ids={(oi,i):u for oi,i,u in keys};p=np.array(positions);old=np.array(original);weights=old.copy()
    mask=(1-smoothstep(.035,.085,abs(p[:,0])))*smoothstep(.025,.065,p[:,1])*smoothstep(1.40,1.46,p[:,2])*(1-smoothstep(1.53,1.59,p[:,2]))
    adjacency=[set() for _ in positions]
    for oi,ob in enumerate(objects):
        for edge in ob.data.edges:
            a,b=[ids[(oi,i)] for i in edge.vertices]
            if a!=b:adjacency[a].add(b);adjacency[b].add(a)
    selected=np.flatnonzero(mask>1e-8)
    for _ in range(iterations):
        new=weights.copy()
        for i in selected:
            ns=sorted(adjacency[i])
            if not ns:continue
            kernel=1/np.maximum(np.linalg.norm(p[ns]-p[i],axis=1),.003)
            avg=np.average(weights[ns],axis=0,weights=kernel)
            new[i]=old[i]*(1-mask[i])+(.5*weights[i]+.5*avg)*mask[i]
        weights=new
    changed=[];max_influences=0
    for oi,i,u in keys:
        if np.max(abs(weights[u]-old[u]))<1e-8:continue
        ob=objects[oi];values=weights[u].copy();values[values<1e-6]=0;values/=values.sum()
        for g in list(ob.data.vertices[i].groups):ob.vertex_groups[g.group].remove([i])
        for name,w in zip(names,values):
            if w<=0:continue
            vg=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name);vg.add([i],float(w),'REPLACE')
        max_influences=max(max_influences,int(np.count_nonzero(values)))
        changed.append({'object':ob.name,'vertex':i,'mask':float(mask[u]),'weight_L1':float(abs(values-old[u]).sum())})
    return {'method':'8 local Jacobi steps; paired seam vertices share one weight vector','changed_vertices':len(changed),'max_influences':max_influences,'rows':changed,'status':'PRIVATE TEST; not anatomy acceptance'}
