"""Derive shared parameters only; preserve native subsystem feature histories."""
import json,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
role=sys.argv[1];assert role in ['leg','head']
reconciled='--reconciled' in sys.argv
bindings={'leg':{'lc_hip_x':'robot_hip_x','lc_roll_y':'robot_roll_y'},'head':{'body_hip_x':'robot_hip_x','body_envelope_width':'2*robot_body_half_width','hood_sensor_seat_z':'robot_sensor_seat_z','saddle_fastener_diametral_clearance':'robot_fastener_diametral_allowance'}}[role]
bindings={name:expression.replace('robot_hip_x','robot_hip_x_Ref').replace('robot_roll_y','robot_roll_y_Ref').replace('robot_body_half_width','robot_body_half_width_Ref').replace('robot_sensor_seat_z','robot_sensor_seat_z_Ref').replace('robot_fastener_diametral_allowance','robot_fastener_diametral_allowance_Ref') for name,expression in bindings.items()}
header=(ROOT/'source/native_documents.py').read_text()
s=header+'''
import adsk.core as core,json

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);assert not doc.isModified or RECONCILED
 if doc!=app.activeDocument:assert doc.activate()
 print(json.dumps({'active':doc.name,'version':doc.dataFile.versionNumber,'modified':doc.isModified}))
'''.replace('ROLE',repr(role)).replace('RECONCILED',repr(reconciled))
r=rpc(s,'activate-'+role+'-for-shared-datums',timeout=30);assert r[0]['success'],r
s=header+'''
import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,ROLE);assert doc==app.activeDocument and (not doc.isModified or RECONCILED);d=fusion.Design.cast(app.activeProduct);source_doc=authoring_document(app,'chassis');assert source_doc.dataFile.versionNumber==7 and source_doc.dataFile.isComplete and not source_doc.isModified;source=fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'));root=d.rootComponent;assert root.features.deriveFeatures.count==0;tick=time.monotonic()
 def inventory():return {c.partNumber:{'features':c.features.count,'sketches':c.sketches.count,'bodies':[{'volume':b.volume,'bounds':b.boundingBox.minPoint.asArray()+b.boundingBox.maxPoint.asArray()} for b in c.bRepBodies]} for c in d.allComponents if c!=root}
 before=inventory();assert d.activateRootComponent();assert d.activeComponent==root;inp=root.features.deriveFeatures.createInput(source);assert len(inp.sourceEntities)==0;inp.isIncludeFavoriteParameters=True;inp.isIncludeComponentParameters=False;feature=root.features.deriveFeatures.add(inp);assert feature,'Derive add returned null';feature.name='Shared robot datums from Chassis';assert feature.bodies.count==0,('Unexpected bodies',feature.bodies.count);d.timeline.moveToEnd();derived=[{'name':p.name,'expression':p.expression,'value':p.value,'unit':p.unit} for p in d.derivedParameters];assert len(derived)==8 and {'robot_hip_x_Ref','robot_roll_y_Ref','robot_body_wall_Ref','robot_sensor_seat_z_Ref','robot_fastener_diametral_allowance_Ref','robot_body_half_width_Ref'}.issubset({p['name'] for p in derived}),derived;rows=[]
 for name,expression in BINDINGS.items():
  p=d.userParameters.itemByName(name);old=p.expression;value=p.value;p.expression=expression;assert abs(p.value-value)<1e-8,(name,value,p.value);rows.append({'parameter':name,'before':old,'expression':expression})
 assert d.computeAll();after=inventory();assert set(after)==set(before)
 for name,expected in before.items():
  actual=after[name];assert actual['features']==expected['features'] and actual['sketches']==expected['sketches'] and len(actual['bodies'])==len(expected['bodies']),(name,expected,actual)
  for a,b in zip(expected['bodies'],actual['bodies']):assert max(abs(x-y) for x,y in zip(a['bounds'],b['bounds']))<1e-6,(name,a,b)
 for c in d.allComponents:assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 print(json.dumps({'passed':True,'saved':False,'role':ROLE,'feature':feature.name,'feature_timeline_index':feature.timelineObject.index,'derived_parameters':derived,'bindings':rows,'custom_or_reference_geometry_imported':False,'bodies_added':feature.bodies.count,'elapsed_seconds':time.monotonic()-tick,'scope':'Shared native parameter links with unchanged baseline geometry. Cross-document edit/update/restore must still be exercised.'}))
'''.replace('ROLE',repr(role)).replace('RECONCILED',repr(reconciled)).replace('BINDINGS',repr(bindings))
r=rpc(s,role+'-shared-robot-datum-link',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/f'{role}-shared-robot-datum-link.json').write_text(json.dumps(record,indent=2));print(record)
