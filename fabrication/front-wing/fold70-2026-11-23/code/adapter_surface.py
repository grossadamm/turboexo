"""Minimal original knot-vector helper used by splitter_chin_v1.swept_solid.

Extracted unchanged from the original adapter_surface.py; unrelated surface
building and its imports are intentionally excluded.
"""
import numpy as np
from OCP.TColStd import TColStd_Array1OfInteger, TColStd_Array1OfReal


def knot_vector(values):
    unique,mult=np.unique(values,return_counts=True)
    k=TColStd_Array1OfReal(1,len(unique));m=TColStd_Array1OfInteger(1,len(unique))
    for i,(v,n) in enumerate(zip(unique,mult),1):
        k.SetValue(i,v);m.SetValue(i,int(n))
    return k,m
