"""Fresh private Joy blue materials and Cyborg-to-Joy retarget pilot; no map edits."""
import unreal as u
import hashlib
import json
import math
import traceback
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
OUT=REPO / '.agent/local/StationRefinement/CpuJoy121/JoyBlue114'
DEST='/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117'
JOY='/Game/SpaceSurvival/Licensed/StationAssets/JoyPurple'
CYB='/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Cyborg'
EDIT=u.EditorAssetLibrary
MAT=u.MaterialEditingLibrary
TOOLS=u.AssetToolsHelpers.get_asset_tools()
REPORT={'state':'IN_PROGRESS','created':[],'clips':[],'errors':[]}

def checkpoint(): (OUT/'Author117.json').write_text(json.dumps(REPORT,indent=2)+'\n')
def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def file_for(asset): return REPO/'Content'/(asset.removeprefix('/Game/').split('.')[0]+'.uasset')
def save(asset):
    assert EDIT.save_loaded_asset(asset,False),asset.get_path_name()
    path=asset.get_path_name()
    if path not in REPORT['created']: REPORT['created'].append(path)
    checkpoint()
def copy(source,target):
    assert not EDIT.does_asset_exist(target),target
    asset=EDIT.duplicate_asset(source,target)
    assert asset,target
    return asset

CHAINS={
 'Spine':(('spine_01','spine_03'),('CC_Base_Waist','CC_Base_Spine02')),
 'Neck':(('neck_01','neck_01'),('CC_Base_NeckTwist01','CC_Base_NeckTwist02')),
 'Head':(('head','head'),('CC_Base_Head','CC_Base_Head')),
}
for letter,side in [('L','l'),('R','r')]:
    CHAINS[letter+'Clavicle']=((f'clavicle_{side}',f'clavicle_{side}'),(f'CC_Base_{letter}_Clavicle',f'CC_Base_{letter}_Clavicle'))
    CHAINS[letter+'Arm']=((f'upperarm_{side}',f'hand_{side}'),(f'CC_Base_{letter}_Upperarm',f'CC_Base_{letter}_Hand'))
    CHAINS[letter+'Leg']=((f'thigh_{side}',f'foot_{side}'),(f'CC_Base_{letter}_Thigh',f'CC_Base_{letter}_Foot'))
    CHAINS[letter+'Toe']=((f'ball_{side}',f'ball_{side}'),(f'CC_Base_{letter}_ToeBase',f'CC_Base_{letter}_ToeBase'))
    for finger,cc in [('thumb','Thumb'),('index','Index'),('middle','Mid'),('ring','Ring'),('pinky','Pinky')]:
        CHAINS[letter+cc]=((f'{finger}_01_{side}',f'{finger}_03_{side}'),(f'CC_Base_{letter}_{cc}1',f'CC_Base_{letter}_{cc}3'))

def rig(name,mesh,side):
    asset=TOOLS.create_asset(name,DEST+'/Rig',u.IKRigDefinition,u.IKRigDefinitionFactory())
    assert asset
    ctl=u.IKRigController.get_controller(asset)
    assert ctl.set_skeletal_mesh(mesh)
    ctl.set_retarget_root('pelvis' if side==0 else 'CC_Base_Hip')
    ctl.set_root_motion_bone('root' if side==0 else 'CC_Base_BoneRoot')
    for name,pair in CHAINS.items():
        assert str(ctl.add_retarget_chain(name,*pair[side],'None'))==name
    for letter in ('L','R'):
        name=letter+'FootGoal'
        foot=('foot_'+letter.lower()) if side==0 else ('CC_Base_'+letter+'_Foot')
        thigh=('thigh_'+letter.lower()) if side==0 else ('CC_Base_'+letter+'_Thigh')
        goal=ctl.add_new_goal(name,foot)
        solver=ctl.add_solver('/Script/IKRig.IKRigLimbSolver')
        ctl.set_start_bone(thigh,solver)
        ctl.connect_goal_to_solver(goal,solver)
        ctl.set_retarget_chain_goal(letter+'Leg',goal)
    save(asset)
    return asset

