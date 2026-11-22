# SPDX-License-Identifier: MIT
"""Measure adjacent-face normal jumps along the exposed CASE9 rim."""
import math
from collections import defaultdict

def rim_edges(shape,center=(96.5,19),bore_radius=3.1,deck_z=5.5,hood_z=13.4):
    faces=defaultdict(list);edges={}
    for face in shape.Faces():
        for edge in face.Edges():
            key=edge.hashCode();edges[key]=edge
            if not any(face.isSame(f) for f in faces[key]):faces[key].append(face)
    records=[]
    for key,edge in edges.items():
        bounds=edge.BoundingBox();point=edge.positionAt(.5);radius=math.hypot(point.x-center[0],point.y-center[1])
        if not(bore_radius-.15<radius<bore_radius+.45 and bounds.zmin>=deck_z-.45 and bounds.zmax>=deck_z-.01 and bounds.zmax<hood_z+.1):continue
        if len(faces[key])!=2:continue
        a,b=[f.normalAt(point) for f in faces[key]]
        angle=math.degrees(math.acos(max(-1,min(1,a.dot(b)))))
        records.append({'edge':edge,'normal_jump_deg':angle,'midpoint_mm':point.toTuple(),'edge_length_mm':edge.Length()})
    return records

def rim_report(shape,**kwargs):
    rows=rim_edges(shape,**kwargs)
    return {'sampled_edges':len(rows),'max_adjacent_normal_jump_deg':max((r['normal_jump_deg'] for r in rows),default=180),
            'samples':[{k:v for k,v in row.items() if k!='edge'} for row in rows],
            'scope':'Midpoint of every two-face edge in the CASE9 exposed-rim radial/height band; excludes screw bearing and concealed cavity edges'}
