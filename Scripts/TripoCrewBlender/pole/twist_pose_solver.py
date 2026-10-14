"""Offline arm orientation repair in evaluated component-space transforms."""
import math
from mathutils import Matrix, Vector, Quaternion

def basis(axis, normal):
    x=axis.normalized(); z=normal.normalized(); y=z.cross(x).normalized()
    return Matrix((x,y,z)).transposed()

def twist_about(q, axis):
    axis=axis.normalized()
    if q.w<0:q=-q
    projection=Vector((q.x,q.y,q.z)).dot(axis)
    result=Quaternion((q.w,*(axis*projection)))
    if result.magnitude<1e-6:return Quaternion()
    result.normalize()
    return result

def solve(old, ref, parents, clavicle=True, state=None):
    new={n:m.copy() for n,m in old.items()}
    for side, sign in [('l',1),('r',-1)]:
        c,u,e,h,ut,lt=[n+'_'+side for n in ('clavicle','upperarm','lowerarm','hand','upperarm_twist_01','lowerarm_twist_01')]
        a,b,end=[old[n].translation.copy() for n in (u,e,h)]
        chest=old['spine_03'].to_quaternion()@ref['spine_03'].to_quaternion().inverted()
        up=chest@Vector((0,0,1))
        axis=(b-a).normalized(); elevation=math.asin(max(-1,min(1,axis.dot(up))))
        if clavicle:
            angle=max(0,elevation)*.28
            # Rotate the clavicle toward elevation only when the arm rises above horizontal.
            pivot=old[c].translation; ca=a-pivot
            liftaxis=ca.cross(up).normalized()
            l1=(ref[e].translation-ref[u].translation).length; l2=(ref[h].translation-ref[e].translation).length
            def reachable(theta):
                dist=(end-(pivot+Quaternion(liftaxis,theta)@ca)).length
                return abs(l1-l2)+1e-4<dist<l1+l2-1e-4
            if not reachable(angle):
                low=0.; high=angle
                for _ in range(24):
                    mid=(low+high)*.5
                    if reachable(mid):low=mid
                    else:high=mid
                angle=low
            dq=Quaternion(liftaxis,angle)
            new[c]=Matrix.LocRotScale(pivot,dq@old[c].to_quaternion(),old[c].to_scale())
            na=pivot+dq@ca
            d=(end-na).normalized(); dist=(end-na).length
            if abs(l1-l2)+1e-4<dist<l1+l2-1e-4:
                hint=(b-na)-d*(b-na).dot(d)
                if hint.length>1e-5:
                    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
                    b=na+d*along+hint.normalized()*math.sqrt(max(0,l1*l1-along*along)); a=na
            else:
                new[c]=old[c].copy()
        # An anatomical pole vector keeps the elbow out of the torso while the grip stays fixed.
        l1=(ref[e].translation-ref[u].translation).length
        l2=(ref[h].translation-ref[e].translation).length
        d=(end-a).normalized(); dist=(end-a).length
        raised=max(0,min(1,((end-a).dot(up)+2)/10)); raised=raised*raised*(3-2*raised)
        hint=chest@Vector((sign*(.10+.75*raised),.25,-1+.45*raised)); hint-=d*hint.dot(d)
        original_hint=(old[e].translation-a)-d*(old[e].translation-a).dot(d)
        old_upper=(old[e].translation-old[u].translation).normalized()
        old_lower=(old[h].translation-old[e].translation).normalized()
        bend=math.degrees(math.acos(max(-1,min(1,old_upper.dot(old_lower)))))
        blend=max(0,min(1,(bend-25)/40)); blend=blend*blend*(3-2*blend)
        blend=1. if side=='r' else max(blend,raised)
        if original_hint.length>1e-5 and hint.length>1e-5:
            hint=original_hint.normalized().lerp(hint.normalized(),blend)
        if abs(l1-l2)+1e-4<dist<l1+l2-1e-4 and hint.length>1e-5:
            along=(l1*l1-l2*l2+dist*dist)/(2*dist)
            b=a+d*along+hint.normalized()*math.sqrt(max(0,l1*l1-along*along))
        ru=ref[e].translation-ref[u].translation; rf=ref[h].translation-ref[e].translation
        pu=b-a; pf=end-b
        rn=ru.cross(rf); pn=pu.cross(pf)
        if rn.length<1e-5 or pn.length<1e-5:continue
        uq=(basis(pu,pn)@basis(ru,rn).transposed()).to_quaternion()@ref[u].to_quaternion()
        neutral=(basis(pf,pn)@basis(rf,rn).transposed()).to_quaternion()@ref[e].to_quaternion()
        # Extract grip roll about the forearm, while preserving the hand and finger world transforms.
        hand_deform=old[h].to_quaternion()@ref[h].to_quaternion().inverted()
        neutral_deform=neutral@ref[e].to_quaternion().inverted()
        wrist_roll=twist_about(hand_deform@neutral_deform.inverted(),pf)
        roll=2*math.atan2(Vector((wrist_roll.x,wrist_roll.y,wrist_roll.z)).dot(pf.normalized()),wrist_roll.w)
        if state is not None:
            previous=state.get(side,roll)
            roll=previous+(roll-previous+math.pi)%(2*math.pi)-math.pi
            state[side]=roll
        # A fractional quaternion power jumps when the grip crosses 180 degrees.
        # The caller bounds wrist turn before the final solve. Keep proximal roll
        # small and distribute most of that bounded roll through the distal helper.
        lowq=Quaternion(pf.normalized(),math.sin(roll)*.15)@neutral
        helperq=Quaternion(pf.normalized(),roll*.75)@neutral
        new[u]=Matrix.LocRotScale(a,uq,old[u].to_scale())
        new[e]=Matrix.LocRotScale(b,lowq,old[e].to_scale())
        ud=new[u]@ref[u].inverted()
        helperpos=ud@ref[ut].translation
        helperrot=ud.to_quaternion()@ref[ut].to_quaternion()
        new[ut]=Matrix.LocRotScale(helperpos,helperrot,old[ut].to_scale())
        helper_rest=ref[e].inverted()@ref[lt]
        helperloc=new[e]@helper_rest.translation
        new[lt]=Matrix.LocRotScale(helperloc,helperq@ref[e].to_quaternion().inverted()@ref[lt].to_quaternion(),old[lt].to_scale())
    return new
