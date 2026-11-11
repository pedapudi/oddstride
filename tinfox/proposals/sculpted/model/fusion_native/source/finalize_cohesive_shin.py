"""Replace retired shin histories with audited linked native manufacturing shells."""
import hashlib,json
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
for side in ['inner','outer','inner-right','outer-right','master']:
 label='cohesive-shin-'+side+'-final';sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  row=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert row[gate] and row['native_step_sha256']==sha
for name in ['service','motion']:
 assert json.loads((ROOT/'audits'/f'cohesive-shin-{name}.json').read_text())['passed']
archives={name:hashlib.sha256((ROOT/'exports'/f'{name}.f3d').read_bytes()).hexdigest() for name in ['shin_inner','shin_outer']}
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;assert len(app.data.personalUseLimits.editableFiles)==4
 oldkeys=['shin_inner_right','shin_outer_right','shin_inner','shin_outer']
 def signature(c):return {'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volumes':[round(b.volume,6) for b in c.bRepBodies],'health':[int(f.healthState) for f in c.features]}
 before={o.component.partNumber:signature(o.component) for o in root.occurrences if o.component.partNumber not in oldkeys and not o.component.partNumber.startswith('CANDIDATE_cohesive_shin_')};removed=[]
 for key in oldkeys:
  o=next(o for o in root.occurrences if o.component.partNumber==key);removed.append({'part':key,'name':o.name,'signature':signature(o.component)});assert o.deleteMe()
 after={o.component.partNumber:signature(o.component) for o in root.occurrences if not o.component.partNumber.startswith('CANDIDATE_cohesive_shin_')};assert before==after,'Retirement affected an unrelated component'
 removed_parameters=[]
 while True:
  eligible=[p for p in d.userParameters if p.name.startswith(('shin_inner_','shin_outer_')) and p.isDeletable]
  if not eligible:break
  for p in eligible:removed_parameters.append(p.name);assert p.deleteMe()
 retained=[p.name for p in d.userParameters if p.name.startswith(('shin_inner_','shin_outer_'))]
 lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C');template=lib.materials.itemByName('PET Plastic');assert template
 name='PETG mass estimate (1270 kg/m3)';material=d.materials.itemByName(name) or d.materials.addByCopy(template,name)
 density=[]
 for propid in ['structural_Density','thermal_Density']:
  prop=core.FloatProperty.cast(material.materialProperties.itemById(propid))
  if prop:assert prop.units=='KilogramPerCubicMeter';prop.value=1270;density.append(propid)
 assert density
 lib=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140');appearance=d.appearances.itemByName('Tinfox charcoal') or d.appearances.addByCopy(lib.appearances.itemByName('Plastic - Matte (White)'),'Tinfox charcoal')
 for propid in ['opaque_albedo','surface_albedo']:
  prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(propid))
  if prop:prop.value=core.Color.create(48,54,50,255)
 rows=[]
 for occ in root.occurrences:
  c=occ.component
  if not c.partNumber.startswith('CANDIDATE_cohesive_shin_'):continue
  suffix=c.partNumber.replace('CANDIDATE_cohesive_shin_','');master=suffix=='master';c.partNumber='shin_design_master' if master else 'shin_'+suffix;c.name='Shin shared design master' if master else ('Right ' if suffix.endswith('_right') else 'Left ')+suffix.split('_')[0]+' shin shell'
  assert c.bRepBodies.count==(0 if master else 1);assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features)
  for sketch in c.sketches:sketch.isLightBulbOn=False
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
  c.attributes.add('Tinfox','SourceModelSHA256','7a30dd8d92258b011e043f6fb43992ff9ac718232dd030ec2a7c79b33f68d63a');c.attributes.add('Tinfox','ManufacturingRelease','False: PETG bearing fits and loaded strength remain untested');occ.isLightBulbOn=not master
  row={'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count}
  if not master:
   body=c.bRepBodies.item(0);body.material=material;body.appearance=appearance;body.isLightBulbOn=True;physical=body.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy);expected=physical.volume*1.27e-3;assert abs(physical.mass-expected)<1e-6,(physical.mass,expected)
   row.update({'faces':body.faces.count,'edges':body.edges.count,'mass_kg':physical.mass,'material':body.material.name})
  rows.append(row)
 assert d.computeAll();folder=os.path.join(tempfile.gettempdir(),'tinfox-native');path=os.path.join(folder,'Tinfox-Leg-native-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path))
 previous=doc.dataFile.versionNumber;assert doc.save('Replace four retired shin histories with shared native master and linked structural halves. Five family edits, bearing service and 109 knee samples qualified; remaining limb parts and whole-robot migration remain open.')
 print(json.dumps({'previous_version':previous,'save_requested':True,'removed_parts':removed,'removed_unused_parameter_count':len(removed_parameters),'retained_old_parameters':retained,'unrelated_components_unchanged':len(before),'parts':rows,'paths':[path],'editable_files':len(app.data.personalUseLimits.editableFiles),'source_of_truth_changed':False,'manufacturing_ready':False}))
'''
r=rpc(s,'cohesive-shin-native-checkpoint',timeout=300);assert r[0]['success'],r
record=json.loads(r[0]['message']);record['retired_local_archives_sha256']=archives;(ROOT/'audits/cohesive-shin-native-checkpoint.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
for path in record['paths']:fetch(path,Path(path).name)
