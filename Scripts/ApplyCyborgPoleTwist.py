"""Adopt only the six verified private Cyborg clips; hashes prevent replay."""
import unreal as u,json,hashlib,shutil,os
from pathlib import Path
APPLY=bool(globals().get('APPLY',False))
O=Path(os.environ.get('SS_CYBORG_TWIST_DATA',str(Path(u.Paths.project_dir())/'.agent/local/CyborgRepair_20261013/TwistRepair')))
D='/Game/SpaceSurvival/Licensed/CyborgRefresh_20261014'
assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
rows=json.loads((O/'CandidateTracks.json').read_text(encoding='utf-8'));audit=json.loads((O/'MotionAudit.json').read_text(encoding='utf-8'));play=json.loads((O/'Playback/Playback.json').read_text(encoding='utf-8'))
assert len(rows)==6 and len(audit)==6 and play['status']=='PLAYED' and len(play['clips'])==6
assert all(r['after_jumps_over_20']==0 and r['max_palm_delta_cm']<.001 and r['right_wrist_turn_deg']<60.1 for r in audit)
expected={'Pole'+n for n in ('Idle','HipCircle','BodyWave','BackSlide','Spin','Kick')};assert {r['name'] for r in rows}==expected
def disk(path):return Path(u.Paths.project_content_dir())/(path.removeprefix('/Game/')+('.umap' if path.endswith('/L_WayfarerRuntime') else '.uasset'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[D+'/Cyborg_Refreshed',D+'/Cyborg_Refreshed_Skeleton','/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew/Cyborg/Rig/SK_Cyborg','/Game/SpaceSurvival/Licensed/StationAssets/JoyLightBlue117/Mesh/SK_JoyLightBlue','/Game/SpaceSurvival/Licensed/WayfarerRuntime/L_WayfarerRuntime']
receipt={'apply':APPLY,'clips':[],'protected':{p:sha(disk(p)) for p in protected}}
preflight=[]
for row in rows:
    path=D+'/Animations/A_Cyborg_'+row['name'];assert row['source']==path
    assert sha(disk(path))==row['source_sha256'], 'Source changed or repair already adopted: '+path
    clip=u.load_asset(path);assert clip
    assert all(len(k)==u.AnimationLibrary.get_num_keys(clip) for k in row['tracks'].values())
    preflight.append((row,clip))
if APPLY:
    backup=O/'BeforeAdoption';backup.mkdir(exist_ok=False)
    for row,clip in preflight:
        shutil.copy2(disk(row['source']),backup/(row['name']+'.uasset'))
    (backup/'Manifest.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
for row,clip in preflight:
    if APPLY:
        ctl=clip.get_editor_property('controller');ctl.open_bracket('Repair custom Cyborg pole arm motion',False)
        try:
            for n,keys in row['tracks'].items():
                assert ctl.set_bone_track_keys(n,[u.Vector(*k['t']) for k in keys],[u.Quat(*k['q'][1:],k['q'][0]) for k in keys],[u.Vector(*k['s']) for k in keys],False)
        finally:ctl.close_bracket(False)
        assert u.EditorAssetLibrary.save_loaded_asset(clip,False)
    receipt['clips'].append({'name':row['name'],'path':row['source'],'before_sha256':row['source_sha256'],'after_sha256':sha(disk(row['source'])),'tracks':list(row['tracks'])})
assert all(sha(disk(p))==h for p,h in receipt['protected'].items())
(O/('Adopted.json' if APPLY else 'AdoptDry.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({'adopted':APPLY,'clips':len(receipt['clips']),'protected_unchanged':len(protected)}))
