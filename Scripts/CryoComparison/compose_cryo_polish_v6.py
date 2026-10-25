"""Bind the exact geometry and idle-jet transitions without mutating native files."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy

WORK = Path(__file__).resolve().parent
API = runpy.run_path(str(WORK / 'upgrade_cryo_fit_unreal.py'))
require, digest, hashes = (API[k] for k in ('require', 'digest', 'package_hashes'))


def read(name):
    return json.loads((WORK / name).read_text(encoding='utf-8-sig'))


def normalized(mapping):
    return {key.replace('\\', '/'): value for key, value in mapping.items()}


def main():
    destination = WORK / 'CryoPolishV6Apply.json'
    require(not destination.exists(), 'Never overwrite v6 authored proof')
    baseline = read('CryoPolishV6Baseline.json')
    previous = read('CryoDisplayV5Apply.json')
    core = read('CryoCoreV6Apply.json')
    idle = read('CryoIdleJetV6Apply.json')
    plan = read('cryo-core-v6-plan.json')
    require(digest(baseline['previous_author']) == baseline['previous_author_sha256'], 'Prior author changed')
    require(core['status'] == 'CORE_V6_SAVED_PENDING_VISUAL_REVIEW' and not core['errors'], 'Core import failed')
    require(idle['status'] == 'IDLE_JETS_V6_SAVED_PENDING_RUNTIME_VISUAL_REVIEW' and not idle['errors'], 'Idle import failed')
    require(normalized(core['native_before_hashes']) == normalized(baseline['native_all']), 'Core does not follow exact baseline')
    require(normalized(core['native_after_hashes']) == normalized(idle['native_before_hashes']), 'Idle does not follow exact core stage')
    require(idle['previous_transition']['sha256'] == digest(WORK / 'CryoCoreV6Apply.json'), 'Idle core receipt binding differs')
    after = hashes()
    require(after == idle['native_after_hashes'], 'Stage changed after native authoring')
    require(digest(core['manifest']) == core['manifest_sha256'], 'Current source manifest changed')
    require(all(digest(p) == row['sha256'] for p, row in core['protected_source_files'].items()), 'Protected input changed')
    report = deepcopy(previous)
    report.update(status='POLISH_V6_SAVED_PENDING_VISUAL_REVIEW', revision='v6', errors=[],
                  utc=datetime.now(timezone.utc).isoformat(), baseline_sha256=digest(WORK / 'CryoPolishV6Baseline.json'),
                  manifest=core['manifest'], manifest_sha256=core['manifest_sha256'],
                  geometry_audit=core['geometry_audit'], geometry_audit_sha256=core['geometry_audit_sha256'],
                  native_before_hashes=baseline['native_all'], native_after_hashes=after,
                  protected_source_files=core['protected_source_files'],
                  original_native_body_packages_preserved=True, active_body_core_collars_changed=True,
                  core_plan=str(WORK / 'cryo-core-v6-plan.json'), core_plan_sha256=digest(WORK / 'cryo-core-v6-plan.json'),
                  core_centers_cm={}, idle_jets={'asset':idle['asset'],'recipe':idle['recipe'],'actors':idle['actors']})
    if 'unchanged_original_bodies' in report:
        report['unchanged_original_bodies'] = False
    current = {row['actor']: row for row in report['changes']}
    for change in core['changes']:
        current[change['actor']] = change
        report['role_bindings'].append({'actor':change['actor'], 'role':'body', 'material':change['material']})
        settings = plan[change['model_id']]
        center = list(settings['core_center_m'])
        center[1] -= settings['forward_offset_m']
        report['core_centers_cm'][change['model_id']] = [v*100 for v in center]
    report['changes'] = list(current.values())
    report['added_packages'] = sorted(set(after)-set(baseline['native_all']))
    report['changed_existing_packages'] = sorted(p for p,h in baseline['native_all'].items() if after.get(p)!=h)
    require(report['changed_existing_packages'] == ['Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap'], 'Unexpected existing package mutation')
    require(len(report['added_packages']) == 5, 'Expected only four body derivatives and one idle system')
    report['v6_transitions'] = [{'path':str(WORK/name), 'sha256':digest(WORK/name)} for name in ('CryoCoreV6Apply.json','CryoIdleJetV6Apply.json')]
    report['preserved_v5_author'] = {'path':baseline['previous_author'], 'sha256':baseline['previous_author_sha256']}
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'receipt':str(destination),'new_packages':len(report['added_packages']),'core_centers_cm':report['core_centers_cm']}))


if __name__ == '__main__':
    main()
