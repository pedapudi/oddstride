"""Check the independent case clearance through both native handed hubs."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);parts={k:next(c for c in d.allComponents if c.partNumber=='CANDIDATE_hc_'+k)for k in ['hip_hub','hip_hub_right']};p=d.userParameters.itemByName('hc_case_radial_clearance');old=p.expression;tick=time.monotonic()
 def capture(radius):
  rows={}
  for key,c in parts.items():
   assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);bb=b.boundingBox;faces=[]
   for f in b.faces:
    cy=core.Cylinder.cast(f.geometry)
    if cy and abs(cy.radius*10-radius)<1e-6:faces.append({'radius_mm':cy.radius*10,'min_y_mm':f.boundingBox.minPoint.y*10,'max_y_mm':f.boundingBox.maxPoint.y*10})
   assert len(faces)==3,(key,faces);rows[key]={'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'clearance_faces':faces,'feature_count':c.features.count,'face_count':b.faces.count}
  return rows
 before=capture(39.75)
 try:p.expression='.6 mm';assert d.computeAll();changed=capture(39.85)
 finally:p.expression=old;assert d.computeAll()
 after=capture(39.75)
 for key in parts:
  assert changed[key]['volume_mm3']<before[key]['volume_mm3'];assert abs(after[key]['volume_mm3']-before[key]['volume_mm3'])<.002;assert max(abs(a-b)for a,b in zip(after[key]['bounds_mm'],before[key]['bounds_mm']))<1e-5;assert after[key]['face_count']==before[key]['face_count']
 print(json.dumps({'passed':True,'parameter':'hc_case_radial_clearance','edit_mm':[.5,.6,.5],'before':before,'changed':changed,'restored':after,'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'elapsed_seconds':time.monotonic()-tick,'scope':'Both handed native clearances edit and restore independently of the nominal motor and tube dimensions.'}))
'''
compile(s,'hub_case_family.py','exec');r=rpc(s,'hub-case-family-edit-restore',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/hub-case-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'seconds':record['elapsed_seconds']})
