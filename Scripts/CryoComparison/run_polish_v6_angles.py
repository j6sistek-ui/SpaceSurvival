import runpy
api = runpy.run_path('D:/Codex/CryoComparison_20261021/work/verify_cryo_polish_v6.py')
settings = api['main'].__globals__
plan = settings['shot_plan']()
assert len(plan) == 48
# Inspect each new core and idle plume before the established all-angle views.
settings['shot_plan'] = lambda: plan[36:] + plan[:36]
api['main']()
