"""CPU planning contact envelope; never a native rig/skin correction.

Constant placement protects the shoulder origin before two-bone IK. The caller
must author/check entry/exit travel; no hidden elbow branch swap is performed.
"""
import numpy as np

OFFSET = np.array([-.360, .200, .106])
WRIST_STANDOFF = .083

def unit(v):
    return v/max(float(np.linalg.norm(v)),1e-10)

def place(pose, offset=OFFSET, wrist_standoff=WRIST_STANDOFF):
    source=np.asarray(pose,dtype=float)
    result=source+np.asarray(offset)
    shoulder=result[4].copy()
    if np.linalg.norm(shoulder[:2]) < .095:
        raise ValueError('Shoulder endpoint penetrates pole; elbow routing cannot fix root placement')
    wrist=np.r_[unit(shoulder[:2])*wrist_standoff,source[6,2]]
    upper=float(np.linalg.norm(source[5]-source[4]))
    lower=float(np.linalg.norm(source[6]-source[5]))
    reach=float(np.linalg.norm(wrist-shoulder))
    if not abs(upper-lower)+1e-5 < reach < (upper+lower)*.999:
        raise ValueError('Wrist unreachable: adjust whole-body/contact height, never bone lengths')
    axis=unit(wrist-shoulder)
    along=(upper*upper-lower*lower+reach*reach)/(2*reach)
    height=np.sqrt(max(0,upper*upper-along*along))
    reference=source[5]-source[4]
    bend=reference-axis*float(reference@axis)
    if np.linalg.norm(bend)<1e-5:
        raise ValueError('Source elbow plane singular: calibrated temporal reference required')
    result[5]=shoulder+axis*along+unit(bend)*height
    result[6]=wrist
    result[7]=wrist+(source[7]-source[6])
    return result
