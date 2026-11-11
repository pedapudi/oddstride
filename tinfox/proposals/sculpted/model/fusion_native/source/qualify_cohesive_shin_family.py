"""Exercise physical shin dimensions and linked shell splits, then restore them."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='''import adsk.core as core,adsk.fusion as fusion,json,math,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;components={o.component.partNumber:o.component for o in root.occurrences if o.component.partNumber.startswith('CANDIDATE_cohesive_shin_')};assert len(components)==3;master=components['CANDIDATE_cohesive_shin_master']
 def state():
  rows={}
  for key,c in components.items():
   assert c.bRepBodies.count==1;body=c.bRepBodies.item(0);box=body.boundingBox;rows[key]={'bounds_mm':[v*10 for v in box.minPoint.asArray()+box.maxPoint.asArray()],'volume_mm3':body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume*1000,'issues':[(f.name,f.errorOrWarningMessage) for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]}
  return rows
 def cylinders():
  rows=[]
  for f in master.bRepBodies.item(0).faces:
   geom=core.Cylinder.cast(f.geometry)
   if geom and abs(geom.axis.y)>.999:rows.append({'radius_mm':geom.radius*10,'x_mm':geom.origin.x*10,'z_mm':geom.origin.z*10})
  return rows
 def planes_y():
  return [core.Plane.cast(f.geometry).origin.y*10 for f in master.bRepBodies.item(0).faces if core.Plane.cast(f.geometry) and abs(core.Plane.cast(f.geometry).normal.y)>.999 and f.area>1]
 baseline=state();assert not any(r['issues'] for r in baseline.values());tests=[]
 for name,value in [('lc_shank_foot_center','158 mm'),('lc_bearing_od','30 mm'),('lc_shell_wall','4.5 mm'),('lc_crank_radius','30 mm'),('lc_shin_split_offset','17 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression;before=state()
  try:
   p.expression=value;assert d.computeAll();changed=state();evidence={}
   if name=='lc_shank_foot_center':
    evidence={'minimum_z_mm':{k:r['bounds_mm'][2] for k,r in changed.items()},'expected_mm':-146};response=all(abs(r['bounds_mm'][2]+146)<.002 for r in changed.values())
   elif name=='lc_bearing_od':
    seats=[r for r in cylinders() if abs(r['radius_mm']-15)<1e-5 and abs(r['x_mm'])<1e-5 and abs(r['z_mm'])<1e-5];evidence={'bearing_radius_mm':15,'matching_seat_faces':seats};response=len(seats)>=2
   elif name=='lc_shell_wall':
    positions=planes_y();evidence={'planar_faces_y_mm':positions,'expected_pocket_walls_mm':[55.5,80.5]};response=all(any(abs(y-target)<.002 for y in positions) for target in [55.5,80.5])
   elif name=='lc_crank_radius':
    expected=[30*math.cos(math.radians(-78)),-30*math.sin(math.radians(-78))];faces=[r for r in cylinders() if abs(r['radius_mm']-3.05)<1e-5];evidence={'expected_pin_xz_mm':expected,'pin_cylinders':faces};response=bool(faces) and all(abs(r['x_mm']-expected[0])<1e-5 and abs(r['z_mm']-expected[1])<1e-5 for r in faces)
   else:
    a=changed['CANDIDATE_cohesive_shin_inner']['bounds_mm'][4];b=changed['CANDIDATE_cohesive_shin_outer']['bounds_mm'][1];evidence={'inner_outer_y_mm':a,'outer_inner_y_mm':b,'expected_mm':68};response=abs(a-68)<.002 and abs(b-68)<.002
  finally:p.expression=old;assert d.computeAll()
  restored=state();errors={k:{'bounds_mm':max(abs(a-b) for a,b in zip(r['bounds_mm'],before[k]['bounds_mm'])),'volume_mm3':abs(r['volume_mm3']-before[k]['volume_mm3'])} for k,r in restored.items()};passed=response and not any(r['issues'] for r in changed.values()) and not any(r['issues'] for r in restored.values()) and all(r['bounds_mm']<.002 and r['volume_mm3']<2e-4*before[k]['volume_mm3'] for k,r in errors.items());row={'parameter':name,'test':value,'restored':old,'evidence':evidence,'restore_errors':errors,'passed':passed};tests.append(row);assert passed,row
 paths=[];folder=os.path.join(tempfile.gettempdir(),'tinfox-native')
 for occ in root.occurrences:
  c=occ.component
  if c.partNumber not in components:continue
  label=c.partNumber.replace('CANDIDATE_cohesive_shin_','cohesive-shin-');occ.isLightBulbOn=True;c.bRepBodies.item(0).isLightBulbOn=True;path=os.path.join(folder,label+'-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));paths.append(path)
  if c==master:occ.isLightBulbOn=False
 print(json.dumps({'tests':tests,'passed':True,'paths':paths,'saved':False,'restore_validation':'Healthy native features, quantitative dimensional responses and restored bounds/mass within stated numerical uncertainty. Restored STEP exports require independent full-boundary/section checks.','scope':'Candidate cohesive shin family only; no loaded strength or whole-robot validation.'}))
'''
r=rpc(s,'cohesive-shin-family-edits',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/cohesive-shin-family-edits.json').write_text(json.dumps(record,indent=2))
for p in record['paths']:fetch(p,Path(p).name)
print({'passed':record['passed'],'tests':[r['parameter'] for r in record['tests']]})
