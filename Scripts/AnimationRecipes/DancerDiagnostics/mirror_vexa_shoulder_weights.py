import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Copy the preserved right shoulder's weights into a guarded left-side region."""
from mathutils import Vector
from mathutils.kdtree import KDTree

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def swap(n):return n[:-2]+('_r' if n.endswith('_l') else '_l') if n.endswith(('_l','_r')) else n
def apply(torso):
 points=[torso.matrix_world@v.co for v in torso.data.vertices]
 originals=[{torso.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-8} for v in torso.data.vertices]
 tree=KDTree(len(points))
 for i,p in enumerate(points):tree.insert(p,i)
 tree.balance();edges={};adj=[set() for _ in points]
 for poly in torso.data.polygons:
  for a,b in poly.edge_keys:
   edges[(a,b)]=edges.get((a,b),0)+1;adj[a].add(b);adj[b].add(a)
 boundary={v for e,n in edges.items() if n==1 for v in e};visited=set(boundary);frontier=set(boundary);protect=[1.]*len(points)
 for factor in (0.,.25,.65):
  for i in frontier:protect[i]=factor
  frontier={j for i in frontier for j in adj[i]}-visited;visited|=frontier
 rows=[]
 for i,p in enumerate(points):
  factor=smooth(.012,.045,p.x)*smooth(1.20,1.32,p.z)*(1-smooth(.25,.35,p.x))*protect[i]
  if factor<1e-6:continue
  q,j,dist=tree.find(Vector((-p.x,p.y,p.z)))
  if dist>.004 or q.x>=0:raise ValueError(f'Unmatched shoulder vertex {i}: {dist}')
  donor={swap(n):w for n,w in originals[j].items()};old=originals[i]
  blended={n:old.get(n,0)*(1-factor)+donor.get(n,0)*factor for n in set(old)|set(donor)}
  total=sum(blended.values());assert abs(total-1)<1e-4,total
  for n in old:torso.vertex_groups[n].remove([i])
  for n,w in blended.items():
   if w>1e-8:torso.vertex_groups[n].add([i],w/total,'REPLACE')
  rows.append({'index':i,'donor':j,'factor':factor,'distance_m':dist})
 return {'status':'LEFT-ONLY PRIVATE WEIGHT TRIAL; ORIGINAL RIGHT PRESERVED','changed_vertices':len(rows),'max_correspondence_m':max(x['distance_m'] for x in rows),'protected_boundary_count':len(boundary),'rows':rows}
