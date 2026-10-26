import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Add relocation evidence without rewriting the immutable old source manifest."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
old=Path('C:/Users/j6sis/OneDrive/Documents/Unreal Projects/AFS')
new=Path('M:/UnrealProjects/AFS')
assert (new/'AFS.uproject').is_file()
manifest=R/'SourceCopyManifest.json'
before=hashlib.sha256(manifest.read_bytes()).hexdigest()
report={'checked_at':datetime.now(timezone.utc).isoformat(),'owner_reported_project_root':str(new),'original_manifest_sha256':before,'rows':[]}
for row in json.loads(manifest.read_text()):
 source=Path(row['source'])
 if not source.is_relative_to(old):continue
 relocated=new/source.relative_to(old)
 actual=hashlib.file_digest(relocated.open('rb'),'sha256').hexdigest() if relocated.is_file() else None
 report['rows'].append({'original':str(source),'relocated':str(relocated),'expected':row['sha256'],'actual':actual,'match':actual==row['sha256']})
report['ok']=len(report['rows'])>0 and all(r['match'] for r in report['rows'])
assert hashlib.sha256(manifest.read_bytes()).hexdigest()==before
(R/'RelocatedAFSSources.json').write_text(json.dumps(report,indent=2))
print('RELOCATED_AFS',report['ok'],len(report['rows']),sum(r['match'] for r in report['rows']))
