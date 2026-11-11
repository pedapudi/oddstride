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
        if p['leg']==q['leg'] and ends in [{'knee_motor','knee_drive_adapter'}, {'knee_motor','input_crank'}, {'hip_motor','hip_hub'}, {'roll_motor','motor_carrier'}, {'roll_motor','motor_carrier_trunnion'}]:return True
        return False

    def check(self,poses):
        for name,p in self.parts.items():self.manager.set_transform(name,matrix(p,poses))
        _,pairs=self.manager.in_collision_internal(return_names=True)
        hits=sorted([list(pair) for pair in pairs if not self.excluded(*pair)])
        return {'collision':bool(hits),'pairs':hits,'checked_parts':len(self.parts),
                'scope':'Nominal rigid meshes; designed pin interfaces excluded. No cables, tolerances or deformation.'}

    def precision_interface(self,a,b):
        p,q=self.parts[a],self.parts[b]
        if p['leg']!=q['leg'] or not p['leg']:return False
        names={a.split('_',1)[-1],b.split('_',1)[-1]}
        if names.intersection({'knee_axle','knee_inner_spacer'}) and names.intersection({'shin_inner','shin_outer'}):return True
        if 'pushrod' in names and names.intersection({'input_pin','output_pin','input_crank','shin_inner','shin_outer'}):return True
        for end,carrier in [('input','input_crank'),('output','shin_inner'),('output','shin_outer')]:
            if any(n.startswith('rod_bush_'+end) for n in names) and (carrier in names or end+'_pin' in names):return True
        return False

    def clearance(self,poses):
        import fcl
        self.check(poses)
        best=float('inf');closest=None
        for a,b in combinations(self.parts,2):
            if self.excluded(a,b) or self.precision_interface(a,b):continue
            d=fcl.distance(self.manager._objs[a]['obj'],self.manager._objs[b]['obj'])
            if d<best:best=float(d);closest=[a,b]
        return {'minimum_distance_mm':best,'pair':closest}

if __name__=='__main__':
    from kinematics import POSES
    c=Checker()
    for name,q in POSES.items():print(name,json.dumps(c.check(q)))
