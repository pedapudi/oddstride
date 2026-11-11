import cadquery as cq,json,hashlib,math
from pathlib import Path
B=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native');R=B/'snapshots/current-hardware/929c06ab624ed80192157e99ce43165c1416db414902cb0a36c19d6d2ad50da6/exact-reference-step';P=B/'exports/dfma-whole-adoption/DFMA_REAR_LOADED_CUP_RL.step';s=cq.importers.importStep(str(P)).val();checks=[];refs={}
def ref(n,shift):
 p=R/(n+'.step');refs[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'translation_mm':shift};return cq.importers.importStep(str(p)).val().translate(shift)
def hit(n,q):
 v=s.intersect(q).Volume();checks.append({'name':n,'overlap_mm3':v,'passed':abs(v)<1e-5})
hit('rear hip motor at barrel centerX−5',ref('hip_motor',(-5,0,0)))
for sign in [-1,1]:
 for name in ['socket','plug','boot','cable']:hit(f'rear hip port{sign} {name}',ref(f'RL_hip_port_{sign}_{name}',(-5,0,0)))
hit('rear roll motor corrected paired datumX+73.5',ref('roll_motor_-1',(6.2,0,0)))
for a in range(0,360,40):
 x=-5+36.5*math.cos(math.radians(a));z=36.5*math.sin(math.radians(a));shaft=cq.Solid.makeCylinder(1.5,8,cq.Vector(x,-8.9,z),cq.Vector(0,1,0));head=cq.Solid.makeCylinder(2.75,3,cq.Vector(x,-.9,z),cq.Vector(0,1,0));hit(f'hip socket{a}',shaft.fuse(head))
for a in range(0,360,60):
 y=12*math.cos(math.radians(a));z=12*math.sin(math.radians(a));shaft=cq.Solid.makeCylinder(2,25,cq.Vector(52.5,y,z),cq.Vector(1,0,0));head=cq.Solid.makeCylinder(3.5,4,cq.Vector(48.5,y,z),cq.Vector(1,0,0));hit(f'rear roll socket{a}',shaft.fuse(head));tool=cq.Solid.makeCylinder(1.74,148.5,cq.Vector(-100,y,z),cq.Vector(1,0,0));hit(f'rear roll3AF driver{a}',tool)
r={'source':{'path':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'valid':s.isValid(),'solids':len(s.Solids())},'references':refs,'checks':checks,'passed':all(x['passed']for x in checks),'coupling_seat':{'rear_underhead_x_mm':52.5,'head_extent_x_mm':[48.5,52.5],'screw_M4x25_tip_x_mm':77.5,'motor_output_face_x_mm':73.5,'nominal_penetration_mm':4,'driver_approach':'from negativeX before motor/adjacent assembly blocks access'},'limitations':['Nominal reference motor/connector bodies and modeled socket heads, not physical harness bending or tolerance qualification.','Only rear cup mating and coupling orientation checked.']};p=Path(__file__).with_name('rear-cup-mating.json');p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
