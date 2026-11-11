"""Bind bottom-supported brace, separate process allowances and battery access width."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/n).read_text() for n in ['native_documents.py','intent_geometry.py','compact_cover_intent.py','frame_deck_intent.py'])+'''
def run(_context: str):
 import json,time,tempfile,os
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert d.activateRootComponent();tick=time.monotonic();before={}
 for c in d.allComponents:
  if c.bRepBodies.count:before[c.id]={'volume':sum(b.volume for b in c.bRepBodies),'bounds':[[v for v in b.boundingBox.minPoint.asArray()]+[v for v in b.boundingBox.maxPoint.asArray()] for b in c.bRepBodies]}
 brace=next(c for c in d.allComponents if c.partNumber=='chassis_lower_brace');deck=next(c for c in d.allComponents if c.partNumber=='electronics_shelf');FrameDeckIntent(IntentGeometry(d,brace)).parameters();changes=[]
 for name,expression in {'frame_brace_center_z':'frame_brace_bottom_z+frame_brace_thickness/2','frame_m3_tap_drill':'frame_m3_tap_drill_nominal+frame_tap_hole_process_compensation','frame_m3_clearance':'frame_m3_nominal+robot_fastener_diametral_allowance+frame_hole_process_compensation','belly_battery_aperture_depth':'2*frame_half_y-2 mm'}.items():
  p=d.userParameters.itemByName(name);value=p.value;old=p.expression;p.expression=expression;assert abs(p.value-value)<1e-8,(name,p.value,value);changes.append({'parameter':name,'before':old,'after':expression})
 for p in deck.modelParameters:
  if 'frame_m3_clearance' in p.expression:
   old=p.expression;value=p.value;p.expression=old.replace('frame_m3_clearance','deck_m3_clearance');assert abs(p.value-value)<1e-8;changes.append({'parameter':p.name,'owner':p.createdBy.name,'before':old,'after':p.expression})
 assert any(row.get('owner') for row in changes),'Expected native deck fit dimensions';assert d.computeAll();error=0
 for c in d.allComponents:
  if c.id in before:
   row=before[c.id];assert abs(sum(b.volume for b in c.bRepBodies)-row['volume'])<1e-6,c.name
   for b,box in zip(c.bRepBodies,row['bounds']):error=max(error,max(abs(a-b) for a,b in zip(list(b.boundingBox.minPoint.asArray())+list(b.boundingBox.maxPoint.asArray()),box)))
  assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 assert error<1e-7;assert not any(c.partNumber=='CANDIDATE_battery_skid' for c in d.allComponents);occ=root.occurrences.addNewComponent(core.Matrix3D.create());c=occ.component;c.name='Shared-frame battery skid';c.partNumber='CANDIDATE_battery_skid';g=IntentGeometry(d,c)
 for name,value in {'battery_skid_width':138,'battery_skid_depth':'2*(frame_half_y-7 mm)','battery_skid_radius':15,'battery_skid_bottom_z':-71,'battery_skid_thickness':1.5}.items():g.parameter(name,value,comment='Battery skid family dimension; thickness and fastening require physical structural qualification.')
 plane=g.plane(c.xYConstructionPlane,'battery_skid_bottom_z','Skid bottom datum');sk=g.rounded_rectangle(plane,'battery_skid_width','battery_skid_depth','battery_skid_radius','0 mm','Rounded battery protection outline');body=g.extrude(sk,'battery_skid_thickness','Constant-thickness battery skid').bodies.item(0);old=next(c for c in d.allComponents if c.partNumber=='battery_skid');body.material=old.bRepBodies.item(0).material;body.appearance=old.bRepBodies.item(0).appearance
 for item in list(c.sketches)+list(c.constructionPlanes):item.isLightBulbOn=False
 path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-intent-battery-skid.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>10000;occ.isLightBulbOn=False
 print(json.dumps({'passed':True,'saved':False,'changes':changes,'baseline_max_bounds_error_mm':error*10,'path':path,'skid_features':c.features.count,'skid_sketches':c.sketches.count,'elapsed_seconds':time.monotonic()-tick,'scope':'Baseline-preserving parameter bindings. Separate process compensation defaults to zero; no print or machining fit has been qualified.'}))
'''
r=rpc(s,'frame-process-family-bindings',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-process-family-bindings.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k!='changes'},flush=True);fetch(record['path'],Path(record['path']).name)
