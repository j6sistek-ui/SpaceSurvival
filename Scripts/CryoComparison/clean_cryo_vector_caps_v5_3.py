"""Remove only microscopic font-cap faces; preserve every valid vertex and face.

Run isolated Blender with -- --apply. All older revisions remain immutable.
"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import argparse, json, struct, sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import upgrade_console_geometry as common

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_displays_v5_2.json'
DEST=OUT/'assembly_displays_v5_3.json'
THRESHOLD_M2=1e-10
NAMES={'Console_1_HUD','Console_2_HUD','Status','Holo'}


def clean(ob):
    old=ob.data; old.calc_loop_triangles()
    assert len(old.loop_triangles)==len(old.polygons),'Glyph mesh must already be triangles'
    points=[v.co.copy() for v in old.vertices]
    kept=[]; removed=[]
    for face in old.polygons:
        assert len(face.vertices)==3
        a,b,c=[ob.matrix_world@points[i] for i in face.vertices]
        area=(b-a).cross(c-a).length*.5
        (removed if area<THRESHOLD_M2 else kept).append((face,area))
    assert removed and kept
    data=bpy.data.meshes.new(old.name+'_CleanCaps')
    data.from_pydata(points,[],[tuple(f.vertices) for f,_ in kept]);data.update()
    for mat in old.materials:data.materials.append(mat)
    for layer in old.uv_layers:
        newlayer=data.uv_layers.new(name=layer.name)
        for newface,(face,_) in zip(data.polygons,kept):
            for newli,oldli in zip(newface.loop_indices,face.loop_indices):
                newlayer.data[newli].uv=layer.data[oldli].uv
    for newface,(face,_) in zip(data.polygons,kept):
        newface.use_smooth=face.use_smooth;newface.material_index=face.material_index
    if old.has_custom_normals:
        data.normals_split_custom_set([tuple(old.corner_normals[li].vector) for f,_ in kept for li in f.loop_indices])
    assert [tuple(v.co) for v in data.vertices]==[tuple(v.co) for v in old.vertices]
    assert [tuple(f.vertices) for f in data.polygons]==[tuple(f.vertices) for f,_ in kept]
    ob.data=data
    return {'removed_triangles':len(removed),'kept_triangles':len(kept),
        'threshold_m2':THRESHOLD_M2,'largest_removed_face_m2':max(a for _,a in removed),
        'total_removed_area_m2':sum(a for _,a in removed),
        'valid_vertices_faces_uv_preserved':True}


def main(apply=False):
    source=json.loads(SOURCE.read_text()); result=deepcopy(source)
    oldreceipt=OUT/'display-v5_2-geometry.json'
    receipt=deepcopy(json.loads(oldreceipt.read_text()))
    protect=receipt['protected_hashes'].copy()
    for p in [SOURCE,oldreceipt]:protect[str(p)]=common.sha(p)
    for model in source['models']:
        for key in ('editable_blend','finished_glb'):protect[model[key]]=common.sha(model[key])
        for row in model['components']:protect[row['file']]=common.sha(row['file'])
    if apply:assert not DEST.exists(),'Preserve an existing final revision'
    receipt.update(utc=datetime.now(timezone.utc).isoformat(),author_script_sha256=common.sha(__file__),
        previous_manifest=str(SOURCE),previous_manifest_sha256=common.sha(SOURCE),models=[])
    for model in result['models']:
        bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
        bpy.context.view_layer.update()
        objects={r['name']:bpy.data.objects[r['name']] for r in model['components']}
        before={n:common.mesh_signature(ob) for n,ob in objects.items() if n not in NAMES}
        details={n:clean(objects[n]) for n in sorted(NAMES)}
        assert all(common.mesh_signature(objects[n])==sig for n,sig in before.items())
        info=deepcopy(model['display_v5']);info['microscopic_cap_cleanup']=details
        print('CAP_CLEANUP',model['id'],json.dumps(details),flush=True)
        if not apply:continue
        folder=Path(model['editable_blend']).parent.parent/'v5_3_vector_displays'
        folder.mkdir(exist_ok=False);(folder/'meshes').mkdir()
        for row in model['components']:
            if row['name'] not in NAMES:continue
            file=folder/'meshes'/('SM_'+model['label'].replace(' ','_')+'_'+row['name']+'_v5_3.obj')
            row.update(file=str(file),triangles=common.export_obj(bpy,objects[row['name']],file),
                display_revision='v5_3_vector_geometry')
            row['source_sha256']=common.sha(file)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects.values():ob.select_set(True)
        bpy.context.view_layer.objects.active=objects['Body']
        stem=model['label'].replace(' ','_')+'_VectorDisplays_v5_3'
        glb=folder/(stem+'.glb');blend=folder/(stem+'_Editable.blend')
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
            export_animations=True,export_keep_originals=False,export_image_format='AUTO')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
        raw=glb.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size])
        assert len(doc['meshes'])==21
        assert all(common.mesh_signature(objects[n])==sig for n,sig in before.items())
        info.update(blend_sha256=common.sha(blend),glb_sha256=common.sha(glb),
            triangles=sum(r['triangles'] for r in model['components']))
        model.update(editable_blend=str(blend),finished_glb=str(glb),display_v5=info)
        receipt['models'].append(info)
    assert all(common.sha(p)==h for p,h in protect.items()),'Protected older revision changed'
    receipt.update(protected_file_count=len(protect),protected_hashes=protect,protected_inputs_unchanged=True)
    if apply:
        result.update(version='v5_3_vector_mesh_displays',previous_manifest=str(SOURCE),previous_manifest_sha256=common.sha(SOURCE))
        DEST.write_text(json.dumps(result,indent=2)+'\n')
        receipt.update(status='VECTOR_DISPLAY_GEOMETRY_AUTHORED_NATIVE_VISUAL_REVIEW_PENDING',manifest=str(DEST),manifest_sha256=common.sha(DEST))
        (OUT/'display-v5_3-geometry.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('CAP_CLEANUP_FINISHED',str(DEST),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.apply)
