"""Measure the motor-plate service path and list unresolved purchased-hardware fits."""
import hashlib,json
import cadquery as cq
from kinematics import ROOT
from build import motor_envelope
out=ROOT/'output';steps=out/'step-parts'
def load(n):return cq.importers.importStep(str(steps/(n+'.step'))).val()
main=load('thigh_inner');cap=load('thigh_outer');plate=load('motor_mount_ring');hub=load('hip_hub')
motor_plate=cq.Compound.makeCompound([motor_envelope((0,54.4,0)),plate])
paths=[]
for label,shape,obstacles in [('Remove outer thigh with integral service ring',cap,[main]),('Insert stator plate with outer thigh removed',plate,[main]),('Insert motor envelope and stator plate',motor_plate,[main,hub])]:
 samples=[]
 for d in [0,.05,.1,.3,.5,1,2,3,5,8,12,20,30,45,60]:
  moving=shape.translate((0,d,0))
  samples.append({'offset_mm':d,'overlap_mm3':sum(max(0,moving.intersect(o).Volume()) for o in obstacles)})
 paths.append({'name':label,'axis':[0,1,0],'samples':samples,'passed':all(s['overlap_mm3']<1e-4 for s in samples)})
assert all(p['passed'] for p in paths),paths
report={'model_sha256':hashlib.sha256((out/'model.json').read_bytes()).hexdigest(),'paths':paths,'split_gap_mm':main.distance(cap),'closed_overlap_mm3':max(0,main.intersect(cap).Volume()),'scope':'Exact-solid axial paths against the inner cradle, and motor insertion against the hip hub. Crank, axial ties, knee shaft retention and wiring must be released first; the outer thigh carries the service ring. Motor fasteners, hand access, bearing retention and complete loaded assembly are not qualified.','open_interfaces':['Roll bearing retaining flanges and preload','Knee axle clamp preload and fits; outer bearing capture is integral with the structural shin','Pushrod pin, bushing and printed retaining lip load/fatigue qualification','Axial motor ties: final screw length, washer stack and accessible nut retention','Foot attachment and cable routing']}
(out/'limb-assembly-audit.json').write_text(json.dumps(report,indent=2));print('Integrated outer thigh and stator plate axial paths clear; remaining interfaces explicitly open.')
