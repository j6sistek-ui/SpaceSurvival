"""Read-only independent OBJ/provenance check of the four local v6 cores."""
from datetime import datetime, timezone
from pathlib import Path
import json, math, struct
from validate_cryo_displays_v5 import BVH, load_obj, sha

WORK=Path(__file__).resolve().parent; OUT=WORK.parent/'outputs/Cryo_Comparison'
MANIFEST=OUT/'assembly_polish_v6.json'; SOURCE=OUT/'assembly_displays_v5_4.json'
AUTHOR=OUT/'core-v6-author.json'; PLAN=WORK/'cryo-core-v6-plan.json'

def field(p,c):
    def ramp(t):
        if t<=0:return 0.,0.
        if t>=1:return 1.,0.
        return t*t*(3-2*t),6*t*(1-t)
    def box(v,lo,hi,band):
        if v<lo:
            w,g=ramp((v-lo+band)/band);return w,g/band
        if v>hi:
            w,g=ramp((hi+band-v)/band);return w,-g/band
        return 1.,0.
    lo,hi,zlo,zhi=c['rigid_xz'];band=c['transition_width_m']
    x,gx=box(p[0],lo,hi,band);z,gz=box(p[2],zlo,zhi,band)
    span=c['depth_zero_y']-c['depth_full_y'];y,gy=ramp((c['depth_zero_y']-p[1])/span)
    return x*y*z,(gx*y*z,-x*gy*z/span,x*y*gz)

def lines(path):
    text=Path(path).read_text().splitlines()
    return {tag:[line for line in text if line.startswith(tag+' ')] for tag in ['v','vt','vn','f']}, [l for l in text if not l.startswith(('v ','vt ','vn '))]

