"""Replace the qualified lower-shell history and checkpoint the same Chassis file."""
import json,hashlib
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
from personal_plan_preflight import script_header,known_files
ROOT=Path(__file__).resolve().parents[1]
label='compact-lower-shell-restored';sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
 r=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert r[gate] and r['native_step_sha256']==sha
assert json.loads((ROOT/'audits/compact-lower-shell-family-qualification.json').read_text())['passed']
keys=[p['key'] for p in json.loads((ROOT/'manifests/current-targets.json').read_text())['targets']['low']['custom_parts'] if any(i['group']=='body' for i in p['instances']) and p['key'] not in ['front_fascia','body_nose_surround']]
assert len(keys)==18
s=script_header()+'''
import adsk.core as core,adsk.fusion as fusion,json,time,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ' and doc.dataFile.versionNumber==5;d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;capacity=require_personal_capacity(app,doc,KNOWN,new_cloud_files=0,reserve_slots=1);tick=time.monotonic();old=next(o for o in root.occurrences if o.component.partNumber=='belly_center_0');candidate=next(o for o in root.occurrences if o.component.partNumber=='CANDIDATE_compact_belly_center_0');c=candidate.component;assert old.component.features.count==112 and c.features.count==15 and c.sketches.count==6;before={'features':old.component.features.count,'sketches':old.component.sketches.count,'faces':old.component.bRepBodies.item(0).faces.count,'edges':old.component.bRepBodies.item(0).edges.count};assert old.deleteMe();c.partNumber='belly_center_0';c.name='Structural lower body shell';candidate.isLightBulbOn=True;c.attributes.add('Tinfox','ConstructionQuality','Shared body transverse profile, uniform shell wall, stepped motor clearance and mirrored access profiles; unchanged frozen shape, four family edits restored.');c.attributes.add('Tinfox','ManufacturingRelease','False');assert d.computeAll();assert c.bRepBodies.count==1 and c.features.count==15
 # Confirm that the replacement retained its own seam dependency after cleanup.
 p=d.userParameters.itemByName('body_shell_seam_gap');oldexpr=p.expression;p.expression='.4 mm';assert abs(c.bRepBodies.item(0).boundingBox.maxPoint.z*10+10.4)<.001;p.expression=oldexpr;assert d.computeAll();assert abs(c.bRepBodies.item(0).boundingBox.maxPoint.z*10+10.3)<.001
 rows=[]
 for part in d.allComponents:
  issues=[(f.name,f.errorOrWarningMessage) for f in part.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not issues,(part.name,issues)
  if part.partNumber in KEYS:rows.append({'part':part.partNumber,'features':part.features.count,'sketches':part.sketches.count,'bodies':part.bRepBodies.count})
 assert not any(p.partNumber.startswith('CANDIDATE_') for p in d.allComponents);assert len([p for p in rows if p['bodies']])==18;path=os.path.join(tempfile.gettempdir(),'tinfox-native','compact-lower-shell-final.step');assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path,c));assert os.path.getsize(path)>50000;assert doc.save('Replace the 112-feature lower shell with 15 native features sharing enclosure dimensions. Matching boundary and sections; four family edit/restore cases pass. Generated CAD remains authoritative pending complete robot audit.');archive=os.path.join(tempfile.gettempdir(),'tinfox-native','Tinfox-Chassis-shared-shell-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(archive));print(json.dumps({'save_requested':True,'version':doc.dataFile.versionNumber,'complete':doc.dataFile.isComplete,'modified':doc.isModified,'before':before,'after':{'features':c.features.count,'sketches':c.sketches.count,'faces':c.bRepBodies.item(0).faces.count,'edges':c.bRepBodies.item(0).edges.count},'parts':rows,'capacity':capacity,'paths':[path,archive],'elapsed_seconds':time.monotonic()-tick,'source_of_truth_changed':False}))
'''.replace('KNOWN',repr(known_files())).replace('KEYS',repr(keys))
r=rpc(s,'compact-lower-shell-checkpoint',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/compact-lower-shell-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['parts','capacity']})
for path in record['paths']:fetch(path,Path(path).name)
