"""Fit preserved chambers to their measured structures; author separate v4 copies.

Four-sided C glazing closes all openings. Other front openings follow their actual
cap and post surfaces. Source meshes/UVs/normals and all earlier exports are guarded.
"""
import bpy, json, math, sys, hashlib
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import upgrade_console_geometry as old

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_holo_consoles.json'
DEST=OUT/'assembly_fit_v4_2.json'
N=32; M=40

def geom(ob):
    return [ob.matrix_world@v.co for v in ob.data.vertices],[tuple(p.vertices) for p in ob.data.polygons]

def mesh(name,verts,faces,uv,mat):
    data=bpy.data.meshes.new(name+'Mesh');data.from_pydata(verts,[],faces);data.update()
    layer=data.uv_layers.new(name='UVMap')
    for p in data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:layer.data[li].uv=uv[data.loops[li].vertex_index]
    data.materials.append(mat);ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
    return ob

def append_tube(vertices,faces,uv,path,r=.005,sides=6):
    base=len(vertices)
    for j,p in enumerate(path):
        tangent=(path[min(j+1,len(path)-1)]-path[max(j-1,0)]).normalized()
        seed=Vector((0,0,1)) if abs(tangent.z)<.95 else Vector((1,0,0))
        a=tangent.cross(seed).normalized();b=tangent.cross(a).normalized()
        for k in range(sides):
            vertices.append(p+r*(a*math.cos(k*math.tau/sides)+b*math.sin(k*math.tau/sides)))
            uv.append((k/sides,j/max(1,len(path)-1)))
    for j in range(len(path)-1):
        for k in range(sides):
            faces.append((base+j*sides+k,base+j*sides+(k+1)%sides,base+(j+1)*sides+(k+1)%sides,base+(j+1)*sides+k))

def add_box(vertices,faces,uv,center,size):
    start=len(vertices);x,y,z=center;dx,dy,dz=[s/2 for s in size]
    vertices.extend(Vector(p) for p in [(x-dx,y-dy,z-dz),(x+dx,y-dy,z-dz),(x+dx,y+dy,z-dz),(x-dx,y+dy,z-dz),(x-dx,y-dy,z+dz),(x+dx,y-dy,z+dz),(x+dx,y+dy,z+dz),(x-dx,y+dy,z+dz)])
    uv.extend([(0,0),(1,0),(1,1),(0,1)]*2)
    for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:faces.append(tuple(start+i for i in f))

def coons(bottom,top,left,right,u,v):
    def sample(arr,t):
        f=t*(len(arr)-1);i=min(len(arr)-2,int(f));return arr[i].lerp(arr[i+1],f-i)
    corners=bottom[0]*(1-u)*(1-v)+bottom[-1]*u*(1-v)+top[0]*(1-u)*v+top[-1]*u*v
    return sample(bottom,u)*(1-v)+sample(top,u)*v+sample(left,v)*(1-u)+sample(right,v)*u-corners

def radial_offset(p,amount):
    normal=Vector((p.x,p.y,0)).normalized();return p+normal*amount

