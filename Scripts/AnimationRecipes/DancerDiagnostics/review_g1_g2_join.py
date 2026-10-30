"""Unsaved, velocity-matched G1-to-G2 join on the preserved Vexa mesh.

No source/animation writes. The current two passages are inputs, not proof
that their join is clear. Render opposing views and screen actual surfaces.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_g2_contact_recipe import geometry, skin, triangle_radii

P = Path(os.environ.get('SS_ANIMATION_PROJECT', str(Path.home()/'SpaceSurvival'))).resolve()
D = P/'SourceAssets/DanceRefinement_20261025'
R = P/'.agent/local/AnimationReview_20261025'
duration = 4.
arc = float(sys.argv[sys.argv.index('--arc')+1]) if '--arc' in sys.argv else 0.
output_name = sys.argv[sys.argv.index('--output')+1] if '--output' in sys.argv else ('G1G2Join' if arc == 0 else f'G1G2JoinArc{arc:g}')
assert Path(output_name).name == output_name
O = R/output_name
assert not O.exists(), 'Preserve earlier join evidence'
O.mkdir()
source = D/'Vexa_G1_ShoulderCap_Candidate.blend'
guards = {str(source): '51c25e242a481e7a98aee5281f11aa09094ecfbf0510272401f7868e87a8128e'}
manifests = [json.loads((D/f'{n}_PalmarGrip_Knots_Manifest.json').read_text()) for n in ('G1','G2')]
for m in manifests: guards[str(D/m['file'])] = m['sha256']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
s = bpy.context.scene
rig = next(o for o in s.objects if o.type=='ARMATURE')
ordered = sorted(rig.pose.bones, key=lambda b:len(b.parent_recursive))
names = [b.name for b in ordered]
assert len(names)==95
rest = {n:rig.matrix_world@rig.data.bones[n].matrix_local for n in names}
parents = {b.name:b.parent.name if b.parent else None for b in ordered}
relative = {n:rest[parents[n]].inverted()@rest[n] if parents[n] else rest[n] for n in names}
actions=[]
for m in manifests:
    with bpy.data.libraries.load(str(D/m['file']), link=False) as (_,loaded): loaded.actions=[m['action']]
    actions.append(loaded.actions[0])
for ob in s.objects:
    if ob.type=='MESH' and ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for k in ob.data.shape_keys.key_blocks:
            if k.name.startswith('REVIEW_'): k.value=0


def sample(which, seconds):
    action=actions[which]; rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    f=1+seconds*manifests[which]['fps'];s.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
    return {n:(rig.matrix_world@rig.pose.bones[n].matrix).copy() for n in names}


def localize(pose):
    return {n:pose[parents[n]].inverted()@pose[n] if parents[n] else pose[n].copy() for n in names}


def qpower(q, exponent):
    q=q.normalized()
    if q.w<0:q.negate()
    axis, angle=q.to_axis_angle()
    return Quaternion(axis, angle*exponent) if abs(angle)>1e-7 else Quaternion()


def slerp(a,b,t):
    b=b.copy()
    if a.dot(b)<0:b.negate()
    return a.slerp(b,t)


def bezier(qs,t):
    a,b,c=[slerp(qs[i],qs[i+1],t) for i in range(3)]
    return slerp(slerp(a,b,t),slerp(b,c,t),t)


def hermite(a,b,va,vb,t):
    return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*duration*va+(-2*t**3+3*t*t)*b+(t**3-t*t)*duration*vb


h=1/120
world=[sample(0,manifests[0]['seconds']-h),sample(0,manifests[0]['seconds']),sample(1,0),sample(1,h)]
local=[localize(p) for p in world]
controls={}
for n in names:
    qm,qa,qb,qp=[p[n].to_quaternion() for p in local]
    controls[n]=[qa,qa@qpower(qm.inverted()@qa,duration/(3*h)),qb@qpower(qb.inverted()@qp,-duration/(3*h)),qb]
pelvis_a,pelvis_b=world[1]['pelvis'].translation,world[2]['pelvis'].translation
velocity_a=(pelvis_a-world[0]['pelvis'].translation)/h
velocity_b=(world[3]['pelvis'].translation-pelvis_b)/h
outward=(pelvis_a+pelvis_b)*.5;outward.z=0
assert outward.length>.1
outward.normalize()


def pose_at(seconds):
    t=max(0,min(1,seconds/duration));pose={}
    for n in names:
        matrices=[p[n] for p in local]
        loc=hermite(matrices[1].translation,matrices[2].translation,(matrices[1].translation-matrices[0].translation)/h,(matrices[3].translation-matrices[2].translation)/h,t)
        q=bezier(controls[n],t)
        scale=matrices[1].to_scale().lerp(matrices[2].to_scale(),t)
        m=Matrix.LocRotScale(loc,q,scale)
        pose[n]=pose[parents[n]]@m if parents[n] else m
    center=hermite(pelvis_a,pelvis_b,velocity_a,velocity_b,t)+outward*(arc*math.sin(math.pi*t)**2)
    shift=Matrix.Translation(center-pose['pelvis'].translation)
    pose={n:shift@m for n,m in pose.items()}
    if '--forward-arm' in sys.argv:
        # The left hand is free throughout this bridge. Keep its elbow/hand
        # local pose, but prevent spherical interpolation drifting behind the
        # torso. The source endpoint poses remain exact.
        chest=pose['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted()
        forward=chest@Vector((0,-1,0))
        origin=pose['upperarm_l'].translation
        upper=(pose['lowerarm_l'].translation-origin).normalized()
        rear=math.degrees(math.asin(max(-1,min(1,-upper.dot(forward)))))
        if rear>0:
            phase=min(1,seconds/.2,max(0,(duration-seconds)/.2));phase=phase*phase*(3-2*phase)
            corrected=math.radians(rear-phase*rear*rear/(rear+1))
            plane=(upper-forward*upper.dot(forward)).normalized()
            target=plane*math.cos(corrected)-forward*math.sin(corrected)
            rotation=upper.rotation_difference(target).to_matrix().to_4x4()
            transform=Matrix.Translation(origin)@rotation@Matrix.Translation(-origin)
            for bone in ordered:
                if bone.name=='upperarm_l' or any(p.name=='upperarm_l' for p in bone.parent_recursive):
                    pose[bone.name]=transform@pose[bone.name]
    return pose


def apply(pose):
    rig.animation_data.action=None
    inv=rig.matrix_world.inverted();p={n:inv@m for n,m in pose.items()}
    for b in ordered:
        base=p[b.parent.name]@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if b.parent else b.bone.matrix_local
        b.matrix_basis=base.inverted()@p[b.name]
    bpy.context.view_layer.update()


if '--setup-only' not in sys.argv:
    meshes=geometry(type('Model',(),{'names':names,'scene':s})())
    inverses=np.array([rest[n].inverted() for n in names])
    rows=[];max_radius=0.
    for frame in range(121):
        seconds=frame/30;pose=pose_at(seconds);matrices=np.array([pose[n] for n in names])@inverses
        pole={};bv=[];bf=[];av=[];af=[]
        for mesh in meshes:
            name,_,faces,_,_,body,arms=mesh;pts=skin(matrices,mesh)
            max_radius=max(max_radius,float(np.linalg.norm(pts[:,:2],axis=1).max()))
            radii=triangle_radii(pts,faces);z=pts[faces,2]
            bad=(radii<.025-.00001)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
            if bad.any():pole[name]={'triangles':int(bad.sum()),'max_depth_mm':float((.025-radii[bad]).max()*1000)}
            if len(body):
                offset=len(bv);bv.extend(pts.tolist());bf.extend((body+offset).tolist())
            if len(arms):
                offset=len(av);av.extend(pts.tolist());af.extend((arms+offset).tolist())
        pairs=BVHTree.FromPolygons(bv,bf,all_triangles=True).overlap(BVHTree.FromPolygons(av,af,all_triangles=True))
        rows.append({'seconds':seconds,'pole':pole,'distal_arm_body_pairs':len(pairs)})
    endpoint_error=max(float(np.abs(np.array(pose_at(t)[n])-np.array(w[n])).max()) for t,w in [(0,world[1]),(duration,world[2])] for n in names)
    report={'sources':guards,'duration':duration,'arc_m':arc,'endpoint_matrix_error':endpoint_error,
            'source_end_pelvis_m':list(pelvis_a),'next_start_pelvis_m':list(pelvis_b),
            'end_velocity_mps':list(velocity_a),'start_velocity_mps':list(velocity_b),
            'pole_flags':sum(bool(r['pole']) for r in rows),'arm_body_flags':sum(bool(r['distal_arm_body_pairs']) for r in rows),
            'max_radius_m':max_radius,'rows':rows,'status':'Unsaved join control, not complete routine or anatomy acceptance.'}
    (O/'Control.json').write_text(json.dumps(report,indent=2))
    assert endpoint_error<.0001
    s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE'
    s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=False
    s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('GJoinWorld');s.world.color=(.035,.045,.055)
    s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
    pole=bpy.context.object;pole.color=(1,.12,0,1);s.display.shading.color_type='OBJECT'
    for ob in s.objects:
        if ob.type=='MESH' and ob!=pole:ob.color=(.55,.55,.55,1)
    bpy.ops.object.camera_add();camera=bpy.context.object;s.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=3.4
    for i in range(9):
        pose=pose_at(i*.5);apply(pose);center=pose['pelvis'].translation+Vector((0,0,.15))
        for view,direction in [('front',Vector((4,-6,2))),('back',Vector((-4,6,2)))]:
            camera.location=center+direction;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
            s.render.filepath=str(O/f'{i:02d}_{view}.png');bpy.ops.render.render(write_still=True)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
    print('G_JOIN_DONE',{k:v for k,v in report.items() if k not in ('rows','sources')},flush=True)
