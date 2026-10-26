"""Save a guarded palmar-grip action, or verify its fresh half-frame replay.

This is a private candidate, not production adoption. The saved action requires
the preserved posterior-hip mesh, waist patch and muted REVIEW_G2_ shapes.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Matrix

CODE=Path(__file__).resolve().parent
sys.path.insert(0,str(CODE))
from g2_palmar_motion_control import PalmarControl

model=PalmarControl(arm_ik=True,staged_release=True,free_wrist=True,index_lead=2.3)
audit_file=model.output/'DenseAudit.json';timing_file=model.output/'Timing.json'
audit=json.loads(audit_file.read_text());timing=json.loads(timing_file.read_text())
control_hash=hashlib.sha256((CODE/'g2_palmar_motion_control.py').read_bytes()).hexdigest()
assert audit['sources']==timing['sources']==model.guards
assert audit['control_sha256']==timing['control_sha256']==control_hash
assert audit['dense'] and audit['samples']==model.manifest['frame_end']
assert not any(audit[n] for n in ('pole_flags','arm_body_flags','digit_flags'))
assert not any(r['rear_flag'] or r['hinge_alignment']<=0 or r['reach_error_m']>.0001 for r in audit['rows'])
source_times=np.array(timing['source_seconds_map']);destination_times=np.array(timing['destination_seconds_map'])
fps=120;count=math.ceil(destination_times[-1]*fps)+1
destination_times*=((count-1)/fps)/destination_times[-1]
knots='--source-knots' in sys.argv
variant='G2_PalmarGrip_Knots' if knots else 'G2_PalmarGrip'
destination=model.source/(variant+'_ActionLibrary.blend')
record=model.source/(variant+'_Manifest.json')
bake_times=np.arange(count,dtype=float)/fps
if knots:
    # Preserve fractional source-action breakpoints. A uniform high-rate bake
    # can straddle an existing corner and alter the pose even at modest speeds.
    key_frames=set()
    for layer in model.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    coordinates=np.empty(len(curve.keyframe_points)*2,dtype=np.float32)
                    curve.keyframe_points.foreach_get('co',coordinates)
                    key_frames.update(coordinates[::2].tolist())
    key_seconds=(np.array(sorted(key_frames))-1)/60
    key_seconds=key_seconds[(key_seconds>=0)&(key_seconds<=model.duration)]
    bake_times=np.unique(np.r_[bake_times,np.interp(key_seconds,source_times,destination_times)])
verify='--verify-only' in sys.argv
assert verify or (not destination.exists() and not record.exists()), 'Preserve prior saved candidate'
if verify:
    manifest=json.loads(record.read_text())
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==manifest['sha256']
    assert manifest['sources']==model.guards and manifest['control_sha256']==control_hash
    assert manifest['timing_sha256']==hashlib.sha256(timing_file.read_bytes()).hexdigest()
    with bpy.data.libraries.load(str(destination),link=False) as (_,loaded):loaded.actions=[manifest['action']]
    candidate=loaded.actions[0]
    if '--surface-only' in sys.argv:
        from validate_g2_contact_recipe import geometry, skin, triangle_radii
        mesh=next(m for m in geometry(SimpleNamespace(names=model.names,scene=model.scene)) if m[0]=='Vexa_Continuous_Hands')
        _,_,triangles,joints,weights,_,_=mesh
        right=(weights*np.array([n.endswith('_r') for n in model.names])[joints]).sum(axis=1)>.5
        triangles=triangles[np.all(right[triangles],axis=1)]
        inverse=np.array([model.rest[n].inverted() for n in model.names])
        model.rig.animation_data.action=candidate;model.rig.animation_data.action_slot=candidate.slots[0]
        minimum=math.inf;flags=[]
        for frame in range(1,count+1):
            model.scene.frame_set(frame);bpy.context.view_layer.update()
            matrices=np.array([model.rig.matrix_world@b.matrix for b in model.ordered])@inverse
            points=skin(matrices,mesh)
            radius=triangle_radii(points,triangles);z=points[triangles,2]
            eligible=(z.max(axis=1)>0)&(z.min(axis=1)<5)
            closest=float(radius[eligible].min()) if eligible.any() else math.inf
            minimum=min(minimum,closest)
            if closest<.02499:flags.append({'frame':frame,'penetration_mm':(.025-closest)*1000})
            if frame%1200==1:print('PALMAR_SAVED_SURFACE',frame,minimum,flush=True)
        report={'passed':not flags,'samples':count,'fps':fps,'minimum_pole_radius_mm':minimum*1000,'flags':flags,
                'action_sha256':manifest['sha256'],'sources':model.guards,
                'scope':'Fresh saved120Hz right-hand triangle/pole screen at0.01mm tolerance. Not other body regions, between-frame or native acceptance.'}
        (model.output/('SavedHandSurfaceKnots.json' if knots else 'SavedHandSurface.json')).write_text(json.dumps(report,indent=2))
        model.assert_guards()
        print('PALMAR_SAVED_SURFACE_RESULT',{k:v for k,v in report.items() if k!='sources'},flush=True)
        assert report['passed']
        raise SystemExit(0)
else:
    values=np.zeros((len(bake_times),len(model.names),10),dtype=np.float64)
previous=None;max_matrix=0.;max_position=0.;actual_start=None;actual_end=None
worst_pose={}
maximum_rate=0.;maximum_root=0.;previous_actual=None
sample_count=(count-1)*2+1 if verify else len(bake_times)
if verify:
    # Evaluate each action in one pass. Alternating a large saved action and
    # the source on every sample repeatedly rebuilds Blender's animation cache.
    expected_cache=np.empty((sample_count,len(model.names),4,4),dtype=np.float32)
    for sample in range(sample_count):
        seconds=sample/(fps*2)
        source_seconds=float(np.interp(seconds,destination_times,source_times))
        expected,_,_=model.pose(source_seconds)
        expected_cache[sample]=np.array([expected[n] for n in model.names])
        if sample%2400==0:print('PALMAR_EXPECTED',sample,flush=True)
    model.rig.animation_data.action=candidate;model.rig.animation_data.action_slot=candidate.slots[0]
for sample in range(sample_count):
    seconds=sample/(fps*2) if verify else bake_times[sample]
    source_seconds=float(np.interp(seconds,destination_times,source_times))
    expected={n:Matrix(expected_cache[sample,j]) for j,n in enumerate(model.names)} if verify else model.pose(source_seconds)[0]
    if verify:
        model.rig.animation_data.action=candidate;model.rig.animation_data.action_slot=candidate.slots[0]
        frame=1+seconds*fps
        model.scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
        actual={b.name:model.rig.matrix_world@b.matrix for b in model.ordered}
        max_matrix=max(max_matrix,max(float(np.abs(np.array(actual[n])-np.array(expected[n])).max()) for n in model.names))
        errors={n:(actual[n].translation-expected[n].translation).length for n in model.names}
        worst=max(errors,key=errors.get)
        if errors[worst]>max_position:
            max_position=errors[worst];worst_pose={'seconds':seconds,'source_seconds':source_seconds,'bone':worst,'error_mm':max_position*1000}
        quats=np.array([list((actual[model.parents[n]].inverted()@actual[n] if model.parents[n] else actual[n]).to_quaternion()) for n in model.names],dtype=float)
        quats/=np.linalg.norm(quats,axis=1)[:,None]
        if previous_actual is not None:
            rate=np.degrees(2*np.arccos(np.clip(np.abs((quats*previous_actual[0]).sum(axis=1)),0,1)))*fps*2
            maximum_rate=max(maximum_rate,float(rate.max()))
            maximum_root=max(maximum_root,(actual['pelvis'].translation-previous_actual[1]).length*fps*2)
        previous_actual=(quats,actual['pelvis'].translation.copy())
        if actual_start is None:actual_start=actual
        actual_end=actual
    else:
        for j,n in enumerate(model.names):
            base=expected[model.parents[n]]@model.relative[n] if model.parents[n] else model.rest[n]
            location,rotation,scale=(base.inverted()@expected[n]).decompose()
            rotation.normalize()
            if previous is not None and np.dot(np.array(rotation),previous[j,3:7])<0:rotation.negate()
            values[sample,j]=[*location,*rotation,*scale]
        previous=values[sample]
    if sample%1200==0:print('PALMAR_BAKE',verify,sample,max_position,flush=True)
if verify:
    loop=max(float(np.abs(np.array(actual_start[n])-np.array(actual_end[n])).max()) for n in model.names)
    report={'passed':max_position<.00015 and max_matrix<.001 and loop<.0001 and maximum_rate<95 and maximum_root<.46,
            'samples':sample_count,'maximum_bone_position_error_mm':max_position*1000,'maximum_matrix_error':max_matrix,'loop_matrix_error':loop,
            'maximum_local_dps':maximum_rate,'maximum_pelvis_mps':maximum_root,'action_sha256':manifest['sha256'],
            'control_sha256':control_hash,'sources':model.guards,'worst_pose':worst_pose,'scope':'Fresh saved120Hz action versus control at240Hz,95 bones. Limited numerical replay; surface/visual/native acceptance separate.'}
    (model.output/('SavedReplayKnots.json' if knots else 'SavedReplay.json')).write_text(json.dumps(report,indent=2))
    print('PALMAR_REPLAY',{k:v for k,v in report.items() if k!='sources'},flush=True)
    assert report['passed']
else:
    candidate=bpy.data.actions.new('A_F3_G2_PalmarGrip_Knots_Review' if knots else 'A_F3_G2_PalmarGrip_Review');candidate.use_fake_user=True
    model.rig.animation_data.action=candidate
    for bone in model.ordered:
        bone.rotation_mode='QUATERNION'
        for prop in ('location','rotation_quaternion','scale'):bone.keyframe_insert(prop,frame=1,group=bone.name)
    frame_numbers=1+bake_times*fps;indices={n:i for i,n in enumerate(model.names)}
    offsets={'location':0,'rotation_quaternion':3,'scale':7};keys=0
    for layer in candidate.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    name=curve.data_path.split('"')[1];kind=curve.data_path.rsplit('.',1)[1]
                    column=values[:,indices[name],offsets[kind]+curve.array_index]
                    times=frame_numbers
                    if np.ptp(column)<1e-8:times=frame_numbers[[0,-1]];column=column[[0,-1]]
                    pairs=np.column_stack((times,column)).ravel()
                    curve.keyframe_points.clear();curve.keyframe_points.add(len(times));curve.keyframe_points.foreach_set('co',pairs)
                    for point in curve.keyframe_points:point.interpolation='LINEAR'
                    curve.update();keys+=len(times)
    candidate['required_weight_patch']='G2_GluteFollow_Manifest.json'
    candidate['required_morph_mute_prefix']='REVIEW_G2_'
    candidate['quality_state']='Private palmar-grip review; saved replay, surfaces, native and artistic acceptance remain required.'
    model.assert_guards()
    bpy.data.libraries.write(str(destination),{candidate},fake_user=True,compress=True)
    manifest={'sources':model.guards,'control_sha256':control_hash,'audit_sha256':hashlib.sha256(audit_file.read_bytes()).hexdigest(),
              'timing_sha256':hashlib.sha256(timing_file.read_bytes()).hexdigest(),'file':destination.name,'action':candidate.name,
              'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'fps':fps,'frame_end':count,'seconds':(count-1)/fps,
              'source_knots_preserved':knots,'bake_sample_count':len(bake_times),
              'source_seconds_map':source_times.tolist(),'destination_seconds_map':destination_times.tolist(),'weight_patch':model.manifest['weight_patch'],
              'morph_mute_prefix':'REVIEW_G2_','key_count':keys,'scope':candidate['quality_state']}
    record.write_text(json.dumps(manifest,indent=2))
    print('PALMAR_SAVED',manifest['sha256'],manifest['seconds'],destination.stat().st_size,flush=True)
model.assert_guards()
