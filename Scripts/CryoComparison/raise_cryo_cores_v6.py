"""Move only each source core/collar forward in separate v6 body derivatives.

Preserves topology, UVs, materials and every vertex outside a compact support
region. The circular face moves rigidly; a smooth existing collar stays joined.
"""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math,struct,sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import upgrade_console_geometry as common

WORK=Path(__file__).resolve().parent;OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_displays_v5_4.json';DEST=OUT/'assembly_polish_v6.json';PLAN=WORK/'cryo-core-v6-plan.json'


def ramp(t):
    if t<=0:return 0.,0.
    if t>=1:return 1.,0.
    return t*t*(3-2*t),6*t*(1-t)


def window(value,lo,hi,band):
    if value<lo:
        w,g=ramp((value-lo+band)/band);return w,g/band
    if value>hi:
        w,g=ramp((hi+band-value)/band);return w,-g/band
    return 1.,0.


def weight_gradient(p,cfg):
    lo,hi,zlo,zhi=cfg['rigid_xz'];band=cfg['transition_width_m']
    x,gx=window(p.x,lo,hi,band);z,gz=window(p.z,zlo,zhi,band)
    span=cfg['depth_zero_y']-cfg['depth_full_y'];y,gy=ramp((cfg['depth_zero_y']-p.y)/span);gy=-gy/span
    return x*y*z,(gx*y*z,x*gy*z,x*y*gz)


def revise_body(ob,cfg):
    data=ob.data;matrix=ob.matrix_world.copy();inverse=matrix.inverted();normal_matrix=matrix.to_3x3().inverted().transposed()
    old_vertices=[v.co.copy() for v in data.vertices];points=[matrix@p for p in old_vertices]
    old_faces=[(tuple(p.vertices),p.material_index,p.use_smooth) for p in data.polygons]
    old_uv=[[tuple(c.uv) for c in layer.data] for layer in data.uv_layers]
    old_normals=[n.vector.copy() for n in data.corner_normals]
    fields=[weight_gradient(p,cfg) for p in points];offset=cfg['forward_offset_m'];selected=[];rigid=[];det=[]
    for i,(p,(w,g)) in enumerate(zip(points,fields)):
        if w>0:
            v=p.copy();v.y-=offset*w;data.vertices[i].co=inverse@v;selected.append(i)
            if w==1:rigid.append(i)
        det.append(1-offset*g[1])
    data.update()
    # Exact inverse-transpose Jacobian for p'=(x,y-offset*w(x,y,z),z).
    # Unchanged/rigid regions retain the original imported corner normal.
    normals=[]
    for li,n in enumerate(old_normals):
        vertex=data.loops[li].vertex_index;w,g=fields[vertex]
        if not any(g):normals.append(tuple(n));continue
        world=(normal_matrix@n).normalized();ny=world.y/(1-offset*g[1])
        adjusted=Vector((world.x+offset*g[0]*ny,ny,world.z+offset*g[2]*ny)).normalized()
        normals.append(tuple((matrix.to_3x3().transposed()@adjusted).normalized()))
    data.normals_split_custom_set(normals)
    assert [(tuple(p.vertices),p.material_index,p.use_smooth) for p in data.polygons]==old_faces
    assert [[tuple(c.uv) for c in layer.data] for layer in data.uv_layers]==old_uv
    outside=[i for i,(w,g) in enumerate(fields) if w==0]
    assert all(tuple(data.vertices[i].co)==tuple(old_vertices[i]) for i in outside)
    unchanged_normal_error=max(((data.corner_normals[li].vector-old_normals[li]).length for li,loop in enumerate(data.loops) if not any(fields[loop.vertex_index][1])),default=0)
    return {'selected_vertices':len(selected),'rigid_vertices':len(rigid),'unselected_vertices':len(outside),
        'unselected_vertices_exact':True,'topology_uv_materials_unchanged':True,
        'unchanged_and_rigid_corner_normal_max_error':unchanged_normal_error,
        'collar_normals':'Original normals transformed by exact deformation inverse-transpose Jacobian; outside/rigid normals preserved.',
        'jacobian_determinant_range':[min(det),max(det)],'new_triangles_added':0,
        'normal_encoding_limit':'Editable Blender/GLB split-normal encoding may introduce the recorded small angular difference; native OBJ preserves original normal lines outside the transition exactly.'},fields


def export_body_obj(ob,path,original,fields,cfg):
    """Keep source OBJ UV/face/unmoved-normal text literally unchanged."""
    lines=Path(original).read_text().splitlines(keepends=True);normal_vertex={};triangles=0
    for line in lines:
        if not line.startswith('f '):continue
        values=line.split()[1:];assert len(values)==3;triangles+=1
        for token in values:
            vi,ti,ni=[int(x)-1 for x in token.split('/')]
            assert ni not in normal_vertex or normal_vertex[ni]==vi
            normal_vertex[ni]=vi
    vindex=nindex=0;output=[];changed_normals=0
    for line in lines:
        if line.startswith('v '):
            if fields[vindex][0]>0:
                p=(ob.matrix_world@ob.data.vertices[vindex].co)*100
                line=f'v {p.x:.8f} {p.y:.8f} {p.z:.8f}\n'
            vindex+=1
        elif line.startswith('vn '):
            g=fields[normal_vertex[nindex]][1]
            if any(g):
                x,y,z=map(float,line.split()[1:]);offset=cfg['forward_offset_m'];ny=y/(1-offset*g[1])
                n=Vector((x+offset*g[0]*ny,ny,z+offset*g[2]*ny)).normalized()
                line=f'vn {n.x:.8f} {n.y:.8f} {n.z:.8f}\n';changed_normals+=1
            nindex+=1
        output.append(line)
    assert vindex==len(ob.data.vertices)
    with path.open('x',encoding='utf-8',newline='') as handle:handle.writelines(output)
    return triangles,changed_normals


