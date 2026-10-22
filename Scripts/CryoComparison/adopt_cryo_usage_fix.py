"""Hash-guarded update of the two newly adopted cryo mist materials only."""
from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone
WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=WORK/'CryoStage/Content/SpaceSurvival/CryoComparison'
TARGET=Path('C:/Users/j6sis/SpaceSurvival/Content/SpaceSurvival/CryoComparison')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=OUT/'native-adoption.json'
    receipt=json.loads(path.read_text())
    allowed={'Materials/M_NiagaraColdMist.uasset','Materials/MI_NiagaraColdMist.uasset'}
    changed=[]
    for row in receipt['files']:
        relative=row['relative_path']
        assert sha(TARGET/relative)==row['sha256'],'Owner content changed; refuse update'
        if sha(SOURCE/relative)!=row['sha256']:
            assert relative in allowed,'Unexpected stage change'
            changed.append(row)
    assert changed and len(changed)<=2
    backup=WORK/'owner-adoption-before/niagara-usage'
    backup.mkdir(exist_ok=False)
    shutil.copy2(path,OUT/'native-adoption-initial.json')
    changes=[]
    for row in changed:
        relative=row['relative_path']
        old=row['sha256']
        shutil.copy2(TARGET/relative,backup/Path(relative).name)
        shutil.copy2(SOURCE/relative,TARGET/relative)
        row['sha256']=sha(SOURCE/relative)
        row['bytes']=(SOURCE/relative).stat().st_size
        assert sha(TARGET/relative)==row['sha256']
        changes.append({'relative_path':relative,'before':old,'after':row['sha256']})
    receipt['bytes']=sum(row['bytes'] for row in receipt['files'])
    receipt['follow_up']={'utc':datetime.now(timezone.utc).isoformat(),'reason':'Enable native Niagara sprite shader usage; rejected runtime checkerboard fixed','changes':changes,'backup':str(backup)}
    receipt['status']='ADOPTED_NEW_NAMESPACE_AND_NIAGARA_FIX_HASH_VERIFIED'
    path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':receipt['status'],'changed':len(changes),'bytes':receipt['bytes']}))
if __name__=='__main__':main()
