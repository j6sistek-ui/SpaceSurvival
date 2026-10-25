from pathlib import Path
import runpy, shutil, hashlib, json
work=Path(__file__).resolve().parent
module=runpy.run_path(str(work/'probe_niagara.py'))
source=Path(r'C:\Users\j6sis\SpaceSurvival\Content');stage=work/'CryoStage'/'Content'
rows=[]
for relative in module['SMOKE_PLUME_FILES']:
    src=source/relative;dst=stage/relative
    assert src.is_file() and not dst.exists(),str(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    a=hashlib.sha256(src.read_bytes()).hexdigest();b=hashlib.sha256(dst.read_bytes()).hexdigest();assert a==b
    rows.append({'relative_path':relative,'bytes':src.stat().st_size,'sha256':a})
(work/'niagara-source-copy.json').write_text(json.dumps(rows,indent=2))
print('Copied native Niagara dependencies',len(rows),sum(r['bytes'] for r in rows))