def main(apply=False):
    source=json.loads(SOURCE.read_text());result=deepcopy(source);plans=json.loads(PLAN.read_text())
    protect=json.loads((OUT/'display-v5_4-geometry.json').read_text())['protected_hashes'].copy()
    for p in [SOURCE,PLAN,OUT/'display-v5_4-geometry.json']:protect[str(p)]=common.sha(p)
    for model in source['models']:
        for key in ['source','editable_blend','finished_glb']:protect[model[key]]=common.sha(model[key])
        for row in model['components']:protect[row['file']]=common.sha(row['file'])
    if apply:assert not DEST.exists(),'Never overwrite an earlier derivative'
    receipt={'utc':datetime.now(timezone.utc).isoformat(),'source_manifest':str(SOURCE),'source_manifest_sha256':common.sha(SOURCE),
        'plan':str(PLAN),'plan_sha256':common.sha(PLAN),'author_script':str(Path(__file__).resolve()),'author_script_sha256':common.sha(__file__),'models':[]}
    for model in result['models']:
        bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False);bpy.context.view_layer.update()
        objects={r['name']:bpy.data.objects[r['name']] for r in model['components']};others={n:common.mesh_signature(ob) for n,ob in objects.items() if n!='Body'}
        cfg=plans[model['id']];body=objects['Body'];detail,fields=revise_body(body,cfg)
        center=list(cfg['core_center_m']);center[1]-=cfg['forward_offset_m']
        detail.update(id=model['id'],core_center_cm=[v*100 for v in center],source_core_center_cm=[v*100 for v in cfg['core_center_m']],
            forward_offset_cm=cfg['forward_offset_m']*100,rigid_bounds_xz_cm=[v*100 for v in cfg['rigid_xz']],
            support_transition_cm=cfg['transition_width_m']*100,depth_transition_cm=[cfg['depth_full_y']*100,cfg['depth_zero_y']*100])
        assert all(common.mesh_signature(objects[n])==h for n,h in others.items())
        print('CORE_V6',json.dumps(detail),flush=True)
        if not apply:continue
        folder=Path(model['editable_blend']).parent.parent/'polish_v6';folder.mkdir(exist_ok=False);(folder/'meshes').mkdir()
        row=next(r for r in model['components'] if r['name']=='Body');before=dict(row)
        file=folder/'meshes'/('SM_'+model['label'].replace(' ','_')+'_Body_CoreV6.obj')
        count,normal_count=export_body_obj(body,file,before['file'],fields,cfg);assert count==row['triangles']
        detail.update(native_obj_transition_normal_count=normal_count,native_obj_unmoved_and_rigid_normal_lines_exact=True)
        row.update(file=str(file),source_sha256=common.sha(file),core_revision='v6_local_supported_core',original_body_file=before['file'],original_body_sha256=common.sha(before['file']))
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects.values():ob.select_set(True)
        bpy.context.view_layer.objects.active=body
        stem=model['label'].replace(' ','_')+'_Polish_v6';glb=folder/(stem+'.glb');blend=folder/(stem+'_Editable.blend')
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_keep_originals=False,export_image_format='AUTO')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
        raw=glb.read_bytes();length=struct.unpack_from('<I',raw,12)[0];assert len(json.loads(raw[20:20+length])['meshes'])==21
        assert all(common.mesh_signature(objects[n])==h for n,h in others.items())
        model.update(editable_blend=str(blend),finished_glb=str(glb),core_v6=detail)
        detail.update(body_obj_sha256=common.sha(file),blend_sha256=common.sha(blend),glb_sha256=common.sha(glb),triangles=sum(r['triangles'] for r in model['components']))
        receipt['models'].append(detail)
    assert all(common.sha(p)==h for p,h in protect.items()),'A protected original or previous asset changed'
    receipt.update(protected_inputs_unchanged=True,protected_file_count=len(protect),protected_hashes=protect)
    if apply:
        result.update(version='v6_supported_forward_cores',previous_manifest=str(SOURCE),previous_manifest_sha256=common.sha(SOURCE),
            core_change='Local body-only derivative; rigid circular face plus existing supported collar transition; no added triangles or changes to accepted glass/display/frost geometry.')
        DEST.write_text(json.dumps(result,indent=2)+'\n');receipt.update(status='CORE_GEOMETRY_AUTHORED_PENDING_VISUAL_REVIEW',manifest=str(DEST),manifest_sha256=common.sha(DEST))
        (OUT/'core-v6-author.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);main(args.apply)
