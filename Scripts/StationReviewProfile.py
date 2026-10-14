"""Prepare private save copies and verify native paths before station Play reviews.

CLI preparation uses only the standard library; it never starts Unreal or restores
production saves. LaunchPlan.json supplies mandatory isolation arguments. Call
verify_before_play() in that offscreen editor before requesting PIE.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid
from datetime import datetime, timezone

MAP = '/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime'


def direct(path):
    """Reject links/junctions before resolving or using any save/profile path."""
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError('Redirected save/profile path: ' + str(part))
    return path


def roots(repo, local_app_data):
    return [direct(repo/'Saved/SaveGames'),
            direct(Path(local_app_data)/'SpaceSurvival/Saved/SaveGames')]


def snapshot(directories):
    manifests, payloads = [], []
    for directory in directories:
        direct(directory)
        rows, files = [], {}
        exists = directory.exists()
        if exists and not directory.is_dir():
            raise RuntimeError('Expected save directory: ' + str(directory))
        for path in sorted(directory.glob('*.sav')) if exists else []:
            direct(path)
            if not path.is_file():
                raise RuntimeError('Save entry is not a regular file: ' + str(path))
            data = path.read_bytes()
            files[path.name] = data
            rows.append({'name':path.name, 'bytes':len(data),
                         'sha256':hashlib.sha256(data).hexdigest()})
        manifests.append({'directory':str(directory), 'exists':exists, 'files':rows})
        payloads.append(files)
    return manifests, payloads


def write_new(path, data):
    direct(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
    if path.read_bytes() != data:
        raise RuntimeError('Backup readback differs: ' + str(path))


def json_new(path, value):
    write_new(path, (json.dumps(value, indent=2)+'\n').encode())


def prepare(repo, local_app_data, editor=None, layout=None):
    repo = direct(repo)
    if not (repo/'SpaceSurvival.uproject').is_file():
        raise RuntimeError('Select the SpaceSurvival checkout')
    directories = roots(repo, local_app_data)
    before, payloads = snapshot(directories)
    token = uuid.uuid4().hex
    run = direct(repo/'.agent/local/StationReview'/token)
    run.mkdir(parents=True, exist_ok=False)
    write_new(run/'.ss-station-review', token.encode())
    for i, files in enumerate(payloads):
        for name, data in files.items():
            write_new(run/'Backups'/str(i)/name, data)
    # Seed only the editor project's saves; preserve the other profile separately.
    user = run/'User'
    (user/'Saved/SaveGames').mkdir(parents=True, exist_ok=False)
    for name, data in payloads[0].items():
        write_new(user/'Saved/SaveGames'/name, data)
    after, _ = snapshot(directories)
    record = {'utc':datetime.now(timezone.utc).isoformat(), 'token':token,
              'repo':str(repo), 'user':str(user), 'production':before,
              'production_unchanged':before == after,
              'backup_file_count':sum(len(p) for p in payloads),
              'native_verified':False, 'process_launched':False}
    json_new(run/'Preparation.json', record)
    if before != after:
        raise RuntimeError('Production saves changed during backup; retain failed snapshot, do not launch')
    if editor or layout:
        if not editor or not layout:
            raise RuntimeError('Launch planning requires both executable and verified offscreen layout')
        editor, layout = direct(editor), direct(layout)
        if not editor.is_file() or not layout.is_file():
            raise RuntimeError('Editor/layout missing; no launch plan')
        write_new(run/'EditorLayout.offscreen.ini', layout.read_bytes())
        args = [str(repo/'SpaceSurvival.uproject'), MAP, '-RenderOffscreen',
                '-unattended', '-NoSound', '-NoSplash', '-NoLiveCoding',
                '-SaveToUserDir', '-UserDir='+user.as_posix(),
                '-SSStationReviewRoot='+run.as_posix(),
                '-EditorLayoutIni='+(run/'EditorLayout.offscreen.ini').as_posix(),
                '-abslog='+(run/'Editor.log').as_posix()]
        json_new(run/'LaunchPlan.json', {'executable':str(editor), 'arguments':args,
                 'working_directory':str(repo), 'required_before_launch':
                 'Owner editor closed; inspect process/VRAM state; launch hidden. Verify native paths before Play.'})
    return run


def argument(command, name):
    matches = re.findall(r'(?:^|\s)-'+re.escape(name)+r'=(?:"([^"]+)"|(\S+))', command, re.I)
    if len(matches) != 1:
        raise RuntimeError('One explicit '+name+' argument required')
    return next(value for value in matches[0] if value)


def verify_before_play():
    import unreal as u
    command = u.SystemLibrary.get_command_line()
    for flag in ('RenderOffscreen', 'SaveToUserDir'):
        if not re.search(r'(?:^|\s)-'+flag+r'(?:\s|$)', command, re.I):
            raise RuntimeError('Review requires -'+flag)
    repo = direct(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    run = direct(argument(command, 'SSStationReviewRoot'))
    if not re.fullmatch('[a-f0-9]{32}', run.name) or run.parent != repo/'.agent/local/StationReview':
        raise RuntimeError('Review root must be the exact checkout GUID profile')
    if (run/'.ss-station-review').read_text() != run.name:
        raise RuntimeError('Profile marker mismatch')
    record = json.loads((run/'Preparation.json').read_text())
    if record['token'] != run.name or direct(record['repo']) != repo or not record['production_unchanged']:
        raise RuntimeError('Preparation did not preserve production saves')
    user, saved = run/'User', run/'User/Saved'
    actual_user = direct(u.Paths.convert_relative_path_to_full(u.Paths.project_user_dir()))
    actual_saved = direct(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))
    if direct(argument(command, 'UserDir')) != user or actual_user != user or actual_saved != saved:
        raise RuntimeError('Resolved native save/profile paths are not isolated')
    direct(saved/'SaveGames')
    current, _ = snapshot([direct(p['directory']) for p in record['production']])
    if current != record['production']:
        raise RuntimeError('Production saves changed since preparation; inspect, do not restore')
    if u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Verify isolation before GameInstance/Play starts')
    receipt = {'pid':os.getpid(), 'utc':datetime.now(timezone.utc).isoformat(),
               'project_user_dir':str(actual_user), 'project_saved_dir':str(actual_saved),
               'production_unchanged':True, 'ready_for_play':True}
    json_new(run/('NativeBeforePlay-'+str(os.getpid())+'-'+uuid.uuid4().hex+'.json'), receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--editor', type=Path)
    parser.add_argument('--layout', type=Path)
    args = parser.parse_args()
    result = prepare(args.repo, os.environ['LOCALAPPDATA'], args.editor, args.layout)
    print(json.dumps({'profile':str(result), 'native_verified':False, 'process_launched':False}))
