"""Import owned source and retarget three previews; lead owns execution and saves.

No level, existing skeleton, character placement, counter, or material changes.
Import reads all FBX takes into memory; only three requested source takes are
returned for saving along with the new source rig and retargeted preview assets.
"""
import hashlib
import json
import math
import re
from pathlib import Path

BASE = '/Game/OutpostSandbox/StationRefinement/BartenderCandidates20261006_V2'
TARGET = '/Game/SpaceSurvival/Licensed/AlienFemalePresentation/SK_AlienFemalePresentation'
SOURCE_SHA = '7e806df360623839aceeb54d170f3db2cab58b61d22824a1ddd60c13562e07d9'
TAKES = tuple('AA_Bar_Counter_Bartender_Type%02d' % i for i in (1, 2, 3))
CHAINS = {'Spine':('Bip01 Spine','Bip01 Spine3','spine_01','spine_03'),
          'Neck':('Bip01 Neck','Bip01 Neck','neck_01','neck_01'),
          'Head':('Bip01 Head','Bip01 Head','head','head')}
for side, word in (('l','L'),('r','R')):
    for role, first, last, tfirst, tlast in (
        ('Clavicle','Clavicle','Clavicle','clavicle','clavicle'),
        ('Arm','UpperArm','Hand','upperarm','hand'),
        ('Leg','Thigh','Toe0','thigh','ball')):
        CHAINS[role+word] = ('Bip01 '+word+' '+first,'Bip01 '+word+' '+last,tfirst+'_'+side,tlast+'_'+side)
    for index, finger in enumerate(('thumb','index','middle','ring','pinky')):
        CHAINS[finger.title()+word] = ('Bip01 '+word+' Finger'+str(index),
            'Bip01 '+word+' Finger'+str(index)+'2',finger+'_01_'+side,finger+'_03_'+side)

def _names(mesh,u):
    modifier=u.SkeletonModifier()
    assert modifier.set_skeletal_mesh(mesh)
    return list(map(str,modifier.get_all_bone_names()))

def _match(names,wanted):
    clean=lambda value:re.sub('[^a-z0-9]','',value.lower())
    matches=[name for name in names if clean(name).endswith(clean(wanted))]
    assert len(matches)==1,'Ambiguous/missing imported bone '+wanted+': '+repr(matches)
    return matches[0]

def _clip_probe(clip,u,presentation):
    api=u.AnimPoseExtensions
    options=u.AnimPoseEvaluationOptions()
    duration=clip.get_play_length()
    reference=api.get_reference_pose(clip.get_editor_property('skeleton'))
    ref={name:api.get_bone_pose(reference,name,u.AnimPoseSpaces.WORLD).translation
         for name in ('head','foot_l','foot_r')}
    reference_height=ref['head'].z-min(ref['foot_l'].z,ref['foot_r'].z)
    assert reference_height>1.,'Invalid native target reference height'
    samples=[]
    for index in range(13):
        seconds=duration*index/12.
        pose=api.get_anim_pose_at_time(clip,seconds,options)
        points={}
        for name in ('root','pelvis','head','hand_l','hand_r','foot_l','foot_r','ball_l','ball_r'):
            p=api.get_bone_pose(pose,name,u.AnimPoseSpaces.WORLD).translation
            points[name]=list(p.to_tuple())
        height=points['head'][2]-min(points['foot_l'][2],points['foot_r'][2])
        assert all(math.isfinite(v) for p in points.values() for v in p)
        ratio=height/reference_height
        assert .35<ratio<1.8,'Retarget body collapsed or wrong scale relative to actual reference pose'
        world={name:[p[0]*presentation['uniform_scale'],p[1]*presentation['uniform_scale'],
                     p[2]*presentation['uniform_scale']+presentation['sole_offset_cm']]
               for name,p in points.items()}
        samples.append({'seconds':seconds,'points':points,'head_above_feet_cm':height,
                        'reference_height_ratio':ratio,'at_gameplay_178cm_fit':world})
    return {'asset':clip.get_path_name(),'duration_seconds':duration,'samples':samples,
            'reference_head_above_feet_cm':reference_height,
            'working_hand_height_ranges_cm':{side:[min(s['at_gameplay_178cm_fit'][side][2] for s in samples),
                max(s['at_gameplay_178cm_fit'][side][2] for s in samples)] for side in ('hand_l','hand_r')},
            'limits':'Bone-space preview only; no rendered hand/prop/counter or loop-contact acceptance'}

