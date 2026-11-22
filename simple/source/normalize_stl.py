# SPDX-License-Identifier: MIT
"""Normalize STL vertex seams and discard only triangles collapsed by rounding.

OpenCascade fillet pole triangles can contain near-duplicate vertices that
collapse at float32 STL precision. A 0.00001 mm key merges their shared vertices;
use an existing float32 coordinate as the representative, then require a closed,
consistently oriented two-manifold. This never fills holes or reshapes a surface.
"""
from pathlib import Path
import struct
import numpy as np

def normalize_stl(path):
    path=Path(path);raw=path.read_bytes();count=struct.unpack('<I',raw[80:84])[0]
    dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    assert len(raw)==84+50*count
    original=np.frombuffer(raw[84:],dtype=dtype)['v'].copy();points=original.reshape(-1,3)
    _,first,ids=np.unique(np.round(points.astype(float),5),axis=0,return_index=True,return_inverse=True)
    representatives=points[first];tri_ids=ids.reshape(-1,3)
    mapped=representatives[ids].reshape(-1,3,3)
    displacement=float(np.linalg.norm(mapped.astype(float)-original.astype(float),axis=2).max())
    assert displacement<2e-5
    keep=(tri_ids[:,0]!=tri_ids[:,1])&(tri_ids[:,0]!=tri_ids[:,2])&(tri_ids[:,1]!=tri_ids[:,2])
    triangles=mapped[keep];faces=tri_ids[keep]
    # Some sub-millimetre fillet junctions tessellate as a microscopic, folded
    # two-sided flap. Remove both exactly coincident, opposite-wound triangles
    # only when their area is tiny. They enclose zero volume; no hole is filled.
    _,group,group_counts=np.unique(np.sort(faces,axis=1),axis=0,return_inverse=True,return_counts=True)
    remove=np.zeros(len(faces),dtype=bool);paired=0
    for key in np.flatnonzero(group_counts>1):
        ids2=np.flatnonzero(group==key);assert len(ids2)==2,'Unexpected duplicate STL faces'
        a,b=faces[ids2];assert any(np.array_equal(a,np.roll(b[::-1],shift)) for shift in range(3)),'Duplicate faces are not an opposite-wound pair'
        t=triangles[ids2[0]].astype(float);area=np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))/2
        assert area<1e-4,'Duplicate-face patch too large for microscopic flap cleanup'
        remove[ids2]=True;paired+=2
    triangles=triangles[~remove];faces=faces[~remove]
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    _,edge_ids,counts=np.unique(np.sort(directed,axis=1),axis=0,return_inverse=True,return_counts=True)
    assert np.all(counts==2),'STL has an actual open or nonmanifold edge'
    balances=np.bincount(edge_ids,weights=np.where(directed[:,0]<directed[:,1],1,-1))
    assert np.all(balances==0),'STL has inconsistent winding'
    t=triangles.astype(float);normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);lengths=np.linalg.norm(normals,axis=1)
    assert np.all(lengths>1e-14),'Collinear noncollapsed triangle: inspect the CAD export'
    data=np.zeros(len(t),dtype=dtype);data['v']=triangles;data['normal']=normals/lengths[:,None]
    path.write_bytes(b'Vertex seams normalized at 0.00001 mm; collapsed pole triangles removed'.ljust(80,b' ')+struct.pack('<I',len(t))+data.tobytes())
    return {'vertex_key_tolerance_mm':1e-5,'max_vertex_displacement_mm':displacement,'triangles_before':count,'triangles_after':len(t),'collapsed_triangles_removed':int((~keep).sum()),'opposite_wound_microscopic_flap_triangles_removed':paired,'closed_oriented_manifold':True,'holes_filled':0}
