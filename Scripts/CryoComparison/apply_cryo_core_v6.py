"""Import four locally projected core/body derivatives into the isolated stage.

Original packages are retained. Only the comparison map may replace an existing
package. The native authoring entry point is dry-run by default.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import shutil
import traceback

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / 'outputs/Cryo_Comparison'
FIT = runpy.run_path(str(WORK / 'upgrade_cryo_fit_unreal.py'))
STAGE, BASE, MAP = (FIT[k] for k in ('STAGE', 'BASE', 'MAP'))
require, digest, hashes = (FIT[k] for k in ('require', 'digest', 'package_hashes'))
MANIFEST = OUT / 'assembly_polish_v6.json'
AUDIT = WORK / 'cryo-core-v6-audit.json'
BASELINE = WORK / 'CryoPolishV6Baseline.json'
MAP_FILE = 'Content\\SpaceSurvival\\CryoComparison\\Maps\\L_CryoComparison.umap'


def prepare():
    baseline = json.loads(BASELINE.read_text())
    require(baseline['status'] == 'V5_4_OWNER_AND_STAGE_MATCH', 'Unexpected pre-v6 baseline')
    require(hashes() == baseline['native_all'], 'Stage changed since exact pre-v6 baseline')
    prior_path = Path(baseline['manifest'])
    require(digest(prior_path) == baseline['manifest_sha256'], 'Prior assembly changed')
    previous, current = json.loads(prior_path.read_text()), json.loads(MANIFEST.read_text())
    audit = json.loads(AUDIT.read_text())
    require(not audit['errors'] and audit['protected_inputs_unchanged'], 'Core geometry audit failed')
    require(audit['manifest_sha256'] == digest(MANIFEST), 'Core audit describes another source assembly')
    require([m['id'] for m in current['models']] == list('ABCD'), 'All four required')
    require(current['shared'] == previous['shared'], 'Shared input changed')
    sources = deepcopy(json.loads(Path(baseline['previous_author']).read_text())['protected_source_files'])
    sources.update({str(p): {'sha256': digest(p)} for p in (MANIFEST, AUDIT, BASELINE)})
    changes = []
    for model, old in zip(current['models'], previous['models']):
        require(all(model[k] == old[k] for k in ('id', 'source', 'source_sha256', 'textures', 'height_cm')), 'Original source identity changed')
        require(len(model['components']) == len(old['components']) == 21, 'Unexpected component count')
        prior = {row['name']: row for row in old['components']}
        require(set(prior) == {row['name'] for row in model['components']}, 'Unexpected component set')
        changed = []
        for row in model['components']:
            path = Path(row['file']).resolve()
            require(path.is_relative_to(WORK.parent) and path.is_file(), 'Expected local derivative on D')
            old_row = prior[row['name']]
            require(row['role'] == old_row['role'], 'Component role changed')
            current_sha, old_sha = digest(path), digest(old_row['file'])
            sources[str(path)] = {'sha256': current_sha}
            if current_sha != old_sha:
                require(row['name'] == 'Body' and row['role'] == 'body', 'Change outside local core/body derivative')
                require(row['triangles'] == old_row['triangles'], 'Topology count changed')
                changed.append(row['name'])
                changes.append({'model_id': model['id'], 'name': 'Body', 'role': 'body',
                                'actor': model['id'] + '_Body', 'new_actor': False,
                                'file': str(path), 'source_sha256': current_sha, 'previous_source_sha256': old_sha,
                                'asset': BASE + '/Meshes/PolishV6/' + model['id'] + '/SM_' + model['id'] + '_Body_CoreV6'})
        require(changed == ['Body'], 'Exactly one body derivative per candidate required')
    require(all(digest(p) == info['sha256'] for p, info in sources.items()), 'Protected source changed')
    return baseline, current, audit, sources, changes


def main(apply=False):
    receipt = WORK / ('CryoCoreV6Apply.json' if apply else 'CryoCoreV6Plan.json')
    require(not receipt.exists(), 'Never overwrite a core import receipt')
    report = {'status': 'FAILED', 'apply': apply, 'utc': datetime.now(timezone.utc).isoformat(), 'errors': []}
    u, allowed = None, False
    try:
        baseline, manifest, audit, sources, changes = prepare()
        report.update(manifest=str(MANIFEST), manifest_sha256=digest(MANIFEST), baseline_sha256=digest(BASELINE),
                      geometry_audit=str(AUDIT), geometry_audit_sha256=digest(AUDIT),
                      protected_source_files=sources, changes=changes, native_before_hashes=baseline['native_all'])
        if not apply:
            report['status'] = 'DRY_RUN_READY_CORE_V6'
            return report
        import unreal as u
        require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == STAGE.resolve(), 'Isolated CryoStage only')
        allowed = True
        require(not u.EditorLevelLibrary.get_pie_worlds(False), 'Active PIE forbidden')
        world = u.EditorLoadingAndSavingUtils.load_map(MAP)
        require(world is not None, 'Comparison map load failed')
        subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
        actors = {a.get_actor_label(): a for a in subsystem.get_all_level_actors()}
        before = {label: FIT['actor_state'](u, actor) for label, actor in actors.items()}
        for change in changes:
            actor = actors.get(change['actor'])
            require(isinstance(actor, u.StaticMeshActor), 'Body actor missing')
            component = actor.get_component_by_class(u.StaticMeshComponent)
            mesh = component.get_editor_property('static_mesh')
            require(mesh and component.get_num_materials() == 1, 'Expected one original body material')
            require(u.EditorAssetLibrary.get_metadata_tag(mesh, 'CryoSourceSHA256') == change['previous_source_sha256'], 'Original native body provenance changed')
            require(not u.EditorAssetLibrary.does_asset_exist(change['asset']), 'New core derivative already exists')
        backup = WORK / ('pre_core_v6_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(exist_ok=False)
        shutil.copy2(STAGE / MAP_FILE, backup / 'L_CryoComparison.umap')
        require(digest(backup / 'L_CryoComparison.umap') == baseline['native_all'][MAP_FILE], 'Map recovery hash mismatch')
        report['map_backup'] = str(backup / 'L_CryoComparison.umap')
        created = []
        for change in changes:
            component = actors[change['actor']].get_component_by_class(u.StaticMeshComponent)
            change['previous_mesh'] = component.get_editor_property('static_mesh').get_path_name()
            change['material'] = component.get_material(0).get_path_name().split('.')[0]
            mesh = FIT['import_mesh'](u, change, component.get_material(0), report['manifest_sha256'])
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'CryoAuthoringVersion', 'CryoCoreV6')
            component.set_static_mesh(mesh)
            created.append(mesh)
        expected = deepcopy(before)
        for change in changes:
            expected[change['actor']]['mesh'] = change['asset'] + '.' + change['asset'].rsplit('/',1)[-1]
        after_actors = {a.get_actor_label(): FIT['actor_state'](u,a) for a in subsystem.get_all_level_actors()}
        require(after_actors == expected, 'Unexpected actor/material/light/effect change')
        for mesh in created:
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,False), 'New body mesh save failed')
        require(u.EditorLoadingAndSavingUtils.save_map(world,MAP), 'Comparison map save failed')
        after = hashes()
        changed = sorted(p for p,h in baseline['native_all'].items() if after.get(p) != h)
        added = sorted(set(after)-set(baseline['native_all']))
        expected_added = sorted('Content\\'+c['asset'][len('/Game/'):].replace('/','\\')+'.uasset' for c in changes)
        require(changed == [MAP_FILE] and added == expected_added, 'Unexpected native package changes')
        require(all(digest(p) == info['sha256'] for p,info in sources.items()), 'Source changed during import')
        report.update(status='CORE_V6_SAVED_PENDING_VISUAL_REVIEW', native_after_hashes=after,
                      added_packages=added, changed_existing_packages=changed,
                      original_native_packages_preserved_except_map=True,
                      unchanged_materials_lights_niagara_sequence=True)
        return report
    except Exception:
        report['errors'].append(traceback.format_exc())
        if u:
            u.log_error(report['errors'][-1])
        return report
    finally:
        receipt.write_text(json.dumps(report,indent=2)+'\n')
        print('CRYO_CORE_V6_RESULT '+json.dumps({'status':report['status'],'receipt':str(receipt)}),flush=True)
        if u and allowed:
            u.SystemLibrary.quit_editor()


if __name__ == '__main__':
    main(False)
