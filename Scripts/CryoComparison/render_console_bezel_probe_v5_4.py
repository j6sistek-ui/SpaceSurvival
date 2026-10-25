"""Read-only CPU source-color renders to measure B/C original bezel openings."""
import json,sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_cryo_displays_v5 import canonical_quad
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/Cryo_Comparison'
folder=OUT/'previews/ConsoleBezelProbe_v5_4';folder.mkdir(exist_ok=False)
manifest=json.loads((OUT/'assembly_fit_v4_4.json').read_text())
records=[]
for model in manifest['models']:
    if model['id'] not in ['B','C']:continue
    bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
    scene=bpy.context.scene;body=bpy.data.objects['Body']
    for ob in bpy.data.objects:
        if ob.type=='MESH':ob.hide_render=ob!=body
    for mat in body.data.materials:
        nt=mat.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
        emission=nt.nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=1
        links=list(bsdf.inputs['Base Color'].links)
        if links:nt.links.new(links[0].from_socket,emission.inputs['Color'])
        else:emission.inputs['Color'].default_value=bsdf.inputs['Base Color'].default_value
        output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');nt.links.new(emission.outputs[0],output.inputs['Surface'])
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.cycles.use_denoising=False
    scene.render.resolution_percentage=100;scene.render.resolution_x=900;scene.render.resolution_y=650
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
    camera=scene.camera;camera.data.type='ORTHO'
    for prefix in ['Console_1','Console_2']:
        ob=bpy.data.objects[prefix+'_Backing'];q=canonical_quad(ob,ob.data.polygons[0])
        center=sum(q,Vector())/4;right=(q[1]-q[0]).normalized();n=right.cross(q[3]-q[0]).normalized();up=n.cross(right).normalized()
        scale=(q[1]-q[0]).length*1.7
        camera.location=center+n*.9;camera.rotation_euler=Matrix((right,up,n)).transposed().to_euler();camera.data.ortho_scale=scale
        scene.render.filepath=str(folder/(model['id']+'_'+prefix+'_source.png'));bpy.ops.render.render(write_still=True)
        records.append({'id':model['id'],'name':prefix,'corners':[list(v) for v in q],'center':list(center),'right':list(right),'up':list(up),'normal':list(n),'ortho_width':scale,'pixels':[900,650],'file':scene.render.filepath})
(ROOT/'work/console-bezel-projection-v5_4.json').write_text(json.dumps(records,indent=2)+'\n')
