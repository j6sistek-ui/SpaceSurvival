"""Stage-only visual corrections following real-RHI capture review."""
from pathlib import Path
import json, runpy, traceback
import unreal as u
WORK=Path(__file__).resolve().parent
api=runpy.run_path(str(WORK/'author_cryo_unreal.py'))
BASE=api['BASE']
report={'status':'FAILED','materials':[],'changed_actors':[]}
try:
    assert Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==(WORK/'CryoStage').resolve()
    world=u.EditorLoadingAndSavingUtils.load_map(BASE+'/Maps/L_CryoComparison')
    assert world
    author=api['Author'](u,{},'visual-refinement-v3',report)
    master=BASE+'/Materials/M_NiagaraColdMist'
    instance=BASE+'/Materials/MI_NiagaraColdMist'
    assert not u.EditorAssetLibrary.does_asset_exist(master)
    mat=author.material('M_NiagaraColdMist',translucent=True,unlit=True,two_sided=True)
    edit=u.MaterialEditingLibrary
    art=author.sample(mat,u.EditorAssetLibrary.load_asset(BASE+'/Textures/T_Cryo_Mist'),'Mist','mask')
    particle=author.node(mat,'MaterialExpressionParticleColor')
    p=author.node(mat,'MaterialExpressionWorldPosition')
    a=author.node(mat,'MaterialExpressionActorPositionWS')
    bound=author.custom(mat,'float3 q=P-A; float3 e=float3(57.0-abs(q.x),43.0-abs(q.y),125.0-abs(q.z-125.0)); return smoothstep(0.0,18.0,min(e.x,min(e.y,e.z)));',{'P':p,'A':a})
    opacity=author.multiply(mat,author.multiply(mat,art,particle,'A','A'),bound)
    author.prop(author.multiply(mat,opacity,0.6),'MP_OPACITY')
    author.prop(author.multiply(mat,author.color(mat,(0.23,0.52,0.67)),particle,b_output='RGB'),'MP_EMISSIVE_COLOR')
    author.compile(mat)
    author.metadata(mat,'BoundedNiagaraMaterial')
    mi=author.new_asset('MI_NiagaraColdMist',BASE+'/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew(),'NiagaraMaterialInstance')
    edit.set_material_instance_parent(mi,mat)
    edit.update_material_instance(mi)
    author.metadata(mi,'BoundedNiagaraMaterialInstance')
    system=u.EditorAssetLibrary.load_asset(BASE+'/FX/NS_CryoMist')
    renderers=[obj for obj in u.ObjectIterator(u.NiagaraSpriteRendererProperties) if obj.get_path_name().startswith(system.get_path_name()+':')]
    report['renderers']=[obj.get_path_name() for obj in renderers]
    # Includes this duplicate's versioned renderer templates; never touch the
    # source emitter package. All owned variants must use the bounded material.
    assert 1 <= len(renderers) <= 8, report['renderers']
    for obj in renderers:
        obj.set_editor_property('material',mi)
        obj.set_editor_property('sub_image_size',u.Vector2D(1,1))
        obj.set_editor_property('cutout_texture',None)
    for obj in (mat,mi,system):
        assert u.EditorAssetLibrary.save_loaded_asset(obj,False)
    report['used_materials']=[str(m.get_path_name()) for info in u.NiagaraFunctionLibrary.get_all_emitters(system) for m in info.get_editor_property('used_renderer_materials')]
    assert mi.get_path_name() in report['used_materials']
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        label=actor.get_actor_label()
        if isinstance(actor,u.StaticMeshActor):
            mesh=actor.get_component_by_class(u.StaticMeshComponent).get_editor_property('static_mesh')
            if mesh and mesh.get_path_name().startswith(BASE+'/Meshes/'):
                actor.set_actor_scale3d(u.Vector(1,1,1))
                report['changed_actors'].append(label)
        elif isinstance(actor,(u.CameraActor,u.RectLight,u.TextRenderActor,u.PlayerStart)):
            pos=actor.get_actor_location()
            rot=actor.get_actor_rotation()
            actor.set_actor_location_and_rotation(u.Vector(pos.x,-pos.y,pos.z),u.Rotator(pitch=rot.pitch,yaw=-rot.yaw,roll=rot.roll),False,False)
            report['changed_actors'].append(label)
        if isinstance(actor,u.RectLight):
            actor.get_component_by_class(u.RectLightComponent).set_intensity(100.0 if label.endswith('_Key') else 40.0)
        elif isinstance(actor,u.PointLight):
            actor.get_component_by_class(u.PointLightComponent).set_intensity(8.0)
    assert u.EditorLoadingAndSavingUtils.save_map(world,BASE+'/Maps/L_CryoComparison')
    report['status']='V3_TUNING_SAVED_PENDING_CAPTURE'
except Exception:
    report['error']=traceback.format_exc()
    u.log_error(report['error'])
finally:
    (WORK/'CryoNativeTuning.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.SystemLibrary.quit_editor()
