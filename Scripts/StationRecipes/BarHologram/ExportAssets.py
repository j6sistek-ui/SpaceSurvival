"""Run with installed Blender in background/factory-startup mode; see BAR_HOLOGRAM.md.
Never use the owner's open Blender session. Fresh output only, original GLBs unchanged.
"""
import bpy,json,hashlib,sys,argparse,shutil
from pathlib import Path
from mathutils import Vector
parser=argparse.ArgumentParser(description="Export owner GLBs as separate native display/tray inputs")
parser.add_argument('--model',type=Path,required=True)
parser.add_argument('--tray',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
D=args.output.resolve();assert not D.exists(), 'Use a new empty output directory'
inputs=[('WaitressHologram',args.model.resolve(),'c76fa699821f1ca0928995516ccedd901a360dcf1866d664478c92a56054a160'),('ServingTray',args.tray.resolve(),'2f08647fa275bb2ff75077721e0b3f6acdb3bec1fabed715c8350087e416b753')]
for label,path,digest in inputs:
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest, 'Input differs from the inspected owner GLB: '+label
(D/'Originals').mkdir(parents=True)
rows=[]
for label,path,digest in inputs:
    shutil.copy2(path,D/'Originals'/path.name);rows.append({'name':label,'source':str(path),'sha256':digest})
(D/'InputInventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');result=[]
for row in rows:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(D/'Originals'/Path(row['source']).name))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    obj=objects[0];obj.name=row['name'];bpy.context.view_layer.objects.active=obj
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bounds=[obj.matrix_world@Vector(c) for c in obj.bound_box];mins=Vector([min(v[i] for v in bounds) for i in range(3)]);maxs=Vector([max(v[i] for v in bounds) for i in range(3)])
    center=Vector(((mins.x+maxs.x)/2,(mins.y+maxs.y)/2,mins.z))
    target=.65 if row['name']=='WaitressHologram' else .34
    size=(maxs.z-mins.z) if row['name']=='WaitressHologram' else max(maxs.x-mins.x,maxs.y-mins.y)
    for v in obj.data.vertices:v.co=(v.co-center)*(target/size)
    output=D/'Export'/row['name'];output.mkdir(parents=True,exist_ok=True)
    textures=[]
    for i,img in enumerate([x for x in bpy.data.images if x.type=='IMAGE' and x.size[0]]):
        name='BaseColor' if 'basecolor' in img.name.lower() else 'Normal' if 'normal' in img.name.lower() else 'MetallicRoughness'
        path=output/(name+'.png');img.filepath_raw=str(path);img.file_format='PNG';img.save()
        textures.append({'name':name,'path':str(path),'size':list(img.size),'color_space':img.colorspace_settings.name})
    fbx=output/(row['name']+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Y',axis_up='Z',bake_anim=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',path_mode='STRIP',use_custom_props=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(output/(row['name']+'.blend')))
    obj.data.calc_loop_triangles();result.append({'name':row['name'],'fbx':str(fbx),'dimensions_m':list(obj.dimensions),'vertices':len(obj.data.vertices),'triangles':len(obj.data.loop_triangles),'textures':textures,'original_sha256':row['sha256']})
(D/'Export.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
