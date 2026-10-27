"""Reproduce the held Joy pour Candidate04 from owner-private pose exports.

CPU / NumPy only. Produces a sparse pose patch and numerical diagnostics.
Does not launch Unreal/Blender, modify/import assets, or claim visual acceptance.
This recipe is bound to the recorded Joy CC_Base source; it is not generic IK.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np

NATIVE_SHA256 = '6a44e5863000034a40d805431c0b94654c816aaa5f90a1d2cc30a730e590bec7'
ORIGINAL_SHA256 = '652b12c9c9f9033a18478b9b0691c1f307a36b18302f87fa937306fc526c49cc'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def qm(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return np.array([w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
                     w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z])

def qr(q, v):
    q = q / np.linalg.norm(q)
    return v + 2*np.cross(q[:3], np.cross(q[:3], v) + q[3]*v)

def fk(row):
    count, bones = len(row['frames']), len(row['names'])
    pos = np.zeros((count, bones, 3)); rot = np.zeros((count, bones, 4))
    scale = np.ones((count, bones, 3)); ids = {n:i for i,n in enumerate(row['names'])}
    for i, parent in enumerate(row['parents']):
        for f in range(count):
            p, q, s = map(np.asarray, row['frames'][f][i])
            q = q / np.linalg.norm(q)
            if parent in ids:
                j = ids[parent]
                assert j < i, 'Expected parent-first export'
                pos[f,i] = pos[f,j] + qr(rot[f,j], scale[f,j]*p)
                rot[f,i] = qm(rot[f,j], q)
                scale[f,i] = scale[f,j]*s
            else:
                pos[f,i], rot[f,i], scale[f,i] = p, q, s
    return pos, rot, ids

def inv(q):
    return np.array([-q[0],-q[1],-q[2],q[3]])/np.dot(q,q)

def unit(v):
    return v/np.linalg.norm(v)

def arc(a,b):
    a,b=unit(a),unit(b)
    dot=float(np.dot(a,b))
    assert dot > -0.999, 'Antipodal direction requires manual review'
    return unit(np.r_[np.cross(a,b),1+dot])

def pose(row, f):
    result={}
    for name,parent,(p,q,s) in zip(row['names'],row['parents'],f):
        p,q,s=np.asarray(p),unit(np.asarray(q)),np.asarray(s)
        if parent in result:
            pp,pq,ps=result[parent]
            result[name]=(pp+qr(pq,ps*p),qm(pq,q),ps*s)
        else:
            result[name]=(p,q,s)
    return result

def set_rotation(row,f,name,world_rotation):
    i=row['names'].index(name)
    p=row['parents'][i]
    w=pose(row,f)
    local=qm(inv(w[p][1]),world_rotation) if p in w else world_rotation
    f[i][1]=unit(local).tolist()

def solve(row,f,side,target):
    a,b,c=['CC_Base_'+side+'_'+part for part in ['Upperarm','Forearm','Hand']]
    w=pose(row,f);p0,p1,p2=[w[n][0] for n in [a,b,c]]
    hrot=w[c][1].copy();l1=np.linalg.norm(p1-p0);l2=np.linalg.norm(p2-p1)
    distance=np.linalg.norm(target-p0)
    assert abs(l1-l2)+1e-5 < distance < l1+l2-1e-5, ('Unreachable',side,distance,l1,l2)
    axis=unit(target-p0)
    bend=(p1-p0)-axis*np.dot(p1-p0,axis)
    assert np.linalg.norm(bend) > 1e-5, 'Singular elbow requires review'
    bend=unit(bend)
    along=(l1*l1+distance*distance-l2*l2)/(2*distance)
    elbow=p0+axis*along+bend*math.sqrt(max(0,l1*l1-along*along))
    set_rotation(row,f,a,qm(arc(p1-p0,elbow-p0),w[a][1]))
    w=pose(row,f)
    set_rotation(row,f,b,qm(arc(w[c][0]-w[b][0],target-w[b][0]),w[b][1]))
    set_rotation(row,f,c,hrot)
    return float(np.linalg.norm(pose(row,f)[c][0]-target))

def smooth(a,b,t):
    x=max(0,min(1,(t-a)/(b-a)))
    return x*x*(3-2*x)

def angle(a,b):
    return math.degrees(2*math.acos(min(1,abs(float(np.dot(unit(a),unit(b)))))))

def from_matrix(m):
    trace=float(np.trace(m))
    if trace>0:
        s=math.sqrt(trace+1)*2
        q=np.array([(m[2,1]-m[1,2])/s,(m[0,2]-m[2,0])/s,(m[1,0]-m[0,1])/s,s/4])
    else:
        k=int(np.argmax(np.diag(m)))
        if k==0:
            s=math.sqrt(1+m[0,0]-m[1,1]-m[2,2])*2
            q=np.array([s/4,(m[0,1]+m[1,0])/s,(m[0,2]+m[2,0])/s,(m[2,1]-m[1,2])/s])
        elif k==1:
            s=math.sqrt(1+m[1,1]-m[0,0]-m[2,2])*2
            q=np.array([(m[0,1]+m[1,0])/s,s/4,(m[1,2]+m[2,1])/s,(m[0,2]-m[2,0])/s])
        else:
            s=math.sqrt(1+m[2,2]-m[0,0]-m[1,1])*2
            q=np.array([(m[0,2]+m[2,0])/s,(m[1,2]+m[2,1])/s,s/4,(m[1,0]-m[0,1])/s])
    return unit(q)

def basis(direction, normal):
    x=unit(direction);z=unit(normal-x*np.dot(x,normal));y=unit(np.cross(z,x))
    return np.column_stack((x,y,z))

def original_frame(standing,source,i):
    f=deepcopy(standing['frames'][i]);old=pose(source,source['frames'][i]);new=pose(standing,f)
    waist='CC_Base_Waist';hip='CC_Base_Hip';wi=standing['names'].index(waist);parent=standing['parents'][wi]
    delta=new[hip][0]-old[hip][0]
    f[wi][0]=(qr(inv(new[parent][1]),old[waist][0]+delta-new[parent][0])/new[parent][2]).tolist()
    set_rotation(standing,f,waist,old[waist][1])
    return f

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-poses',type=Path,required=True,help='Private Inputs.json exported from the actual Joy action')
    parser.add_argument('--original-poses',type=Path,required=True,help='Private ContactPoses.json containing the original retargeted pour')
    parser.add_argument('--output-dir',type=Path,required=True,help='Isolated output directory, not Content or the production project')
    args=parser.parse_args()
    native_hash=hashlib.sha256(args.native_poses.read_bytes()).hexdigest()
    original_hash=hashlib.sha256(args.original_poses.read_bytes()).hexdigest()
    assert native_hash==NATIVE_SHA256, 'Native source changed; review provenance before adapting this recipe'
    assert original_hash==ORIGINAL_SHA256, 'Original source changed; review provenance before adapting this recipe'
    OUT=args.output_dir.resolve()
    OUT.mkdir(parents=True,exist_ok=False)
    inputs=read(args.native_poses)['joy']
    base=dict(inputs['poses']['Pour'],names=inputs['names'],parents=inputs['parents'])
    raw_data=read(args.original_poses)
    raw=raw_data['A_Joy_Bar_PourAndServe'];standing=raw_data['A_Joy_PourStanding']
    assert len(base['names'])==101 and base['names']==raw['names']==standing['names']
    assert len(base['frames'])==381 and base['parents']==standing['parents']
    arc=deepcopy(base)
    positions,orientations,ids=fk(base);source_positions,source_orientations,source_ids=fk(raw)
    source_anchor=source_positions[150,source_ids['CC_Base_L_Hand']]
    for i,f in enumerate(arc['frames']):
        t=i/30;amount=smooth(1.5,2,t)*(1-smooth(8,8.3,t))
        if amount<=0:continue
        offset=(source_positions[i,source_ids['CC_Base_L_Hand']]-source_anchor)*amount
        for side in ['L','R']:
            solve(arc,f,side,positions[i,ids['CC_Base_'+side+'_Hand']]+offset)
    original=[pose(standing,original_frame(standing,raw,i)) for i in range(len(base['frames']))]
    current=[pose(arc,f) for f in arc['frames']]
    candidate=deepcopy(arc);calibration={};angles={};normal_tracks={};direction_checks={}
    for side in ['L','R']:
        chain=['CC_Base_'+side+'_'+n for n in ['Upperarm','Forearm','Hand']]
        rest=original[60];a,b,c=[rest[n][0] for n in chain]
        h=unit(np.cross(b-a,c-b));local_hinge=qr(inv(rest[chain[0]][1]),h)
        calibration[side]={'source_frame':60,'source_time_seconds':2.0,'hinge_axis_upperarm_local':local_hinge.tolist(),
          'source_elbow_flex_degrees':math.degrees(math.acos(float(np.dot(unit(b-a),unit(c-b)))))}
        values={n:[] for n in chain[:2]};normal_list=[];degenerate=[];source_plane_quality=[]
        for i,(src,dst) in enumerate(zip(original,current)):
            a,b,c=[src[n][0] for n in chain];A,B,C=[dst[n][0] for n in chain]
            source_normal=qr(src[chain[0]][1],local_hinge)
            geometric=np.cross(B-A,C-B)
            quality=np.linalg.norm(geometric)/(np.linalg.norm(B-A)*np.linalg.norm(C-B))
            if quality<0.1:
                # Geometric target normal is poorly conditioned near extension.
                # A source-directed normal projected perpendicular to both arm
                # direction and reach line supplies the same calibrated side.
                preferred=source_normal if not normal_list else np.asarray(normal_list[-1])
                target_normal=unit(preferred-unit(C-A)*np.dot(preferred,unit(C-A)))
                degenerate.append(i)
            else:
                target_normal=unit(geometric)
            normal_list.append(target_normal.tolist())
            for n,axis,source_axis in [(chain[0],B-A,b-a),(chain[1],C-B,c-b)]:
                transverse=source_normal-unit(source_axis)*np.dot(source_normal,unit(source_axis))
                source_plane_quality.append(float(np.linalg.norm(transverse)))
                assert np.linalg.norm(transverse)>0.2,('Unreliable source hinge plane',i,n)
                r=basis(axis,target_normal)@basis(source_axis,source_normal).T
                desired=qm(from_matrix(r),src[n][1]);delta=unit(qm(desired,inv(dst[n][1])))
                assert np.linalg.norm(qr(delta,unit(axis))-unit(axis))<1e-5
                signed=2*math.atan2(float(np.dot(delta[:3],unit(axis))),float(delta[3]))
                values[n].append(signed)
        for n,v in values.items():
            unwrapped=np.unwrap(v)
            unwrapped-=round(float(unwrapped[0])/(2*math.pi))*2*math.pi
            angles[n]=unwrapped
        normals=np.asarray(normal_list)
        normal_steps=np.degrees(np.arccos(np.clip(np.sum(normals[:-1]*normals[1:],axis=1),-1,1)))
        normal_tracks[side]=normal_list
        direction_checks[side]={'target_geometric_plane_fallback_frames':degenerate,
          'minimum_source_transverse_axis_length':min(source_plane_quality),
          'maximum_target_plane_step_degrees':float(normal_steps.max()),
          'worst_target_plane_step_time_seconds':int(np.argmax(normal_steps))/30}
    for i,f in enumerate(candidate['frames']):
        t=i/30
        # Exactly the original contact solve's engagement/release envelope;
        # no new short exit blend and no broad animation smoothing.
        amount=smooth(.1,1.5,t)*(1-smooth(base['length']-1.5,base['length']-.1,t))
        if amount<=0:continue
        for side in ['L','R']:
            chain=['CC_Base_'+side+'_'+n for n in ['Upperarm','Forearm','Hand']]
            dst=current[i]
            for n,child in zip(chain[:2],chain[1:]):
                axis=unit(dst[child][0]-dst[n][0]);theta=float(angles[n][i])*amount
                roll=np.r_[axis*math.sin(theta/2),math.cos(theta/2)]
                set_rotation(candidate,f,n,qm(roll,dst[n][1]))
            set_rotation(candidate,f,chain[2],dst[chain[2]][1])
    p0,q0,ids=fk(arc);p1,q1,_=fk(candidate)
    hands=[ids['CC_Base_'+s+'_Hand'] for s in ['L','R']]
    arms=[ids['CC_Base_'+s+'_'+n] for s in ['L','R'] for n in ['Upperarm','Forearm','Hand']]
    unchanged=[i for i,n in enumerate(base['names']) if n not in ['CC_Base_'+s+'_'+part for s in ['L','R'] for part in ['Upperarm','Forearm','Hand']]]
    assert all(all(a[k]==b[k] for k in unchanged) for a,b in zip(base['frames'],candidate['frames']))
    assert candidate['frames'][0]==base['frames'][0] and candidate['frames'][-1]==base['frames'][-1]
    metrics={'status':'ISOLATED RIG-FRAME TRIAL; no visual or runtime acceptance',
      'method':'Calibrated upper-arm-local hinge axis from original frame 60; source-directed frame orientation, continuous signed roll representation, original contact envelope. No quaternion filtering.',
      'calibration':calibration,'direction_checks':direction_checks,
      'arm_joint_centres_max_change_cm':float(np.linalg.norm(p1[:,arms]-p0[:,arms],axis=2).max()),
      'hand_world_orientation_max_change_deg':max(angle(a,b) for k in hands for a,b in zip(q0[:,k],q1[:,k])),
      'pour_assembly_relative_position_max_change_cm':float(np.linalg.norm((p1[:,hands[1]]-p1[:,hands[0]])-(p0[:,hands[1]]-p0[:,hands[0]]),axis=1).max()),
      'rows':{},'roll_corrections_degrees':{n:[float(np.degrees(a).min()),float(np.degrees(a).max())] for n,a in angles.items()},
      'unchanged_track_count':len(unchanged),'source_fallback_used':False,
      'limitation':'Numerical continuity and geometry do not prove plausible skin or joint direction; actual-world clearance and natural-play validation are still required.'}
    event_frames=[27,82,115,132,170,0,len(base['frames'])-2]
    for label,row in [('baseline',base),('arc_only',arc),('rig_frame_trial',candidate),('original',raw)]:
        ri={n:i for i,n in enumerate(row['names'])};record={}
        for n in ['CC_Base_'+s+'_'+part for s in ['L','R'] for part in ['Upperarm','Forearm','Hand']]:
            qs=[f[ri[n]][1] for f in row['frames']];steps=[angle(a,b) for a,b in zip(qs,qs[1:])]
            record[n]={'maximum_step_degrees':max(steps),'maximum_step_time_seconds':int(np.argmax(steps))/30,
              'specified_steps':{str(i/30):steps[i] for i in event_frames}}
        metrics['rows'][label]=record
    patch=dict(base_inputs_sha256=native_hash,base_key='joy.poses.Pour',name='Joy_Pour_SourceCupArc_RigFrame_LocalCandidate04',frames_per_second=30,tracks={})
    changed=[n for k,n in enumerate(base['names']) if any(a[k]!=b[k] for a,b in zip(base['frames'],candidate['frames']))]
    patch['tracks']={n:[f[ids[n]] for f in candidate['frames']] for n in changed}
    (OUT/'RigFrameCandidate04Patch.json').write_text(json.dumps(patch,separators=(',',':')))
    (OUT/'RigFrameCandidate04Metrics.json').write_text(json.dumps(metrics,indent=2))
    assert hashlib.sha256(args.native_poses.read_bytes()).hexdigest()==native_hash
    assert hashlib.sha256(args.original_poses.read_bytes()).hexdigest()==original_hash
    (OUT/'InputProvenance.json').write_text(json.dumps(dict(native_source_sha256=native_hash,original_source_sha256=original_hash,patch_sha256=hashlib.sha256((OUT/'RigFrameCandidate04Patch.json').read_bytes()).hexdigest(),no_native_adoption=True),indent=2))
    print(json.dumps(dict(status=metrics['status'],patch=str(OUT/'RigFrameCandidate04Patch.json'),patch_sha256=hashlib.sha256((OUT/'RigFrameCandidate04Patch.json').read_bytes()).hexdigest()),indent=2))


if __name__=='__main__':main()
