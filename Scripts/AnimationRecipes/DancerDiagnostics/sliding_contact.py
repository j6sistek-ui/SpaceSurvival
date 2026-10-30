"""Fit a smooth pole-XY placement to an unchanged periodic 20-joint pose callable.

CPU planning helper only. Capsule radii approximate the study renderer; actual
skin/contact and physical support must be verified separately. No source edits.
"""
import numpy as np

# (start, end, radius metres), exact study line widths / 2.
CAPSULES=[(0,1,.14),(1,2,.055),(2,3,.0525),(4,5,.06),(5,6,.045),
    (6,7,.035),(8,9,.06),(9,10,.045),(10,11,.035),(12,13,.09),
    (13,14,.06),(14,15,.045),(16,17,.09),(17,18,.06),(18,19,.045)]

def basis(t,period=.5):
    phase=np.asarray(t)/period*2*np.pi
    return np.stack([np.ones_like(phase),np.cos(phase),np.sin(phase),
        np.cos(2*phase),np.sin(2*phase)],axis=-1)

def evaluate(coefficients,t,period=.5):
    return basis(t,period)@np.asarray(coefficients)

def distances(points,pose,pole_radius=.035):
    values=[]
    for i,j,r in CAPSULES:
        a,b=pose[i,:2],pose[j,:2];d=b-a
        fraction=np.clip((points-a)@d/max(float(d@d),1e-12),0,1)
        values.append(np.linalg.norm(points-a-fraction[...,None]*d,axis=-1)-r-pole_radius)
    return np.min(values,axis=0)

def fit(pose_fn,period=.5):
    times=np.arange(60)/60*period
    poses=[np.asarray(pose_fn(float(t)))for t in times]
    pools=[];wants=[];q=[]
    theta=np.arange(144)/144*2*np.pi
    normals=np.column_stack([np.cos(theta),np.sin(theta)])
    for p in poses:
        k=p[13,:2];u=p[12]-p[13];v=p[14]-p[13]
        inner=u/np.linalg.norm(u)+v/np.linalg.norm(v)
        inner/=np.linalg.norm(inner)
        wanted=k+.12*inner[:2];points=[]
        for target,r in [(12,.09),(14,.06)]:
            for f in np.linspace(.08,.52,12):
                points.extend(k+f*(p[target,:2]-k)+normals*(r+.035+.012))
        points=np.asarray(points);points=points[distances(points,p)>=.008]
        if not len(points):raise ValueError('No capsule-clear support-side candidate')
        pools.append(points);wants.append(wanted)
        score=np.linalg.norm(points-wanted,axis=1)
        if q:score+=3*np.linalg.norm(points-q[-1],axis=1)
        q.append(points[int(np.argmin(score))])
    q=np.array(q)
    for iteration in range(40):
        before=q.copy()
        for i,pool in enumerate(pools):
            centre=(q[(i-1)%60]+q[(i+1)%60])/2
            score=np.sum((pool-centre)**2,axis=1)+.01*np.sum((pool-wants[i])**2,axis=1)
            q[i]=pool[int(np.argmin(score))]
        if np.max(np.linalg.norm(q-before,axis=1))<1e-10:break
    coefficients=np.linalg.lstsq(basis(times,period),q,rcond=None)[0]
    # Preserve the low-frequency curve. A single small global offset finds
    # conservative clearance without jittering the contact every frame.
    checks=np.linspace(0,period,241);checkposes=[np.asarray(pose_fn(float(t)))for t in checks]
    curve=evaluate(coefficients,checks,period)
    grid=np.arange(-.04,.04001,.0025)
    shifts=np.array([(x,y)for x in grid for y in grid])
    allgaps=np.stack([distances(curve[i]+shifts,p)for i,p in enumerate(checkposes)])
    mins=allgaps.min(axis=0);maxs=allgaps.max(axis=0)
    valid=(mins>=.003)&(maxs<=.055)
    if not np.any(valid):
        return {'feasible':False,'reason':'No two-harmonic + <=4cm constant shift clears all capsules while keeping <=5.5cm contact gap',
            'best_unshifted_min_gap':float(min(distances(curve[i:i+1],p)[0]for i,p in enumerate(checkposes)))}
    score=np.linalg.norm(shifts,axis=1)+.25*maxs;score[~valid]=np.inf
    index=int(np.argmin(score));coefficients[0]+=shifts[index]
    final=evaluate(coefficients,checks,period)
    speed=np.linalg.norm(np.diff(final,axis=0)/(period/240),axis=1)
    return {'feasible':True,'period_seconds':period,'coefficients':coefficients.tolist(),
        'coordinate_basis':'Exactly the input pose callable XY; do not subtract an additional donor yaw.',
        'capsules':CAPSULES,'pole_radius_m':.035,'minimum_capsule_gap_m':float(mins[index]),
        'maximum_contact_gap_m':float(maxs[index]),'constant_shift_m':shifts[index].tolist(),
        'peak_offset_speed_per_source_second':float(speed.max()),
        'peak_offset_speed_at_4second_turn':float(speed.max()*period/4),
        'xy_range_m':(final.max(axis=0)-final.min(axis=0)).tolist(),
        'periodic_position_error_m':float(np.linalg.norm(evaluate(coefficients,0,period)-evaluate(coefficients,period,period))),
        'smoothness':'Finite sine/cosine sum: position and every derivative periodic; preserves all input joint directions and lengths.',
        'limitation':'Distances concern proxy capsules only; support gap and appearance need opposing-view review, actual mesh clearance remains untested.'}
