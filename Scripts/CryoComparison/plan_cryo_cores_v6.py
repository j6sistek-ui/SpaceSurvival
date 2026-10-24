"""Read-only core/rim clearance measurements in Blender export coordinates."""
import json,math
from pathlib import Path
from validate_cryo_displays_v5 import load_obj,BVH
WORK=Path(__file__).resolve().parent;OUT=WORK.parent/'outputs/Cryo_Comparison'
CONFIG={
 'A':{'center_xz':[.0045,.670],'face_radius':.18,'rigid_xz':[-.215,.225,.35,.86],'depth_full_y':-.72,'depth_zero_y':-.50},
 'B':{'center_xz':[0,.4135],'face_radius':.20,'rigid_xz':[-.24,.24,.13,.66],'depth_full_y':-.72,'depth_zero_y':-.50},
 'C':{'center_xz':[-.0375,.667],'face_radius':.18,'rigid_xz':[-.25,.175,.35,.86],'depth_full_y':-.72,'depth_zero_y':-.50},
 'D':{'center_xz':[0,.4375],'face_radius':.205,'rigid_xz':[-.24,.24,.13,.68],'depth_full_y':-.91,'depth_zero_y':-.69}}

def clip(poly,axis,value,sign):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=(a[axis]-value)*sign,(b[axis]-value)*sign
        if da>=0:result.append(a)
        if (da>=0)!=(db>=0):
            t=da/(da-db);result.append(tuple(a[i]+(b[i]-a[i])*t for i in range(3)))
    return result

def measure(model):
    cfg=CONFIG[model['id']].copy();rows={r['name']:r for r in model['components']};body=load_obj(rows['Body']['file']);tree=BVH(body['triangles'])
    x,z=cfg['center_xz'];r=cfg['face_radius'];samples=[]
    for j in range(41):
        for i in range(41):
            dx=(i/40*2-1)*r;dz=(j/40*2-1)*r
            if dx*dx+dz*dz>r*r:continue
            distance=tree.ray((x+dx,-2,z+dz),(0,1,0),2)
            if distance is not None and -2+distance<cfg['depth_full_y']:samples.append([x+dx,-2+distance,z+dz])
    center_dist=tree.ray((x,-2,z),(0,1,0),2);cfg['core_center_m']=[x,-2+center_dist,z]
    obstacles={};obstacle_triangles=[]
    for name in ['Glass','Frost','Housing','Trim']:
        pts=[]
        mesh=load_obj(rows[name]['file']);obstacle_triangles.extend(mesh['triangles'])
        for tri in mesh['triangles']:
            poly=list(tri['p'])
            for axis,value,sign in [(0,x-r,1),(0,x+r,-1),(2,z-r,1),(2,z+r,-1)]:
                poly=clip(poly,axis,value,sign)
                if not poly:break
            pts.extend(poly)
        if pts:obstacles[name]={'min_y_m':min(p[1] for p in pts),'max_y_m':max(p[1] for p in pts)}
    front=min(v['min_y_m'] for v in obstacles.values());backface=max(p[1] for p in samples)
    obstacle_tree=BVH(obstacle_triangles);local=[]
    for p in samples:
        hit=obstacle_tree.ray((p[0],-2,p[2]),(0,1,0),2)
        if hit is not None:local.append(p[1]-(-2+hit))
    required=max(local,default=0)+.025
    offset=max(.04,math.ceil(required*1000)/1000)
    cfg.update(face_front_surface_y_range_m=[min(p[1] for p in samples),backface],face_samples=len(samples),
        obstacles=obstacles,forward_offset_m=offset,target_minimum_forward_clearance_m=.025,
        conservative_noncorresponding_global_clearance_m=front-(backface-offset),
        overlapping_pane_rim_samples=len(local),predicted_corresponding_face_clearance_m=offset-max(local,default=0),transition_width_m=.075)
    return cfg

if __name__=='__main__':
    m=json.loads((OUT/'assembly_displays_v5_4.json').read_text());result={v['id']:measure(v) for v in m['models']}
    (WORK/'cryo-core-v6-plan.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
