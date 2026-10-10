"""Resume inspected Joy118 partial set; preserve animated clips and static poses."""
import unreal as u
import json
import hashlib
import math
import traceback
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
OUT=REPO / '.agent/local/StationRefinement/CpuJoy121/JoyBlue114'
DEST='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117'
JOY='/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple'
CYB='/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Cyborg'
report={'state':'IN_PROGRESS','clips':[],'bindings':[],'errors':[]}
def checkpoint(): (OUT/'Complete121.json').write_text(json.dumps(report,indent=2)+'\n')
def file_for(asset): return REPO/'Content'/(asset.removeprefix('/Game/').split('.')[0]+'.uasset')
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(asset):assert u.EditorAssetLibrary.save_loaded_asset(asset,False),asset.get_path_name()
def main():
    assert not (OUT/'Complete121.json').exists(),'Inspect prior receipt before resuming.'
    pilot=json.loads((OUT/'Author117.json').read_text()); assert not pilot['errors']
    partial=json.loads((OUT/'Complete118.json').read_text())
    assert partial['state']=='FAILED_RETAIN_PARTIAL_FOR_INSPECTION' and len(partial['clips'])==4
    assert 'A_Joy_LookL' in partial['errors'][0] and 'static at sampled frames' in partial['errors'][0]
    assert not file_for(DEST+'/Animations/A_Joy_LookL').exists(),'Failed LookL should not have been saved.'
    for path,expected in pilot['protected'].items(): assert sha(Path(path))==expected,path
    expected_assets={asset.split('.')[0]:digest for asset,digest in pilot['destination_hashes'].items()}
    expected_assets.update({r['target'].split('.')[0]:r['sha256'] for r in partial['clips']})
    for asset,expected in expected_assets.items(): assert sha(file_for(asset))==expected,asset
    source=u.load_asset(CYB+'/Rig/SK_Cyborg'); target=u.load_asset(DEST+'/Mesh/SK_JoyLightBlue')
    retarget=u.load_asset(DEST+'/Rig/RTG_CyborgToJoy');assert source and target and retarget
    rows=json.loads((OUT/'NativeInspection116.json').read_text())['clips']
    registry=u.AssetRegistryHelpers.get_asset_registry();edit=u.EditorAssetLibrary
    pilot_paths={r['target'] for r in pilot['clips']}|{r['target'] for r in partial['clips']}
    for row in rows:
        name=row['asset'].split('.')[-1].replace('A_Cyborg_','A_Joy_',1)
        path=DEST+'/Animations/'+name
        if path not in pilot_paths:
            assert not edit.does_asset_exist(path),path
            inputs=u.IKRetargetBatchOperationInputs()
            for key,value in dict(assets_to_retarget=[registry.get_asset_by_object_path(row['asset'])],source_mesh=source,
                target_mesh=target,ik_retarget_asset=retarget,search='A_Cyborg_',replace='A_Joy_',target_path=DEST+'/Animations',
                use_source_path=False,include_referenced_assets=False,overwrite_existing_files=False).items():inputs.set_editor_property(key,value)
            u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        anim=u.load_asset(path);assert isinstance(anim,u.AnimSequence),path
        assert anim.get_editor_property('skeleton')==target.skeleton
        assert abs(anim.get_editor_property('sequence_length')-row['duration'])<.0001,path
        assert anim.get_editor_property('enable_root_motion')==row['root_motion'],path
        frames=u.AnimationLibrary.get_num_frames(anim);assert frames>0
        options=u.AnimPoseEvaluationOptions();poses=[]
        for f in (0,frames//3,2*frames//3,frames):
            p=u.AnimPoseExtensions.get_anim_pose_at_frame(anim,f,options)
            coords=[]
            for bone in ('CC_Base_Hip','CC_Base_Head','CC_Base_L_Hand','CC_Base_R_Hand','CC_Base_L_Foot','CC_Base_R_Foot'):
                t=u.AnimPoseExtensions.get_bone_pose(p,bone,u.AnimPoseSpaces.WORLD)
                coords.extend(t.translation.to_tuple());coords.extend((t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w))
            assert all(math.isfinite(v) and abs(v)<10000 for v in coords),path
            poses.append(coords)
        motion=max(abs(a-b) for p in poses[1:] for a,b in zip(p,poses[0]))
        source_anim=u.load_asset(row['asset'])
        source_frames=u.AnimationLibrary.get_num_frames(source_anim)
        source_poses=[]
        for f in (0,source_frames//3,2*source_frames//3,source_frames):
            p=u.AnimPoseExtensions.get_anim_pose_at_frame(source_anim,f,options)
            coords=[]
            for bone in ('pelvis','head','hand_l','hand_r','foot_l','foot_r'):
                t=u.AnimPoseExtensions.get_bone_pose(p,bone,u.AnimPoseSpaces.WORLD)
                coords.extend(t.translation.to_tuple());coords.extend((t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w))
            source_poses.append(coords)
        source_motion=max(abs(a-b) for p in source_poses[1:] for a,b in zip(p,source_poses[0]))
        assert source_motion<=1e-6 or motion>1e-6,(path,'source animates but target is static')
        assert frames==source_frames,(path,frames,source_frames)
        if path not in pilot_paths:save(anim)
        report['clips'].append({'source':row['asset'],'target':path,'frames':frames,'duration':row['duration'],
                               'sampled_motion':motion,'source_sampled_motion':source_motion,
                               'motion_type':'static_source_pose' if source_motion<=1e-6 else 'animated',
                               'sha256':sha(file_for(path))})
        checkpoint()
        print('JOY121_CLIP',len(report['clips']),name,flush=True)
    for family in ('base','streak'):
        path=DEST+'/Hair/GB_Joy_'+family
        assert not edit.does_asset_exist(path)
        groom=u.load_asset(JOY+'/Hair/G_JoyHair_'+family+'_Rest');assert groom
        binding=u.GroomLibrary.create_new_groom_binding_asset_with_path(path,groom,target,100,None,0)
        assert isinstance(binding,u.GroomBindingAsset),path
        save(binding)
        report['bindings'].append({'family':family,'binding':binding.get_path_name(),'groom':groom.get_path_name()})
        checkpoint()
    path=DEST+'/BP_JoyLightBlue_Review';assert not edit.does_asset_exist(path)
    bp=edit.duplicate_asset(JOY+'/BP_JoyPurple_Review',path);assert bp
    sub=u.get_engine_subsystem(u.SubobjectDataSubsystem);api=u.SubobjectDataBlueprintFunctionLibrary
    handles=sub.k2_gather_subobject_data_for_blueprint(bp)
    comps={}
    for handle in handles:
        obj=api.get_object_for_blueprint(api.get_data(handle),bp)
        if obj:comps[obj.get_path_name()]=obj
    bodies=[x for x in comps.values() if isinstance(x,u.SkeletalMeshComponent)]
    assert len(bodies)==1
    body=bodies[0];body.set_skeletal_mesh_asset(target)
    body.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
    data=body.get_editor_property('animation_data')
    data.set_editor_property('anim_to_play',u.load_asset(DEST+'/Animations/A_Joy_Idle'))
    data.set_editor_property('saved_looping',True);data.set_editor_property('saved_playing',True)
    body.set_editor_property('animation_data',data)
    hairs=[x for x in comps.values() if isinstance(x,u.GroomComponent)];assert len(hairs)==2
    for hair in hairs:
        family='streak' if 'streak' in hair.get_name() else 'base'
        hair.set_binding_asset(u.load_asset(DEST+'/Hair/GB_Joy_'+family))
        if family=='streak':hair.set_material(0,u.load_asset(DEST+'/Materials/MI_JoyBlue_HairStreak'))
    edit.set_metadata_tag(bp,'ReviewOnly','Light-blue material and 135 Cyborg-derived clips. Native visual motion/groom/contact review pending; no permanent placement.')
    u.BlueprintEditorLibrary.compile_blueprint(bp);assert bp.generated_class()
    save(bp);report['blueprint']=bp.get_path_name()
    for path,expected in pilot['protected'].items():assert sha(Path(path))==expected,path
    report['source_assets_preserved']=True
    report['state']='ASSETS_SAVED_NATIVE_VISUAL_REVIEW_PENDING'
    report['native_packages']=[{'asset':a.package_name.__str__(),'sha256':sha(file_for(str(a.package_name)))} for a in registry.get_assets_by_path(DEST,True)]
    checkpoint()
try:main()
except Exception:
    report['errors'].append(traceback.format_exc());report['state']='FAILED_RETAIN_PARTIAL_FOR_INSPECTION';checkpoint();raise
print('JOY121_RESULT',report['state'],len(report['clips']),'clips')
