"""Smooth, bilateral rest-space mask for the reported posterior-hip collapse.

Coordinates are the preserved Vexa world rest coordinates in metres. This
mask is specific to that asset; do not reuse its dimensions on another body.
"""
import numpy as np

def ramp(value):
    value=np.clip(value,0,1)
    return value*value*(3-2*value)

def posterior_mask(points,centers):
    distance=np.linalg.norm(points[:,None,:]-centers[None,:,:],axis=2).min(axis=1)
    mask=ramp((.30-distance)/.15)
    mask*=ramp((points[:,1]-.005)/.04)
    mask*=ramp((np.abs(points[:,0])-.025)/.035)
    mask*=ramp((points[:,2]-.80)/.10)
    mask*=ramp((1.14-points[:,2])/.09)
    return mask
