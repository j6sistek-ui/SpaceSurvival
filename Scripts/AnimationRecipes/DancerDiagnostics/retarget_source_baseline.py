import os
from pathlib import Path
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Native FK retarget baseline. No fixed-hand IK, new orbit, smoothing or choreography."""
import unreal as u,json,traceback
from pathlib import Path
BASE='/Game/SpaceSurvival/Licensed/ZeroGSourceBaseline_20261025'
lib=u.EditorAssetLibrary;tools=u.AssetToolsHelpers.get_asset_tools()
report={'sources':[],'retargeted':[],'errors':[],'method':'Native aligned IK Retargeter, pelvis and FK only'}
def asset(name,cls,factory):
    return lib.load_asset(BASE+'/'+name) if lib.does_asset_exist(BASE+'/'+name) else tools.create_asset(name,BASE,cls,factory())
try:
    assert 'CharacterWorkbench' in u.Paths.get_project_file_path()
    registry=u.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True)
    clips=[];source=None
    for key in ('g1','g2','b1','b2'):
        task=u.AssetImportTask();task.filename=str(R/'SourceBaseline'/f'{key}_Source.fbx')
        task.destination_path=BASE+'/Source';task.destination_name=key+'_Source';task.automated=True;task.save=True;task.replace_existing=True
        opts=u.FbxImportUI();opts.automated_import_should_detect_type=False
        opts.import_as_skeletal=True;opts.import_mesh=True;opts.import_animations=True
        opts.import_materials=False;opts.import_textures=False;opts.create_physics_asset=False
        opts.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH
        opts.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False)
        opts.anim_sequence_import_data.set_editor_property('custom_sample_rate',60)
        opts.anim_sequence_import_data.set_editor_property('preserve_local_transform',True)
        if source:opts.skeleton=source.skeleton
        task.options=opts;tools.import_asset_tasks([task])
        loaded=[lib.load_asset(p) for p in task.imported_object_paths]
        mesh=next(a for a in loaded if isinstance(a,u.SkeletalMesh))
        anim=next(a for a in loaded if isinstance(a,u.AnimSequence))
        if source is None:source=mesh
        clips.append(anim);report['sources'].append({'key':key,'mesh':mesh.get_path_name(),'animation':anim.get_path_name(),'seconds':anim.sequence_length})
        print('BASELINE_SOURCE',key,flush=True)
    target=lib.load_asset('/Game/XANDRA/Characters/F3/Base/Models/SK_F3_FullCharacter_Quinn_Base');assert target
    source_chains={'Spine':('spine_JNT','spine2_JNT'),'Head':('neck_JNT','head_JNT')}
    target_chains={'Spine':('spine_01','spine_05'),'Head':('neck_01','head')}
    for side,label in [('l','Left'),('r','Right')]:
        for kind,src,tgt in [('Clavicle',('shoulder','shoulder'),('clavicle','clavicle')),
                             ('Arm',('arm','hand'),('upperarm','hand')),('Leg',('upleg','foot'),('thigh','foot')),
                             ('Toe',('toebase','toebase'),('ball','ball'))]:
            source_chains[label+kind]=tuple(side+'_'+n+'_JNT' for n in src)
            target_chains[label+kind]=tuple(n+'_'+side for n in tgt)
        for finger in ('Thumb','Index','Middle','Ring','Pinky'):
            source_chains[label+finger]=(side+'_hand'+finger+'1_JNT',side+'_hand'+finger+'3_JNT')
            target_chains[label+finger]=(finger.lower()+'_01_'+side,finger.lower()+'_03_'+side)
    rigs=[]
    for name,mesh,pelvis,chains in [('IK_Source',source,'hips_JNT',source_chains),('IK_F3',target,'pelvis',target_chains)]:
        rig=asset(name,u.IKRigDefinition,u.IKRigDefinitionFactory);ctrl=u.IKRigController.get_controller(rig)
        ctrl.set_skeletal_mesh(mesh);ctrl.set_retarget_root(pelvis)
        for old in ctrl.get_retarget_chains():ctrl.remove_retarget_chain(old.chain_name)
        for chain,(start,end) in chains.items():ctrl.add_retarget_chain(chain,start,end,'')
        lib.save_loaded_asset(rig);rigs.append(rig)
    rt=asset('RT_SourceToF3',u.IKRetargeter,u.IKRetargetFactory)
    ctrl=u.IKRetargeterController.get_controller(rt);source_side=u.RetargetSourceOrTarget.SOURCE;target_side=u.RetargetSourceOrTarget.TARGET
    ctrl.set_ik_rig(source_side,rigs[0]);ctrl.set_ik_rig(target_side,rigs[1]);ctrl.set_preview_mesh(target_side,target)
    ctrl.add_default_ops();ctrl.auto_map_chains(u.AutoMapChainType.EXACT,True)
    report['ops']=[]
    for i in range(ctrl.get_num_retarget_ops()):
        name=str(ctrl.get_op_name(i));enabled='Pelvis' in name or 'FK' in name
        ctrl.set_retarget_op_enabled(i,enabled);report['ops'].append({'name':name,'enabled':enabled})
    pose=ctrl.create_retarget_pose('SourceAligned',target_side);ctrl.set_current_retarget_pose(pose,target_side)
    ctrl.auto_align_all_bones(target_side,u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    report['mapping']={key:str(ctrl.get_source_chain(key)) for key in target_chains}
    assert all(report['mapping'][key]==key for key in target_chains),report['mapping']
    lib.save_loaded_asset(rt)
    inputs=u.IKRetargetBatchOperationInputs()
    inputs.assets_to_retarget=[lib.find_asset_data(a.get_path_name()) for a in clips]
    inputs.source_mesh=source;inputs.target_mesh=target;inputs.ik_retarget_asset=rt
    inputs.prefix='A_F3_Baseline_';inputs.target_path=BASE+'/Retargeted';inputs.include_referenced_assets=False;inputs.overwrite_existing_files=True
    out=u.IKRetargetBatchOperation.run_batch_retarget(inputs)
    assert len(out)==4,len(out)
    for data in out:
        a=data.get_asset();a.set_retarget_source_asset(target);a.update_retarget_source_asset_data();lib.save_loaded_asset(a)
        report['retargeted'].append(a.get_path_name())
    report['ok']=True
except Exception:report['errors'].append(traceback.format_exc())
(R/'NativeSourceBaseline.json').write_text(json.dumps(report,indent=2));print('BASELINE_RESULT',report,flush=True)
