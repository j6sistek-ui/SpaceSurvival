"""Save/reload the four-second G1-to-G2 bridge and its paired morph curves.

Action-only library plus eight compact morph deltas, not another full character
copy. Existing G1/G2 libraries remain unchanged. Never loop this bridge alone.
"""
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CODE=Path(__file__).resolve().parent
sys.path.insert(0,str(CODE))
from validate_g2_contact_recipe import geometry, triangle_radii

verify='--verify' in sys.argv
sys.argv+=['--forward-arm','--setup-only','--output','G1G2JoinForwardReplay' if verify else 'G1G2JoinForwardSaved']
c=runpy.run_path(str(CODE/'review_g1_g2_join.py'))
rig,scene,out=c['rig'],c['s'],c['O']
names,ordered,parents,rest=c['names'],c['ordered'],c['parents'],c['rest']
body=bpy.data.objects['Vexa_Continuous_Hands']
fit_dir=c['R']/'G1G2JoinForward'
fit=json.loads((fit_dir/'Fit.json').read_text())
assert fit['passed'] and fit['sources']==c['guards'] and fit['independent_basis'] and fit['forward_arm']
assert fit['maximum_coefficient']<=1.00001
fit_data=np.load(fit_dir/'Coefficients.npz');basis=np.load(fit_dir/'AdditionalBasis.npz')
times,coeff=fit_data['seconds'],fit_data['values']
base=np.array([tuple(v.co) for v in body.data.shape_keys.key_blocks[0].data])
keys=[k for k in body.data.shape_keys.key_blocks if k.name.startswith('REVIEW_G1_LeftAxilla_')]
for i,delta in enumerate(basis['deltas']):
    key=body.shape_key_add(name=f'REVIEW_GJoin_LeftAxilla_{i:02d}',from_mix=False)
    key.slider_min,key.slider_max=-10,10
    coordinates=base.copy();coordinates[basis['active']]+=delta
    key.data.foreach_set('co',coordinates.ravel());keys.append(key)
assert len(keys)==coeff.shape[1]==96+fit['added_morphs']
destination=c['D']/'G1G2_Join_ActionLibrary.blend'
manifest_path=c['D']/'G1G2_Join_Manifest.json'
delta_path=c['D']/'G1G2_Join_MorphBasis.npz'
guard_files={str(fit_dir/f):hashlib.sha256((fit_dir/f).read_bytes()).hexdigest() for f in ('Fit.json','Coefficients.npz','AdditionalBasis.npz')}
guards=c['guards']|guard_files

def curves(action):
    return [curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags for curve in bag.fcurves]

def set_curve(curve,frames,values):
    curve.keyframe_points.clear();curve.keyframe_points.add(len(frames))
    curve.keyframe_points.foreach_set('co',np.column_stack((frames,values)).ravel())
    for point in curve.keyframe_points:point.interpolation='LINEAR'
    curve.update()

def seek(seconds):
    frame=1+seconds*120
    scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()

if not verify:
    assert not any(p.exists() for p in (destination,manifest_path,delta_path)), 'Preserve existing join delivery'
    values=np.empty((481,len(names),10));previous=None
    for i,t in enumerate(times):
        pose=c['pose_at'](float(t))
        for j,n in enumerate(names):
            parent=pose[parents[n]]@c['relative'][n] if parents[n] else rest[n]
            location,rotation,scale=(parent.inverted()@pose[n]).decompose();rotation.normalize()
            if previous is not None and np.dot(np.array(rotation),previous[j,3:7])<0:rotation.negate()
            values[i,j]=[*location,*rotation,*scale]
        previous=values[i]
    action=bpy.data.actions.new('A_F3_G1G2_Join');action.use_fake_user=True
    rig.animation_data.action=action
    for b in ordered:
        b.rotation_mode='QUATERNION'
        for prop in ('location','rotation_quaternion','scale'):b.keyframe_insert(prop,frame=1,group=b.name)
    index={n:i for i,n in enumerate(names)};offset={'location':0,'rotation_quaternion':3,'scale':7}
    frames=1+times*120
    for curve in curves(action):
        name=curve.data_path.split('"')[1];kind=curve.data_path.rsplit('.',1)[1]
        column=values[:,index[name],offset[kind]+curve.array_index]
        take=[0,-1] if np.ptp(column)<1e-8 else slice(None)
        set_curve(curve,frames[take],column[take])
    for key in keys:key.keyframe_insert('value',frame=1)
    shape=body.data.shape_keys.animation_data.action;shape.name='A_F3_G1G2_Join_Correctives';shape.use_fake_user=True
    index={key.path_from_id('value'):i for i,key in enumerate(keys)}
    for curve in curves(shape):set_curve(curve,frames,coeff[:,index[curve.data_path]])
else:
    manifest=json.loads(manifest_path.read_text())
    assert manifest['sources']==guards
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==manifest['sha256']
    assert hashlib.sha256(delta_path.read_bytes()).hexdigest()==manifest['morph_basis_sha256']
    with bpy.data.libraries.load(str(destination),link=False) as (_,loaded):loaded.actions=[manifest['action'],manifest['shape_action']]
    action,shape=loaded.actions
    rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    body.data.shape_keys.animation_data_create()
    body.data.shape_keys.animation_data.action=shape;body.data.shape_keys.animation_data.action_slot=shape.slots[0]
