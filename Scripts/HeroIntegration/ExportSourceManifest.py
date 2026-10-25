"""Read supplied Blender heroes without editing them; retain material graph/packed-image provenance."""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.agent/local/HeroIntegration_20261020';OUT.mkdir(parents=True,exist_ok=True)
SRC=Path(r'C:\Users\j6sis\Downloads\Hero_EX7_Rigged')
CASES=[('EX7',SRC,'Hero_EX7_Rigged_8K.blend','Hero_EX7_Skeletal.fbx'),('Green',SRC/'GreenHero_Alternate','GreenHero_Alt_RigRepair.blend','GreenHero_Alt_Skeletal.fbx'),('Blue',SRC/'BlueHero_Alternate','BlueHero_Alt_RigRepair.blend','BlueHero_Alt_Skeletal.fbx'),('Cloth',SRC/'ClothHero_Alternate','ClothHero_ClothRig.blend','ClothHero_Alt_Skeletal.fbx')]
def value(v):
    if isinstance(v,(str,float,int,bool)):return v
    try:return list(v)
    except:return str(v)
report={'heroes':[],'source_files_edited':False}
for key,folder,blend,fbx in CASES:
    path=folder/blend;bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
    if key=='EX7':objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    else:objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and (o.name in ['GreenHero_Body','GreenHero_Helmet','BlueHero_Body','BlueHero_Helmet','ClothHero_Armor'] or o.name.endswith('_Render'))]
    images={};mats=[];materialset={m for o in objects for m in o.data.materials}
    for mat in sorted(materialset,key=lambda m:m.name):
        nodes=[]
        for n in mat.node_tree.nodes:
            record={'name':n.name,'type':n.bl_idname,'inputs':[{'name':p.name,'id':p.identifier,'value':value(p.default_value) if hasattr(p,'default_value') else None} for p in n.inputs]}
            for prop in ['operation','blend_type','data_type','clamp_factor','clamp_result','space','interpolation']:
                if hasattr(n,prop):record[prop]=value(getattr(n,prop))
            if n.type=='TEX_IMAGE' and n.image:
                im=n.image;raw=bytes(im.packed_file.data);digest=hashlib.sha256(raw).hexdigest();ext='.png' if raw.startswith(b'\x89PNG') else '.jpg'
                target=OUT/'SourceTextures'/(digest+ext);target.parent.mkdir(exist_ok=True)
                if not target.exists():target.write_bytes(raw)
                record['image']=digest;images[digest]={'file':str(target),'size':list(im.size),'color_space':im.colorspace_settings.name,'name':im.name,'sha256':digest}
            nodes.append(record)
        links=[{'from':l.from_node.name,'output':l.from_socket.identifier,'output_name':l.from_socket.name,'to':l.to_node.name,'input':l.to_socket.identifier,'input_name':l.to_socket.name} for l in mat.node_tree.links]
        mats.append({'name':mat.name,'nodes':nodes,'links':links})
    r={'key':key,'source_blend':str(path),'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'fbx':str(folder/fbx),'fbx_sha256':hashlib.sha256((folder/fbx).read_bytes()).hexdigest(),'materials':mats,'images':images,
        'mesh_materials':{o.name:[m.name for m in o.data.materials] for o in objects}}
    report['heroes'].append(r)
    print('SOURCE_MATERIALS',key,len(mats),len(images),sorted({n['type'] for m in mats for n in m['nodes']}),flush=True)
(OUT/'SourceManifest.json').write_text(json.dumps(report,indent=2));print('SOURCE_MANIFEST_READY',str(OUT/'SourceManifest.json'),flush=True)
