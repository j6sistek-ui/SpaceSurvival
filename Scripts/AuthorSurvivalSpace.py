"""Private deep-space sky for the October6 survival pass. No map/vendor writes.

Retains the owned fixed stars, restrains nebula exposure independently, and adds
a distant textured world in the sky direction (no collision or global atmosphere).
Back up every existing private output before changing it.
"""
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
BASE = '/Game/SpaceSurvival/Licensed/Atmosphere'
LIB = u.EditorAssetLibrary
EDIT = u.MaterialEditingLibrary


def main():
    out = ROOT / 'Artifacts/SurvivalQuality/Sky' / uuid.uuid4().hex
    out.mkdir(parents=True)
    names = ('DA_DeepSpaceLook', 'M_SurvivalSpaceSky')
    before = {}
    for name in names:
        p = ROOT / 'Content/SpaceSurvival/Licensed/Atmosphere' / (name + '.uasset')
        if p.exists():
            before[name] = hashlib.sha256(p.read_bytes()).hexdigest()
            shutil.copy2(p, out / p.name)
    look = u.load_asset(BASE + '/DA_DeepSpaceLook')
    path = BASE + '/M_SurvivalSpaceSky'
    material = LIB.load_asset(path) if LIB.does_asset_exist(path) else LIB.duplicate_asset(BASE + '/M_RegionSky', path)
    assert look and material
    expressions = EDIT.get_material_expressions(material)
    for expression in expressions:
        if isinstance(expression, u.MaterialExpressionScalarParameter):
            name = str(expression.get_editor_property('parameter_name'))
            if name == 'SkyBrightness':
                expression.set_editor_property('default_value', .024)
            elif name == 'StarBrightness':
                expression.set_editor_property('default_value', 1.15)
    grade = next((n for n in expressions if isinstance(n, u.MaterialExpressionCustom)
                  and n.get_editor_property('description') == 'Survival distant world'), None)
    if grade is None:
        original = EDIT.get_material_property_input_node(material, u.MaterialProperty.MP_EMISSIVE_COLOR)
        grade = EDIT.create_material_expression(material, u.MaterialExpressionCustom, 1800, 0)
        grade.set_editor_property('description', 'Survival distant world')
        grade.set_editor_property('output_type', u.CustomMaterialOutputType.CMOT_FLOAT3)
        inputs = []
        for name in ('Sky', 'View', 'Surface'):
            pin = u.CustomInput()
            pin.set_editor_property('input_name', name)
            inputs.append(pin)
        grade.set_editor_property('inputs', inputs)
        view = EDIT.create_material_expression(material, u.MaterialExpressionCameraVectorWS, 1600, 180)
        surface = EDIT.create_material_expression(material, u.MaterialExpressionTextureObject, 1600, 350)
        surface.set_editor_property('texture', u.load_asset('/Game/Planet_Project/Assets/Textures/Moon/T_8k_moon'))
        assert EDIT.connect_material_expressions(original, '', grade, 'Sky')
        assert EDIT.connect_material_expressions(view, '', grade, 'View')
        assert EDIT.connect_material_expressions(surface, '', grade, 'Surface')
    grade.set_editor_property('code', '''
// Keep the owned stars, but remove their exaggerated green/magenta speckling.
// The distant celestial body below has its own independently lit color.
float luminance = dot(Sky,float3(.2126,.7152,.0722));
Sky = lerp(luminance.xxx,Sky,.12) * float3(.9,.95,1.0);
float3 d = normalize(-View);
float3 axis = normalize(float3(.85,.46,.25));
float3 right = normalize(cross(float3(0,0,1),axis));
float3 up = cross(axis,right);
float z = dot(d,axis);
float2 p = float2(dot(d,right),dot(d,up)) / max(z,.001) / .13;
float r2 = dot(p,p);
if (z <= 0 || r2 >= 1) return Sky;
float3 n = float3(p,sqrt(saturate(1-r2)));
float2 uv = float2(atan2(n.x,n.z)/6.2831853+.5,acos(clamp(n.y,-1,1))/3.14159265);
float3 tex = Texture2DSample(Surface,SurfaceSampler,uv).rgb;
float sunlight = pow(saturate(dot(n,normalize(float3(-.75,.2,.55)))),1.1);
float rim = pow(1-n.z,5) * sunlight;
float3 planet = tex * float3(.22,.43,.62) * (.015+sunlight*1.5) + rim*float3(.02,.12,.26);
float edge = 1-smoothstep(.987,1,r2);
return lerp(Sky,planet,edge);
''')
    assert EDIT.connect_material_property(grade, '', u.MaterialProperty.MP_EMISSIVE_COLOR)
    EDIT.recompile_material(material)
    assert LIB.save_loaded_asset(material, False)
    look.set_editor_property('sky_material', material)
    assert LIB.save_loaded_asset(look, False)
    report = {'status': 'AUTHORED_REQUIRES_RENDER', 'before': before, 'sky': path,
              'sky_brightness': .024, 'star_brightness': 1.15, 'star_saturation': .12,
              'vendor_or_map_writes': False,
              'planet': 'Fixed distant textured celestial backdrop; non-gameplay sky geometry'}
    (out/'report.json').write_text(json.dumps(report, indent=2))
    u.log('SURVIVAL_SPACE_AUTHORED ' + str(out))


if __name__ == '__main__':
    main()
