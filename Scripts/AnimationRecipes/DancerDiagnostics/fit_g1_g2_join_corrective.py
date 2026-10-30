"""Carry the saved shoulder into the G1/G2 join without reusing its timing.

New private control only. Test the existing 96 bases, or use independently
normalized join bases; refuse adoption if the fit or holdouts are inadequate.
The original mesh, weights, clips and calibrated hands remain read-only.
"""
import hashlib
import json
import math
import os
import runpy
import sys
from pathlib import Path

os.environ.setdefault('OPENBLAS_NUM_THREADS', '4')
import bpy
import numpy as np
from mathutils import Vector

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from shoulder_support import shoulder_mask

augment = '--augment-basis' in sys.argv
independent = '--independent-basis' in sys.argv
assert not independent or (augment and '--forward-arm' in sys.argv)
sys.argv += ['--setup-only', '--output', 'G1G2JoinForward' if independent else 'G1G2JoinAugmented' if augment else 'G1G2JoinCorrective']
c = runpy.run_path(str(CODE/'review_g1_g2_join.py'))
rig, scene, out = c['rig'], c['s'], c['O']
names, rest = c['names'], c['rest']
duration, pose_at, apply = c['duration'], c['pose_at'], c['apply']
body = bpy.data.objects['Vexa_Continuous_Hands']
shape = bpy.data.actions['A_F3_G1_LeftAxilla_Correctives']
keys = [k for k in body.data.shape_keys.key_blocks if k.name.startswith('REVIEW_G1_LeftAxilla_')]
assert len(keys) == 96
base = np.array([tuple(v.co) for v in body.data.shape_keys.key_blocks[0].data])
basis = np.array([np.array([tuple(v.co) for v in key.data])-base for key in keys])
curves = {curve.data_path: curve for layer in shape.layers for strip in layer.strips for bag in strip.channelbags for curve in bag.fcurves}
end_frame = c['manifests'][0]['frame_end']
def coefficients(frame):
    return np.array([curves[key.path_from_id('value')].evaluate(frame) for key in keys])
end_coeff = coefficients(end_frame)
end_rate = (end_coeff-coefficients(end_frame-1))*120
end_delta = np.einsum('k,kvi->vi', end_coeff, basis)
end_delta_rate = np.einsum('k,kvi->vi', end_rate, basis)
mask, _ = shoulder_mask(body, [rest['upperarm_l'].translation])
points = np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices])
def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)
mask *= smooth(.09, .14, points[:, 0])*smooth(1.15, 1.24, points[:, 2])
active = np.flatnonzero(mask > 0)
outside = np.flatnonzero(mask == 0)
group = body.vertex_groups.new(name='REVIEW_Join_Target')
for i in active:
    group.add([int(i)], float(mask[i]), 'REPLACE')
modifier = body.modifiers.new('REVIEW_Join_Target', 'CORRECTIVE_SMOOTH')
modifier.vertex_group = group.name
modifier.factor, modifier.iterations = .5, 8
modifier.rest_source, modifier.use_pin_boundary = 'ORCO', True
modifier.show_viewport = False
weights = np.zeros((len(base), len(names)))
index = {name:i for i,name in enumerate(names)}
for vertex in body.data.vertices:
    for item in vertex.groups:
        name = body.vertex_groups[item.group].name
        if name in index: weights[vertex.index,index[name]] = item.weight
weights /= np.maximum(weights.sum(axis=1)[:,None], 1e-12)
left = body.matrix_world.inverted()@rig.matrix_world
right = rig.matrix_world.inverted()@body.matrix_world
scale = max(body.matrix_world.to_scale())
fit_basis = basis[:, active].reshape(len(keys), -1)
projection = np.linalg.pinv(fit_basis)

def positions():
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = np.empty(len(evaluated.data.vertices)*3)
    evaluated.data.vertices.foreach_get('co', points)
    return points.reshape(-1,3)

def target(seconds):
    for key in keys: key.value = 0
    apply(pose_at(seconds))
    modifier.show_viewport = False
    bpy.context.view_layer.update()
    before = positions()
    modifier.show_viewport = True
    bpy.context.view_layer.update()
    after = positions()
    modifier.show_viewport = False
    bpy.context.view_layer.update()
    assert np.linalg.norm((after-before)[outside],axis=1).max()*scale < 1e-7
    matrices = np.array([(left@rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@right).to_3x3() for n in names])
    skin = np.einsum('vb,bij->vij',weights[active],matrices,optimize=True)
    assert np.abs(np.linalg.det(skin)).min() > .01
    delta = np.linalg.solve(skin,(after-before)[active,:,None])[...,0]
    # Preserve the G1 endpoint and its first derivative, then approach the
    # target. Fade to zero before G2, which uses its own preserved rig repair.
    blend = smooth(0,.2,seconds)
    fade = 1-smooth(duration-.6,duration,seconds)
    return ((1-blend)*(end_delta[active]+seconds*end_delta_rate[active])+blend*delta)*fade

