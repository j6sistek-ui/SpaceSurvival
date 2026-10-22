"""Finish D's original rear service monitor; preserve all earlier versions."""
from copy import deepcopy
from datetime import datetime, timezone
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import upgrade_console_geometry as common
import validate_cryo_fit_v4 as audit

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_fit_v4_3.json'
DEST=OUT/'assembly_fit_v4_4.json'


def append_geometry(ob, world_points, faces, vertex_uv):
    old=ob.data
    points=[v.co.copy() for v in old.vertices]
    polygons=[tuple(p.vertices) for p in old.polygons]
    loops_uv=[tuple(item.uv) for item in old.uv_layers.active.data]
    normals=[tuple(item.vector) for item in old.corner_normals]
    smooth=[p.use_smooth for p in old.polygons]
    count=len(points);old_faces=len(polygons);old_loops=len(loops_uv)
    inverse=ob.matrix_world.inverted()
    points.extend(inverse@p for p in world_points)
    polygons.extend(tuple(count+i for i in face) for face in faces)
    new=bpy.data.meshes.new(ob.name+'_v4_4Mesh')
    new.from_pydata(points,[],polygons);new.update()
    layer=new.uv_layers.new(name=old.uv_layers.active.name)
    for index,uv in enumerate(loops_uv):layer.data[index].uv=uv
    for p in new.polygons:
        p.use_smooth=smooth[p.index] if p.index<old_faces else False
        if p.index>=old_faces:
            for li in p.loop_indices:layer.data[li].uv=vertex_uv[new.loops[li].vertex_index-count]
    normals.extend(tuple(item.vector) for item in new.corner_normals[old_loops:])
    new.normals_split_custom_set(normals)
    for mat in old.materials:new.materials.append(mat)
    ob.data=new
    assert [tuple(v.co) for v in new.vertices[:count]]==[tuple(v.co) for v in old.vertices]
    assert [tuple(p.vertices) for p in new.polygons[:old_faces]]==[tuple(p.vertices) for p in old.polygons]
    assert [tuple(item.uv) for item in layer.data[:old_loops]]==loops_uv
    return {'preserved_front_vertices':count,'preserved_front_faces':old_faces,
            'appended_vertices':len(world_points),'appended_faces':len(faces)}


