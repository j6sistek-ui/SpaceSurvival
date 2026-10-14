"""Rebuild six custom pole arm tracks from native evaluated poses, without editing a mesh.

Run with installed Blender (no add-ons):
  blender -b --factory-startup -P repair_twist.py -- accepted.blend evidence_directory
The directory must contain the immutable BaselineKeys.json captured before repair.
Writes CandidateTracks/Poses and TrackReport. It does not save the blend or import assets.
Native adoption is separately guarded by Scripts/ApplyCyborgPoleTwist.py and review receipts.
"""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
R=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:]
assert len(args)==2, 'Expected accepted blend and evidence directory'
source=Path(args[0]).resolve(); O=Path(args[1]).resolve()
assert source.is_file() and (O/'BaselineKeys.json').is_file()
sys.path.insert(0,str(R)); from twist_pose_solver import solve
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
parents={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
data=json.loads((O/'BaselineKeys.json').read_text(encoding='utf-8'))
def mat(d):return Matrix.LocRotScale(Vector(d['t']),Quaternion(d['q']),Vector(d['s']))
def tr(m):
    t,q,s=m.decompose(); return {'t':list(t),'q':list(q),'s':list(s)}
ref={n:mat(d) for n,d in data['reference'].items()}
names=[n+'_'+s for s in ('l','r') for n in ('clavicle','upperarm','lowerarm','hand','upperarm_twist_01','lowerarm_twist_01')]
palm_local={s:ref['hand_'+s].inverted()@Vector(((.003477+sign*.490)*100,-4.9,142.3)) for s,sign in [('l',1),('r',-1)]}
rows=[]; summaries=[]
for clip in data['clips']:
    clipnames=names+[n for n in parents if clip['name']=='PoleSpin' and n.endswith('_l') and n.startswith(('thumb_','index_','middle_','ring_','pinky_'))]
    tracks={n:[] for n in clipnames}; samples=[]; prior={}; jumps=[]
    solved=[]
    for i,sample in enumerate(clip['samples']):
        old={n:mat(d) for n,d in sample['bones'].items()}; pose={n:m.copy() for n,m in old.items()}
        if clip['name']=='PoleSpin':
            chest=old['spine_03'].to_quaternion()@ref['spine_03'].to_quaternion().inverted()
            pose['hand_l'].translation=old['upperarm_l'].translation+chest@Vector((14,8,-18))
        free_hand=pose['hand_l'].translation.copy()
        new=solve(pose,ref,parents)
        palm=old['hand_r']@palm_local['r']
        for iteration in range(8):
            for side in ('l','r'):
                h='hand_'+side;e='lowerarm_'+side
                straight=new[e].to_quaternion()@ref[e].to_quaternion().inverted()@ref[h].to_quaternion()
                goal=straight.copy() if clip['name']=='PoleSpin' and side=='l' else old[h].to_quaternion()
                if goal.dot(straight)<0:goal.negate()
                angle=straight.rotation_difference(goal).angle
                limit=math.radians(60 if side=='r' else 50)
                q=straight.slerp(goal,min(1,limit/max(angle,1e-6)))
                loc=palm-q@palm_local[side] if side=='r' else free_hand
                pose[h]=Matrix.LocRotScale(loc,q,old[h].to_scale())
            new=solve(pose,ref,parents)
        # Fingers retain their authored curl relative to the repaired hand.
        for n in parents:
            p=parents[n]
            if p and (p.startswith(('hand_','thumb_','index_','middle_','ring_','pinky_'))):
                local=old[p].inverted()@old[n]
                if clip['name']=='PoleSpin' and n.endswith('_l'):
                    rest_local=ref[p].inverted()@ref[n]
                    local=Matrix.LocRotScale(local.translation,rest_local.to_quaternion().slerp(local.to_quaternion(),.35),local.to_scale())
                new[n]=new[p]@local
        assert all((new[n].translation-old[n].translation).length<1e-5 for n in ('head','pelvis','spine_03'))
        assert ((new['hand_r']@palm_local['r'])-palm).length<1e-4
        solved.append(new)
    # Filter helper orientation only; changing main arm axes would move the native grip.
    # Gaussian quaternion filtering is sign-invariant and never averages Euler angles.
    filtered=[]
    for i,new0 in enumerate(solved):
        new={n:m.copy() for n,m in new0.items()}
        for n in clipnames:
            if 'twist_01' not in n:continue
            center=new0[n].to_quaternion(); accum=[0.0]*4
            for offset in range(-4,5):
                q=solved[min(len(solved)-1,max(0,i+offset))][n].to_quaternion()
                if q.dot(center)<0:q.negate()
                w=math.exp(-offset*offset/8)
                for j in range(4):accum[j]+=q[j]*w
            q=Quaternion(accum).normalized()
            new[n]=Matrix.LocRotScale(new0[n].translation,q,new0[n].to_scale())
        filtered.append(new)
    for i,(new,sample) in enumerate(zip(filtered,clip['samples'])):
        for n in clipnames:
            local=new[parents[n]].inverted()@new[n]; t=tr(local); q=Quaternion(t['q'])
            if n in prior:
                dq=q.rotation_difference(prior[n]); deg=min(math.degrees(dq.angle),360-math.degrees(dq.angle))
                if deg>20:jumps.append({'key':i,'bone':n,'degrees':deg})
                if q.dot(prior[n])<0:q.negate(); t['q']=list(q)
            prior[n]=q; tracks[n].append(t)
        samples.append({'time':sample['time'],'bones':{n:tr(m) for n,m in new.items()}})
    rows.append({'name':clip['name'],'source':clip['path'],'duration':clip['duration'],'source_sha256':clip['sha256'],'tracks':tracks})
    summaries.append({'clip':clip['name'],'keys':len(samples),'right_palm_position_delta_cm_max':max(((filtered[i]['hand_r']@palm_local['r'])-(mat(s['bones']['hand_r'])@palm_local['r'])).length for i,s in enumerate(clip['samples'])),'jumps_over_20_deg':jumps})
    clip['samples']=samples
(O/'CandidateTracks.json').write_text(json.dumps(rows,separators=(',',':')),encoding='utf-8')
(O/'CandidatePoses.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
(O/'TrackReport.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
print(json.dumps([{**{k:v for k,v in r.items() if k!='jumps_over_20_deg'},'jump_count':len(r['jumps_over_20_deg']),'largest_jump':max([j['degrees'] for j in r['jumps_over_20_deg']],default=0)} for r in summaries]),flush=True)
