"""Create the linked opposite rail and test paired frame dimensional edits."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'audits/frame-intent-right-rail-geometry.json').read_text())['geometric_gate_passed']
s=(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');assert doc==app.activeDocument;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();source=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_chassis_beam_102');assert not any(c.partNumber=='CANDIDATE_chassis_beam_-102' for c in d.allComponents);tick=time.monotonic();occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Shared-datum left motor rail';c.partNumber='CANDIDATE_chassis_beam_-102';objects=core.ObjectCollection.create();objects.add(source.bRepBodies.item(0));copy=c.features.copyPasteBodies.add(objects);copy.name='Parametric reference to the right rail';assert copy.isParametric;original=copy.bodies.item(0);objects=core.ObjectCollection.create();objects.add(original);inp=c.features.mirrorFeatures.createInput(objects,c.xZConstructionPlane);inp.isCombine=False;feature=c.features.mirrorFeatures.add(inp);feature.name='Opposed left rail';c.features.removeFeatures.add(original).name='Keep the left rail only';assert c.bRepBodies.count==1;occ.isLightBulbOn=False;parts={'right':source,'left':c,'brace':next(c for c in d.allComponents if c.partNumber=='chassis_lower_brace'),'deck':next(c for c in d.allComponents if c.partNumber=='electronics_shelf')}
 def measure():
  rows={}
  for key,c0 in parts.items():
   b=c0.bRepBodies.item(0);box=b.boundingBox;rows[key]={'bounds':[v*10 for v in [box.minPoint.x,box.minPoint.y,box.minPoint.z,box.maxPoint.x,box.maxPoint.y,box.maxPoint.z]],'volume_mm3':b.volume*1000,'cylinders':[]}
   for face in b.faces:
    cy=core.Cylinder.cast(face.geometry)
    if cy:rows[key]['cylinders'].append({'center':[cy.origin.x*10,cy.origin.y*10,cy.origin.z*10],'axis':list(cy.axis.asArray()),'radius':cy.radius*10})
   assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c0.features),c0.name
  return rows
 def near(a,b,tolerance=.002):assert abs(a-b)<tolerance,(a,b)
 def hole(record,axis,x,y,z,r):
  indices=[i for i in range(3) if i!=axis];point=[x,y,z];assert any(abs(row['axis'][axis])>.999999 and abs(row['radius']-r)<.0001 and all(abs(row['center'][i]-point[i])<.0001 for i in indices) for row in record['cylinders']),(axis,point,r)
 baseline=measure();edits=[]
 for name,expr in [('robot_roll_y','73 mm'),('robot_hip_x','190 mm'),('robot_fastener_diametral_allowance','.6 mm')]:
  p=d.userParameters.itemByName(name);old=p.expression
  try:
   p.expression=expr;assert d.computeAll();edited=measure();half=d.userParameters.itemByName('frame_half_y').value*10;hip=d.userParameters.itemByName('robot_hip_x').value*10;clear=d.userParameters.itemByName('frame_m3_clearance').value*10
   for key,side in [('right',1),('left',-1)]:
    expected=list(baseline[key]['bounds'])
    if name=='robot_roll_y':expected[1]+=side*5;expected[4]+=side*5
    if name=='robot_hip_x':expected[0]-=5;expected[3]+=5
    for a,b in zip(edited[key]['bounds'],expected):near(a,b)
    for x in [-(hip-59.5),hip-59.5]:
     for z in [-12,24]:hole(edited[key],1,x,0,z,clear/2)
    for x in [-63,63]:hole(edited[key],2,x,side*(half-5),0,1.25)
   for sx in [-1,1]:
    for sy in [-1,1]:hole(edited['brace'],2,sx*63,sy*(half-5),0,clear/2);hole(edited['brace'],2,sx*52,sy*(half-14),0,1.25);hole(edited['deck'],2,sx*52,sy*(half-14),0,clear/2)
   edits.append({'parameter':name,'edited_expression':expr,'measurements':edited,'passed':True})
  finally:p.expression=old;assert d.computeAll()
  restored=measure();error=max(abs(a-b) for key in parts for a,b in zip(restored[key]['bounds'],baseline[key]['bounds']));assert error<.002;assert all(abs(restored[key]['volume_mm3']-baseline[key]['volume_mm3'])<.001 for key in parts);edits[-1]['restore_max_bounds_error_mm']=error
 for c0 in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage) for f in c0.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(c0.name,issues)
 paths=[]
 for side in ['right','left']:
  c0=parts[side];occ0=next(o for o in root.occurrences if o.component==c0);visible=occ0.isLightBulbOn;occ0.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-'+side+'-rail-restored.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c0));occ0.isLightBulbOn=visible;assert os.path.getsize(path)>10000;paths.append(path)
 print(json.dumps({'passed':True,'saved':False,'baseline':baseline,'edits':edits,'paths':paths,'native_mirror':{'source_part':source.partNumber,'features':c.features.count,'linked':copy.isParametric},'elapsed_seconds':time.monotonic()-tick,'scope':'Both motor rails, brace and deck share width, shoulder mounting and fastener datums. Transverse ties, cassette and fixed hardware placements still need equivalent bindings.'}))
'''
r=rpc(s,'frame-rail-family-edit-restore',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-rail-family-edit-restore.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'cases':len(record['edits']),'seconds':record['elapsed_seconds']},flush=True)
for p in record['paths']:fetch(p,Path(p).name)
