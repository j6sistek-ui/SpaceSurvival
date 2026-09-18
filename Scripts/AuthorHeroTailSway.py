"""A subtle tail sway on the squirrel clips that were retargeted from a body with no tail.

    & 'C:\\Program Files\\EpicGames2\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe' `
      'C:\\Users\\j6sis\\SpaceSurvival\\SpaceSurvival.uproject' -unattended -stdout `
      -FullStdOutLogOutput -NullRHI -DisablePlugins=UAssetBrowser `
      '-ExecutePythonScript=C:\\Users\\j6sis\\SpaceSurvival\\Scripts\\AuthorHeroTailSway.py'

The owner's instruction, verbatim: "just a subtle wobble to each for now, leave walk as is, and idle no
wobble", then "can dial it in more later / no major validation on it, simple". So this touches the two
stand fidgets and the two fast gaits and nothing else, and dialling it in means editing CLIPS below and
running it again.

RUNNING IT AGAIN IS THE WHOLE POINT, SO IT HAS TO BE IDEMPOTENT
  The sway is composed onto whatever rotation the clip already has on that bone. Do that naively and a
  second run stacks a second sway on top of the first, so "dial 7 down to 4" would actually dial it up to
  11. An earlier version of this file did exactly that while its docstring claimed otherwise.

  So the first run records the untouched tail tracks to BASELINE (beside the clips, in the git-ignored
  Licensed tree) and every run afterwards composes from that recording rather than from what is in the
  asset. Dialling in is then exact at any value, in any order, any number of times.

  A first run will not take a baseline from a tail that is already moving: these clips come out of
  AuthorHeroMocapRetarget.py with no tail motion at all - no chain in the retargeter touches Tail_01..05,
  and their local transforms measure 0.000 deviation from frame 0 - so a moving tail with no baseline
  file means a sway was applied and the recording was lost. Rebuild the clips with that script and run
  this one again; guessing at the baseline would bake the old sway in permanently.
"""
from pathlib import Path
import json
import math
import traceback

import unreal as u

DIR = '/Game/SpaceSurvival/Licensed/Hero'
BASELINE = Path(u.Paths.project_content_dir()) / 'SpaceSurvival' / 'Licensed' / 'Hero' / 'TailBaseline.json'
REPORT = Path(__file__).resolve().parents[1] / '.agent' / 'local' / 'HeroTailSway.json'
TAIL = ['Tail_01', 'Tail_02', 'Tail_03', 'Tail_04', 'Tail_05']
# Clip -> how far the tip swings, in degrees. The gaits get less: the body is already swinging the
# rigid tail through a wide arc there, and more would read as a wag.
CLIPS = {'A_SquirrelFidgetA': 7.0, 'A_SquirrelFidgetB': 7.0, 'A_SquirrelJog': 4.0, 'A_SquirrelRun': 4.0}
# Not touched, and named here so the list is a decision rather than an omission: the walk is authored
# for this game and the owner asked for it left exactly as it is, and a fidget is only readable as a
# break from a still idle.
LEFT_ALONE = ['A_SquirrelIdle', 'A_SquirrelWalk']
# A tail that is already moving and has no recording behind it. Anything under this reads as the
# retarget's own numerical noise; the measured deviation is 0.000.
STILL_DEGREES = 0.05

report = {'what': 'a subtle tail sway on the retargeted clips', 'clips': {}, 'left_alone': LEFT_ALONE,
          'baseline': str(BASELINE), 'baseline_taken': [], 'failures': []}


def sway(index, phase):
    """Yaw and pitch for one tail bone at one point around the loop, in degrees of the tip's swing.

    Amplitude grows toward the tip because a tail is a chain: the root barely moves and the end carries
    the travel. Each bone lags the one above it by a fifth of a cycle, which is what makes the motion
    look like it is passing along the tail rather than the whole thing turning at once.
    """
    share = (index + 1) / len(TAIL)
    lag = index * (math.tau / 5.0)
    return math.sin(phase - lag) * share, math.sin(phase * 0.5 - lag) * share * 0.45


