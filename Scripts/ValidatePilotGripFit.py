"""Fresh candidate reload and four unsaved resident-texture native comparison views."""
import importlib.util
import sys
from pathlib import Path
import unreal as u


ROOT = Path(__file__).resolve().parents[1]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ('Scripts/' + name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


pair = module('AuthorPilotGripFit')
grip = module('AuthorGripFit')

def main(render=False):
    record = pair.main(True)
    report, digest = grip.checked_source()
    mesh = u.load_asset(grip.PATH)
    record['grip'] = grip.validate(mesh, report, digest)
    record['comparison'] = 'Before is original grip/Pilot; After is candidate grip/Pilot. Same camera, lighting, mesh mount and forced hero texture residency; both geometry and pose intentionally change.'
    if render:
        protected = {p: pair.sha(p) for folder in ('Source', 'Config', 'Content') for p in (ROOT / folder).rglob('*') if p.is_file()}
        old = u.load_asset('/Game/SpaceSurvival/Meshes/SM_AcornShipV2')
        cases = [
            ('UnrealResidentBefore', old, 'Pilot', 0, (165, -165, 185), (12, 0, 94)),
            ('UnrealResidentAfter', mesh, 'PilotGripFit', 0, (165, -165, 185), (12, 0, 94)),
            ('UnrealReleaseLift', mesh, 'DisembarkGripFit', 0.1, (165, -165, 185), (12, 0, 94)),
            ('UnrealReleaseRetract', mesh, 'DisembarkGripFit', 8 / 30, (165, -165, 185), (12, 0, 94)),
        ]
        grip.SOURCE = pair.SOURCE
        grip.preview(mesh, record, protected, True, cases, str(ROOT / 'Saved/Validation/PilotGripFitPreview.json'))


if __name__ == '__main__':
    main('--preview' in sys.argv)
