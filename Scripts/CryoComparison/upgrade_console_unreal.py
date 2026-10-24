"""Import only v3 raised glass/HUD console assemblies into this owned stage."""
from pathlib import Path
import json,runpy,traceback
import unreal as u
WORK=Path(__file__).resolve().parent
api=runpy.run_path(str(WORK/'author_cryo_unreal.py'))
BASE=api['BASE']
api['ROLES'].update({'console_backing','console_glass','console_frame'})
report={'status':'FAILED','meshes':[],'materials':[],'textures':[],'actors':[],'cameras':[],'replaced_actors':[]}
try:
    assert Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==(WORK/'CryoStage').resolve()
    manifest,sources,digest=api['prepare'](WORK.parent/'outputs/Cryo_Comparison/assembly_holo_consoles.json')
    world=u.EditorLoadingAndSavingUtils.load_map(BASE+'/Maps/L_CryoComparison')
    assert world
    author=api['Author'](u,manifest,digest,report)
    texture=author.import_texture('T_Cryo_ConsoleHolo',manifest['shared']['console'],'color')
    texture.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_SHARPEN4)
    backing=author.material('M_ConsoleBacking',unlit=True,two_sided=True)
    author.prop(author.color(backing,(.001,.003,.005)),'MP_EMISSIVE_COLOR')
    author.compile(backing)
    glass=author.material('M_ConsoleGlass',translucent=True,two_sided=True)
    author.prop(author.color(glass,(.05,.15,.2)),'MP_BASE_COLOR')
    fresnel=author.node(glass,'MaterialExpressionFresnel',exponent=4.0,base_reflect_fraction=0.0)
    opacity=author.node(glass,'MaterialExpressionAdd',const_b=.055)
    author.wire(author.multiply(glass,fresnel,.2),opacity,'A')
    author.prop(opacity,'MP_OPACITY')
    author.prop(author.scalar(glass,.09),'MP_ROUGHNESS')
    author.compile(glass)
    hud=author.material('M_ConsoleHUD',translucent=True,unlit=True,two_sided=True)
    uv=author.node(hud,'MaterialExpressionTextureCoordinate',coordinate_index=0)
    clock=author.node(hud,'MaterialExpressionTime')
    art=author.sample(hud,texture,'ConsoleHUD',uv=uv)
    scan=author.custom(hud,'float s=frac(Clock/5.5); float d=abs(UV.x-s); return 1.0+0.28*exp(-d*d*1400.0);',{'UV':uv,'Clock':clock})
    author.prop(author.multiply(hud,author.multiply(hud,art,scan,'RGB'),1.8),'MP_EMISSIVE_COLOR')
    author.prop(author.multiply(hud,art,.9,'A'),'MP_OPACITY')
    author.compile(hud)
    frame=author.material('M_ConsoleFrame',unlit=True)
    author.prop(author.color(frame,(.025,.22,.32)),'MP_EMISSIVE_COLOR')
    author.compile(frame)
    mats={'console':hud,'console_glass':glass,'console_backing':backing,'console_frame':frame}
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    old={a.get_actor_label():a for a in actors.get_all_level_actors()}
    expected={f'{mid}_Console_{i}' for mid in 'ABCD' for i in (1,2)}
    assert expected.issubset(old)
    for model,x in zip(manifest['models'],api['X_OFFSETS']):
        changed=[c for c in model['components'] if c['role'] in mats]
        assert len(changed)==8
        for component in changed:
            mesh=author.import_mesh(model,component,mats[component['role']])
            actor=author.actor(u.StaticMeshActor,model['id']+'_'+component['name'],(x,0,0),folder='CryoComparison/'+model['id'])
            comp=actor.get_component_by_class(u.StaticMeshComponent)
            comp.set_static_mesh(mesh)
            comp.set_collision_profile_name('NoCollision')
            comp.set_cast_shadow(False)
            if component['role'] in ('console','console_glass'):
                comp.set_editor_property('translucency_sort_priority',6 if component['role']=='console' else 5)
    # Retain original imported mesh packages as recovery; remove only the eight
    # superseded scene actors after the replacement assets have been built.
    for name in sorted(expected):
        actor=old[name]
        mesh=actor.get_component_by_class(u.StaticMeshComponent).get_editor_property('static_mesh')
        assert mesh.get_path_name().startswith(BASE+'/Meshes/')
        assert actors.destroy_actor(actor)
        report['replaced_actors'].append(name)
    detail=author.camera('DETAIL_D_Consoles',(540,370,150),(540,80,30),48)
    detail.get_component_by_class(u.CameraComponent).set_aspect_ratio(16/9)
    for asset in author.created:
        assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
    assert u.EditorLoadingAndSavingUtils.save_map(world,BASE+'/Maps/L_CryoComparison')
    report['source_files']=sources
    report['saved_assets']=[obj.get_path_name() for obj in author.created]
    report['status']='CONSOLE_GLASS_HUD_SAVED_PENDING_RENDER'
except Exception:
    report['error']=traceback.format_exc()
    u.log_error(report['error'])
finally:
    (WORK/'CryoConsoleUpgrade.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
