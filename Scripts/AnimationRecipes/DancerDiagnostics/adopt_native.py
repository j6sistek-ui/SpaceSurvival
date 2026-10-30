import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Explicit, hash-backed scoped adoption. Never copies a station/observatory map."""
from pathlib import Path
import hashlib,json,shutil,sys
P=R.parents[2];W=R.parent/'CharacterBatch_20261021/WorkbenchNative'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mode=sys.argv[-1];assert mode in ('originals','library')
if mode=='originals':
 receipt=json.loads((R/'ExistingRetargetRepair.json').read_text());assert receipt['ok']
 rels=[Path('Content/SpaceSurvival/Licensed/CharacterWorkshop/Animations')/('A_F3_'+n+'.uasset') for n in ('g1','g2','b1','b2','G1_G2_Routine','B1_B2_Routine')]
else:
 raise RuntimeError('Library adoption disabled: owner rejected V8 contact motion. Native numeric passes do not approve visual quality; implement a reviewed, hash-bound replacement gate before adoption.')
 assert json.loads((R/'NativeCandidates.json').read_text())['ok']
 assert json.loads((R/'LiveReview_ContactCheck.json').read_text())['ok']
 assert json.loads((R/'LiveReview_SwappedFinal.json').read_text())['ok']
 relroot=Path('Content/SpaceSurvival/Licensed/ZeroGChoreography_20261025')
 rels=[x.relative_to(W) for x in (W/relroot).rglob('*') if x.is_file() and x.suffix in ('.uasset','.umap','.uexp','.ubulk')]
assert rels
rows=[]
for rel in rels:
 src=W/rel;dest=P/rel;assert dest.resolve().is_relative_to(P.resolve()) and src.resolve().is_relative_to(W.resolve())
 before=sha(dest) if dest.exists() else None
 if before:
  backup=R/'BeforeAdoption'/rel;backup.parent.mkdir(parents=True,exist_ok=True)
  if backup.exists():assert sha(backup)==before,'Existing backup differs; stop for inspection'
  else:shutil.copy2(dest,backup)
  assert sha(backup)==before and sha(dest)==before
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);assert sha(src)==sha(dest)
 rows.append({'file':str(rel),'before':before,'after':sha(dest),'bytes':dest.stat().st_size})
(R/('Adoption_'+mode+'.json')).write_text(json.dumps(rows,indent=2));print('ADOPTED',mode,len(rows),sum(r['bytes'] for r in rows))
