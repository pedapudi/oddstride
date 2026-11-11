"""Publish qualified frame-process bindings, cassette and matching protection plate."""
import hashlib,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
for report in ['frame-cassette-family-edit-restore','frame-process-family-edit-restore']:assert json.loads((ROOT/'audits'/f'{report}.json').read_text())['passed']
labels={'battery_cassette':'frame-intent-battery-cassette-restored'}|{key:'frame-process-'+key+'-restored' for key in ['chassis_lower_brace','electronics_shelf','belly_center_0','battery_skid']}
for key,label in labels.items():
 sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  r=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert r[gate] and r['native_step_sha256']==sha
s=script_header()+'\n'+(ROOT/'source/native_documents.py').read_text()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,tempfile,os

def run(_context: str):
 app=core.Application.get();doc=authoring_document(app,'chassis');doc.activate();assert doc.dataFile.versionNumber==15;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);before=[];after=[]
 for key in ['battery_cassette','battery_skid']:
  old=next(o for o in root.occurrences if o.component.partNumber==key);before.append({'part':key,'features':old.component.features.count,'sketches':old.component.sketches.count});assert old.deleteMe();occ=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_'+key);c=occ.component;c.partNumber=key;occ.isLightBulbOn=True;c.attributes.add('Tinfox','ConstructionQuality','Shared frame width; independently dimensioned pack envelope and process-fit allowances. Native edits and restoration plus frozen boundaries and sections are qualified.');c.attributes.add('Tinfox','ManufacturingRelease','False');c.attributes.add('Tinfox','CNC_Access','Unverified: inspect internal guide-window and upper-gusset cutter access; preserve frozen geometry pending a separate design revision.' if key=='battery_cassette' else 'Unverified setup and fastening plan; constant-thickness open outline.');after.append({'part':key,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count})
 removed=[]
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith(('battery_cassette_','battery_skid_')) and p.isDeletable]
  if not eligible:break
  for p in eligible:removed.append(p.name);assert p.deleteMe()
 assert d.computeAll();assert not any(c.partNumber.startswith('CANDIDATE_') for c in d.allComponents)
 for c in d.allComponents:assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),c.name
 paths=[]
 for key in KEYS:
  occ=next(o for o in root.occurrences if o.component.partNumber==key);c=occ.component;visible=occ.isLightBulbOn;occ.isLightBulbOn=True;path=os.path.join(tempfile.gettempdir(),'tinfox-native','frame-checkpoint-'+key+'.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));occ.isLightBulbOn=visible;assert os.path.getsize(path)>10000;paths.append(path)
 assert doc.save('Replace the battery cassette with a forty-one-feature native construction and shared-frame skid. Preserve frozen geometry; qualify width, independent hole/nut compensation and edit restoration. Anchor brace thickness at its rail contact plane and propagate deck support. Fixed reference placement, selected batteries, screw engagement, CNC guide-window access, physical fits and structural qualification remain separate gates. Generated CAD remains authoritative.');print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'before':before,'after':after,'removed_unused_parameters':removed,'paths':paths,'capacity':capacity,'source_of_truth':False}))
'''.replace('KNOWN',repr(known_files())).replace('KEYS',repr(list(labels)))
r=rpc(s,'frame-cassette-native-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/frame-cassette-native-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['capacity','removed_unused_parameters']},flush=True)
for path in record['paths']:fetch(path,Path(path).name)
