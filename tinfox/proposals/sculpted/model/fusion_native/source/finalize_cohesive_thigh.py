"""Checkpoint audited native thigh shells in the existing Leg document."""
import hashlib,json,shutil
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
for side in ['inner','outer','inner-right','outer-right']:
 label='cohesive-thigh-'+side+'-final';sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest();a=json.loads((ROOT/'audits'/f'{label}-geometry.json').read_text());assert a['geometric_gate_passed'] and a['native_step_sha256']==sha
for name in ['cohesive-thigh-direct-native-section-comparison','cohesive-thigh-family-edits','cohesive-native-leg-interfaces','cohesive-native-leg-motion','cohesive-leg-silhouettes']:
 assert json.loads((ROOT/'audits'/f'{name}.json').read_text())['passed'],name
archives={name:hashlib.sha256((ROOT/'exports'/name).read_bytes()).hexdigest() for name in ['thigh_outer.f3d','Tinfox-Leg-native-checkpoint.f3d']}
previous=ROOT/'exports/Tinfox-Leg-v5-shin-checkpoint.f3d'
if not previous.exists():shutil.copyfile(ROOT/'exports/Tinfox-Leg-native-checkpoint.f3d',previous)
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert len(app.data.personalUseLimits.editableFiles)==4;oldkeys=['thigh_inner_right','thigh_outer_right','thigh_inner','thigh_outer']
 def signature(c):return {'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volumes':[round(b.volume,6) for b in c.bRepBodies],'health':[int(f.healthState) for f in c.features]}
 before={o.component.partNumber:signature(o.component) for o in root.occurrences if o.component.partNumber not in oldkeys and not o.component.partNumber.startswith('CANDIDATE_cohesive_thigh_')};removed=[]
 for key in oldkeys:
  occ=next(o for o in root.occurrences if o.component.partNumber==key);removed.append({'part':key,'name':occ.name,'signature':signature(occ.component)});assert occ.deleteMe()
 after={o.component.partNumber:signature(o.component) for o in root.occurrences if not o.component.partNumber.startswith('CANDIDATE_cohesive_thigh_')};assert before==after,'Retirement affected an unrelated component'
 removed_parameters=[]
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith(('thigh_inner_','thigh_outer_')) and p.isDeletable]
  if not eligible:break
  for p in eligible:removed_parameters.append(p.name);assert p.deleteMe()
 retained=[p.name for p in d.userParameters if p.name.startswith(('thigh_inner_','thigh_outer_'))];material=d.materials.itemByName('PETG mass estimate (1270 kg/m3)');assert material
 lib=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140');template=lib.appearances.itemByName('Plastic - Matte (White)');appearances={}
 for role,rgb in [('ivory',(231,223,208)),('orange',(205,100,47))]:
  appearance=d.appearances.itemByName('Tinfox '+role) or d.appearances.addByCopy(template,'Tinfox '+role)
  for propid in ['opaque_albedo','surface_albedo']:
   prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(propid))
   if prop:prop.value=core.Color.create(*rgb,255)
  appearances[role]=appearance
 rows=[]
 for occ in root.occurrences:
  c=occ.component
  if not c.partNumber.startswith('CANDIDATE_cohesive_thigh_'):continue
  suffix=c.partNumber.replace('CANDIDATE_cohesive_thigh_','');master=suffix=='master';c.partNumber='thigh_design_master' if master else 'thigh_'+suffix;c.name='Thigh shared design master' if master else ('Right ' if suffix.endswith('_right') else 'Left ')+suffix.split('_')[0]+' thigh shell';assert c.bRepBodies.count==(0 if master else 1);assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
  for sketch in c.sketches:sketch.isLightBulbOn=False
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
  c.attributes.add('Tinfox','SourceModelSHA256','7a30dd8d92258b011e043f6fb43992ff9ac718232dd030ec2a7c79b33f68d63a');c.attributes.add('Tinfox','NativeGeometryStatus','Surface, direct native sections, family edits, silhouettes, fixed hardware and sampled motion qualified. Raw STEP face-distance diagnostics retained separately.');c.attributes.add('Tinfox','ManufacturingRelease','False: printed fit, strength, full robot range and remaining native assembly integration unqualified');occ.isLightBulbOn=not master;row={'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count}
  if not master:
   body=c.bRepBodies.item(0);body.material=material;body.appearance=appearances['orange' if suffix.startswith('outer') else 'ivory'];body.isLightBulbOn=True;physical=body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy);assert abs(physical.mass-physical.volume*1.27e-3)<1e-6;row.update({'faces':body.faces.count,'edges':body.edges.count,'mass_kg':physical.mass,'material':body.material.name})
  rows.append(row)
 assert d.computeAll();folder=os.path.join(tempfile.gettempdir(),'tinfox-native');path=os.path.join(folder,'Tinfox-Leg-native-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));previous=doc.dataFile.versionNumber;assert doc.save('Replace retired thigh histories with native shared envelope, linked structural halves and integral revolved bearing stops. Direct native sections, five family edits, 110 interfaces and 109 knee samples checked; whole-robot migration remains open.')
 print(json.dumps({'previous_version':previous,'save_requested':True,'removed_parts':removed,'removed_unused_parameter_count':len(removed_parameters),'retained_old_parameters':retained,'unrelated_components_unchanged':len(before),'parts':rows,'paths':[path],'editable_files':len(app.data.personalUseLimits.editableFiles),'source_of_truth_changed':False,'manufacturing_ready':False}))
'''
r=rpc(s,'cohesive-thigh-native-checkpoint',timeout=300);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['retired_local_archives_sha256']=archives;(ROOT/'audits/cohesive-thigh-native-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['removed_parts','parts']})
for path in record['paths']:fetch(path,Path(path).name)
