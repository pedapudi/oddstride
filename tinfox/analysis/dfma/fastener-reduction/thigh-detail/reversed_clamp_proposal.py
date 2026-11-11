import cadquery as cq,json,math,hashlib
from pathlib import Path
R=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native/exports/dfma-architecture-v1');O=Path(__file__).parent
ss={k:cq.importers.importStep(str(R/f'dfma-thigh-{k}-detailed.step')).val()for k in ['primary','secondary']}
rows=[]
for x,z in [(-36,-66),(5,-70)]:
 tool=cq.Solid.makeCylinder(5,72,cq.Vector(x,-15,z),cq.Vector(0,1,0))
 pts=[cq.Vector(x+7/math.sqrt(3)*math.cos(math.radians(a)),53.8,z+7/math.sqrt(3)*math.sin(math.radians(a)))for a in range(0,360,60)]
 wire=cq.Wire.makePolygon(pts+[pts[0]]);nut=cq.Solid.extrudeLinear(wire,[],cq.Vector(0,3.2,0)).cut(cq.Solid.makeCylinder(2,3.2,cq.Vector(x,53.8,z),cq.Vector(0,1,0)))
 innerWasher=cq.Face.makeFromWires(cq.Wire.makeCircle(6,cq.Vector(x,58,z),cq.Vector(0,1,0)),[cq.Wire.makeCircle(2.15,cq.Vector(x,58,z),cq.Vector(0,1,0))])
 # Tangency can duplicate faces, so contact is compared against footprint outside sleeve bore, not internal washer ID.
 footprint=cq.Face.makeFromWires(cq.Wire.makeCircle(6,cq.Vector(x,58.001,z),cq.Vector(0,1,0)),[cq.Wire.makeCircle(4.1,cq.Vector(x,58.001,z),cq.Vector(0,1,0))])
 outerRemaining=[]
 for y in [88.999,89,89.001]:
  sec=ss['secondary'].intersect(cq.Face.makePlane(250,250,(0,y,0),(0,1,0)))
  probe=cq.Face.makeFromWires(cq.Wire.makeCircle(6,cq.Vector(x,y,z),cq.Vector(0,1,0)),[cq.Wire.makeCircle(4.1,cq.Vector(x,y,z),cq.Vector(0,1,0))])
  common=sec.intersect(probe);outerRemaining.append({'y':y,'existing_floor_area_mm2':sum(f.Area()for f in common.Faces())})
 rows.append({'center_xz_mm':[x,z],'socket_proxy':{'OD_mm':10,'axial_interval_mm':[-15,57],'overlap_mm3':{k:s.intersect(tool).Volume()for k,s in ss.items()}},'ordinary_M4_nut':{'AF_mm':7,'thickness_mm':3.2,'interval_y_mm':[53.8,57],'overlap_mm3':{k:s.intersect(nut).Volume()for k,s in ss.items()}},'inner_washer_land_contact_mm2':sum(f.Area()for f in ss['primary'].intersect(footprint).Faces()),'current_outer_floor_probe':outerRemaining})
r={'scope':'Current detailed native thigh; reversed-clamp proposal route only, before revised floor construction','sources':{str(R/f'dfma-thigh-{k}-detailed.step'):hashlib.sha256((R/f'dfma-thigh-{k}-detailed.step').read_bytes()).hexdigest()for k in ss},'rows':rows,'proposed_stack':{'M4x40_underhead_y':90,'tip_y':50,'inner_nut_y':[53.8,57],'projection_mm':3.8,'washers_y':[[57,58],[89,90]],'sleeve_y':[58,89],'sleeve_length_mm':31},'qualification':'Outer Y89 washer floor is not present in old geometry; actual revised floor support needs the new export.'};(O/'reversed-clamp-proposal.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