def main():
    assert not EDIT.does_directory_exist(DEST),'Fresh-create only. Inspect any partial result before repair.'
    original=json.loads((REPO/'.agent/local/StationRefinement/Lineup92/JoyFinal95.json').read_text())
    protected={str(file_for(r['asset'])):r['sha256'] for r in original['assets']}
    for path,expected in protected.items(): assert sha(Path(path))==expected,path
    inspection=json.loads((OUT/'NativeInspection116.json').read_text())
    for row in inspection['clips']: protected[str(file_for(row['asset']))]=sha(file_for(row['asset']))
    REPORT['protected']=protected
    checkpoint()
    mesh=copy(JOY+'/Mesh/SK_JoyPurple',DEST+'/Mesh/SK_JoyLightBlue')
    slots=list(mesh.materials)
    for i,slot in enumerate(slots):
        if str(slot.material_slot_name).startswith('Joy_Purple_Std_Skin_'):
            part=str(slot.material_slot_name).removeprefix('Joy_Purple_Std_Skin_')
            mat=copy(slot.material_interface.get_path_name(),DEST+'/Materials/MI_JoyBlue_Skin_'+part)
            MAT.set_material_instance_vector_parameter_value(mat,'Tint',u.LinearColor(.46,.66,.84,1.))
            assert MAT.get_material_instance_scalar_parameter_value(mat,'LuminanceTint')==1.
            save(mat)
            slot.set_editor_property('material_interface',mat)
            slots[i]=slot
    mesh.set_editor_property('materials',slots)
    save(mesh)
    hair=copy(JOY+'/Materials/MI_JoyHair_streak',DEST+'/Materials/MI_JoyBlue_HairStreak')
    MAT.set_material_instance_vector_parameter_value(hair,'Tint',u.LinearColor(.008,.009,.012,1.))
    save(hair)
    source=u.load_asset(CYB+'/Rig/SK_Cyborg')
    assert source and source.skeleton.get_path_name()==inspection['characters']['Cyborg']['skeleton']
    source_rig=rig('IK_CyborgSource',source,0)
    target_rig=rig('IK_Joy',mesh,1)
    retarget=TOOLS.create_asset('RTG_CyborgToJoy',DEST+'/Rig',u.IKRetargeter,u.IKRetargetFactory())
    ctl=u.IKRetargeterController.get_controller(retarget)
    S=u.RetargetSourceOrTarget.SOURCE; T=u.RetargetSourceOrTarget.TARGET
    ctl.set_ik_rig(S,source_rig);ctl.set_ik_rig(T,target_rig)
    ctl.set_preview_mesh(S,source);ctl.set_preview_mesh(T,mesh)
    ctl.add_default_ops()
    assert ctl.add_retarget_op('/Script/IKRig.IKRetargetIKChainsOp')>=0
    ctl.assign_ik_rig_to_all_ops(S,source_rig);ctl.assign_ik_rig_to_all_ops(T,target_rig)
    ctl.auto_map_chains(u.AutoMapChainType.EXACT,True)
    REPORT['mapping']={name:str(ctl.get_source_chain(name)) for name in CHAINS}
    assert all(name==source for name,source in REPORT['mapping'].items())
    pose=ctl.create_retarget_pose('JoyAlignedToCyborg',T)
    ctl.set_current_retarget_pose(pose,T)
    align=[pair[1][0] for pair in CHAINS.values()]
    ctl.auto_align_bones(align,u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN,T)
    for i in range(ctl.get_num_retarget_ops()):
        op=ctl.get_op_controller(i)
        if isinstance(op,u.IKRetargetFKChainsController):
            settings=op.get_settings();chains=settings.get_editor_property('chains_to_retarget')
            for j,chain in enumerate(chains):
                if str(chain.target_chain_name)!='Neck':
                    chain.set_editor_property('rotation_mode',u.FKChainRotationMode.ONE_TO_ONE)
                    chains[j]=chain
            settings.set_editor_property('chains_to_retarget',chains);op.set_settings(settings)
    save(retarget)
    selected=['A_Cyborg_Idle','A_Cyborg_PoleIdle','A_Cyborg_PoleSpin']
    registry=u.AssetRegistryHelpers.get_asset_registry()
    for name in selected:
        rows=[r for r in inspection['clips'] if r['asset'].split('.')[-1]==name]
        assert len(rows)==1,name
        row=rows[0];asset=registry.get_asset_by_object_path(row['asset'])
        inputs=u.IKRetargetBatchOperationInputs()
        for key,value in dict(assets_to_retarget=[asset],source_mesh=source,target_mesh=mesh,ik_retarget_asset=retarget,
            search='A_Cyborg_',replace='A_Joy_',target_path=DEST+'/Animations',use_source_path=False,
            include_referenced_assets=False,overwrite_existing_files=False).items(): inputs.set_editor_property(key,value)
        made=u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        path=DEST+'/Animations/'+name.replace('A_Cyborg_','A_Joy_')
        anim=u.load_asset(path)
        assert isinstance(anim,u.AnimSequence),(path,[str(x.package_name) for x in made])
        assert anim.get_editor_property('skeleton')==mesh.skeleton
        assert abs(anim.get_editor_property('sequence_length')-row['duration'])<.0001
        save(anim)
        frames=u.AnimationLibrary.get_num_frames(anim)
        options=u.AnimPoseEvaluationOptions()
        samples=[]
        for f in sorted(set([0,frames//4,frames//2,3*frames//4,frames])):
            p=u.AnimPoseExtensions.get_anim_pose_at_frame(anim,f,options)
            points={b:list(u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.WORLD).translation.to_tuple()) for b in ['CC_Base_Hip','CC_Base_Head','CC_Base_L_Hand','CC_Base_R_Hand','CC_Base_L_Foot','CC_Base_R_Foot']}
            assert all(math.isfinite(v) and abs(v)<10000 for xyz in points.values() for v in xyz)
            samples.append({'frame':f,'points':points})
        REPORT['clips'].append({'source':row['asset'],'target':path,'duration':row['duration'],'frames':frames,'samples':samples})
        checkpoint()
    for path,expected in protected.items(): assert sha(Path(path))==expected,path
    REPORT['state']='PILOT_ASSETS_SAVED_VISUAL_REVIEW_PENDING'
    REPORT['source_assets_preserved']=True
    REPORT['destination_hashes']={a:sha(file_for(a)) for a in REPORT['created']}
    checkpoint()
try:
    main()
except Exception:
    REPORT['errors'].append(traceback.format_exc());REPORT['state']='FAILED_RETAIN_PARTIAL_FOR_INSPECTION';checkpoint();raise
print('JOY117_RESULT',REPORT['state'],len(REPORT['clips']),'clips')
