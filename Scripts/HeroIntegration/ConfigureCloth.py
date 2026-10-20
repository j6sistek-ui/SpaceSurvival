"""Explicit, private-only low resolution Chaos cloth binding. Original Blender files are read-only."""
import json
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
assert '-SSApplyHeroCloth' in u.SystemLibrary.get_command_line().split(), 'Explicit local authoring flag required'
mesh = u.load_asset('/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/Cloth/SK_Cloth')
result = json.loads(u.SSPlayableHeroTools.configure_cloth(mesh, str(OUT / 'ClothPhysicalSource.json')))
(OUT / 'ChaosBinding.json').write_text(json.dumps(result, indent=2))
assert result['success'], result
for slot in mesh.materials:
    if str(slot.material_slot_name) != 'Cloth_Armor':
        u.MaterialEditingLibrary.set_base_material_usage(slot.material_interface, u.MaterialUsage.MATUSAGE_CLOTHING, True)
        u.MaterialEditingLibrary.recompile_material(slot.material_interface)
        assert u.EditorAssetLibrary.save_loaded_asset(slot.material_interface, False)
assert u.EditorAssetLibrary.save_loaded_asset(mesh, False)
print('HERO_CLOTH_BOUND', result, flush=True)
