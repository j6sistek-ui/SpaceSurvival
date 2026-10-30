"""G2-only authored smooth leg envelope; no universal/medical joint-limit claim."""
import math
from mathutils import Matrix, Quaternion, Vector

def corrected_pose(original, rest, descendants):
 pose={n:m.copy() for n,m in original.items()}
 body=original['pelvis'].to_quaternion()@rest['pelvis'].to_quaternion().inverted()
 rows=[]
 def smooth(x):
  x=max(0.,min(1.,x));return x*x*(3-2*x)
 for side,sign in [('l',1),('r',-1)]:
  name='thigh_'+side;pivot=original[name].translation
  direction=body.inverted()@(original['calf_'+side].translation-pivot).normalized()
  angle=math.degrees(math.atan2(direction.y,-direction.z))
  target_angle=angle if angle<=5 else 5+5*math.tanh((angle-5)/5)
  posterior=1.0  # Avoid the narrow activation band that caused a 37-degree frame jump.
  lateral=math.asin(max(-1,min(1,direction.x)))
  own_lateral=sign*math.degrees(lateral)
  bound=own_lateral if own_lateral>=-5 else -5-5*math.tanh((-own_lateral-5)/5)
  target_lateral=math.radians(sign*(own_lateral+(bound-own_lateral)*posterior))
  target=Vector((math.sin(target_lateral),math.sin(math.radians(target_angle))*math.cos(target_lateral),-math.cos(math.radians(target_angle))*math.cos(target_lateral)))
  q=(body@direction).rotation_difference(body@target)
  transform=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)
  for n in descendants[name]:pose[n]=transform@original[n]
  relative=body.inverted()@pose[name].to_quaternion()@rest[name].to_quaternion().inverted()
  if relative.w<0:relative.negate()
  axis=(rest['calf_'+side].translation-rest[name].translation).normalized()
  axial=axis*Vector((relative.x,relative.y,relative.z)).dot(axis)
  twist=Quaternion((relative.w,*axial));twist.normalize()
  if twist.w<0:twist.negate()
  signed=math.degrees(twist.angle)*(1 if Vector((twist.x,twist.y,twist.z)).dot(axis)>=0 else -1)
  bounded=signed if abs(signed)<=15 else math.copysign(15+5*math.tanh((abs(signed)-15)/5),signed)
  new_twist=Quaternion(axis,math.radians(signed+(bounded-signed)*posterior))
  desired=relative@twist.inverted()@new_twist
  q2=body@desired@relative.inverted()@body.inverted()
  transform2=Matrix.Translation(pivot)@q2.to_matrix().to_4x4()@Matrix.Translation(-pivot)
  for n in descendants[name]:pose[n]=transform2@pose[n]
  rows.append({'side':side,'before_deg':angle,'after_deg':target_angle,'adduction_before_deg':-own_lateral,'adduction_after_deg':-sign*math.degrees(target_lateral),'twist_before_deg':signed,'twist_after_deg':signed+(bounded-signed)*posterior})
 return pose,rows
