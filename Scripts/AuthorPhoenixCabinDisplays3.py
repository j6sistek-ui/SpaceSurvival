"""Create two local-UV cabin screens from the reviewed Operations artwork.

The lead owns native execution and saves. Only two new private materials are
created. The images are decorative briefing diagrams, not simulated ship stats.
No source texture, map, actor, exposure or save is modified.
"""
import hashlib
import json
import re
from pathlib import Path

PRIVATE = '/Game/SpaceSurvival/Licensed/PhoenixCabin'
TEXTURES = '/Game/OutpostSandbox/StationRefinement/OperationsDisplayReadability20261007/Textures/T_'
TARGETS = (('M_CabinNavigation', '01_Navigation'), ('M_CabinSystems', '02_SystemDiagnostics'))
ART_MANIFEST_SHA = '314f57730a2e2c469aa831aa3ff2b276a91b86b9e0f60a301905a0bc152934cc'
TEXTURE_SHA = {'01_Navigation': 'be6df21cbbdb33168ae12c798fba1b2ba3a83a718dd716f8f4fa12b0b8f4c414',
               '02_SystemDiagnostics': '1bd1eca69db63d1ae477e994d4ea007b97ac4e2cb3dd1b925f1bc7ea027276ee'}


def apply():
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    edit, assets = u.MaterialEditingLibrary, u.EditorAssetLibrary
    tools = u.AssetToolsHelpers.get_asset_tools()
    manifest = root / '.agent/local/StationRefinement/OperationsGraphics1/preview_v2/manifest.json'
    if sha(manifest) != ART_MANIFEST_SHA:
        raise RuntimeError('Approved cabin artwork manifest changed')
    art_rows = {row['name']: row for row in json.loads(manifest.read_text())['assets']}
    originals, created, diagrams = {}, [], []
    for name, artwork in TARGETS:
        package = TEXTURES + artwork
        file = root / ('Content/' + package[6:] + '.uasset')
        if not file.is_file() or assets.does_asset_exist(PRIVATE + '/' + name):
            raise RuntimeError('Require saved approved artwork and a new private cabin destination')
        originals[package] = sha(file)
        pixels = Path(art_rows[artwork]['file'])
        png = pixels.read_bytes()
        source_dimensions = [int.from_bytes(png[16:20], 'big'), int.from_bytes(png[20:24], 'big')]
        if originals[package] != TEXTURE_SHA[artwork] or sha(pixels) != art_rows[artwork]['sha256'] or \
                png[:8] != bytes((137, 80, 78, 71, 13, 10, 26, 10)) or source_dimensions != [2048, 1024]:
            raise RuntimeError('Approved saved texture or original 2048x1024 image changed')
        texture = assets.load_asset(package)
        if not isinstance(texture, u.Texture2D) or not texture.get_editor_property('never_stream'):
            raise RuntimeError('Require the reviewed resident 2048x1024 artwork')
        before_size = [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())]
        # Fresh load can precede async platform-data compilation. Finish it;
        # do not confuse a temporarily unavailable resource with changed art.
        u.AutomationLibrary.finish_loading_before_screenshot()
        observed_size = [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())]
        tag = str(assets.find_asset_data(texture.get_path_name()).get_tag_value('Dimensions'))
        tag_size = [int(n) for n in re.findall(r'\d+', tag)]
        readback = {'source_png': source_dimensions, 'registry_dimensions_tag': tag,
                    'before_resource_size': before_size, 'after_resource_size': observed_size}
        if observed_size != [2048, 1024] or tag_size[:2] != [2048, 1024]:
            raise RuntimeError('Reviewed cabin artwork dimension readback failed: ' + json.dumps(readback))
        material = tools.create_asset(name, PRIVATE, u.Material, u.MaterialFactoryNew())
        if not isinstance(material, u.Material):
            raise RuntimeError('Cannot create private cabin material')
        material.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
        material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
        material.set_editor_property('two_sided', False)
        uv = edit.create_material_expression(material, u.MaterialExpressionTextureCoordinate)
        uv.set_editor_property('coordinate_index', 0)
        art = edit.create_material_expression(material, u.MaterialExpressionTextureObjectParameter)
        art.set_editor_property('parameter_name', 'CabinDiagram')
        art.set_editor_property('texture', texture)
        art.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_COLOR)
        shader = edit.create_material_expression(material, u.MaterialExpressionCustom)
        shader.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT3)
        # The approved image is 2:1; keep its aspect inside the 80x48 cm pane.
        # UV projection follows the mesh when the ship moves. Letterbox margins
        # read as inset display glass instead of stretching the illustration.
        shader.set_editor_property('code', '''
float2 p=float2(UV.x,(UV.y-0.0833333333)/0.8333333333);
if(p.y<0 || p.y>1) return float3(0.003,0.009,0.016);
float3 art=Texture2DSample(CabinDiagram,CabinDiagramSampler,p).rgb;
return art*2.0;
''')
        inputs = []
        for input_name in ('UV', 'CabinDiagram'):
            input_value = u.CustomInput()
            input_value.set_editor_property('input_name', input_name)
            inputs.append(input_value)
        shader.set_editor_property('inputs', inputs)
        if not edit.connect_material_expressions(uv, '', shader, 'UV') or not edit.connect_material_expressions(art, '', shader, 'CabinDiagram'):
            raise RuntimeError('Cabin diagram local-UV connection failed')
        if not edit.connect_material_property(shader, '', u.MaterialProperty.MP_EMISSIVE_COLOR):
            raise RuntimeError('Cabin diagram emissive connection failed')
        edit.layout_material_expressions(material)
        compile_errors = edit.recompile_material(material)
        if compile_errors:
            raise RuntimeError('Private cabin display material failed compilation: ' + str(compile_errors))
        created.append(material)
        diagrams.append({'material': material.get_path_name(), 'source_texture': package,
                         'source_sha256': originals[package], 'uv_channel': 0,
                         'gain': 2., 'pane_cm': [80., 48.], 'image_aspect': 2.,
                         'dimension_readback': readback,
                         'native_compile_errors': list(compile_errors),
                         'decorative_briefing_only': True})
    # Source hashes are rechecked before any asset is persisted.
    if any(sha(root / ('Content/' + p[6:] + '.uasset')) != h for p, h in originals.items()):
        raise RuntimeError('Cabin authoring changed a source texture')
    return {'scope': 'TWO_PRIVATE_LOCAL_UV_PHOENIX_CABIN_DISPLAYS',
            'source_sha256': originals, 'diagrams': diagrams,
            'dirty_assets': created, 'new_light_assets': 0,
            'maps_or_actor_changes': False,
            'limits': 'Native cockpit walk captures still must establish orientation, visibility and room fit.'}
