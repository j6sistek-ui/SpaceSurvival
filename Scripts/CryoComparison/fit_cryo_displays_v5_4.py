"""Fit B/C complete console stacks to observed inner bezels; support D status.

Only separate v5_4 copies are saved. No Unreal, source-body, or older-file writes.
The four opening corners are measured on read-only orthographic source renders.
"""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,struct,sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import upgrade_console_geometry as common
from build_cryo_displays_v5 import Grid,quad_point,world_geometry,mesh,design,perimeter_frame
from clean_cryo_vector_caps_v5_3 import clean as clean_caps

WORK=Path(__file__).resolve().parent;OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_displays_v5_3.json';DEST=OUT/'assembly_displays_v5_4.json'
PROJECTION=WORK/'console-bezel-projection-v5_4.json'
# Top-left/top-right/bottom-right/bottom-left; inside the black gasket, outside
# all original blue display art. The outer metal bezel remains untouched.
PIXEL_CORNERS={
 ('B','Console_1'):[(176,126),(795,120),(808,528),(174,535)],
 ('B','Console_2'):[(205,121),(773,116),(783,490),(207,495)],
 ('C','Console_1'):[(117,102),(823,84),(845,557),(80,558)],
 ('C','Console_2'):[(169,127),(819,135),(837,576),(169,579)]}


def build_console(record,bodytree,old,prefix):
    center=Vector(record['center']);right=Vector(record['right']);up=Vector(record['up']);normal=Vector(record['normal'])
    scale=record['ortho_width'];w,h=record['pixels']
    def point(pixel):return center+right*((pixel[0]/w-.5)*scale)+up*((.5-pixel[1]/h)*scale*h/w)
    tl,tr,br,bl=[point(p) for p in PIXEL_CORNERS[(record['id'],prefix)]]
    q=[bl,br,tr,tl];normal=(q[1]-q[0]).cross(q[3]-q[0]).normalized()
    inset=.025;deltas=[]
    for j in range(41):
        for i in range(61):
            p=quad_point(q,inset+(1-2*inset)*i/60,inset+(1-2*inset)*j/40)
            hit,_,_,_=bodytree.ray_cast(p+normal*.15,-normal,.35)
            assert hit is not None,'Measured screen footprint lacks source support'
            deltas.append((hit-p).dot(normal))
    lift=max(deltas)+.0015
    assert -.03<lift<.04,('Unexpected screen mounting depth',record['id'],prefix,lift)
    grid=Grid([quad_point(q,inset+(1-2*inset)*i/16,inset+(1-2*inset)*j/12)+normal*lift for j in range(13) for i in range(17)],16,12)
    ps,fs,uv=grid.geometry(0)
    ring=[(i/grid.nx,0) for i in range(grid.nx)]+[(1,j/grid.ny) for j in range(grid.ny)]+[(1-i/grid.nx,1) for i in range(grid.nx)]+[(0,1-j/grid.ny) for j in range(grid.ny)]
    base=len(ps);steps=10;contact=[]
    for u,v in ring:
        inner,_=grid.sample(u,v)
        # Tiny corner bevel remains within the source's chamfered black gasket.
        r=.018
        if u+v<r:u+=(r-u-v)/2;v=r-u
        elif (1-u)+v<r:u-=(r-(1-u)-v)/2;v=r-(1-u)
        elif (1-u)+(1-v)<r:u-=(r-(1-u)-(1-v))/2;v=1-(r-(1-u))
        elif u+(1-v)<r:u+=(r-u-(1-v))/2;v=1-(r-u)
        outer=quad_point(q,u,v)
        for j in range(steps+1):
            p=inner.lerp(outer,j/steps)
            hit,_,_,_=bodytree.ray_cast(p+normal*.15,-normal,.35)
            assert hit is not None,'Coverage rim lacks source support'
            if j==steps:p=hit+normal*.0015;contact.append((p-hit).dot(normal))
            elif (p-hit).dot(normal)<.0015:p=hit+normal*.0015
            ps.append(p);uv.append((u,v))
    for i in range(len(ring)):
        for j in range(steps):
            a=base+i*(steps+1)+j;b=base+((i+1)%len(ring))*(steps+1)+j;fs.extend([(a,b,b+1),(a,b+1,a+1)])
    backing=mesh(prefix+'_Backing_new',ps,fs,uv,old[prefix+'_Backing'].data.materials[0])
    for p in backing.data.polygons:p.use_smooth=True
    ps,fs,uv=grid.geometry(.008);lens=mesh(prefix+'_Glass_new',ps,fs,uv,old[prefix+'_Glass'].data.materials[0])
    aspect=(grid.sample(0,1)[0]-grid.sample(0,0)[0]).length/(grid.sample(1,0)[0]-grid.sample(0,0)[0]).length
    glyph=design('console',aspect).mapped(prefix+'_HUD_new',grid.sample,.003,old[prefix+'_HUD'].data.materials[0]);cleanup=clean_caps(glyph)
    frame=perimeter_frame(grid,old[prefix+'_Frame'].data.materials[0],prefix+'_Frame_new')
    return {prefix+'_Backing':backing,prefix+'_Glass':lens,prefix+'_HUD':glyph,prefix+'_Frame':frame},{
      'name':prefix,'projection_source':record['file'],'projection_source_sha256':common.sha(record['file']),
      'measured_inner_bezel_pixel_corners_tl_tr_br_bl':PIXEL_CORNERS[(record['id'],prefix)],
      'reference_quad_world_m':[list(p) for p in q],'clean_inset_fraction':inset,
      'source_depth_range_mm':[min(deltas)*1000,max(deltas)*1000],'clean_base_lift_mm':lift*1000,
      'dense_source_samples':len(deltas),'minimum_clean_clearance_mm':1.5,
      'rim_contact_mm':[min(contact)*1000,max(contact)*1000],
      'content_mm':3,'lens_mm':8,'smooth_rim_normals':True,'glyph_cleanup':cleanup}


