"""Author separate tail layers; body retargeting remains independent."""
import bpy, math, json
from pathlib import Path
from mathutils import Quaternion, Vector
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
rig=bpy.data.objects['Armature'];mesh=bpy.data.objects['SquirrelHero_Replacement'];scene=bpy.context.scene
rig.animation_data.action=None
for action in list(bpy.data.actions):
    if action.name.startswith('Tail_'):bpy.data.actions.remove(action)
for b in rig.pose.bones:b.rotation_quaternion=Quaternion();b.location=(0,0,0)
names=['tail_%02d'%i for i in range(1,8)]
def smoothcurve(points,t):
    if t<=points[0][0]:return points[0][1]
    for (a,x),(b,y) in zip(points,points[1:]):
        if t<=b:
            f=(t-a)/(b-a);f=f*f*(3-2*f);return x+(y-x)*f
    return points[-1][1]
def values(kind,t,i,duration):
    lag=i*.38;share=(i+1)/7
    if kind=='Idle':
        envelope=math.sin(math.pi*t/duration)**4
        return envelope*(.8+1.8*share)*math.sin(4*math.pi*t/duration-lag),envelope*.45*math.sin(2*math.pi*t/duration-lag)
    if kind in ('Walk','Run'):
        phase=2*math.pi*t/duration
        amp=2.4 if kind=='Walk' else 1.9
        return (amp*share)*math.sin(phase-lag),(.35+.9*share)*math.cos(phase*2-lag)+(1.0 if kind=='Run' else 0)
    if kind=='JumpAir':
        wave=math.sin(2*math.pi*t/duration-lag)-math.sin(-lag)
        return .4*share*wave,-1.2+.45*share*wave
    if kind=='JumpStart':
        pitch=smoothcurve([(0,0),(.1,2.2),(.3,-1.2)],max(0,t-i*.008*math.sin(math.pi*t/duration)))
        return .2*share*math.sin(math.pi*t/duration),pitch
    # Landing response: root leads, softer tip settles later; exact neutral endpoints.
    envelope=math.sin(math.pi*t/duration)**2
    return .4*share*envelope*math.sin(5*math.pi*t/duration-lag),smoothcurve([(0,-1.2),(.14,2.6),(.32,-1.6),(.53,.8),(.85,0)],max(0,t-i*.009))*(1-smoothcurve([(.70,0),(.85,1)],t))
report=[]
for kind,duration in [('Idle',12),('Walk',1.0),('Run',.6),('JumpStart',.3),('JumpAir',.8),('JumpLand',.85)]:
    action=bpy.data.actions.new('Tail_'+kind);action.use_fake_user=True;rig.animation_data.action=action
    frames=round(duration*30);scene.render.fps=30;scene.frame_start=1;scene.frame_end=frames+1
    for f in range(frames+1):
        t=f/frames*duration
        for i,name in enumerate(names):
            pb=rig.pose.bones[name];world=rig.matrix_world@pb.bone.matrix_local;inv=world.to_3x3().inverted()
            yaw,pitch=values(kind,t,i,duration)
            pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(inv@Vector((0,0,1)),math.radians(yaw))@Quaternion(inv@Vector((1,0,0)),math.radians(pitch));pb.keyframe_insert('rotation_quaternion',frame=f+1,group=name)
    scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(OUT/(action.name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z')
    report.append({'clip':action.name,'seconds':duration,'frames':frames+1,'body_motion':'reference pose; compose as an additive layer','loop':kind in ('Idle','Walk','Run','JumpAir')})
# Present the idle tail layer on a relaxed body for a Blender-only preview.
rig.animation_data.action=bpy.data.actions['Tail_Idle'];scene.frame_start=1;scene.frame_end=361;scene.frame_set(1)
for name,deg in [('upperarm_l',65),('upperarm_r',-65)]:
    pb=rig.pose.bones[name];axis=(rig.matrix_world@pb.bone.matrix_local).to_3x3().inverted()@Vector((0,1,0));pb.rotation_quaternion=Quaternion(axis,math.radians(deg))
rig.show_in_front=False
scene.camera.location=(1.5,-2,.9);scene.camera.rotation_euler=(Vector((0,0,.45))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SquirrelHero_Rigged.blend'))
(OUT/'tail_clips.json').write_text(json.dumps(report,indent=2))
print('TAIL_ANIMATION_EXPORT_OK')
