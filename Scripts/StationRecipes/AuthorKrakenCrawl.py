"""Create an animation-only candidate; never save or replace the fitted body file."""
import bpy,json,math,hashlib,random,argparse,sys
import numpy as np
from mathutils import Quaternion,Vector,Matrix
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--output',required=True)
parser.add_argument('--chains',required=True)
parser.add_argument('--source-sha256',required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
R=Path(args.output).resolve();R.mkdir(parents=True,exist_ok=True)
assert not (R/'Candidate.json').exists(),'Use a fresh candidate folder'
source=Path(bpy.data.filepath)
before=hashlib.sha256(source.read_bytes()).hexdigest()
assert before==args.source_sha256
rig=bpy.data.objects['Kraken_Rig'];body=bpy.data.objects['Kraken_Body']
chains=json.loads(Path(args.chains).read_text())
FPS=25;SECONDS=24;END=FPS*SECONDS
rig.animation_data_clear();rig.animation_data_create();rig.data.pose_position='POSE'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4);pb.rotation_mode='QUATERNION'
action=bpy.data.actions.new('Kraken_IndependentCrawl_24s');action.use_fake_user=True
rig.animation_data.action=action
for pb in rig.pose.bones:
    pb.keyframe_insert('rotation_quaternion',frame=0,group=pb.name)
    pb.keyframe_insert('location',frame=0,group=pb.name)
    pb.keyframe_insert('scale',frame=0,group=pb.name)
bag=action.layers[0].strips[0].channelbags[0]
curves={(f.data_path,f.array_index):f for f in bag.fcurves}
params=[];samples={};rng=random.Random(20261021)
for ci,c in enumerate(chains):
    # Different cycle counts close seamlessly after24s, without left/right footfall pairing.
    cycles=rng.choice([4,5,6,7]) if c['kind']=='lower' else rng.choice([3,4,5])
    phase=rng.uniform(0,math.tau);variation=rng.uniform(0,math.tau)
    params.append(dict(name=c['name'],cycles=cycles,phase=phase,variation=variation))
    for j,name in enumerate(c['bones']):
        pb=rig.pose.bones[name];b=pb.bone
        w=max(0.,(j-1)/(len(c['bones'])-2))**1.45
        inverse=b.matrix_local.to_quaternion().inverted()
        radial=Vector(c['points'][-1])-Vector(c['points'][0]);radial.z=0
        if radial.length<.01:radial=Vector((1,0,0))
        radial.normalize();curl_axis=radial.cross(Vector((0,0,1))).normalized()
        curl_local=inverse@curl_axis;sweep_local=inverse@Vector((1,0,0))
        values=[]
        for frame in range(END+1):
            t=math.tau*frame/END
            p=cycles*t+phase-j*.50+.18*math.sin(t+variation)
            modulation=.78+.22*math.sin(2*t+variation)
            # Long reach/pull stroke, shorter curling recovery. Smooth, never per-frame noise.
            recovery=((1+math.sin(p))*.5)**2
            if c['kind']=='lower':
                curl=.14*w*modulation*recovery
                sweep=.105*w*modulation*(math.sin(p)+.22*math.sin(2*p))
            elif c['kind']=='arm':
                curl=.12*w*modulation*math.sin(p)
                sweep=.075*w*math.sin(cycles*t+phase-j*.65+1.1)
            else:
                curl=.035*w*math.sin(p);sweep=.018*w*math.sin(cycles*t+phase)
            q=Quaternion(curl_local,curl)@Quaternion(sweep_local,sweep)
            values.append(tuple(q))
        for index in range(4):
            f=curves[(pb.path_from_id('rotation_quaternion'),index)]
            f.keyframe_points.clear();f.keyframe_points.add(END+1)
            f.keyframe_points.foreach_set('co',np.array([(i,q[index]) for i,q in enumerate(values)],np.float32).ravel())
            for key in f.keyframe_points:key.interpolation='LINEAR'
            f.update()
        assert max(abs(a-b) for a,b in zip(values[0],values[-1]))<1e-6
action.asset_mark();action.asset_data.description='Upright Kraken: staggered reach/pull/curl motion, fixed attachment roots, no human leg cycle. Seeded24-second seamless loop; original body and clips retained.'
bpy.context.scene.render.fps=FPS;bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=END
rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
for c in chains:samples[c['name']]=[]
surface=[];root_positions={};head_positions=[]
for frame in range(0,END+1,5):
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    for c in chains:
        samples[c['name']].append(list(rig.pose.bones[c['bones'][-1]].tail))
        root_positions.setdefault(c['name'],[]).append(list(rig.pose.bones[c['bones'][0]].head))
    head_positions.append(list(rig.pose.bones['head'].head))
    evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evaluated.to_mesh()
    coords=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',coords);coords=coords.reshape((-1,3))
    surface.append({'frame':frame,'min_z':float(coords[:,2].min())});evaluated.to_mesh_clear()
def span(points):return float(np.linalg.norm(np.ptp(np.array(points),axis=0)))
report={'source':str(source),'source_sha256':before,'clip':action.name,'seconds':SECONDS,'fps':FPS,'frames':END+1,
 'params':params,'tip_spans_m':{k:span(v) for k,v in samples.items()},'root_spans_m':{k:span(v) for k,v in root_positions.items()},
 'head_span_m':span(head_positions),'surface':surface,'original_clips_preserved_on_disk':True,'native_adopted':False}
assert max(report['root_spans_m'].values())<1e-6 and report['head_span_m']<1e-6
bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.context.scene.frame_set(0)
bpy.ops.export_scene.fbx(filepath=str(R/'Kraken_IndependentCrawl_24s.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=True,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y')
# Armature/action library only: avoids another duplicate of the large fitted mesh and its textures.
library=R/'Kraken_IndependentCrawl_Animation.blend'
bpy.data.libraries.write(str(library),{rig,action},fake_user=True,compress=True)
report['library']=str(library);report['library_bytes']=library.stat().st_size
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(R/'Candidate.json').write_text(json.dumps(report,indent=2));(R/'Tips.json').write_text(json.dumps(samples))
print('KRAKEN_CANDIDATE',report['library_bytes'],report['tip_spans_m'])
