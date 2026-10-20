"""Finish the explicitly requested private cloth and foot-contact work, then remeasure."""
from pathlib import Path
import runpy
SCRIPTS = Path(__file__).resolve().parent
for name in ['CorrectGroundContact.py', 'ConfigureCloth.py', 'ValidateHeroes.py']:
    print('HERO_FINISH_BEGIN', name, flush=True)
    runpy.run_path(str(SCRIPTS / name), run_name='__main__')
    print('HERO_FINISH_PASS', name, flush=True)
