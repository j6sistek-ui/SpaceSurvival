from pathlib import Path
import json
import unreal as u

OUT = Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
results = []
for name in ('sci-fi_squirrel_3d_model', 'space-suited_squirrel_3d_model'):
    mesh = u.load_asset('/Game/TripoModels/' + name + '/' + name)
    assert isinstance(mesh, u.SkeletalMesh), name
    task = u.AssetExportTask()
    options = u.FbxExportOption()
    options.set_editor_property('ascii', False)
    options.set_editor_property('level_of_detail', False)
    options.set_editor_property('bake_material_inputs', u.FbxMaterialBakeMode.DISABLED)
    task.object = mesh
    task.filename = str(OUT / (name + '.fbx'))
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    task.exporter = u.SkeletalMeshExporterFBX()
    task.options = options
    assert u.Exporter.run_asset_export_task(task), name
    row = {'name': name, 'mesh': mesh.get_path_name(), 'materials': []}
    for slot in mesh.get_editor_property('materials'):
        mat = slot.material_interface
        textures = []
        if isinstance(mat, u.MaterialInstanceConstant):
            textures = [v.parameter_value for v in mat.get_editor_property('texture_parameter_values') if v.parameter_value]
        elif isinstance(mat, u.Material):
            textures = list(u.MaterialEditingLibrary.get_used_textures(mat))
        for tex in textures:
            texture_task = u.AssetExportTask()
            texture_task.object = tex
            texture_task.filename = str(OUT / (tex.get_name() + '.tga'))
            texture_task.automated = True
            texture_task.prompt = False
            texture_task.replace_identical = True
            u.Exporter.run_asset_export_task(texture_task)
        row['materials'].append({'name': mat.get_name(), 'textures': [t.get_name() for t in textures]})
    results.append(row)
(OUT / 'exports.json').write_text(json.dumps(results, indent=2))
u.log('REPLACEMENT_HERO_EXPORT_OK')
