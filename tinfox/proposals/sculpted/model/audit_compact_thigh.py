"""Check service paths for the stepped motor-cup thigh candidate."""
import hashlib,json,sys
import cadquery as cq
import build as b
import service_design as sd
from kinematics import ROOT
OUT=__import__('pathlib').Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output/compact-thigh-work'
data=json.loads((OUT/'model.json').read_text())
inner=cq.importers.importStep(str(OUT/'step/thigh_inner.step')).val()
outer=cq.importers.importStep(str(OUT/'step/thigh_outer.step')).val()
motor=b.motor_envelope((0,54.4,0))
for sign in [-1,1]:motor=motor.fuse(sd.connector_parts(54.4,sign)[0])
plate_path=OUT/'step/motor_mount_ring.step'
if not plate_path.exists():plate_path=ROOT/'output/service-design/step/motor_mount_ring.step'
plate=cq.importers.importStep(str(plate_path)).val()
rows=[]
def fit(name,a,c):
    common=a.intersect(c)
    v=max(0,sum(s.Volume() for s in common.Solids()))
    rows.append({'interface':name,'overlap_mm3':v,'passed':v<.001})
for dy in [0,.1,.5,1,2,4,8,12,20,30,40,60,80]:
    fit('Outer shell removal '+str(dy)+' mm',inner,outer.translate((0,dy,0)))
    fit('Outer shell / fixed motor and sockets '+str(dy)+' mm',motor,outer.translate((0,dy,0)))
for dy in [0,.1,.5,1,2,4,6,8,10,12,16,20,24,28,32,36,40,50,60,80]:
    fit('Motor with bare sockets insertion '+str(dy)+' mm',inner,motor.translate((0,dy,0)))
    fit('Stator plate insertion '+str(dy)+' mm',inner,plate.translate((0,dy,0)))
for sign in [-1,1]:
    socket,plug,boot,clearance,withdrawal=sd.connector_parts(54.4,sign)
    center,tangent,axial,radial=sd.port_frame(54.4,sign)
    for travel in [0,2,5,10,20,30]:
        fit('Plug radial insertion '+str(sign)+' / '+str(travel),inner.fuse(outer),plug.translate(tuple(radial*travel)))
    fit('Cable boot '+str(sign),inner.fuse(outer),boot)
report={'model_sha256':hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),'checks':rows,'passed':all(r['passed'] for r in rows),'scope':'Nominal exact-solid service paths. Outer half removed before sliding the motor and mounting plate outwards. Socket envelopes use the existing provisional connector geometry. Flexible cables, tools and print fit remain unqualified.'}
(OUT/'motor-cup-assembly.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'checks':len(rows),'failed':[r for r in rows if not r['passed']]}),flush=True)