def main(apply=False):
    assert not DEST.exists(),'Preserve existing v4_4 manifest'
    source=json.loads(SOURCE.read_text());result=deepcopy(source)
    protected={str(SOURCE):common.sha(SOURCE)}
    for m in source['models']:
        for key in ('source','editable_blend','finished_glb'):protected[m[key]]=common.sha(m[key])
        for row in m['components']:protected[row['file']]=common.sha(row['file'])
    model=next(m for m in result['models'] if m['id']=='D')
    bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    signatures={row['name']:common.mesh_signature(bpy.data.objects[row['name']]) for row in model['components']}
    body=audit.surface(bpy.data.objects['Body'])
    camera=Vector((0,6.5,1.6));fx=480/math.tan(math.radians(17.5))
    # Inner display corners from the unmodified 960x1200 native D_back view.
    pixels=[(413,922),(547,922),(547,1008),(413,1008)]
    hits=[]
    for px,py in pixels:
        direction=Vector(((480-px)/fx,-1,(600-py)/fx)).normalized()
        hit,normal,_,_=body['tree'].ray_cast(camera,direction,20)
        assert hit is not None and .8<hit.y<1.25 and .1<hit.z<.5
        hits.append(hit)
    normal=(hits[3]-hits[0]).cross(hits[1]-hits[0]).normalized()
    assert normal.y>.8 and .3<normal.z<.6,'Unexpected rear service panel normal'
    fitted=[p+normal*.003 for p in hits]
    # Test the actual two-triangle cover against the underlying original display.
    def point(u,v):
        if v<=u:return fitted[0]*(1-u)+fitted[1]*(u-v)+fitted[2]*v
        return fitted[0]*(1-v)+fitted[2]*u+fitted[3]*(v-u)
    offsets=[]
    for i in range(21):
        for j in range(21):
            p=point(i/20,j/20)
            hit,_,_,dist=body['tree'].ray_cast(p+normal*.05,-normal,.15)
            assert hit is not None,'Underlying service face missing'
            offsets.append((p-hit).dot(normal))
    lift=max(0,.001-min(offsets))
    print('REAR_CONSOLE_CONTACT',json.dumps({'normal':list(normal),'corners':[list(p) for p in hits],
        'min_mm':min(offsets)*1000,'max_mm':max(offsets)*1000,'lift_mm':lift*1000}),flush=True)
    assert lift<.006,'Unexpected service face curvature requires review'
    fitted=[p+normal*lift for p in fitted]
    offsets=[d+lift for d in offsets]
    assert min(offsets)>.0009 and max(offsets)<.012,'Service backing fit outside tolerance'
    # Reverse the image-space corner order for +Y/up outward winding.
    uv=[(0,1),(1,1),(1,0),(0,0)]
    details={}
    for suffix,amount in [('Backing',0),('Glass',.008),('HUD',.010)]:
        name='Console_1_'+suffix
        details[name]=append_geometry(bpy.data.objects[name],[p+normal*amount for p in fitted],[(0,3,2,1)],uv)
    vertices=[];faces=[];frame_uv=[]
    for i,p in enumerate(fitted):
        q=fitted[(i+1)%4];side=normal.cross((q-p).normalized())*.0025;base=len(vertices)
        vertices.extend([p-side,q-side,q+side,p+side,p-side+normal*.008,q-side+normal*.008,q+side+normal*.008,p+side+normal*.008])
        frame_uv.extend([(0,0),(1,0),(1,1),(0,1)]*2)
        for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:faces.append(tuple(base+k for k in f))
    details['Console_1_Frame']=append_geometry(bpy.data.objects['Console_1_Frame'],vertices,faces,frame_uv)
    bpy.context.view_layer.update()
    unchanged=[row['name'] for row in model['components'] if row['name'] not in details]
    assert all(common.mesh_signature(bpy.data.objects[n])==signatures[n] for n in unchanged),'Unrelated component changed'
    receipt={'status':'DRY_RUN_REAR_CONSOLE_FIT_READY','utc':datetime.now(timezone.utc).isoformat(),
        'source_manifest':str(SOURCE),'source_manifest_sha256':common.sha(SOURCE),
        'camera_pixels':pixels,'source_corner_points_m':[list(p) for p in hits],
        'backing_corner_points_m':[list(p) for p in fitted],'outward_normal_blender':list(normal),
        'backing_to_source_normal_gap_mm':{'min':min(offsets)*1000,'max':max(offsets)*1000,'samples':len(offsets)},
        'glass_offset_mm':8,'HUD_offset_mm':10,'frame_width_mm':5,'frame_depth_mm':8,
        'append_details':details,'unchanged_component_signatures':{n:signatures[n] for n in unchanged},
        'body_geometry_sha256':signatures['Body'],'protected_inputs_unchanged':True,'protected_hashes':protected,
        'source_review':'A/B all nine native angles and C all nine Blender angles show no additional distinct rear/base monitor face. This is D-specific original service monitor coverage.'}
    if not apply:
        (WORK/'cryo-D-rear-console-v4_4-plan.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('REAR_CONSOLE_DRY_RUN',json.dumps(receipt['backing_to_source_normal_gap_mm']),flush=True)
        return
    folder=Path(model['editable_blend']).parent.parent/'v4_4_rear_console'
    folder.mkdir(exist_ok=False);(folder/'meshes').mkdir()
    changes=[]
    for row in model['components']:
        if row['name'] not in details:continue
        previous=row['file'];path=folder/'meshes'/('SM_Meshy_Raccoon_'+row['name']+'_v4_4.obj')
        triangles=common.export_obj(bpy,bpy.data.objects[row['name']],path)
        assert triangles==row['triangles']+(48 if row['role']=='console_frame' else 2)
        row.update(file=str(path),triangles=triangles)
        changes.append({'model_id':'D','name':row['name'],'role':row['role'],'file':str(path),
            'source_sha256':common.sha(path),'previous_file':previous,'previous_source_sha256':common.sha(previous),'triangles':triangles})
    bpy.ops.object.select_all(action='DESELECT')
    for row in model['components']:bpy.data.objects[row['name']].select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects['Body']
    glb=folder/'Meshy_Raccoon_Fitted_v4_4.glb';blend=folder/'Meshy_Raccoon_Fitted_v4_4_Editable.blend'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_keep_originals=False,export_image_format='AUTO')
    glb_info=common.inspect_glb(glb)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
    assert all(common.mesh_signature(bpy.data.objects[n])==signatures[n] for n in unchanged)
    assert all(common.sha(p)==h for p,h in protected.items()),'Protected earlier file changed'
    model['editable_blend']=str(blend);model['finished_glb']=str(glb)
    model['fit_v4']['rear_service_console']={'count':1,'appended_to_existing_console_group':'Console_1','glass_offset_mm':8,'HUD_offset_mm':10,
        'outward_normal_blender':list(normal),'backing_corner_points_m':[list(p) for p in fitted]}
    result['version']='v4_4_D_rear_console';result['source_manifest']=str(SOURCE)
    result['same_finish']+=' D original rear service monitor also uses the same shallow glass/HUD finish within existing 19 components.'
    DEST.write_text(json.dumps(result,indent=2)+'\n')
    receipt.update(status='D_REAR_SERVICE_CONSOLE_AUTHORED_NATIVE_REVIEW_PENDING',manifest=str(DEST),manifest_sha256=common.sha(DEST),
        changes=changes,new_blend=str(blend),new_blend_sha256=common.sha(blend),new_glb=str(glb),glb_validation=glb_info,
        protected_file_count=len(protected),triangles_added=54,total_D_triangles=sum(r['triangles'] for r in model['components']))
    (OUT/'fit-v4_4-rear-console.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (OUT/'native-v4_4-mesh-changes.json').write_text(json.dumps({'manifest':str(DEST),'manifest_sha256':common.sha(DEST),
        'changes':changes,'unchanged_models':['A','B','C'],'unchanged_D_components':unchanged},indent=2)+'\n')
    print('REAR_CONSOLE_V4_4',json.dumps({'manifest':str(DEST),'fit_mm':receipt['backing_to_source_normal_gap_mm'],'triangles_added':54,'protected':len(protected)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.apply)
