"""Classify the two flagged whole-robot pairs using the current native solids."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,math,time
def run(_context:str):
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);tm=fusion.TemporaryBRepManager.get();rows=[]
 def reference(name):return next(c for c in d.allComponents if c.attributes.itemByName('Tinfox','BenchReferenceName')and c.attributes.itemByName('Tinfox','BenchReferenceName').value==name).bRepBodies.item(0)
 def moved(body,angle=0,shift=(0,0,0)):
  out=tm.copy(body);m=core.Matrix3D.create();m.setToRotation(math.radians(angle),core.Vector3D.create(0,1,0),core.Point3D.create(0,0,0));m.translation=core.Vector3D.create(*[v/10 for v in shift]);assert tm.transform(out,m);return out
 def overlap(name,a,b,conditions):
  target=tm.copy(a);before=target.volume*1000;assert tm.booleanOperation(target,b,fusion.BooleanTypes.DifferenceBooleanType);after=target.volume*1000;volume=before-after;assert volume>=-1e-5;rows.append({'pair':name,'overlap_mm3':max(0,volume),'target_volume_before_mm3':before,'target_volume_after_mm3':after,'conditions':conditions,'classification':'positive solid interference'if volume>1e-5 else'no positive solid interference'})
 overlap(['FL_carrier_closure_bolt_215','FL_pod_tie_210'],reference('FL_carrier_closure_bolt_215'),moved(reference('Pod M3x60 screw 210'),-10),{'hip_deg':-10,'roll_deg':0,'frame':'Common bench pitch frame. Closure stays fixed; tie rotates about Y. Equal world translations cancel.'})
 chassis=authoring_document(app,'chassis');cd=fusion.Design.cast(chassis.products.itemByProductType('DesignProductType'));beam=next(c for c in cd.allComponents if c.partNumber=='chassis_beam_102').bRepBodies.item(0);bb=beam.boundingBox;bounds=[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]];assert abs(bounds[1]-93)<.01 and abs(bounds[4]-108.5)<.01,bounds
 overlap(['FL_roll_stator_bolt_0','chassis_beam_102'],moved(reference('FL_roll_stator_bolt_0'),shift=(190,68,0)),beam,{'fixed_mount':True,'bench_to_whole_translation_mm':[190,68,0],'chassis_version':chassis.dataFile.versionNumber,'chassis_modified':chassis.isModified,'beam_bounds_mm':bounds})
 print(json.dumps({'leg_version':doc.dataFile.versionNumber,'leg_upload_complete':doc.dataFile.isComplete,'leg_modified':doc.isModified,'checks':rows,'checker':'Native temporary BRep exact Boolean difference; source document geometry is not altered.','whole_source_target':'1ef89695619c6ff8853d0ac458b55eaccebfcc65ad6622c614fbe259ceae8c2f','scope':'Two flagged FL pairs only; no motion or strength release.'}))
'''
r=rpc(s,'whole-hardware-native-suspects',timeout=120,read_only=True);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/whole-hardware-native-suspects.json').write_text(json.dumps(record,indent=2));print(record)
