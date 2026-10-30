"""Opposing continuous views across both saved G1/join/G2 boundaries.

Blender Workbench review, not the selected native normal path or gameplay.
Source actions retain their timing; only the separate bridge is new.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

project=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()
source=project/'SourceAssets/DanceRefinement_20261025'
review=project/'.agent/local/AnimationReview_20261025'
boundary_only='--boundary-only' in sys.argv
out=review/('G1G2JoinBoundary' if boundary_only else 'G1G2JoinMotion')
assert not out.exists(),'Preserve earlier motion evidence'
manifest=json.loads((source/'G1G2_Join_Manifest.json').read_text())
for name in ('Replay.json','Surface.json'):
    assert json.loads((review/'G1G2JoinForwardReplay'/name).read_text())['passed']
guards=dict(manifest['sources'])
guards[str(source/manifest['file'])]=manifest['sha256']
guards[str(source/manifest['morph_basis'])]=manifest['morph_basis_sha256']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
out.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(source/'Vexa_G1_ShoulderCap_Candidate.blend'),load_ui=False)
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
body=bpy.data.objects['Vexa_Continuous_Hands'];keys=body.data.shape_keys
g1_shape=keys.animation_data.action
for ob in scene.objects:
    if ob.type=='MESH' and ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in ob.data.shape_keys.key_blocks:
            if key.name.startswith('REVIEW_'):key.value=0
basis=np.load(source/manifest['morph_basis'])
base=np.array([tuple(v.co) for v in keys.key_blocks[0].data])
for name,delta in zip(manifest['new_morphs'],basis['deltas']):
    key=body.shape_key_add(name=name,from_mix=False);key.slider_min,key.slider_max=-10,10
    coordinates=base.copy();coordinates[basis['active']]+=delta
    key.data.foreach_set('co',coordinates.ravel())
with bpy.data.libraries.load(str(source/manifest['file']),link=False) as (_,loaded):loaded.actions=[manifest['action'],manifest['shape_action']]
join,join_shape=loaded.actions
clips=[];clip_manifests=[]
for short in ('G1','G2'):
    m=json.loads((source/f'{short}_PalmarGrip_Knots_Manifest.json').read_text());clip_manifests.append(m)
    assert hashlib.sha256((source/m['file']).read_bytes()).hexdigest()==m['sha256']
    with bpy.data.libraries.load(str(source/m['file']),link=False) as (_,loaded):loaded.actions=[m['action']]
    clips.append(loaded.actions[0])
keys.animation_data_create();previous_segment=None
def set_segment(segment,seconds):
    global previous_segment
    action=[clips[0],join,clips[1]][segment]
    shape=[g1_shape,join_shape,None][segment]
    if segment!=previous_segment:
        rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
        keys.animation_data.action=shape
        if shape:keys.animation_data.action_slot=shape.slots[0]
        for key in keys.key_blocks:
            if key.name.startswith('REVIEW_'):key.value=0
        previous_segment=segment
    frame=1+seconds*120;scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()

def seek(t):
    segment=0 if t<2 else 1 if t<6 else 2
    set_segment(segment,[clip_manifests[0]['seconds']-2+t,t-2,t-6][segment])

def snapshot():
    result={}
    for ob in scene.objects:
        if ob.type=='MESH' and not ob.hide_render:
            ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            data=np.empty(len(ev.data.vertices)*3);ev.data.vertices.foreach_get('co',data)
            result[ob.name]=(np.column_stack((data.reshape(-1,3),np.ones(len(ev.data.vertices))))@np.array(ob.matrix_world).T)[:,:3]
    bones={b.name:np.array((rig.matrix_world@b.matrix).translation) for b in rig.pose.bones}
    return result,bones

rows=[]
for label,a,b in [('G1 to join',(0,clip_manifests[0]['seconds']),(1,0)),('join to G2',(1,4),(2,0))]:
    set_segment(*a);surfaces1,bones1=snapshot();set_segment(*b);surfaces2,bones2=snapshot()
    surfaces={n:float(np.linalg.norm(surfaces1[n]-surfaces2[n],axis=1).max())*1000 for n in surfaces1}
    bone_error=max(float(np.linalg.norm(bones1[n]-bones2[n]))*1000 for n in bones1)
    rows.append({'join':label,'surface_error_mm':surfaces,'max_bone_error_mm':bone_error})
report={'rows':rows,'sources':guards,'passed':all(max(r['surface_error_mm'].values())<.3 and r['max_bone_error_mm']<.15 for r in rows),
        'scope':'Both exact boundary poses, actual evaluated visible meshes and95 bones; not native or continuous artistry.'}
(out/'Boundary.json').write_text(json.dumps(report,indent=2));assert report['passed'],report
if boundary_only:
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
    print('JOIN_BOUNDARIES',rows,flush=True)
    raise SystemExit(0)

scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='OBJECT'
scene.display.shading.show_cavity=False;scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('SavedJoinReview');scene.world.color=(.035,.045,.055)
scene.render.resolution_x=scene.render.resolution_y=800;scene.render.resolution_percentage=100
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
pole=bpy.context.object;pole.color=(1,.12,0,1)
for ob in scene.objects:
    if ob.type=='MESH' and ob!=pole:ob.color=(.55,.55,.55,1)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO'
camera.data.ortho_scale=3.5
center=Vector((.5,-.65,3.1))
for view,direction in [('front',Vector((4,-6,2))),('back',Vector((-4,6,2))),('side',Vector((6,4,1)))]:
    folder=out/view;folder.mkdir()
    camera.location=center+direction;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    for i in range(193):
        seek(i/24);scene.render.filepath=str(folder/f'{i:04d}.png');bpy.ops.render.render(write_still=True)
(out/'Motion.json').write_text(json.dumps({'sources':guards,'fps':24,'frames_per_view':193,'views':['front','back','side'],
    'join_start_seconds':2,'join_end_seconds':6,'scope':'Saved Blender Workbench motion; original normals, no native or owner acceptance.'},indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
print('JOIN_MOTION_DONE',flush=True)
