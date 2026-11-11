"""Triangle-mesh collision checks using FCL; no cable or load deflection model."""
import json
from itertools import combinations
import numpy as np
import trimesh
from kinematics import ROOT, matrix

class Checker:
    def __init__(self):
        self.data=json.loads((ROOT/'output'/'model.json').read_text())
        self.parts={p['name']:p for p in self.data['parts'] if p['check']}
        self.manager=trimesh.collision.CollisionManager()
        cache={}
        for name,p in self.parts.items():
            key=p['mesh']
            if key not in cache:
                m=self.data['meshes'][key]
                cache[key]=trimesh.Trimesh(vertices=m['vertices'],faces=m['faces'],process=False)
            self.manager.add_object(name,cache[key])

    def excluded(self,a,b):
        p,q=self.parts[a],self.parts[b]
        # Rigidly attached pairs are omitted from motion sweeps; fits need a separate audit.
        if p['leg']==q['leg'] and p['group']==q['group']:return True
        if p['group'] in ['body','mount'] and q['group'] in ['body','mount']:return True
        # Output-rocker and eye joints intentionally share their pin interfaces.
        ends={a.split('_',1)[-1],b.split('_',1)[-1]}
        if p['leg']==q['leg'] and ends in [{'input_crank','pushrod'},{'output_crank','pushrod'}, {'knee_motor','knee_drive_adapter'}, {'hip_motor','hip_hub'}, {'roll_motor','motor_carrier'}]:return True
        return False

    def check(self,poses):
        for name,p in self.parts.items():self.manager.set_transform(name,matrix(p,poses))
        _,pairs=self.manager.in_collision_internal(return_names=True)
        hits=sorted([list(pair) for pair in pairs if not self.excluded(*pair)])
        return {'collision':bool(hits),'pairs':hits,'checked_parts':len(self.parts),
                'scope':'Nominal rigid meshes; designed pin interfaces excluded. No cables, tolerances or deformation.'}

    def clearance(self,poses):
        import fcl
        self.check(poses)
        best=float('inf');closest=None
        for a,b in combinations(self.parts,2):
            if self.excluded(a,b):continue
            d=fcl.distance(self.manager._objs[a]['obj'],self.manager._objs[b]['obj'])
            if d<best:best=float(d);closest=[a,b]
        return {'minimum_distance_mm':best,'pair':closest}

if __name__=='__main__':
    from kinematics import POSES
    c=Checker()
    for name,q in POSES.items():print(name,json.dumps(c.check(q)))
