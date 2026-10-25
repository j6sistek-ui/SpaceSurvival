"""Enable required sprite shader permutations on the owned cryo mist material."""
from pathlib import Path
import hashlib,json,traceback
import unreal as u
WORK=Path(__file__).resolve().parent
BASE='/Game/SpaceSurvival/CryoComparison'
report={'status':'FAILED','errors':[]}
try:
    assert Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==(WORK/'CryoStage').resolve()
    material=u.EditorAssetLibrary.load_asset(BASE+'/Materials/M_NiagaraColdMist')
    instance=u.EditorAssetLibrary.load_asset(BASE+'/Materials/MI_NiagaraColdMist')
    assert material and instance
    report['usage_before']=material.get_editor_property('used_with_niagara_sprites')
    u.MaterialEditingLibrary.set_material_usage(material,u.MaterialUsage.MATUSAGE_NIAGARA_SPRITES)
    u.MaterialEditingLibrary.recompile_material(material)
    u.MaterialEditingLibrary.update_material_instance(instance)
    assert material.get_editor_property('used_with_niagara_sprites')
    for asset in (material,instance):
        assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
    report['usage_after']=material.get_editor_property('used_with_niagara_sprites')
    report['status']='NIAGARA_SPRITE_USAGE_SAVED_PENDING_RUNTIME_RENDER'
except Exception:
    report['errors'].append(traceback.format_exc())
    u.log_error(report['errors'][-1])
finally:
    (WORK/'CryoNiagaraUsage.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