scene.render.fps=120;scene.frame_start=1;scene.frame_end=481
hinge={}
for side in ('l','r'):
    a,b,d=[rest[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
    hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(d.translation-b.translation).normalized()
max_bone=0.;max_matrix=0.;max_shape=0.;max_rate=0.;max_root=0.;previous=None;arms=[]
for i in range(961):
    t=i/240;seek(t);pose={n:rig.matrix_world@rig.pose.bones[n].matrix for n in names};expected=c['pose_at'](t)
    max_bone=max(max_bone,max((pose[n].translation-expected[n].translation).length for n in names))
    max_matrix=max(max_matrix,max(float(np.abs(np.array(pose[n])-np.array(expected[n])).max()) for n in names))
    wanted=np.array([np.interp(t,times,coeff[:,k]) for k in range(len(keys))])
    max_shape=max(max_shape,max(abs(key.value-wanted[k]) for k,key in enumerate(keys)))
    local=[pose[parents[n]].inverted()@pose[n] if parents[n] else pose[n] for n in names]
    quats=np.array([list(m.to_quaternion().normalized()) for m in local],dtype=float)
    if previous is not None:
        rates=np.degrees(2*np.arccos(np.clip(np.abs((quats*previous[0]).sum(axis=1)),0,1)))*240
        max_rate=max(max_rate,float(rates.max()));max_root=max(max_root,(pose['pelvis'].translation-previous[1]).length*240)
    previous=quats,pose['pelvis'].translation.copy()
    chest=pose['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted()
    forward=chest@Vector((0,-1,0));up=chest@Vector((0,0,1))
    for side in ('l','r'):
        a,b,d=[pose[n+'_'+side] for n in ('upperarm','lowerarm','hand')]
        upper=(b.translation-a.translation).normalized();lower=(d.translation-b.translation).normalized()
        axis=upper.cross(lower);bend=math.degrees(upper.angle(lower))
        alignment=(a.to_quaternion().inverted()@axis.normalized()).dot(hinge[side]) if axis.length>.01 else 1.
        rear=math.degrees(math.asin(max(-1.,min(1.,-upper.dot(forward)))))
        if rear>(12 if upper.dot(up)>0 else 2) or (alignment<=0 and bend>10):
            arms.append({'seconds':t,'side':side,'rear_degrees':rear,'hinge_alignment':alignment,'bend':bend})
report={'sources':guards,'samples':961,'max_bone_error_mm':max_bone*1000,'max_matrix_error':max_matrix,
        'max_shape_coefficient_error':max_shape,'max_local_dps':max_rate,'max_pelvis_mps':max_root,'arm_direction_flags':arms,
        'passed':bool(max_bone<.00015 and max_matrix<.001 and max_shape<.00001 and not arms and max_rate<95 and max_root<.46),
        'scope':'Fresh reload' if verify else 'In-memory save gate'}
(out/'Replay.json').write_text(json.dumps(report,indent=2))
print('JOIN_ACTION_REPLAY',{k:v for k,v in report.items() if k not in ('sources','arm_direction_flags')},'arm flags',len(arms),flush=True)
assert report['passed'], 'Join direction, pacing or replay gate failed'
if not verify:
    bpy.data.libraries.write(str(destination),{action,shape},fake_user=True,compress=True)
    delta_path.write_bytes((fit_dir/'AdditionalBasis.npz').read_bytes())
    manifest={'sources':guards,'file':destination.name,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
              'action':action.name,'shape_action':shape.name,'morph_basis':delta_path.name,
              'morph_basis_sha256':hashlib.sha256(delta_path.read_bytes()).hexdigest(),
              'fps':120,'frame_end':481,'seconds':4.,'new_morphs':[k.name for k in keys[96:]],
              'order':[c['manifests'][0]['action'],action.name,c['manifests'][1]['action']],
              'scope':'Private nonlooping bridge; requires preserved G1 mesh plus independent join morphs. Fresh saved/surface/native/motion review remains required.'}
    manifest_path.write_text(json.dumps(manifest,indent=2))
else:
    # Test actual evaluated surface, including the shoulder morphs.
    for key in keys:key.value=0
    meshes=geometry(type('Model',(),{'names':names,'scene':scene})())
    rows=[];max_radius=0.
    for i in range(481):
        t=i/120;seek(t);bv=[];bf=[];av=[];af=[];pole={}
        for name,_,faces,_,_,bt,at in meshes:
            ob=bpy.data.objects[name];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            data=np.empty(len(ev.data.vertices)*3);ev.data.vertices.foreach_get('co',data)
            p=(np.column_stack((data.reshape(-1,3),np.ones(len(ev.data.vertices))))@np.array(ob.matrix_world).T)[:,:3]
            max_radius=max(max_radius,float(np.linalg.norm(p[:,:2],axis=1).max()))
            radius=triangle_radii(p,faces);z=p[faces,2]
            bad=(radius<.02499)&(z.max(axis=1)>0)&(z.min(axis=1)<5)
            if bad.any():pole[name]=int(bad.sum())
            if len(bt):offset=len(bv);bv.extend(p.tolist());bf.extend((bt+offset).tolist())
            if len(at):offset=len(av);av.extend(p.tolist());af.extend((at+offset).tolist())
        pairs=BVHTree.FromPolygons(bv,bf,all_triangles=True).overlap(BVHTree.FromPolygons(av,af,all_triangles=True))
        if pole or pairs:rows.append({'seconds':t,'pole':pole,'arm_body_pairs':len(pairs)})
    surface={'samples':481,'flags':rows,'max_radius_m':max_radius,'passed':not rows,
             'scope':'Actual saved skin/morph surfaces versus pole and distal-arm/body screen; not full anatomy or native acceptance.'}
    (out/'Surface.json').write_text(json.dumps(surface,indent=2))
    print('JOIN_SAVED_SURFACE',surface,flush=True);assert surface['passed']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guards.items())
print('JOIN_SAVED_DONE',verify,flush=True)