def author(ctx,apply=False):
    import unreal as u
    root=Path(u.Paths.project_dir()).resolve()
    source=root/'User downloaded assets/VaultCache/FabLibrary/Bar_Counter_People-1622ca48/fbx/aa_bar_counter_people.fbx'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(source)==SOURCE_SHA
    report={'scope':'THREE_MOCAP_RETARGET_PREVIEWS_NO_MAP_OR_EXISTING_ASSET_EDITS',
            'apply':apply,'source':str(source),'source_sha256':SOURCE_SHA,'takes':TAKES,
            'target':TARGET,'destination':BASE,'dirty_assets':[]}
    if not apply:return report
    lib=u.EditorAssetLibrary
    assert not lib.does_directory_exist(BASE),'Preserve prior bartender candidate attempt'
    protected=list((root/'Content/SpaceSurvival/Licensed/AlienFemalePresentation').rglob('*.uasset'))
    protected+=list((root/'Content/TripoModels/AlienFemale').glob('*.uasset'))
    before={str(p.relative_to(root)):sha(p) for p in protected}
    target=ctx.asset(TARGET)
    assert isinstance(target,u.SkeletalMesh)
    target_names=_names(target,u)
    assert {'root','pelvis','head','hand_l','hand_r','ball_l','ball_r'}<=set(target_names)
    bounds=target.get_bounds()
    height=float(bounds.box_extent.z)*2.
    assert height>1.
    presentation={'native_mesh_origin_cm':list(bounds.origin.to_tuple()),
                  'native_mesh_extent_cm':list(bounds.box_extent.to_tuple()),'native_mesh_height_cm':height,
                  'fit_height_cm':178.,'uniform_scale':178./height,
                  'sole_offset_cm':-(float(bounds.origin.z)-float(bounds.box_extent.z))*178./height,
                  'basis':'Existing FSSHeroDefinition AlienFemale FitHeight178 and RenderedScale/ScaledSoleOffset'}
    report['target_presentation']=presentation
    options=u.FbxImportUI()
    for key,value in {'import_mesh':True,'import_as_skeletal':True,'import_animations':True,
        'import_materials':False,'import_textures':False,'create_physics_asset':False,
        'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,'override_full_name':True}.items():
        options.set_editor_property(key,value)
    for data_name in ('skeletal_mesh_import_data','anim_sequence_import_data'):
        data=options.get_editor_property(data_name)
        data.set_editor_property('import_uniform_scale',1.)
        data.set_editor_property('convert_scene',True)
        data.set_editor_property('force_front_x_axis',False)
    data=options.get_editor_property('anim_sequence_import_data')
    data.set_editor_property('use_default_sample_rate',True)
    data.set_editor_property('import_custom_attribute',False)
    data.set_editor_property('import_bone_tracks',True)
    task=u.AssetImportTask()
    for key,value in {'filename':str(source),'destination_path':BASE+'/Source','destination_name':'SK_BarCounterSource',
        'automated':True,'replace_existing':False,'save':False,'options':options,'factory':u.FbxFactory()}.items():
        task.set_editor_property(key,value)
    tools=u.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    registry=u.AssetRegistryHelpers.get_asset_registry()
    task_objects=list(task.get_objects())
    registry_objects=[data.get_asset() for data in registry.get_assets_by_path(BASE+'/Source',True,False)]
    unique={obj.get_path_name():obj for obj in task_objects+registry_objects if obj}
    imported=list(unique.values())
    meshes=[o for o in imported if isinstance(o,u.SkeletalMesh)]
    clips=[o for o in imported if isinstance(o,u.AnimSequence)]
    diagnostic={'task_imported_object_paths':list(task.get_editor_property('imported_object_paths')),
                'task_get_objects':[obj.get_path_name() for obj in task_objects if obj],
                'registry_objects':[{'asset':obj.get_path_name(),'class':obj.get_class().get_name()}
                                    for obj in registry_objects if obj],
                'mesh_count':len(meshes),'animation_count':len(clips),'source_sha256':SOURCE_SHA,
                'target_presentation':presentation}
    diagnostic_path=root/'.agent/local/StationRefinement/StationBartenderImportEnumeration2.json'
    with diagnostic_path.open('x',encoding='utf-8') as stream:json.dump(diagnostic,stream,indent=2)
    assert len(meshes)==1 and len(clips)==45,'Expected1mesh/45takes; exact native enumeration retained in '+str(diagnostic_path)
    expected_takes={f'AA_Bar_Counter_{role}_Type{i:02d}' for role,count in (('Bartender',10),('Customer',35))
                    for i in range(1,count+1)}
    actual_takes={name[name.index('AA_Bar_Counter_'):] for name in (c.get_name() for c in clips)
                  if 'AA_Bar_Counter_' in name}
    assert actual_takes==expected_takes,'Native45takes do not match the inspected45FBXstacks'
    report['import_enumeration']=diagnostic
    source_mesh=meshes[0]
    source_names=_names(source_mesh,u)
    selected={take:next((clip for clip in clips if clip.get_name().endswith(take)),None) for take in TAKES}
    assert all(selected.values()),'Imported source take names do not match the inspected FBX'
    dirty=[source_mesh,source_mesh.get_editor_property('skeleton'),*selected.values()]
    report['imported_in_memory']=[o.get_path_name() for o in imported if o]
    report['unsaved_unselected_take_count']=len(clips)-len(selected)
    report['source_bones']=source_names
    report['source_selected_durations']={k:v.get_play_length() for k,v in selected.items()}

    def rig(name,mesh,names,source_side):
        asset=tools.create_asset(name,BASE+'/Retarget',u.IKRigDefinition,u.IKRigDefinitionFactory())
        assert asset
        c=u.IKRigController.get_controller(asset)
        assert c.set_skeletal_mesh(mesh)
        assert c.set_retarget_root(_match(names,'Bip01 Pelvis') if source_side else 'pelvis')
        assert c.set_root_motion_bone(_match(names,'Bip01') if source_side else 'root')
        for chain,anchors in CHAINS.items():
            start,end=anchors[:2] if source_side else anchors[2:]
            if source_side:start,end=_match(names,start),_match(names,end)
            assert start in names and end in names,'Missing native chain '+chain
            assert str(c.add_retarget_chain(chain,start,end,'None'))==chain
        dirty.append(asset)
        return asset
    sr=rig('IK_BarCounterSource',source_mesh,source_names,True)
    tr=rig('IK_FemaleBartender',target,target_names,False)
    rt=tools.create_asset('RTG_BarCounterToFemale',BASE+'/Retarget',u.IKRetargeter,u.IKRetargetFactory())
    assert rt
    control=u.IKRetargeterController.get_controller(rt)
    source_side,target_side=u.RetargetSourceOrTarget.SOURCE,u.RetargetSourceOrTarget.TARGET
    for side,asset,mesh in ((source_side,sr,source_mesh),(target_side,tr,target)):
        control.set_ik_rig(side,asset);control.set_preview_mesh(side,mesh)
    control.add_default_ops()
    for side,asset in ((source_side,sr),(target_side,tr)):
        control.assign_ik_rig_to_all_ops(side,asset)
    control.auto_map_chains(u.AutoMapChainType.EXACT,True)
    pose=control.create_retarget_pose('FemaleBartenderAligned',target_side)
    assert str(pose)=='FemaleBartenderAligned' and control.set_current_retarget_pose(pose,target_side)
    control.auto_align_all_bones(target_side,u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    control.snap_bone_to_ground('ball_l',target_side)
    dirty.append(rt)
    registry=u.AssetRegistryHelpers.get_asset_registry()
    report['clips']=[]
    for take,clip in selected.items():
        data=registry.get_asset_by_object_path(clip.get_path_name())
        assert data.is_valid()
        name='A_FemaleBartender_'+take.rsplit('_',1)[1]
        inputs=u.IKRetargetBatchOperationInputs()
        for key,value in {'assets_to_retarget':[data],'source_mesh':source_mesh,'target_mesh':target,'ik_retarget_asset':rt,
            'search':clip.get_name(),'replace':name,'target_path':BASE+'/Preview','use_source_path':False,
            'include_referenced_assets':False,'overwrite_existing_files':False}.items():
            inputs.set_editor_property(key,value)
        made=u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        assert len(made)==1,'Retarget must produce only the requested preview'
        output=lib.load_asset(BASE+'/Preview/'+name)
        assert isinstance(output,u.AnimSequence) and output.get_editor_property('skeleton')==target.get_editor_property('skeleton')
        assert abs(output.get_play_length()-clip.get_play_length())<.04
        report['clips'].append(_clip_probe(output,u,presentation));dirty.append(output)
    after={str(p.relative_to(root)):sha(p) for p in protected}
    assert before==after and sha(source)==SOURCE_SHA
    report.update(dirty_assets=dirty,source_sha256_before=before,source_sha256_after=after,
                  target_originals_unchanged=True,map_changes=False,character_replaced=False,
                  note='Save only returned11assets;42unselected source takes remain unsaved. Original animations/rig unchanged.')
    return report
