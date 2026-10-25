"""Expose concise actual-game evidence and verify delivered native package identity."""
from pathlib import Path
import hashlib,json,shutil
from datetime import datetime,timezone
WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
OWNER=Path('C:/Users/j6sis/SpaceSurvival')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(WORK.glob('CryoGameRuntime_*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
raw=files[0]
r=json.loads(raw.read_text())
assert r['status']=='NATIVE_GAME_AUTOPLAY_LOOP_PHASE_AND_RESTORE_VERIFIED' and not r['errors']
assert r['native_cvar_restoration_verified'] and r['native_hashes_unchanged'] and r['original_source_hashes_unchanged']
assert len(r['screenshots'])==3
delivered=[]
for relative,digest in r['protected_native_hashes'].items():
    if relative.replace('\\','/').startswith('Content/SpaceSurvival/CryoComparison/'):
        assert sha(OWNER/relative)==digest, 'Owner copy differs from the verified native game'
        delivered.append(relative)
assert len(delivered)==125
adoption=json.loads((OUT/'native-adoption.json').read_text())
assert all(sha(OWNER/'Content/SpaceSurvival/CryoComparison'/row['relative_path'])==row['sha256'] for row in adoption['files'])
for shot in r['screenshots']:
    assert sha(Path(shot['png']))==shot['sha256']
    shot['relative_image']=Path(shot['png']).resolve().relative_to(OUT.resolve()).as_posix()
evidence=OUT/'evidence'
evidence.mkdir(exist_ok=True)
shutil.copy2(raw,evidence/raw.name)
summary={key:r.get(key) for key in ('status','started_utc','finished_utc','engine','mode','map','sequence','errors','events','analysis','screenshots','native_cvar_restoration_verified','local_fog_start_distance_before_beginplay_cm','local_fog_start_distance_after_endplay_cm','native_hashes_unchanged','original_source_hashes_unchanged','limits')}
summary.update({'raw_receipt':'evidence/'+raw.name,'raw_sha256':sha(raw),'owner_files_match_verified_game':125,
    'owner_project_launched':False,'generated_utc':datetime.now(timezone.utc).isoformat(),
    'visual_review':'Lead reviewed D runtime pair and all-four overview: no checkerboard particles; bounded cold mist and cyan illumination remain visible. Owner preference is still unconfirmed.',
    'prior_rejected_render':'CryoGameRuntime_20261022T031017Z_38784: missing NiagaraSprites material usage; repaired and reverified.',
    'warning_scope':'Only a startup slow-Python-command warning in accepted native game log; no missing Niagara material usage warning.',
    'presentation_only':'Detached review cameras used; disposable DefaultPawn hidden only for captures. No light/sequence seek or play setter is used.'})
(OUT/'runtime-verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'receipt':str(OUT/'runtime-verification.json'),'run':raw.stem,'status':r['status'],'delivered_files_verified':len(delivered)}))
