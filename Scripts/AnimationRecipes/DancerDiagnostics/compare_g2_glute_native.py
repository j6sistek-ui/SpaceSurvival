"""Compare fresh native surfaces with exact saved-action/weight-patch samples."""
import json
import os
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree

P = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
variant = os.environ.get('SS_G2_VARIANT', '')
assert variant in ('', 'glute_follow', 'glute_follow_240', 'palmar', 'g1_shoulder', 'g1_shoulder_cap')
O = P / '.agent/local/AnimationReview_20261025' / ('G1ShoulderNative240' if variant == 'g1_shoulder' else 'G2PalmarNative240' if variant == 'palmar' else 'G2GluteFollowNative240' if variant == 'glute_follow_240' else 'G2GluteFollowNative')
if variant == 'g1_shoulder_cap':
    O = P / '.agent/local/AnimationReview_20261025/G1ShoulderCapNative240'
source = json.loads((O / 'SourceControls.json').read_text())
native = json.loads((O / 'NativeCapture.json').read_text())
assert native['ok'] and source['source_sha256'] == native['source_sha256']
assert source['action_sha256'] == native['action_sha256']
rows = {r['label']: r for r in source['rows']}
captures = [r for r in native['captures'] if r['kind'] == 'still' and r['view'] == 'front']
assert len(captures) == 8
names = list(captures[0]['bones_world_cm'])
assert len(names) == 95
src = np.array([rows[captures[0]['label']]['bones_m'][n] for n in names]) * 100
dst = np.array([captures[0]['bones_world_cm'][n] for n in names])
U, _, V = np.linalg.svd((src-src.mean(axis=0)).T @ (dst-dst.mean(axis=0)))
rotation = U @ V
translation = dst.mean(axis=0) - src.mean(axis=0) @ rotation
surfaces = np.load(O / 'SourceSurfaces.npz')

def distances(query, ref):
    tree = KDTree(len(ref))
    for i, point in enumerate(ref):
        tree.insert(tuple(point), i)
    tree.balance()
    return np.array([tree.find(tuple(point))[2] for point in query])

report = {'source_sha256': source['source_sha256'], 'action_sha256': source['action_sha256'],
          'basis': rotation.tolist(), 'translation_cm': translation.tolist(), 'rows': [],
          'scope': 'Eight fresh native95-bone and visible-surface comparisons with one fixed coordinate transform; not full joint or garment acceptance.'}
for capture in captures:
    label = capture['label']
    expected = np.array([rows[label]['bones_m'][n] for n in names])*100 @ rotation + translation
    actual = np.array([capture['bones_world_cm'][n] for n in names])
    bone_error = np.linalg.norm(expected-actual, axis=1)
    arrays = {k: surfaces[k]*100 @ rotation + translation for k in surfaces.files if k.startswith(label+'__')}
    points = np.concatenate(list(arrays.values()))
    actual_surface = np.array(json.loads((O / 'NativeViews' / (label+'_Surface.json')).read_text())['vertices_world_cm'])
    forward = distances(actual_surface, points)
    backward = distances(points, actual_surface)
    report['rows'].append({'label': label, 'seconds': capture['seconds'], 'bone_max_mm': float(bone_error.max()*10),
                           'source_vertices': len(points), 'native_vertices': len(actual_surface),
                           'surface_max_mm': float(max(forward.max(), backward.max())*10),
                           'parts': {n: float(distances(a, actual_surface).max()*10) for n, a in arrays.items()}})
report['max_bone_error_mm'] = max(r['bone_max_mm'] for r in report['rows'])
report['max_surface_error_mm'] = max(r['surface_max_mm'] for r in report['rows'])
report['ok'] = report['max_bone_error_mm'] < .5 and report['max_surface_error_mm'] < .5
(O / 'NativeParity.json').write_text(json.dumps(report, indent=2))
print('GLUTE_NATIVE_PARITY', report['ok'], report['max_bone_error_mm'], report['max_surface_error_mm'], flush=True)
assert report['ok']
