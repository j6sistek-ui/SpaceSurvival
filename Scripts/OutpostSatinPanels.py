"""Private satin derivatives for the two explicitly selected clean panel meshes.

Native textures, colors, normal maps and all other properties stay inherited.
Only four roughness/metallic channels change on quiet ceiling/promenade actors.
"""
import hashlib
from pathlib import Path

TARGET='/Game/OutpostSandbox/L_AsteroidOutpost'
BASE='/Game/StarterBundle/ModularScifiProps/'
PRIVATE='/Game/OutpostSandbox/Materials/MI_SatinPanel_'
MESHES={'QuietCeiling/':BASE+'Meshes/SM_Ceiling_B.SM_Ceiling_B',
        'QuietPromenade/':BASE+'Meshes/SM_Floor_A.SM_Floor_A'}


def apply(api):
    u,edit,lib=api['u'],api['EDIT'],api['LIB']
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0]!=TARGET:
        raise RuntimeError('Satin panels require the saved private outpost')
    staged=[]
    for actor in api['EAS'].get_all_level_actors():
        prefix=next((p for p in MESHES if actor.get_actor_label().startswith(p)),None)
        if not prefix:continue
        if 'OutpostAuthored' not in map(str,actor.tags):
            raise RuntimeError('Unowned actor in quiet panel namespace')
        components=actor.get_components_by_class(u.StaticMeshComponent)
        if len(components)!=1 or components[0].static_mesh.get_path_name()!=MESHES[prefix]:
            raise RuntimeError('Unexpected quiet panel geometry')
        component=components[0]
        if component.get_num_materials()!=2:raise RuntimeError('Quiet panel slot count changed')
        for slot,record in enumerate(component.static_mesh.static_materials):
            source=record.material_interface
            if source.get_path_name() not in [BASE+'Materials/MI_Base_'+n+'.MI_Base_'+n for n in ('Light','Dark')]:
                raise RuntimeError('Unreviewed native panel finish')
            current=component.get_material(slot)
            allowed=(source.get_path_name(),PRIVATE+source.get_name()+'.'+('MI_SatinPanel_'+source.get_name()))
            if current.get_path_name() not in allowed:raise RuntimeError('Quiet panel has artist override')
            staged.append((component,slot,source))
    if not staged:raise RuntimeError('No authored quiet panels')
    replacements={};report=[]
    for _,_,source in staged:
        path=source.get_path_name()
        if path in replacements:continue
        filename=Path(api['ROOT'])/('Content/'+path.split('.')[0][len('/Game/'):]+'.uasset')
        before=hashlib.sha256(filename.read_bytes()).hexdigest()
        names={str(n) for n in edit.get_scalar_parameter_names(source)}
        parameters={}
        for channel in ('Red','Green','Blue','Other'):
            rough,metal='Roughness '+channel,'Metallic '+channel
            if rough not in names or metal not in names:raise RuntimeError('Native panel shader interface changed')
            parameters[rough]=.72
            parameters[metal]=min(.45,edit.get_material_instance_scalar_parameter_value(source,metal))
        name='MI_SatinPanel_'+source.get_name();dest='/Game/OutpostSandbox/Materials/'+name
        child=api['load'](dest) if lib.does_asset_exist(dest) else api['TOOLS'].create_asset(
            name,'/Game/OutpostSandbox/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        edit.set_material_instance_parent(child,source)
        overrides=child.get_editor_property('base_property_overrides')
        overrides.set_editor_property('override_two_sided',True)
        overrides.set_editor_property('two_sided',True)
        child.set_editor_property('base_property_overrides',overrides)
        for name,value in parameters.items():
            # UE5.8 returns false despite successful scalar writes; use readback.
            edit.set_material_instance_scalar_parameter_value(child,name,value)
            if abs(edit.get_material_instance_scalar_parameter_value(child,name)-value)>.00001:
                raise RuntimeError('Satin scalar readback failed: '+name)
        edit.update_material_instance(child)
        if not lib.save_loaded_asset(child):raise RuntimeError('Satin material save failed')
        if hashlib.sha256(filename.read_bytes()).hexdigest()!=before:raise RuntimeError('Native panel material changed')
        replacements[path]=child
        report.append({'source':path,'source_sha256':before,'private':dest,'parameters':parameters,'two_sided':True})
    for component,slot,source in staged:component.set_material(slot,replacements[source.get_path_name()])
    return {'assigned_slots':len(staged),'materials':report,'geometry_changed':False,
            'native_sources_unchanged':True,'appearance':'Pending native capture'}
