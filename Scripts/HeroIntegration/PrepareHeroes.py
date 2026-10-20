"""Run private import, retarget and native checks in order, stopping on any failed stage."""
from pathlib import Path
import runpy
import unreal as u

assert '-SSApplyPlayableHeroes' in u.SystemLibrary.get_command_line().split()
SCRIPTS = Path(__file__).resolve().parent
for stage in ['ImportHeroes.py', 'RetargetHeroes.py', 'ValidateHeroes.py']:
    print('HERO_STAGE_BEGIN', stage, flush=True)
    runpy.run_path(str(SCRIPTS / stage), run_name='__main__')
    print('HERO_STAGE_PASS', stage, flush=True)
