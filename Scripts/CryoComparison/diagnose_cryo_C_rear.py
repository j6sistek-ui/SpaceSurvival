"""Read-only rear-window/source overlap diagnosis. No saves or renders."""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import validate_cryo_fit_v4 as audit

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest',type=Path,default=OUT/'assembly_fit_v4_3.json')
parser.add_argument('--receipt',type=Path,default=WORK/'cryo-C-rear-intersection-v4_3.json')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert not args.receipt.exists(),'Preserve existing audit receipt; choose a new path'
manifest=json.loads(args.manifest.read_text())
model=next(m for m in manifest['models'] if m['id']=='C')
guards={model[k]:audit.sha(model[k]) for k in ('source','editable_blend','finished_glb')}
bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
surfaces={name:audit.surface(bpy.data.objects[name]) for name in ('Body','Glass','Frost','Housing')}
camera=Vector((0,6.5,1.6));fx=480/math.tan(math.radians(35/2))
hits=[]
for px,py in ((365,688),(365,660),(365,710),(350,688),(380,688),(330,680),(400,680)):
    direction=Vector(((480-px)/fx,-1,(600-py)/fx)).normalized()
    row={'pixel':[px,py],'camera_blender_m':list(camera),'direction':list(direction),'hits':{}}
    for name,surf in surfaces.items():
        p,n,i,d=surf['tree'].ray_cast(camera,direction,20)
        row['hits'][name]=None if p is None else {'point':list(p),'distance_m':d,'triangle':i,'normal':list(n)}
    hits.append(row)
outside=[];back=surfaces['Glass']['tree'];body=surfaces['Body']
for index,p in enumerate(body['points']):
    if not(abs(p.x)<.62 and .87<p.z<2.7 and p.y>.45):continue
    q,n,i,d=back.ray_cast(Vector((p.x,2.,p.z)),Vector((0,-1,0)),4)
    if q is not None and q.y>.4 and p.y>q.y+.0005:
        depth=6.5-p.y
        outside.append({'vertex':index,'point':list(p),'glass_at_same_xz':list(q),'outward_y_mm':(p.y-q.y)*1000,
                        'projected_pixel':[480-fx*p.x/depth,600-fx*(p.z-1.6)/depth]})
blob=[p for p in outside if 310<p['projected_pixel'][0]<430 and 620<p['projected_pixel'][1]<760]
def bounds(rows):
    return None if not rows else {'min':[min(r['point'][i] for r in rows) for i in range(3)],'max':[max(r['point'][i] for r in rows) for i in range(3)],
                                 'count':len(rows),'max_outward_y_mm':max(r['outward_y_mm'] for r in rows)}
report={'model':'C','basis':'Blender meters; rear +Y; Unreal OBJ import negates Y',
        'manifest':str(args.manifest.resolve()),'manifest_sha256':audit.sha(args.manifest),
        'camera_projection':'Native back camera local(0,-650,160)cm, FOV35,960x1200; converted to Blender basis',
        'pixel_rays':hits,'rear_opening_outside_vertices':bounds(outside),'blob_region':bounds(blob),
        'worst_outside_vertices':sorted(outside,key=lambda r:r['outward_y_mm'],reverse=True)[:30],
        'blob_vertices':sorted(blob,key=lambda r:r['outward_y_mm'],reverse=True)[:50],
        'protected_files_unchanged':all(audit.sha(p)==h for p,h in guards.items())}
if manifest['version']=='v4_3_C_tail_clearance':
    import fit_cryo_C_tail_v4_3 as tail
    points=tail.tail_samples(body)
    points += [p for p in body['points'] if .20<=p.x<=.57 and 1.05<=p.z<=1.55 and .60<p.y<.90]
    report['fresh_loaded_tail_clearance']=tail.clearance(points,surfaces['Glass'])
    assert report['fresh_loaded_tail_clearance']['minimum_euclidean_clearance_mm']>=5
path=args.receipt;path.write_text(json.dumps(report,indent=2)+'\n')
print('C_REAR_INTERSECTION',json.dumps({'report':str(path),'outside':bounds(outside),'blob':bounds(blob),'hashes_unchanged':report['protected_files_unchanged']}),flush=True)
