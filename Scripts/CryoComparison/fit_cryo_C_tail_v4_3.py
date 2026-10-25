"""New-only C rear Glass/Frost clearance fix. No Unreal launch or body edits."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import upgrade_console_geometry as common
import validate_cryo_fit_v4 as audit

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_fit_v4_2.json'
DEST=OUT/'assembly_fit_v4_3.json'


def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)


def plateau(value,lo,inner_lo,inner_hi,hi):
    if value<=lo or value>=hi:return 0.
    if value<inner_lo:return smooth((value-lo)/(inner_lo-lo))
    if value>inner_hi:return smooth((hi-value)/(hi-inner_hi))
    return 1.


def tail_samples(body):
    """Sample the rear-facing tail at a 2.5mm X/Z grid; no source modification."""
    result=[]
    for ix in range(149):
        x=.20+ix*.0025
        for iz in range(201):
            z=1.05+iz*.0025
            p,n,i,d=body['tree'].ray_cast(Vector((x,2.,z)),Vector((0,-1,0)),4.)
            if p is not None and .60<p.y<.90:
                result.append(p)
    return result


def clearance(points,glass):
    rows=[]
    for p in points:
        q,_,_,_=glass['tree'].ray_cast(Vector((p.x,2.,p.z)),Vector((0,-1,0)),4.)
        assert q is not None and q.y>.4,'Rear pane missing from tail region'
        nearest,_,_,distance=glass['tree'].find_nearest(p)
        signed=distance if q.y>=p.y else -distance
        rows.append((signed,q.y-p.y,tuple(p),tuple(nearest)))
    return {'samples':len(rows),'minimum_euclidean_clearance_mm':min(row[0] for row in rows)*1000,
            'minimum_outward_Y_clearance_mm':min(row[1] for row in rows)*1000,
            'body_samples_outside_glass':sum(row[0]<0 for row in rows),
            'worst_samples_m':[{'signed_nearest_clearance_mm':s*1000,'outward_Y_clearance_mm':y*1000,'body':p,'glass_nearest':q}
                               for s,y,p,q in sorted(rows)[:12]]}


def main():
    assert not DEST.exists(),'Refusing to overwrite an existing v4_3 manifest'
    manifest=json.loads(SOURCE.read_text());result=deepcopy(manifest)
    protected={str(SOURCE):common.sha(SOURCE)}
    for model in manifest['models']:
        for key in ('source','editable_blend','finished_glb'):protected[model[key]]=common.sha(model[key])
        for row in model['components']:protected[row['file']]=common.sha(row['file'])
    model=next(m for m in result['models'] if m['id']=='C')
    bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    signatures={row['name']:common.mesh_signature(bpy.data.objects[row['name']]) for row in model['components']}
    body=audit.surface(bpy.data.objects['Body']);glass_ob=bpy.data.objects['Glass'];frost_ob=bpy.data.objects['Frost']
    initial=audit.surface(glass_ob);frost_initial=audit.surface(frost_ob)
    points=tail_samples(body)
    # Include original tail vertices as well as dense projected surface samples.
    points += [p for p in body['points'] if .20<=p.x<=.57 and 1.05<=p.z<=1.55 and .60<p.y<.90]
    before=clearance(points,initial)
    cols,rows=model['fit_v4']['glass_grid'];per_pane=(cols+1)*(rows+1)
    assert len(initial['points'])==len(frost_initial['points'])==per_pane*4
    start=per_pane*2;end=start+per_pane
    weights={i:plateau(p.x,.15,.30,.53,.62)*plateau(p.z,.92,1.10,1.45,1.68)
             for i,p in enumerate(initial['points']) if start<=i<end}
    attempts=[];after=None
    for amplitude in (.030,.0325,.035):
        for i,weight in weights.items():
            delta=Vector((0,amplitude*weight,0))
            glass_ob.data.vertices[i].co=glass_ob.matrix_world.inverted()@(initial['points'][i]+delta)
            frost_ob.data.vertices[i].co=frost_ob.matrix_world.inverted()@(frost_initial['points'][i]+delta)
        glass_ob.data.update();frost_ob.data.update();bpy.context.view_layer.update()
        current=audit.surface(glass_ob);after=clearance(points,current)
        attempts.append({'maximum_lift_mm':amplitude*1000,**after})
        if after['minimum_euclidean_clearance_mm']>=5.:break
    assert after['minimum_euclidean_clearance_mm']>=5.,'Local lift did not reach required tail clearance'
    changed=[i for i,weight in weights.items() if weight>0]
    assert changed and all(start<=i<end for i in changed)
    assert all((current['points'][i]-initial['points'][i]).length<1e-8 for edge in initial['boundary'] for i in edge),'Pane perimeter moved'
    frost_now=audit.surface(frost_ob)
    assert all(((frost_now['points'][i]-current['points'][i])-(frost_initial['points'][i]-initial['points'][i])).length<3e-7
               for i in range(len(current['points']))),'Glass/frost separation changed'
    unchanged=[row['name'] for row in model['components'] if row['name'] not in ('Glass','Frost')]
    assert all(common.mesh_signature(bpy.data.objects[name])==signatures[name] for name in unchanged),'Unrelated geometry changed'
    folder=Path(model['editable_blend']).parent.parent/'v4_3_tail_clearance'
    folder.mkdir(exist_ok=False);(folder/'meshes').mkdir()
    changes=[]
    for component in model['components']:
        if component['name'] not in ('Glass','Frost'):continue
        original=component['file'];path=folder/'meshes'/('SM_Futuristic_Fox_'+component['name']+'_v4_3.obj')
        tris=common.export_obj(bpy,bpy.data.objects[component['name']],path)
        assert tris==component['triangles'],'Triangle count changed'
        component['file']=str(path)
        changes.append({'model_id':'C','name':component['name'],'role':component['role'],'file':str(path),
                        'source_sha256':common.sha(path),'previous_file':original,'previous_source_sha256':common.sha(original),
                        'triangles':tris})
    bpy.ops.object.select_all(action='DESELECT')
    for component in model['components']:bpy.data.objects[component['name']].select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects['Body']
    glb=folder/'Futuristic_Fox_Fitted_v4_3.glb';blend=folder/'Futuristic_Fox_Fitted_v4_3_Editable.blend'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_keep_originals=False,export_image_format='AUTO')
    glb_info=common.inspect_glb(glb)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
    model['finished_glb']=str(glb);model['editable_blend']=str(blend)
    model['fit_v4']['tail_clearance_v4_3']={'affected_sector':'rear (+Y in Blender)','maximum_lift_mm':amplitude*1000,
        'changed_vertices_each_mesh':len(changed),'support_x_m':[.15,.30,.53,.62],'support_z_m':[.92,1.10,1.45,1.68],
        'minimum_sampled_tail_clearance_mm':after['minimum_euclidean_clearance_mm'],'samples':after['samples'],
        'unchanged_perimeter':True,'unchanged_original_body':True,'unchanged_housing_rails_and_front_HUD':True}
    result['version']='v4_3_C_tail_clearance';result['source_manifest']=str(SOURCE)
    assert all(common.sha(p)==h for p,h in protected.items()),'Original or v4_2 artifact mutated'
    DEST.write_text(json.dumps(result,indent=2)+'\n')
    receipt={'status':'C_REAR_TAIL_CLEARANCE_AUTHORED_NATIVE_REVIEW_PENDING','utc':datetime.now(timezone.utc).isoformat(),
        'source_manifest':str(SOURCE),'source_manifest_sha256':protected[str(SOURCE)],'manifest':str(DEST),'manifest_sha256':common.sha(DEST),
        'changes':changes,'before':before,'after':after,'candidate_attempts':attempts,
        'maximum_lift_mm':amplitude*1000,'changed_vertices_each_mesh':len(changed),'unchanged_component_signatures':{name:signatures[name] for name in unchanged},
        'body_geometry_sha256':signatures['Body'],'pane_perimeter_unchanged':True,'all_four_source_GLBS_and_v4_2_files_unchanged':True,
        'protected_file_count':len(protected),'protected_hashes':protected,'new_blend':str(blend),'new_blend_sha256':common.sha(blend),
        'new_glb':str(glb),'glb_validation':glb_info,
        'sampling_limit':'Dense 2.5mm rear-facing tail surface grid plus source vertices; native frozen rear visual recheck remains required.'}
    (OUT/'fit-v4_3-tail-clearance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (OUT/'native-v4_3-mesh-changes.json').write_text(json.dumps({'manifest':str(DEST),'manifest_sha256':common.sha(DEST),
        'changes':changes,'unchanged_models':['A','B','D'],'unchanged_C_components':unchanged},indent=2)+'\n')
    print('CRYO_C_TAIL_V4_3',json.dumps({'manifest':str(DEST),'lift_mm':amplitude*1000,'before':before['minimum_euclidean_clearance_mm'],
        'after':after['minimum_euclidean_clearance_mm'],'samples':after['samples'],'changed_vertices_each_mesh':len(changed),'protected':len(protected)}),flush=True)


if __name__=='__main__':main()