def main():
    current=json.loads(MANIFEST.read_text());previous=json.loads(SOURCE.read_text())
    author=json.loads(AUTHOR.read_text());plans=json.loads(PLAN.read_text());errors=[];models=[];changed=[];unchanged=[]
    def check(ok,label):
        if not ok:errors.append(label)
    protected=all(Path(p).is_file() and sha(p)==h for p,h in author['protected_hashes'].items())
    check(protected,'Protected input hash changed')
    check(sha(MANIFEST)==author['manifest_sha256'],'Author manifest hash')
    for model,old in zip(current['models'],previous['models']):
        key=model['id'];cfg=plans[key];rows={r['name']:r for r in model['components']};oldrows={r['name']:r for r in old['components']}
        check(len(rows)==21 and set(rows)==set(oldrows),key+' component identity/count')
        for name,row in rows.items():
            same=sha(row['file'])==sha(oldrows[name]['file'])
            (unchanged if same else changed).append(key+'/'+name)
            check(same==(name!='Body'),key+'/'+name+' unexpected change')
        a,non_a=lines(oldrows['Body']['file']);b,non_b=lines(rows['Body']['file'])
        check(non_a==non_b,key+' face/UV index/topology/material text changed')
        check(a['vt']==b['vt'],key+' UV values changed')
        check(all(len(a[t])==len(b[t]) for t in a),key+' OBJ counts changed')
        vertices=[tuple(float(v)/100 for v in l.split()[1:4]) for l in a['v']]
        revised=[tuple(float(v)/100 for v in l.split()[1:4]) for l in b['v']]
        fields=[field(p,cfg) for p in vertices]
        outside=[i for i,(w,g) in enumerate(fields) if w==0]
        rigid=[i for i,(w,g) in enumerate(fields) if w==1]
        check(all(a['v'][i]==b['v'][i] for i in outside),key+' unmoved vertex text changed')
        xz_error=max(max(abs(q[k]-p[k]) for k in [0,2]) for p,q in zip(vertices,revised))
        field_error=max(abs((p[1]-q[1])-cfg['forward_offset_m']*w) for p,q,(w,g) in zip(vertices,revised,fields))
        check(xz_error<2e-7 and field_error<2e-7,key+' local deformation differs from plan')
        normal_vertex={}
        for line in a['f']:
            for token in line.split()[1:]:
                vi,ti,ni=[int(v)-1 for v in token.split('/')];normal_vertex[ni]=vi
        keep=[i for i in range(len(a['vn'])) if not any(fields[normal_vertex[i]][1])]
        check(all(a['vn'][i]==b['vn'][i] for i in keep),key+' untouched/rigid native normals changed')
        oldtree=BVH(load_obj(oldrows['Body']['file'])['triangles']);newtree=BVH(load_obj(rows['Body']['file'])['triangles'])
        obstacles=BVH([t for name in ['Glass','Frost','Housing','Trim'] for t in load_obj(rows[name]['file'])['triangles']])
        center_x,center_z=cfg['center_xz'];r=cfg['face_radius'];clearances=[];shifts=[]
        for j in range(41):
            for i in range(41):
                dx=(i/40*2-1)*r;dz=(j/40*2-1)*r
                if dx*dx+dz*dz>r*r:continue
                origin=(center_x+dx,-2,center_z+dz);oldhit=oldtree.ray(origin,(0,1,0),2)
                if oldhit is None or oldhit-2>=cfg['depth_full_y']:continue
                newhit=newtree.ray(origin,(0,1,0),2)
                if newhit is None:errors.append(key+' lost core ray hit');continue
                shifts.append(oldhit-newhit)
                obstacle=obstacles.ray(origin,(0,1,0),2)
                if obstacle is not None:clearances.append(obstacle-newhit)
        check(bool(clearances) and min(clearances)>=.025-2e-7,key+' core/pane forward clearance below25mm')
        # Samples may land on transition triangles at the casing silhouette, so report rather than assume all are rigid.
        glb=Path(model['finished_glb']).read_bytes();n=struct.unpack_from('<I',glb,12)[0];doc=json.loads(glb[20:20+n])
        check(len(doc['meshes'])==21,key+' GLB mesh count')
        check(sha(model['finished_glb'])==model['core_v6']['glb_sha256'],key+' GLB hash')
        check(sha(model['editable_blend'])==model['core_v6']['blend_sha256'],key+' Blend hash')
        result={'id':key,'core_center_cm':model['core_v6']['core_center_cm'],'forward_offset_cm':cfg['forward_offset_m']*100,
            'body_obj':rows['Body']['file'],'body_obj_sha256':sha(rows['Body']['file']),'body_vertices':len(vertices),'body_triangles':len(a['f']),
            'assembly_triangles':sum(r['triangles'] for r in rows.values()),'components':21,'unmoved_vertex_lines_exact':len(outside),
            'rigid_vertices':len(rigid),'topology_uv_materials_exact':non_a==non_b and a['vt']==b['vt'],
            'unmoved_and_rigid_normal_lines_exact':len(keep),'max_xz_error_m':xz_error,'max_deformation_error_m':field_error,
            'core_front_samples':len(shifts),'core_shift_range_cm':[min(shifts)*100,max(shifts)*100],
            'overlapping_pane_rim_samples':len(clearances),'minimum_corresponding_forward_clearance_mm':min(clearances)*1000,
            'body_only_local_derivative':True,'author_blender_normal_encoding_max_delta':model['core_v6']['unchanged_and_rigid_corner_normal_max_error']}
        models.append(result);print(json.dumps(result),flush=True)
    receipt={'status':'PASS_LOCAL_CORE_GEOMETRY_AND_PRESERVATION' if not errors else 'FAIL','utc':datetime.now(timezone.utc).isoformat(),
        'manifest':str(MANIFEST),'manifest_sha256':sha(MANIFEST),'source_manifest':str(SOURCE),'source_manifest_sha256':sha(SOURCE),
        'author_receipt':str(AUTHOR),'author_receipt_sha256':sha(AUTHOR),'author_script':author['author_script'],'author_script_sha256':sha(author['author_script']),
        'plan':str(PLAN),'plan_sha256':sha(PLAN),'audit_script':str(Path(__file__).resolve()),'audit_script_sha256':sha(__file__),
        'errors':errors,'protected_inputs_unchanged':protected,'protected_file_count':len(author['protected_hashes']),
        'changed_components':changed,'unchanged_components':unchanged,'models':models,
        'limits':['Local geometry/provenance check only; native all-angle visual review remains required.',
            'Dense corresponding front rays establish sampled pane/rim clearance, not visibility from arbitrary occluded rear angles.',
            'Continuous compact deformation keeps existing indexed connections; it does not repair pre-existing source defects.',
            'Native OBJ untouched/rigid normals are copied exactly. Blender/GLB normal encoding differences are recorded separately.']}
    (WORK/'cryo-core-v6-audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'],errors)
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
