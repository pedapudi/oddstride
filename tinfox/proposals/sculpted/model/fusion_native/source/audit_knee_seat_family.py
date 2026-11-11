"""Edit and restore the seating allowance through both final handed plates."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,math
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);tick=time.monotonic();components={k:next(c for c in d.allComponents if c.partNumber=='CANDIDATE_ks_'+k)for k in ['motor_mount_ring','motor_mount_ring_right']};p=d.userParameters.itemByName('ks_seat_diametral_allowance');original=p.expression;assert abs(p.value)<1e-10
 def snapshot():
  rows={}
  for key,c in components.items():
   assert c.bRepBodies.count==1 and all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);b=c.bRepBodies.item(0);cones=[f for f in b.faces if f.geometry.objectType==core.Cone.classType()];assert len(cones)==9
   rims=[]
   for face in cones:
    circles=[core.Circle3D.cast(e.geometry)for e in face.edges];radii=[x.radius*10 for x in circles if x];assert len(radii)>=2,(key,radii);rims.append(max(radii))
   bb=b.boundingBox;rows[key]={'volume_mm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'bounds_mm':[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]],'seat_radii_mm':rims,'feature_count':c.features.count,'healthy':True}
  return rows
 before=snapshot();changed=None
 try:
  p.expression='0.1 mm';assert d.computeAll();changed=snapshot()
  for key in components:
   assert all(abs(r-3)<1e-6 for r in changed[key]['seat_radii_mm']),(key,changed[key]);assert changed[key]['volume_mm3']<before[key]['volume_mm3']-.1
 finally:
  p.expression=original;assert d.computeAll()
 restored=snapshot()
 for key in components:
  assert all(abs(r-2.95)<1e-6 for r in restored[key]['seat_radii_mm']);assert max(abs(a-b)for a,b in zip(before[key]['bounds_mm'],restored[key]['bounds_mm']))<1e-5;assert abs(before[key]['volume_mm3']-restored[key]['volume_mm3'])<.002
 print(json.dumps({'passed':True,'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'parameter':'ks_seat_diametral_allowance','edit_mm':[0,.1,0],'original_expression':original,'before':before,'changed':changed,'restored':restored,'elapsed_seconds':time.monotonic()-tick,'scope':'Both handed final plate cones propagate the shared process allowance and restore. This does not qualify a physical printed fit.'}))
'''
r=rpc(s,'knee-seat-family-edit-restore',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/knee-seat-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'seconds':record['elapsed_seconds']})
