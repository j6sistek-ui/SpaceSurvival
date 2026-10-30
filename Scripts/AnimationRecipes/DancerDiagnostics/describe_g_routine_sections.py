"""Expose the actual source coverage and timing of the current review edit.

These are descriptive chapters, not an approved replacement choreography.
"""
import hashlib
import html
import json
import os
import struct
from pathlib import Path

import numpy as np

project = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home() / 'SpaceSurvival'))).resolve()
source = project / 'SourceAssets/DanceRefinement_20261025'
review = project / '.agent/local/AnimationReview_20261025'
output = review / 'CurrentGFullLegReview'
delivery = json.loads((output / 'Delivery.json').read_text())
g1 = json.loads((source / 'G1_PalmarGrip_Knots_Manifest.json').read_text())
g2 = json.loads((source / 'G2_PalmarGrip_Knots_Manifest.json').read_text())
pace = json.loads((review / 'G2PosteriorHip/PacedHipAction.json').read_text())
offset = delivery['clip_start_seconds'][2]


def first_time(raw_frame):
    seconds = (raw_frame - 780) / 12
    return float(np.interp(seconds, g1['source_seconds_map'], g1['destination_seconds_map']))


def second_time(base_seconds):
    paced = (np.interp(1 + base_seconds * 60, pace['source_frames'], pace['destination_frames']) - 1) / 60
    return offset + float(np.interp(paced, g2['source_seconds_map'], g2['destination_seconds_map']))


def clip_info(name, start, end):
    path = project / 'SourceAssets/CharacterWorkshop_20261021/MotionSources' / name
    with path.open('rb') as file:
        assert file.read(4) == b'glTF'
        file.read(8)
        size, kind = struct.unpack('<II', file.read(8))
        assert kind == 0x4e4f534a
        data = json.loads(file.read(size))
    samplers = data['animations'][0]['samplers']
    accessors = [data['accessors'][s['input']] for s in samplers]
    length = max(a['max'][0] for a in accessors) - min(a['min'][0] for a in accessors)
    return {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'full_duration_seconds': length, 'selected_frames_60hz': [start, end],
            'selected_source_seconds': [(start - 1) / 60, (end - 1) / 60],
            'selected_span_seconds': (end - start) / 60}


rows = [
    (0., first_time(920), 'G1 supported passage', 'Original source780–920; contact-repaired excerpt. Review shape changes and support, not merely orbit speed.'),
    (first_time(920), first_time(940), 'G1 release', 'Original source920–940 with staged grip release. Preserve release clearance.'),
    (first_time(940), g1['seconds'], 'G1 departure', 'End of selected passage, source940–1000. Earlier original moves are absent.'),
    (delivery['clip_start_seconds'][1], offset, 'Bridge', 'New four-second body/shoulder transition; not an original source move.'),
    (offset, second_time(2.5), 'G2 approach', 'Held source-start shape plus approach. New alternating leg detail does not add a distinct large move.'),
    (second_time(2.5), second_time(2.5 + 200 / 12 + 1), 'G2 supported excerpt', 'Only source570–770, slowed and paced. Main place to recover missing original movement variety.'),
    (second_time(2.5 + 200 / 12 + 1), second_time(5 + 200 / 12 + 1), 'G2 release', 'Held end shape and support release; leg follow added in this area.'),
    (second_time(5 + 200 / 12 + 1), second_time(7 + 200 / 12 + 1), 'Move away', 'Added two-second base-time displacement with held end pose; not a source move.'),
    (second_time(7 + 200 / 12 + 1), second_time(11 + 200 / 12 + 1), 'Return blend', 'Added four-second base-time interpolation back to the starting shape. Revisit choreography after review.'),
    (second_time(11 + 200 / 12 + 1), offset + g2['seconds'], 'Return approach', 'Added two-second base-time displacement to close the G2 test loop.'),
]
report = {'video_sha256': delivery['sha256'], 'clips': [clip_info('g1_default.glb', 780, 1000), clip_info('g2_default.glb', 570, 770)],
          'sections': [{'start': a, 'end': b, 'name': name, 'meaning': meaning} for a, b, name, meaning in rows],
          'scope': 'Timing/source-coverage map only. Original moves outside selected excerpts remain unincorporated; no revised choreography is claimed.'}
(output / 'Sections.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
page = source / 'CurrentGLegReview.html'
document = page.read_text(encoding='utf-8')
assert '<h2>What is actually in this review</h2>' not in document
document += '<h2>What is actually in this review</h2><p>Only7 seconds of selected original G1/G2 motion are represented, with slow pacing, added approaches, a bridge and returns. Most original moves are not included yet. Leg detail improves held shapes; choreography variety remains open.</p><table style="width:100%;border-collapse:collapse">'
for a, b, name, meaning in rows:
    document += f'<tr><td style="padding:12px;border-top:1px solid #456"><button onclick="routine.currentTime={a};routine.play()">{a:.1f}–{b:.1f}s</button></td><td style="padding:12px;border-top:1px solid #456"><b>{html.escape(name)}</b><br>{html.escape(meaning)}</td></tr>'
document += '</table>'
page.write_text(document, encoding='utf-8')
print('ROUTINE_SECTIONS', [(round(a, 2), round(b, 2), name) for a, b, name, _ in rows])
