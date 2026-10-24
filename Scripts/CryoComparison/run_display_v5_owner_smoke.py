from pathlib import Path
import runpy
api = runpy.run_path('D:/Codex/CryoComparison_20261021/work/verify_cryo_owner_smoke.py')
api['main'].__globals__['PROOF'] = Path('D:/Codex/CryoComparison_20261021/work/CryoInteractionV5_20261024T004425Z_39480.json')
api['main']()
