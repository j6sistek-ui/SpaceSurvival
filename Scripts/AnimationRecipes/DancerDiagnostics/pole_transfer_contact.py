"""Private finite hand-to-leg transfer proposal, not native animation.

Whole-body Y corridor clears the approaching folded leg; the hand slides on
the pole until 48.90s, then departs on a polar route. This is not a fixed grip.
"""
import math
import numpy as np

def unit(v):
    v=np.asarray(v,dtype=float);length=float(np.linalg.norm(v))
    if not np.isfinite(v).all() or length<1e-10:
        raise ValueError('Degenerate transfer direction needs a calibrated guide')
    return v/length
def smooth(t):
    t=float(np.clip(t,0,1));return t*t*(3-2*t)
def clip_height(x,limit,width=.012):
    sign=1 if x>=0 else -1;v=abs(x);start=max(0,limit-width)
    if v<=start:return x
    if v>=limit:return sign*limit
    u=(v-start)/width
    return sign*(start+width*(u+u*u-u*u*u))
def rotate_z(v,a):
    c,s=math.cos(a),math.sin(a)
    return np.array([c*v[0]-s*v[1],s*v[0]+c*v[1],v[2]])

def direction_arc(a,b,u):
    """Spherical interpolation with an explicit antipodal diagnostic."""
    a,b=unit(a),unit(b);dot=float(np.clip(a@b,-1,1))
    if dot>1-1e-10:return unit(a*(1-u)+b*u)
    if dot<-1+1e-8:raise ValueError('Antipodal finger arc needs a calibrated guide')
    angle=math.acos(dot)
    return (a*math.sin((1-u)*angle)+b*math.sin(u*angle))/math.sin(angle)

def released_finger(held,outgoing,outward,u):
    # A direct normalized blend nearly cancels opposite directions, snapping
    # the finger near the midpoint. Route a spherical quadratic through the
    # outward direction instead; the held and outgoing endpoints stay exact.
    first=direction_arc(held,outward,u)
    second=direction_arc(outward,outgoing,u)
    return direction_arc(first,second,u)

def place(pose,t,entry):
    original=np.asarray(pose,dtype=float);p=original.copy()
    u=float(np.clip((t-47.5)/1.5,0,1))
    # .31259m is the measured minimum amplitude for a .18m shoulder-axis
    # corridor on the audited transfer. Rounded up, not an elbow gain sweep.
    p[:,1]-=.315*math.sin(math.pi*u)**2
    shoulder=p[4];radius=float(np.linalg.norm(shoulder[:2]));az=math.atan2(shoulder[1],shoulder[0])
    upper=float(np.linalg.norm(p[5]-p[4]));lower=float(np.linalg.norm(p[6]-p[5]));limit=(upper+lower)*.985
    horizontal=abs(radius-.083)
    if horizontal>=limit:raise ValueError('Holding wrist unreachable horizontally')
    dz=clip_height(original[6,2]-shoulder[2],math.sqrt(limit*limit-horizontal*horizontal))
    held=np.array([.083*math.cos(az),.083*math.sin(az),shoulder[2]+dz])
    f=smooth((t-48.9)/.6)
    outgoing=p[6].copy();outaz=math.atan2(outgoing[1],outgoing[0]);angle_delta=(outaz-az+math.pi)%(2*math.pi)-math.pi
    wr=.083*(1-f)+float(np.linalg.norm(outgoing[:2]))*f;wa=az+angle_delta*f
    wrist=np.array([wr*math.cos(wa),wr*math.sin(wa),held[2]*(1-f)+outgoing[2]*f])
    reach=float(np.linalg.norm(wrist-shoulder))
    if not abs(upper-lower)+1e-5<reach<(upper+lower)*.999:
        raise ValueError('Release wrist unreachable')
    axis=unit(wrist-shoulder);ref=original[5]-original[4];bend=ref-axis*float(ref@axis)
    if np.linalg.norm(bend)<1e-5:raise ValueError('Source elbow plane singular')
    along=(upper*upper-lower*lower+reach*reach)/(2*reach);height=math.sqrt(max(0,upper*upper-along*along))
    p[5]=shoulder+axis*along+unit(bend)*height;p[6]=wrist
    initial_angle=math.atan2(entry[6,1],entry[6,0]);held_finger=rotate_z(entry[7]-entry[6],az-initial_angle)
    outward=np.array([math.cos(az),math.sin(az),0.])
    finger=released_finger(held_finger,original[7]-original[6],outward,f)*np.linalg.norm(original[7]-original[6])
    p[7]=wrist+finger
    return p

def place_calibrated(pose,t,entry):
    """Keep the bridge elbow outside the pole; blend back to source endpoints."""
    p=place(pose,t,entry);source=np.asarray(pose)
    shoulder=p[4];wrist=p[6];axis=unit(wrist-shoulder)
    ref=source[5]-source[4];ref=unit(ref-axis*float(ref@axis))
    # Fixed positive-Z bend guide, projected into the current reach plane.
    # A radial-outward guide flips when the wrist crosses shoulder height;
    # this calibrated reference does not change sign at that event.
    guide=np.array([0.,0.,1.])
    outer=unit(guide-axis*float(guide@axis))
    angle=math.atan2(float(axis@np.cross(ref,outer)),float(ref@outer))
    weight=smooth((t-47)/.5)*(1-smooth((t-48.7)/.8))
    a=angle*weight;bend=ref*math.cos(a)+np.cross(axis,ref)*math.sin(a)
    upper=float(np.linalg.norm(source[5]-source[4]));lower=float(np.linalg.norm(source[6]-source[5]))
    reach=float(np.linalg.norm(wrist-shoulder));along=(upper*upper-lower*lower+reach*reach)/(2*reach)
    height=math.sqrt(max(0,upper*upper-along*along))
    p[5]=shoulder+axis*along+bend*height
    return p
