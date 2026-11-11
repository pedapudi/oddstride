"""Prove meaningful thigh dimensions propagate through the shared native shells."""
import json
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);targets=[o.component for o in d.rootComponent.occurrences if o.component.partNumber.startswith('CANDIDATE_cohesive_thigh_')];assert len(targets)==3;rows=[]
 def inspect():
  result={}
  for c in targets:
   assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),[(f.name,f.healthState) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];b=c.bRepBodies.item(0);cylinders=[]
   for face in b.faces:
    cyl=core.Cylinder.cast(face.geometry)
    if cyl:cylinders.append({'radius_mm':cyl.radius*10,'origin_mm':cyl.origin.asArray()})
   result[c.partNumber]={'bounds_mm':[v*10 for v in b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()],'volume_cm3':b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume,'cylinders':cylinders}
  return result
 baseline=inspect()
 for name,value in [('lc_thigh_length','180 mm'),('lc_shell_wall','4.5 mm'),('lc_thigh_outer_y','102 mm'),('lc_shin_split_offset','17 mm'),('lc_stop_axial_gap','0.5 mm')]:
  parameter=d.userParameters.itemByName(name);old=parameter.expression
  try:
   parameter.expression=value;assert d.computeAll();changed=inspect()
   if name=='lc_thigh_length':
    for key,row in changed.items():assert abs(row['bounds_mm'][2]-baseline[key]['bounds_mm'][2]+10)<.01,(key,row)
   elif name=='lc_thigh_outer_y':assert abs(changed['CANDIDATE_cohesive_thigh_outer']['bounds_mm'][4]-102)<.001
   elif name=='lc_shin_split_offset':assert abs(changed['CANDIDATE_cohesive_thigh_inner']['bounds_mm'][4]-68)<.001 and abs(changed['CANDIDATE_cohesive_thigh_outer']['bounds_mm'][1]-68)<.001
   else:assert any(abs(row['volume_cm3']-baseline[key]['volume_cm3'])>.01 for key,row in changed.items())
  finally:parameter.expression=old;assert d.computeAll()
  restored=inspect();assert all(max(abs(a-b) for a,b in zip(row['bounds_mm'],baseline[key]['bounds_mm']))<.002 and abs(row['volume_cm3']-baseline[key]['volume_cm3'])<.01 for key,row in restored.items());rows.append({'parameter':name,'changed_expression':value,'changed':changed,'restored':True,'passed':True})
 print(json.dumps({'tests':rows,'passed':True,'scope':'Shared thigh exterior, wall, shell split and axial stops. Existing whole-robot occurrence transforms and other legacy parts are not yet a scalable assembly.','saved':False}))
'''
r=rpc(s,'cohesive-thigh-family-edits',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-thigh-family-edits.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'tests':len(record['tests'])})
