"""Load the retained F3 grip calibration only for its exact source revisions."""
from pathlib import Path
import json


def load_supported_grip(source_hashes):
    path = Path(__file__).resolve().parent / 'calibration/vexa_right_pole_50mm.json'
    preset = json.loads(path.read_text(encoding='utf-8'))
    actual = {Path(name).name: digest for name, digest in source_hashes.items()}
    for name, digest in preset['source_sha256'].items():
        if actual.get(name) != digest:
            raise ValueError(f'Grip calibration requires the recorded revision of {name}')
    if preset['pole_radius_m'] != 0.025 or preset['side'] != 'right':
        raise ValueError('Unsupported pole or hand calibration')
    return preset['fit']
