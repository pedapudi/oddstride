"""Place the unchanged common M4 buttons on their parameter-driven recessed seats."""
import json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
s='\n'.join((ROOT/'source'/p).read_text()for p in ['native_documents.py','intent_geometry.py'])+'''
def run(_context:str):
 import json,os,tempfile,time
 app=core.Application.get();doc=authoring_document(app,'leg');assert doc==app.activeDocument or doc.activate();d=fusion.Design.cast(app.activeProduct);assert d.activateRootComponent();root=d.rootComponent;tick=time.monotonic();assert not any(c.partNumber=='CANDIDATE_RECESSED_CLOSURE_REFERENCES'for c in d.allComponents);holder=root.occurrences.addNewComponent(core.Matrix3D.create());holder.component.name='Recessed common closure-button references';holder.component.partNumber='CANDIDATE_RECESSED_CLOSURE_REFERENCES';holder.isLightBulbOn=False;rows=[]
 for angle in [90,215,325]:
  name='FL_carrier_closure_bolt_'+str(angle);source=next(c for c in d.allComponents if c.partNumber=='BENCH_REFERENCE_'+name).bRepBodies.item(0);o=holder.component.occurrences.addNewComponent(core.Matrix3D.create());c=o.component;c.name='Recessed M4x16 button '+str(angle);c.partNumber='BENCH_REFERENCE_RECESSED_CLOSURE_'+str(angle);c.attributes.add('Tinfox','BenchReferenceName',name);c.attributes.add('Tinfox','BenchReferenceRole','standard_hardware');c.attributes.add('Tinfox','Specification','M4 x 16 ISO7380-1 button; no separate closure washer');g=IntentGeometry(d,c);g.parameter('rc_original_button_underhead_y',-.1);items=core.ObjectCollection.create();items.add(source);copy=c.features.copyPasteBodies.add(items);copy.name='Unchanged common M4x16 button reference';body=copy.bodies.item(0);items=core.ObjectCollection.create();items.add(body);mi=c.features.moveFeatures.createInput2(items);assert mi.defineAsTranslateXYZ(g.value('0 mm'),g.value('rc_head_floor_y-rc_original_button_underhead_y'),g.value('0 mm'),True);move=c.features.moveFeatures.add(mi);move.name='Head follows recessed bearing floor';body=c.bRepBodies.item(0);body.name=c.name;bb=body.boundingBox;bounds=[v*10 for v in [*bb.minPoint.asArray(),*bb.maxPoint.asArray()]];assert abs(bounds[1]+18.2)<1e-6 and abs(bounds[4])<1e-6,bounds;path=os.path.join(tempfile.gettempdir(),'tinfox-native','recessed-closure-reference-'+str(angle)+'.step');holder.isLightBulbOn=True;o.isLightBulbOn=True;body.isLightBulbOn=True;assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>5000;holder.isLightBulbOn=False;rows.append({'name':name,'component':c.partNumber,'path':path,'bounds_mm':bounds,'volume_mm3':body.volume*1000})
 gaps=[]
 for row in rows:
  for angle in [90,210,330]:
   tie=next(c for c in d.allComponents if c.partNumber=='BENCH_REFERENCE_Pod_M3x60_screw_'+str(angle)).bRepBodies.item(0);gap=tie.boundingBox.minPoint.y*10-row['bounds_mm'][4];assert gap>=1-1e-6;gaps.append({'head':row['name'],'tie_angle_deg':angle,'continuous_hip_rotation_gap_lower_bound_mm':gap,'proof':'Rotation about Y preserves each solid Y interval; strict axial separation holds at every angle.'})
 print(json.dumps({'saved_version':doc.dataFile.versionNumber,'working_modified':doc.isModified,'candidate_only':True,'references':rows,'continuous_gap_checks':gaps,'remove_reference_names':['FL_carrier_closure_washer_'+str(a)for a in [90,215,325]],'elapsed_seconds':time.monotonic()-tick}))
'''
r=rpc(s,'recessed-closure-references',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/recessed-closure-references.json').write_text(json.dumps(record,indent=2))
for row in record['references']:fetch(row['path'],Path(row['path']).name)
print({'references':len(record['references']),'continuous_pairs':len(record['continuous_gap_checks'])})