def append_status_pad(ob,base_y):
    old=ob.data;points=[v.co.copy() for v in old.vertices];faces=[tuple(p.vertices) for p in old.polygons]
    oldpoints=[tuple(p) for p in points];oldfaces=list(faces);n=len(points)
    # Pad rear overlaps the already fitted Housing by 3mm; front supports the
    # translated screen. No original housing vertex or face is moved.
    lo=(-.93,base_y-.008,1.7925);hi=(-.71,base_y+.004,2.1675)
    world=[Vector((x,y,z)) for z in [lo[2],hi[2]] for y in [lo[1],hi[1]] for x in [lo[0],hi[0]]]
    inv=ob.matrix_world.inverted();points.extend(inv@p for p in world)
    faces.extend(tuple(n+i for i in f) for f in [(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(0,2,3,1),(4,5,7,6)])
    data=bpy.data.meshes.new(old.name+'_SupportedStatus');data.from_pydata(points,[],faces);data.update()
    for mat in old.materials:data.materials.append(mat)
    for layer in old.uv_layers:
        new=data.uv_layers.new(name=layer.name)
        for li in range(len(old.loops)):new.data[li].uv=layer.data[li].uv
    for i,p in enumerate(old.polygons):data.polygons[i].use_smooth=p.use_smooth;data.polygons[i].material_index=p.material_index
    normals=[tuple(n.vector) for n in old.corner_normals]+[tuple(n.vector) for n in data.corner_normals[len(old.loops):]]
    data.normals_split_custom_set(normals)
    assert [tuple(v.co) for v in data.vertices[:len(oldpoints)]]==oldpoints
    assert [tuple(p.vertices) for p in data.polygons[:len(oldfaces)]]==oldfaces
    ob.data=data
    return {'translation_world_m':[0,-.008,0],'pad_world_bounds_m':[lo,hi],
        'preserved_housing_vertex_prefix':len(oldpoints),'preserved_housing_polygon_prefix':len(oldfaces),
        'old_housing_front_y_m':base_y+.001,'pad_rear_overlap_mm':3,'pad_thickness_mm':12}


def main(apply=False):
    result=json.loads(SOURCE.read_text());receipt=deepcopy(json.loads((OUT/'display-v5_3-geometry.json').read_text()))
    protect=receipt['protected_hashes'].copy()
    for p in [SOURCE,OUT/'display-v5_3-geometry.json',PROJECTION]:protect[str(p)]=common.sha(p)
    for model in result['models']:
        for key in ('editable_blend','finished_glb'):protect[model[key]]=common.sha(model[key])
        for row in model['components']:protect[row['file']]=common.sha(row['file'])
    projections={(r['id'],r['name']):r for r in json.loads(PROJECTION.read_text())}
    if apply:assert not DEST.exists()
    receipt.update(utc=datetime.now(timezone.utc).isoformat(),author_script_sha256=common.sha(__file__),previous_manifest=str(SOURCE),previous_manifest_sha256=common.sha(SOURCE),models=[])
    for model in result['models']:
        if model['id']=='A':receipt['models'].append(model['display_v5']);continue
        bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False);bpy.context.view_layer.update()
        objects={r['name']:bpy.data.objects[r['name']] for r in model['components']};signatures={n:common.mesh_signature(ob) for n,ob in objects.items()}
        changed={};info=deepcopy(model['display_v5'])
        if model['id'] in ['B','C']:
            p,f=world_geometry(objects['Body']);tree=BVHTree.FromPolygons(p,f);info['console_bezel_refit_v5_4']=[]
            for prefix in ['Console_1','Console_2']:
                parts,detail=build_console(projections[(model['id'],prefix)],tree,objects,prefix);changed.update(parts);info['console_bezel_refit_v5_4'].append(detail)
        else:
            for name in ['Status','Status_Glass']:
                ob=objects[name]
                for v in ob.data.vertices:v.co.y-=.008
                ob.data.update();changed[name]=ob
            info['status_support_v5_4']=append_status_pad(objects['Housing'],-.5428679585456848)
            changed['Housing']=objects['Housing'];info['unchanged_geometry'].pop('Housing',None)
        print('V5_4_FIT',model['id'],json.dumps(info.get('console_bezel_refit_v5_4',info.get('status_support_v5_4'))),flush=True)
        assert all(common.mesh_signature(ob)==signatures[n] for n,ob in objects.items() if n not in changed)
        if not apply:continue
        folder=Path(model['editable_blend']).parent.parent/'v5_4_fitted_displays';folder.mkdir(exist_ok=False);(folder/'meshes').mkdir()
        for row in model['components']:
            name=row['name']
            if name not in changed:continue
            ob=changed[name]
            if ob!=objects[name]:bpy.data.objects.remove(objects[name],do_unlink=True);ob.name=name;objects[name]=ob
            file=folder/'meshes'/('SM_'+model['label'].replace(' ','_')+'_'+name+'_v5_4.obj')
            row.update(file=str(file),triangles=common.export_obj(bpy,ob,file),display_revision='v5_4_fitted_geometry');row['source_sha256']=common.sha(file)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects.values():ob.select_set(True)
        bpy.context.view_layer.objects.active=objects['Body']
        stem=model['label'].replace(' ','_')+'_FittedDisplays_v5_4';glb=folder/(stem+'.glb');blend=folder/(stem+'_Editable.blend')
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_keep_originals=False,export_image_format='AUTO')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
        raw=glb.read_bytes();size=struct.unpack_from('<I',raw,12)[0];assert len(json.loads(raw[20:20+size])['meshes'])==21
        info.update(blend_sha256=common.sha(blend),glb_sha256=common.sha(glb),triangles=sum(r['triangles'] for r in model['components']))
        model.update(editable_blend=str(blend),finished_glb=str(glb),display_v5=info);receipt['models'].append(info)
    assert all(common.sha(p)==h for p,h in protect.items())
    receipt.update(protected_file_count=len(protect),protected_hashes=protect,protected_inputs_unchanged=True)
    if apply:
        result.update(version='v5_4_fitted_vector_displays',previous_manifest=str(SOURCE),previous_manifest_sha256=common.sha(SOURCE))
        DEST.write_text(json.dumps(result,indent=2)+'\n');receipt.update(status='VECTOR_DISPLAY_GEOMETRY_AUTHORED_NATIVE_VISUAL_REVIEW_PENDING',manifest=str(DEST),manifest_sha256=common.sha(DEST))
        (OUT/'display-v5_4-geometry.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);main(args.apply)