times = np.arange(481)/120
targets, values, errors = [], [], []
for i,t in enumerate(times):
    delta = target(float(t))
    value = np.zeros(96) if independent else delta.ravel()@projection
    fitted = (value@fit_basis).reshape(-1,3)
    targets.append(delta);values.append(value)
    errors.append(float(np.linalg.norm(fitted-delta,axis=1).max())*scale)
    if i%120 == 0: print('JOIN_SHAPE_FIT',i,max(errors)*1000,flush=True)
values = np.array(values)
added = 0
rank_trials = []
if augment:
    residual = np.array(targets).reshape(len(times),-1)-values@fit_basis
    u,singular,v = np.linalg.svd(residual,full_matrices=False)
    for rank in (4,8,16,24,32,48,64):
        remainder = residual-(u[:,:rank]*singular[:rank])@v[:rank]
        error = float(np.linalg.norm(remainder.reshape(len(times),-1,3),axis=2).max())*scale
        rank_trials.append({'rank':rank,'max_error_mm':error*1000})
        if error < .0001:
            added = rank
            break
    assert added, rank_trials
    extra_values = u[:,:added]*singular[:added]
    amplitude = np.maximum(np.abs(extra_values).max(axis=0),1e-8)
    extra_basis = v[:added]*amplitude[:,None]
    fit_basis = np.vstack((fit_basis,extra_basis))
    values = np.column_stack((values,extra_values/amplitude))
    errors = np.linalg.norm((values@fit_basis-np.array(targets).reshape(len(times),-1)).reshape(len(times),-1,3),axis=2).max(axis=1)*scale
    for k in range(added):
        key=body.shape_key_add(name=f'REVIEW_GJoin_LeftAxilla_{k:02d}',from_mix=False)
        key.slider_min,key.slider_max=-10,10
        coordinates=base.copy();coordinates[active]+=extra_basis[k].reshape(-1,3)
        key.data.foreach_set('co',coordinates.ravel())
        keys.append(key)
    np.savez_compressed(out/'AdditionalBasis.npz',active=active,deltas=extra_basis.reshape(added,-1,3))
np.savez_compressed(out/'Coefficients.npz',seconds=times,values=values)
holdouts = []
for i in range(0,480,2):
    t=(i+.5)/120
    delta=target(t)
    fitted=(np.array([np.interp(t,times,values[:,k]) for k in range(len(keys))])@fit_basis).reshape(-1,3)
    holdouts.append(float(np.linalg.norm(fitted-delta,axis=1).max())*scale)
report={'sources':c['guards'],'existing_morphs':96,'added_morphs':added,'rank_trials':rank_trials,'active_vertices':len(active),
        'forward_arm': '--forward-arm' in sys.argv,'independent_basis':independent,
        'maximum_coefficient':float(np.abs(values).max()),
        'fit_samples':len(times),'max_fit_error_mm':max(errors)*1000,
        'holdout_samples':len(holdouts),'max_holdout_error_mm':max(holdouts)*1000,
        'start_coefficient_error':float(np.max(np.abs(values[0,:96]-end_coeff))),
        'start_additional_coefficient_error':float(np.max(np.abs(values[0,96:]))) if added else 0.,
        'end_coefficient_error':float(np.max(np.abs(values[-1]))),
        'passed':max(errors)<.0001 and max(holdouts)<.0003,
        'scope':'Unsaved shoulder-only join target; no complete routine, native or owner acceptance.'}
(out/'Fit.json').write_text(json.dumps(report,indent=2))
print('JOIN_SHAPE_RESULT',report,flush=True)
assert report['passed'], 'Existing shoulder bases do not cover this new transition'
body.modifiers.remove(modifier);body.vertex_groups.remove(group)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='OBJECT'
scene.display.shading.show_cavity=False;scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('JoinCorrectiveReview');scene.world.color=(.035,.045,.055)
scene.render.resolution_x=scene.render.resolution_y=800;scene.render.resolution_percentage=100
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.025,depth=5,location=(0,0,2.5))
pole=bpy.context.object;pole.color=(1,.12,0,1)
for ob in scene.objects:
    if ob.type=='MESH' and ob!=pole:ob.color=(.55,.55,.55,1)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=3.4
for i,t in enumerate(np.linspace(0,duration,9)):
    pose=pose_at(t);apply(pose)
    for k,key in enumerate(keys):key.value=float(np.interp(t,times,values[:,k]))
    bpy.context.view_layer.update();center=pose['pelvis'].translation+Vector((0,0,.15))
    for view,direction in [('front',Vector((4,-6,2))),('back',Vector((-4,6,2)))]:
        camera.location=center+direction;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/f'{i:02d}_{view}.png');bpy.ops.render.render(write_still=True)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in c['guards'].items())
print('JOIN_SHAPE_DONE',flush=True)