def build():
    assert not DEST.exists(),'Preserve previous v4; choose a new revision instead'
    source=json.loads(SOURCE.read_text());result=deepcopy(source)
    protected={str(SOURCE):old.sha(SOURCE)}
    for model in source['models']:
        for key in ['source','finished_glb','editable_blend']:
            protected[model[key]]=old.sha(model[key])
        for row in model['components']:protected[row['file']]=old.sha(row['file'])
    result['version']='v4_2_fitted_enclosures'
    result['source_manifest']=str(SOURCE)
    result['same_finish']='Measured structure-mounted glass and frost, inset transparent bottom consoles, fitted front HUD and post-mounted status; C has four sealed window sectors. Shared native effects.'
    receipt={'utc':datetime.now(timezone.utc).isoformat(),'models':[]}
    for model in result['models']:
        bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
        bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
        body=bpy.data.objects['Body'];signature=old.mesh_signature(body)
        verts,polys=geom(body);tree=BVHTree.FromPolygons(verts,polys)
        # Restrict cap fitting so the merged hero cannot become an anchor.
        low=[p for p in polys if max(verts[i].z for i in p)<1.04 and min(verts[i].z for i in p)>.40]
        high=[p for p in polys if min(verts[i].z for i in p)>2.72]
        lowtree=BVHTree.FromPolygons(verts,low);hightree=BVHTree.FromPolygons(verts,high)
        mats={row['role']:bpy.data.objects[row['name']].data.materials[0] for row in model['components']}
        original_objects={row['name']:bpy.data.objects[row['name']] for row in model['components']}
        folder=Path(model['editable_blend']).parent.parent/'v4_2_fitted_enclosure'
        folder.mkdir();(folder/'meshes').mkdir()
        patches=[];patch_trees=[]
        if model['id']=='C':
            # Shared corner posts in clockwise plan order. Each seam is sampled once
            # and reused on both adjacent sectors, so the four windows have no gaps.
            seeds=[Vector((-.6706,-.7005,0)),Vector((.6619,-.6907,0)),Vector((.6758,.7046,0)),Vector((-.6597,.6907,0))]
            mids=[Vector((0,-.79,0)),Vector((.73,0,0)),Vector((0,.79,0)),Vector((-.73,0,0))]
            seams=[];posttrees=[]
            for seed in seeds:
                sx=1 if seed.x>0 else -1;sy=1 if seed.y>0 else -1
                region=[p for p in polys if all(verts[i].x*sx>.52 and verts[i].y*sy>.52 for i in p)]
                posttree=BVHTree.FromPolygons(verts,region);posttrees.append(posttree)
                line=[posttree.find_nearest(Vector((seed.x,seed.y,.80+(2.86-.80)*j/M)))[0] for j in range(M+1)]
                line[0]=lowtree.find_nearest(Vector((seed.x,seed.y,.80)))[0]
                line[-1]=hightree.find_nearest(Vector((seed.x,seed.y,2.86)))[0]
                seams.append(line)
            for k in range(4):
                bottom=[];top=[]
                for i in range(N+1):
                    u=i/N;linear=seeds[k].lerp(seeds[(k+1)%4],u)
                    midlinear=(seeds[k]+seeds[(k+1)%4])*.5
                    p=linear+(mids[k]-midlinear)*(1-(2*u-1)**4)
                    bottom.append(lowtree.find_nearest(Vector((p.x,p.y,.80)))[0])
                    top.append(hightree.find_nearest(Vector((p.x,p.y,2.86)))[0])
                bottom[0]=seams[k][0];bottom[-1]=seams[(k+1)%4][0]
                top[0]=seams[k][-1];top[-1]=seams[(k+1)%4][-1]
                patches.append((bottom,top,seams[k],seams[(k+1)%4]))
                patch_trees.append((lowtree,hightree,posttrees[k],posttrees[(k+1)%4]))
        else:
            w,b,t,front,edge=model['glass_fit_m']
            bottom=[];top=[]
            for i in range(N+1):
                x=(i/N-.5)*w;y=front+(edge-front)*(2*i/N-1)**2
                bottom.append(lowtree.find_nearest(Vector((x,y,b)))[0])
                top.append(hightree.find_nearest(Vector((x,y,t)))[0])
            sides=[];posttrees=[]
            for end,sign in [(0,-1),(-1,1)]:
                region=[p for p in polys if all(verts[i].x*sign>.64 for i in p)]
                posttree=BVHTree.FromPolygons(verts,region);posttrees.append(posttree)
                line=[]
                for j in range(M+1):
                    v=j/M;p=bottom[end].lerp(top[end],v)
                    # Track the post rather than a straight chord through air.
                    line.append(posttree.find_nearest(p)[0])
                line[0]=bottom[end];line[-1]=top[end];sides.append(line)
            patches=[(bottom,top,*sides)]
            patch_trees=[(lowtree,hightree,*posttrees)]
        glassverts=[];frostverts=[];faces=[];uv=[]
        for patch in patches:
            start=len(glassverts)
            for j in range(M+1):
                for i in range(N+1):
                    p=coons(*patch,i/N,j/M)
                    glassverts.append(p);frostverts.append(radial_offset(p,.0015));uv.append((i/N,j/M))
            for j in range(M):
                for i in range(N):
                    a=start+j*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
        replacements={}
        replacements['Glass']=mesh('Glass_v4',glassverts,faces,uv,mats['glass'])
        replacements['Frost']=mesh('Frost_v4',frostverts,faces,uv,mats['frost'])
        # Remap all artwork within the fitted front pane. No HUD can extend below it.
        hv=[];huv=[];hf=[];nu=17;nv=19
        # Reuse the exact underlying grid/triangulation to avoid interpolated
        # artwork cutting through a curved or irregular fitted pane.
        for j in range(nv+1):
            for i in range(nu+1):
                gi=i+6;gj=j+5;index=gj*(N+1)+gi;p=glassverts[index]
                across=glassverts[index+1]-glassverts[index-1]
                up=glassverts[index+N+1]-glassverts[index-N-1]
                normal=across.cross(up).normalized()
                if normal.dot(Vector((p.x,p.y,0)))<0:normal=-normal
                hv.append(p+normal*.0025);huv.append((i/nu,j/nv))
        for j in range(nv):
            for i in range(nu):
                a=j*(nu+1)+i;hf.append((a,a+1,a+nu+2,a+nu+1))
        replacements['Holo']=mesh('Holo_v4',hv,hf,huv,mats['holo'])
        # Seated perimeter gasket, same construction on every opening.
        housingv=[];housingf=[];housinguv=[];trimv=[];trimf=[];trimuv=[]
        for patch,attachment_trees in zip(patches,patch_trees):
            for line,attachment_tree in zip(patch,attachment_trees):
                append_tube(housingv,housingf,housinguv,line,r=.006)
                # A fitted opaque seating flange bridges irregular generated
                # post recesses. Its inner edge meets the glass; its outer edge
                # is embedded in measured source metal, with no dangling stalk.
                start=len(housingv)
                dense=[]
                for a,b in zip(line,line[1:]):
                    for step in range(8):dense.append(a.lerp(b,step/8))
                dense.append(line[-1])
                for index,p in enumerate(dense):
                    q,normal,_,distance=attachment_tree.find_nearest(p)
                    direction=(q-p).normalized() if (q-p).length>.0001 else -normal
                    q=q+direction*.025
                    # Closed 4mm-thick seating rail, extending beyond the
                    # measured body contact. Valid from both camera sides.
                    radial=Vector((p.x,p.y,0)).normalized()*.002
                    housingv.extend([p+radial,q+radial,q-radial,p-radial]);housinguv.extend([(0,index/len(dense)),(1,index/len(dense)),(1,index/len(dense)),(0,index/len(dense))])
                for j in range(len(dense)-1):
                    a=start+j*4
                    for k in range(4):housingf.append((a+k,a+(k+1)%4,a+4+(k+1)%4,a+4+k))
                housingf.append(tuple(start+i for i in (3,2,1,0)))
                end=start+(len(dense)-1)*4;housingf.append(tuple(end+i for i in range(4)))
            for line in patch[:2]:
                short=[radial_offset(p,.003) for p in line[9:24]]
                append_tube(trimv,trimf,trimuv,short,r=.002,sides=5)
        # Front status display seats on its own measured structural post.
        sx={'A':-.78,'B':-.84,'C':-.67,'D':-.82}[model['id']];sz=1.98
        support=[]
        for dx in [-.055,.055]:
            for dz in [-.12,.12]:
                p,n,face,dist=tree.ray_cast(Vector((sx+dx,-2,sz+dz)),Vector((0,1,0)),3)
                assert p is not None,'Missing physical status support'
                support.append(p)
        sy=min(p.y for p in support)-.008
        add_box(housingv,housingf,housinguv,(sx,sy-.009,sz),(.245,.018,.405))
        for p in support:
            depth=p.y-sy+.006
            add_box(housingv,housingf,housinguv,(p.x,sy+depth/2, p.z),(.022,depth,.024))
        replacements['Status']=mesh('Status_v4',[(sx-.11,sy-.019,sz-.1875),(sx+.11,sy-.019,sz-.1875),(sx+.11,sy-.019,sz+.1875),(sx-.11,sy-.019,sz+.1875)],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)],mats['status'])
        # Four small nozzle outlets beneath the lid; repeated identically per opening.
        nozzles=[]
        for u in [.30,.70]:
            p=coons(*patches[0],u,1);p.y+=.09
            anchor=hightree.find_nearest(p)[0]
            center=anchor-Vector((0,0,.023))
            add_box(housingv,housingf,housinguv,center,(.045,.055,.05))
            nozzles.append(list(center-Vector((0,0,.026))))
        replacements['Housing']=mesh('Housing_v4',housingv,housingf,housinguv,mats['housing'])
        replacements['Trim']=mesh('Trim_v4',trimv,trimf,trimuv,mats['trim'])
        # Keep the subtle artwork cards inside the volume, including at oblique
        # views. Camera-facing native Niagara and local fog provide the volume.
        for j in range(4):
            oldmist=original_objects['Mist_'+str(j+1)]
            z=[1.0,1.2,2.5,2.65][j];half=.39;h=.55
            points=[(-half,-.20,z-h/2),(half,-.20,z-h/2),(half,-.20,z+h/2),(-half,-.20,z+h/2)]
            if j%2:points=[(-y,x,zp) for x,y,zp in points]
            ob=mesh('Mist_'+str(j+1)+'_v4',points,[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)],mats['mist'])
            for frame,offset in [(1,0),(121,.035),(241,0)]:
                ob.location=(offset if j%2 else -offset,0,offset);ob.keyframe_insert('location',frame=frame)
            ob.location=(0,0,0);replacements['Mist_'+str(j+1)]=ob
        # Lower consoles: inset into bezel, only 8/10 mm above the backing.
        console_info=[]
        for k in [1,2]:
            prefix=f'Console_{k}';ob=original_objects[prefix+'_Backing']
            pts=[ob.matrix_world@v.co for v in ob.data.vertices]
            center=sum(pts,Vector())/4
            normal=(ob.matrix_world.to_3x3()@ob.data.polygons[0].normal).normalized()
            inset=[center+(p-center)*.94 for p in pts]
            fitted=[]
            for p in inset:
                hit,_,_,_=tree.ray_cast(p+normal*.15,-normal,.4)
                assert hit is not None,'Console backing surface miss'
                fitted.append(hit+normal*.003)
            # Preserve original corner UV/winding and small source curvature.
            faces0=[tuple(p.vertices) for p in ob.data.polygons]
            uv0=[None]*4
            for poly in ob.data.polygons:
                for li in poly.loop_indices:uv0[ob.data.loops[li].vertex_index]=tuple(ob.data.uv_layers.active.data[li].uv)
            for suffix,role,offset in [('Backing','console_backing',0),('Glass','console_glass',.008),('HUD','console',.010)]:
                replacements[prefix+'_'+suffix]=mesh(prefix+'_'+suffix+'_v4',[p+normal*offset for p in fitted],faces0,uv0,mats[role])
            fv=[];ff=[];fuv=[]
            polygon=[fitted[i] for i in faces0[0]]
            # Four rails 8mm deep, closed against the backing, avoiding the old 4cm slab.
            for i,p in enumerate(polygon):
                q=polygon[(i+1)%4];edge=(q-p).normalized();side=normal.cross(edge)*.0025
                base=len(fv)
                fv.extend([p-side,q-side,q+side,p+side,p-side+normal*.008,q-side+normal*.008,q+side+normal*.008,p+side+normal*.008]);fuv.extend([(0,0),(1,0),(1,1),(0,1)]*2)
                for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:ff.append(tuple(base+x for x in f))
            replacements[prefix+'_Frame']=mesh(prefix+'_Frame_v4',fv,ff,fuv,mats['console_frame'])
            console_info.append({'name':prefix,'glass_mm':8,'hud_mm':10,'inset_scale':.94})
        rows=[];objects=[]
        for row in model['components']:
            name=row['name']
            if name in replacements:
                bpy.data.objects.remove(original_objects[name],do_unlink=True)
                ob=replacements[name];ob.name=name
                path=folder/'meshes'/('SM_'+model['label'].replace(' ','_')+'_'+name+'.obj')
                triangles=old.export_obj(bpy,ob,path)
                rows.append({**row,'file':str(path),'triangles':triangles})
            else:
                ob=original_objects[name];rows.append(row)
            objects.append(ob)
        assert old.mesh_signature(body)==signature,'Original body changed'
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects:ob.select_set(True)
        bpy.context.view_layer.objects.active=body
        glb=folder/(model['label'].replace(' ','_')+'_Fitted_v4_2.glb')
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_keep_originals=False,export_image_format='AUTO')
        blend=folder/(model['label'].replace(' ','_')+'_Fitted_v4_2_Editable.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
        model['components']=rows;model['editable_blend']=str(blend);model['finished_glb']=str(glb)
        model['fit_v4']={'panes':len(patches),'glass_grid':[N,M],'body_geometry_sha256':signature,'console':console_info,'holo_front_uv_bounds':[6/N,23/N,5/M,24/M],'holo_offset_mm':2.5,'seating_flange':'Closed 4mm rail, post/cap-restricted attachment regions and 25mm extension beyond source contact','nozzle_outlets_blender_m':nozzles,'status_support_rear_points':[list(p) for p in support], 'panel_boundaries':[[[list(p) for p in curve] for curve in patch] for patch in patches]}
        receipt['models'].append({'id':model['id'],'body_preserved':True,'panes':len(patches),'blend_sha256':old.sha(blend),'glb_sha256':old.sha(glb),'triangles':sum(row['triangles'] for row in rows)})
        print('FIT_V4_AUTHORED',model['id'],flush=True)
    assert all(old.sha(p)==h for p,h in protected.items()),'Earlier artifact mutated'
    receipt['protected_file_count']=len(protected);receipt['protected_hashes_unchanged']=True
    DEST.write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'fit-v4_2-geometry.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':build()
