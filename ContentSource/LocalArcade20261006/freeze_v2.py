"""Freeze reviewed V2 deliverables while verifying every Frozen1 source is intact."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'.agent/local/ArcadeGeneration'
NAMES=('CreditExchangeV2','RiftSalvageV2')


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    target=WORK/'FROZEN_V2_MANIFEST.json'
    if target.exists():raise RuntimeError('V2 is already frozen; use another version for changes')
    previous=WORK/'FROZEN_MANIFEST.json'
    preserved=set()
    for row in json.loads(previous.read_text())['station_imports']:
        assert sha(row['manifest_path'])==row['manifest_sha256']
        data=json.loads(Path(row['manifest_path']).read_text())
        for path,digest in data['source_sha256'].items():
            assert sha(path)==digest, 'Frozen1 source changed: '+path
            preserved.add(path)
    now=datetime.now(timezone.utc).isoformat()
    result={'created_utc':now,'local_only':True,'authoring':'Existing local Blender 5.2.2, CPU rendering; no cloud/model downloads','station_imports':[],
            'previous_manifest':str(previous),'previous_manifest_sha256':sha(previous),'previous_sources_preserved':len(preserved),
            'review':'Root accepted V2 rendered candidates for native review; final small legend/grounding corrections inspected by author; owner/native room quality remains open'}
    for name in NAMES:
        folder=WORK/'final'/name;path=folder/'asset.json';data=json.loads(path.read_text())
        assert not data.get('frozen')
        assert data['uv_validation']['zero_area_triangles']==0
        assert data['uv_validation']['degenerate_uv_triangles']==0
        if 'prize_grounding' in data:
            assert all(abs(r['min_z_m']-r['bed_z_m'])<.00001 for r in data['prize_grounding'])
        files={str(p.resolve()) for ext in ('*.fbx','*.glb','*.blend') for p in folder.glob(ext)}
        files.update(m['base_color_texture'] for m in data['materials'] if m.get('base_color_texture'))
        assert all(Path(m['base_color_texture']).parent==WORK/'final/textures_v2' for m in data['materials'] if m.get('base_color_texture'))
        for view in ('front','quarter','detail'):assert (folder/(name+'_'+view+'.png')).is_file()
        data['source_sha256']={p:sha(p) for p in sorted(files)}
        data['frozen']=True;data['frozen_utc']=now
        data['status']='Frozen V2 static export, root candidate approved; native placement/owner acceptance remain open'
        path.write_text(json.dumps(data,indent=2))
        result['station_imports'].append({'name':name,'manifest_path':str(path),'manifest_sha256':sha(path),'dimensions_m':data['dimensions_m'],'triangles':data['triangles'],'fbx_parts':data['fbx_parts'],'render_sha256':{str(folder/(name+'_'+v+'.png')):sha(folder/(name+'_'+v+'.png')) for v in ('front','quarter','detail')}})
    target.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
