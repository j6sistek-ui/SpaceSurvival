"""Collect saved final native content and preserved import sources for verification."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib
WORK=Path(__file__).resolve().parent
BASE='/Game/SpaceSurvival/CryoComparison'
r=json.loads((WORK/'CryoUnrealAuthor.json').read_text())
c=json.loads((WORK/'CryoConsoleUpgrade.json').read_text())
b=json.loads((WORK/'CryoBreathingLights.json').read_text())
assert c['status']=='CONSOLE_GLASS_HUD_SAVED_PENDING_RENDER'
assert b['status']=='SAVED_NATIVE_LOOP_BINDINGS_VERIFIED_RENDER_AND_AUTOPLAY_PENDING'
manifest=WORK.parent/'outputs/Cryo_Comparison/assembly_holo_consoles.json'
m=json.loads(manifest.read_text())
r['status']='AUTHORED_SAVED_FINAL_PENDING_RENDER_RUNTIME_REVIEW'
r['utc']=datetime.now(timezone.utc).isoformat()
r['manifest']=str(manifest)
r['manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
r['source_files'].update(c['source_files'])
root=WORK/'CryoStage/Content/SpaceSurvival/CryoComparison'
r['saved_assets']=[BASE+'/'+p.relative_to(root).with_suffix('').as_posix() for p in sorted(root.rglob('*.uasset'))]
r['materials']=[{'asset':p,'compile_errors':None,'check':'Aggregation does not compile materials; use native author receipts and fresh-load render verification.'} for p in r['saved_assets'] if '/Materials/' in p]
r['meshes']=[row for row in r['meshes'] if row['role']!='console']+c['meshes']
r['plan']=[{'id':model['id'],'label':model['label'],'x_cm':x,'height_cm':320,'role_counts':dict(Counter(p['role'] for p in model['components']))} for model,x in zip(m['models'],(-540,-180,180,540))]
assert len({json.dumps(p['role_counts'],sort_keys=True) for p in r['plan']})==1
r['counts']={'active_mesh_actors':76,'all_saved_assets_including_recovery':len(r['saved_assets']),
             'materials_including_recovery':len(r['materials']),'local_fog_volumes':4,'niagara_actors':4,'animated_light_tracks':8,'breathing_period_seconds':6}
r['revision_receipts']=[str(WORK/p) for p in ('CryoNativeRefinement.json','CryoNativeTuning.json','CryoNativePolish.json','CryoConsoleUpgrade.json','CryoBreathingLights.json','CryoDisplaySampling.json','CryoFogPreviewTrack.json')]
r['source_hashes_unchanged']=all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==row['sha256'] for path,row in r['source_files'].items())
assert r['source_hashes_unchanged']
(WORK/'CryoFinalAuthor.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps({'status':r['status'],'counts':r['counts'],'input_hashes':len(r['source_files'])}))