def read_tail(seq, frames):
    """The clip's own local tail tracks, as plain numbers so they survive a round trip through JSON."""
    lib = u.AnimationLibrary
    tracks = {}
    for bone in TAIL:
        keys = []
        for frame in range(frames):
            local = lib.get_bone_pose_for_frame(seq, bone, frame, False)
            rotation, translation, scale = local.rotation, local.translation, local.scale3d
            keys.append([[rotation.x, rotation.y, rotation.z, rotation.w],
                         [translation.x, translation.y, translation.z],
                         [scale.x, scale.y, scale.z]])
        tracks[bone] = keys
    return tracks


def moves(tracks):
    """How far the tail travels across the clip, in degrees, measured off its own first frame."""
    worst = 0.0
    for keys in tracks.values():
        first = u.Quat(*keys[0][0])
        for key in keys[1:]:
            delta = (u.Quat(*key[0]) * first.inversed()).normalized()
            worst = max(worst, abs(math.degrees(2.0 * math.acos(min(1.0, abs(delta.w))))))
    return worst


def baseline_for(name, seq, frames, store):
    """The untouched tail, recorded on the first run and reused by every run after it."""
    recorded = store.get(name)
    if recorded and len(next(iter(recorded.values()))) == frames:
        return recorded
    live = read_tail(seq, frames)
    travel = moves(live)
    if travel > STILL_DEGREES:
        raise RuntimeError(
            f'{name}: no recorded baseline and its tail already travels {travel:.2f} degrees, so a sway '
            f'was applied and the recording was lost. Rebuild the clips with AuthorHeroMocapRetarget.py '
            f'and run this again.')
    store[name] = live
    report['baseline_taken'].append(name)
    return live


def apply(name, degrees, store):
    path = f'{DIR}/{name}.{name}'
    seq = u.load_asset(path)
    if not seq:
        report['failures'].append(f'{name}: not found at {path}')
        return
    frames = u.AnimationLibrary.get_num_frames(seq)
    if frames < 2:
        report['failures'].append(f'{name}: {frames} frames')
        return
    controller = seq.get_editor_property('controller')
    if not controller:
        report['failures'].append(f'{name}: no data controller on the sequence')
        return
    base = baseline_for(name, seq, frames, store)
    # Take the bracket so the whole tail is one transaction and the asset is notified once at the end.
    # Reading is on AnimationLibrary; writing is only on the sequence's own data controller.
    controller.open_bracket('Tail sway', False)
    written = {}
    for index, bone in enumerate(TAIL):
        positions, rotations, scales = [], [], []
        peak = 0.0
        for frame, key in enumerate(base[bone]):
            # One whole cycle across the clip, so the last key meets the first and the loop holds.
            phase = math.tau * frame / float(frames)
            yaw, pitch = sway(index, phase)
            delta = u.Rotator(roll=0.0, pitch=pitch * degrees, yaw=yaw * degrees).quaternion()
            # Composed on the bone's own axes, and on the RECORDING rather than on the asset, so a clip
            # that does move its tail keeps that motion and a second run replaces the sway rather than
            # adding to it.
            rotations.append((u.Quat(*key[0]) * delta).normalized())
            positions.append(u.Vector(*key[1]))
            scales.append(u.Vector(*key[2]))
            peak = max(peak, abs(yaw * degrees))
        controller.add_bone_curve(bone, False)
        controller.set_bone_track_keys(bone, positions, rotations, scales, False)
        written[bone] = round(peak, 2)
    controller.close_bracket(False)
    u.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    report['clips'][name] = {'frames': frames, 'tip_degrees': degrees, 'per_bone_peak_yaw_degrees': written}


store = {}
if BASELINE.is_file():
    store = json.loads(BASELINE.read_text(encoding='utf-8'))
try:
    for clip, degrees in CLIPS.items():
        apply(clip, degrees, store)
except Exception:
    report['failures'].append('exception: ' + traceback.format_exc().strip().replace('\n', ' | ')[-1200:])
    # A run that dies part way leaves some clips written and others not; say which, so the next run is
    # not guessing. Re-running is safe: every clip is rebuilt from the recording, never accumulated.
    report['partial'] = sorted(report['clips'])
finally:
    if store:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(store), encoding='utf-8')
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    u.log(('TAIL_SWAY_OK ' if not report['failures'] else 'TAIL_SWAY_FAIL ') +
          json.dumps({'written': sorted(report['clips']), 'baseline_taken': report['baseline_taken'],
                      'failures': report['failures'][:2]}))
