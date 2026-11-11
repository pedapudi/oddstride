"""Promote a source-qualified compact bezel inside the existing Head design."""
import json,hashlib
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
export=ROOT/'exports/sensor_bezel-intent.step';sha=hashlib.sha256(export.read_bytes()).hexdigest()
for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
 audit=json.loads((ROOT/f'audits/sensor_bezel-intent-{suffix}.json').read_text());assert audit['native_step_sha256']==sha and audit[gate]
script='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:cwZZGJRSR5aVlwkk9TcEUA'
 d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_sensor_bezel');c=occ.component
 assert c.features.count==9 and c.sketches.count==8 and c.bRepBodies.count==1
 def volume():return c.bRepBodies.item(0).getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000
 tests=[]
 for name,value in [('bezel_outer_width','176 mm'),('bezel_outer_height','48 mm'),('bezel_pocket_depth','1.9 mm'),('head_face_vertical_crown','11 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression;before=volume()
  try:
   p.expression=value;assert d.computeAll();changed=volume();issues=[f.name for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]
  finally:p.expression=old;d.computeAll()
  restored=volume();test={'parameter':name,'changed_expression':value,'baseline_mm3':before,'changed_mm3':changed,'restored_mm3':restored,'passed':not issues and abs(changed-before)>.01 and abs(before-restored)<.001};tests.append(test);assert test['passed'],test
 old=next(o for o in root.occurrences if o.component.partNumber=='sensor_bezel');old_name=old.name;assert old.deleteMe()
 c.partNumber='sensor_bezel';c.name='Sensor bezel';occ.isLightBulbOn=True
 c.attributes.add('Tinfox','ConstructionStatus','Compact native construction; frozen V0 surface and section gates passed; four dimensional edits restored.')
 c.attributes.add('Tinfox','QualifiedExportSHA256',EXPORT_SHA)
 # These dimensions arrived with the original Head copy but drive no Head feature.
 unused=[p for p in d.userParameters if p.name.startswith(('electronics_shelf_','lidar_lid_','power_button_'))]
 removed=[]
 for p in unused:
  name=p.name;assert p.deleteMe();removed.append(name)
 body=c.bRepBodies.item(0);appearance=body.appearance
 props=[(p.id,p.name,p.objectType) for p in appearance.appearanceProperties] if appearance else []
 assert doc.save('Replace dense bezel lofts with dimensional compound sweeps and analytic rounded contours; preserve qualified V0 shape.')
 print(json.dumps({'part':'sensor_bezel','head_version':doc.dataFile.versionNumber,'saved':True,'removed_reference':old_name,'removed_unused_parameters':removed,'features':c.features.count,'sketches':c.sketches.count,'edits':tests,'body_appearance_properties':props,'root_parts':[o.component.partNumber for o in root.occurrences],'source_of_truth_changed':False}))
'''.replace('EXPORT_SHA',repr(sha))
r=rpc(script,'sensor-bezel-intent-qualification',timeout=90);assert r[0]['success'],r
record=json.loads(r[0]['message']);(ROOT/'audits/sensor-bezel-intent-qualification.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
