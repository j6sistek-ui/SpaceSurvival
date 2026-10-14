"""Repair only private Cyborg pole-clip copies from retained Blender bend-axis data.

Run in the canonical authoring Editor after its private mesh/skeleton preflight.
Default is read-only. Set APPLY=True explicitly for the six private derivatives.
Inputs are local/private under .agent/local/CyborgRepair_20261013/RiggedDelivery.
See docs/validation/2026-10-14-cyborg-arm-repair.md for limits and provenance.
"""
import unreal as u,json,hashlib,math
from pathlib import Path
APPLY=bool(globals().get('APPLY',False))
O=Path(u.Paths.project_dir())/'.agent/local/CyborgRepair_20261013/RiggedDelivery'
D='/Game/SpaceSurvival/Licensed/CyborgRefresh_20261014';L=u.EditorAssetLibrary;P=u.AnimPoseExtensions
data=json.loads((O/'ExistingAnimationPoses.json').read_text());corrections=json.loads((O/'ArmChecks/NativeFingerCorrections.json').read_text())
assert set(corrections)=={f'{finger}_{joint:02}_{side}' for finger in ('thumb','index','middle','ring','pinky') for joint in (1,2,3) for side in ('l','r')}
assert all(len(q)==4 and all(math.isfinite(v) for v in q) and abs(sum(v*v for v in q)-1)<.001 for q in corrections.values())
clips=[r for r in data['clips'] if r['name'].startswith('A_Cyborg_Pole')];assert len(clips)==6
assert all(r['path'].startswith('/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Cyborg/Role/A_Cyborg_Pole') for r in clips)
ref=P.get_reference_pose(u.load_asset(data['skeleton']));local={n:P.get_bone_pose(ref,n,u.AnimPoseSpaces.LOCAL) for n in corrections}
protected={r['path']:hashlib.sha256((Path(u.Paths.project_content_dir())/(r['path'].split('.')[0].removeprefix('/Game/')+'.uasset')).read_bytes()).hexdigest() for r in clips}
receipt={'apply':APPLY,'source_hashes':protected,'finger_bones':len(corrections),'clips':[]}
for row in clips:
    src=u.load_asset(row['path']);dest=D+'/Animations/'+row['name'];assert isinstance(src,u.AnimSequence)
    frames=u.AnimationLibrary.get_num_frames(src);num=u.AnimationLibrary.get_num_keys(src);assert num==frames+1,(frames,num)
    result={'source':row['path'],'destination':dest,'frames':frames,'duration':src.sequence_length}
    if APPLY:
        # Always derive keys from the preserved original, including partial-run recovery.
        dst=L.load_asset(dest) if L.does_asset_exist(dest) else L.duplicate_asset(row['path'].split('.')[0],dest);assert dst and dst!=src
        controller=dst.get_editor_property('controller');controller.open_bracket('Repair Cyborg pole finger bend axes',False)
        try:
            for bone,values in corrections.items():
                corr=u.Quat(*values);bind=local[bone].rotation
                keys=[u.AnimationLibrary.get_bone_pose_for_time(src,bone,i*src.sequence_length/frames,False) for i in range(num)]
                rots=[(bind*corr*(bind.inversed()*k.rotation)*corr.inversed()).normalized() for k in keys]
                assert controller.set_bone_track_keys(bone,[k.translation for k in keys],rots,[k.scale3d for k in keys],False)
        finally:controller.close_bracket(False)
        assert L.save_loaded_asset(dst,False)
        # Body, arm and wrist keys must stay unchanged: only finger rotations were edited.
        errors=[]
        for bone in ('root','pelvis','spine_03','upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r'):
            for i in range(0,num,max(1,frames//12)):
                t=i*src.sequence_length/frames;a=u.AnimationLibrary.get_bone_pose_for_time(src,bone,t,False);b=u.AnimationLibrary.get_bone_pose_for_time(dst,bone,t,False)
                dot=sum(getattr(a.rotation,k)*getattr(b.rotation,k) for k in 'xyzw')
                if (a.translation-b.translation).length()>.001 or abs(dot)<.999999:errors.append([bone,i])
        assert not errors,errors
        result['non_finger_samples_unchanged']=True
    receipt['clips'].append(result)
receipt['original_clips_unchanged']=all(hashlib.sha256((Path(u.Paths.project_content_dir())/(p.split('.')[0].removeprefix('/Game/')+'.uasset')).read_bytes()).hexdigest()==h for p,h in protected.items())
assert receipt['original_clips_unchanged']
(O/('PoleFingerRepair.json' if APPLY else 'PoleFingerDryRun.json')).write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
