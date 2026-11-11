"""Qualify the common native shin master and its full-width bearing interfaces."""
import json
from pathlib import Path
import cadquery as cq
from audit_part import audit,cylinders,volume
from audit_sections import audit as sections
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'snapshots/cohesive-limb';a=cq.importers.importStep(str(src/'step/shin_inner.step')).val();b=cq.importers.importStep(str(src/'step/shin_outer.step')).val();s=a.fuse(b).clean();path=src/'intent/shin-master.step';cq.exporters.export(s,str(path));clearance=cq.importers.importStep(str(src/'intent/continuous-rod-clearance.step')).val();record={'id':'cohesive_shin_master','source_step':str(path.relative_to(ROOT)),'functional_clearance_cylinders':cylinders(clearance),'functional_clearance_proof':'audits/cohesive-rod-envelope-equivalence.json'};audit('cohesive_shin_master','cohesive-shin-master',record);sections('cohesive_shin_master','cohesive-shin-master',record)
n=cq.importers.importStep(str(ROOT/'exports/cohesive-shin-master.step')).val()
def cyl(r,y,h,x=0,z=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(0,1,0))
def ring(r0,r1,y,h):return cyl(r1,y,h).cut(cyl(r0,y-.1,h+.2))
checks=[]
for name,region,expected in [('inner bearing bore',cyl(13.99,53.01,7.98),'empty'),('outer bearing bore',cyl(13.99,77.01,7.98),'empty'),('inner full-width seat backing',ring(14.05,15,53.05,7.9),'solid'),('outer full-width seat backing',ring(14.05,15,77.05,7.9),'solid'),('inner axial shoulder',ring(8.25,13.95,61.05,5.4),'solid'),('outer axial shoulder',ring(8.25,13.95,73.55,3.4),'solid')]:
 if 'shoulder' in name:
  for x in [-12.7,12.7]:region=region.cut(cyl(1.35,60,18,x))
 errors=[abs(volume(shape.intersect(region) if expected=='empty' else region.cut(shape))[0]) for shape in [s,n]];checks.append({'check':name,'expect':expected,'source_error_volume_mm3':errors[0],'native_error_volume_mm3':errors[1],'pass':errors[1]<.001})
result={'checks':checks,'passed':all(r['pass'] for r in checks),'scope':'Entire three-dimensional seat bands and axial-stop volumes; excludes deliberate extraction holes with 0.05 mm margin. Supplements source/full-surface comparison.'};(ROOT/'audits/cohesive-shin-bearing-support.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
