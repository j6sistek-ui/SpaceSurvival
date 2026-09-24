"""Activate the replacement only after native import and pose checks. Keeps Squirrel ID."""
import os
import unreal as u,json,shutil
from pathlib import Path
B='/Game/SpaceSurvival/Licensed/HeroReplacement/Final/';OUT=Path(os.environ['SS_HERO_SOURCE']);L=u.EditorAssetLibrary
assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
assert hasattr(u.SSHeroDefinition(), 'tail_root_bone'), 'Build the replacement-hero runtime module before activation'
m=u.load_asset(B+'SK_SquirrelHeroReplacement');ref=u.AnimPoseExtensions.get_reference_pose(m.skeleton);assert len(u.AnimPoseExtensions.get_bone_names(ref))==69
root=u.AnimPoseExtensions.get_bone_pose(ref,'root',u.AnimPoseSpaces.LOCAL);assert abs(root.scale3d.x-1)<.001
paths={'mesh_path':m.get_path_name()}
for field,name in [('walk_clip_path','Walk'),('idle_clip_path','Idle'),('jog_clip_path','Jog'),('run_clip_path','Run'),('pilot_clip_path','Pilot'),('jump_start_clip_path','JumpStart'),('jump_air_clip_path','JumpAir'),('jump_land_clip_path','JumpLand')]:
 a=u.load_asset(B+'A_'+name);assert a and a.sequence_length>0 and a.get_editor_property('skeleton')==m.skeleton;paths[field]=a.get_path_name()
da=u.load_asset('/Game/SpaceSurvival/Data/DA_Phase1');rows=da.heroes;idx=[i for i,h in enumerate(rows) if str(h.id)=='Squirrel'][0];h=rows[idx]
backup=OUT/'DA_Phase1.before_replacement.uasset'
if not backup.exists():shutil.copy2(Path(u.Paths.project_content_dir())/'SpaceSurvival/Data/DA_Phase1.uasset',backup)
if not (OUT/'previous_hero_definition.txt').exists():(OUT/'previous_hero_definition.txt').write_text(h.export_text())
fit=json.loads((OUT/'fit_measurements.json').read_text())
values={**paths,'idle_fidget_clip_paths':[],'idle_fidget_seconds':0.,'fit_height':135.,'mesh_yaw':-90.,'sole_offset':0.,'mesh_scale':1.5,'walk_handoff_seconds':0.,'root_bone':'root','pelvis_bone':'pelvis','left_foot_bone':'foot_l','right_foot_bone':'foot_r','left_hand_bone':'hand_l','right_hand_bone':'hand_r','tail_root_bone':'tail_01','pilot_mount_offset':u.Vector(*fit['pilot_mount'])}
for n in ['Walk','Jog','Run']:values[n.lower()+'_speed']=fit['gaits'][n]['median_contact_speed_cm_s']
for k,v in values.items():h.set_editor_property(k,v)
rows[idx]=h;da.set_editor_property('heroes',rows);assert L.save_loaded_asset(da,False)
(OUT/'activated_hero_definition.txt').write_text(h.export_text());print('ACTIVATED',h.id,h.mesh_path,h.tail_root_bone)

