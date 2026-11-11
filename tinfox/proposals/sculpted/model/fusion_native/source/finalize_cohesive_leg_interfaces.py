"""Retire superseded limb histories and save the current native Leg checkpoint."""
import gzip,hashlib,json,re,shutil
from pathlib import Path
from run_native import rpc
from fetch_exports import fetch
ROOT=Path(__file__).resolve().parents[1]
KEYS=['input_crank','motor_carrier_1','motor_carrier_-1','knee_inner_spacer','pushrod','sleeve_0','sleeve_1','knee_axle','foot'];keys=[k+s for k in KEYS for s in ['', '_right']]
for key in keys:
 label='cohesive-'+key.replace('_','-');sha=hashlib.sha256((ROOT/'exports'/f'{label}.step').read_bytes()).hexdigest()
 for suffix,gate in [('geometry','geometric_gate_passed'),('sections','section_gate_passed')]:
  report=json.loads((ROOT/'audits'/f'{label}-{suffix}.json').read_text());assert report[gate] and report['native_step_sha256']==sha,(key,suffix)
for name in ['cohesive-input-crank-family','cohesive-carrier-family','cohesive-link-sleeves','cohesive-foot-family','cohesive-native-leg-interfaces']:
 assert json.loads((ROOT/'audits'/f'{name}.json').read_text())['passed'],name
model=json.loads(gzip.decompress((ROOT/'snapshots/cohesive-limb/model.json.gz').read_bytes()));materials={p['mesh']:p['material'] for p in model['parts'] if p.get('leg')};palette=json.loads((ROOT.parents[3]/'design/appearance.json').read_text());roles={}
for key,material in materials.items():roles[key]=next((rule['role'] for rule in palette['rules'] if re.search(rule['pattern'],key)),palette['material_defaults'][material])
archive=ROOT/'exports/Tinfox-Leg-v6-shell-checkpoint.f3d'
if not archive.exists():shutil.copyfile(ROOT/'exports/Tinfox-Leg-native-checkpoint.f3d',archive)
s='''import adsk.core as core,adsk.fusion as fusion,json,os,tempfile

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:Uoyid7qvSf2B89DwCbvTLQ';d=fusion.Design.cast(app.activeProduct);root=d.rootComponent;limits=app.data.personalUseLimits;assert len(limits.editableFiles)<=9;oldkeys=KEYS
 def signature(c):return {'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count,'volumes':[round(b.volume,6) for b in c.bRepBodies],'health':[int(f.healthState) for f in c.features]}
 before={o.component.partNumber:signature(o.component) for o in root.occurrences if o.component.partNumber not in oldkeys and not o.component.partNumber.startswith('CANDIDATE_')};removed=[]
 for key in sorted(oldkeys,key=lambda k:(not k.endswith('_right'),k)):
  occ=next(o for o in root.occurrences if o.component.partNumber==key);removed.append({'part':key,'name':occ.name,'signature':signature(occ.component)});assert occ.deleteMe()
 after={o.component.partNumber:signature(o.component) for o in root.occurrences if not o.component.partNumber.startswith('CANDIDATE_')};assert before==after,'Retirement affected unrelated native geometry'
 removed_parameters=[];prefixes=['input_crank_','motor_carrier_','knee_inner_spacer_','pushrod_','sleeve_0_','sleeve_1_','knee_axle_','foot_']
 while True:
  eligible=[p for p in d.userParameters if any(p.name.startswith(prefix) for prefix in prefixes) and p.isDeletable]
  if not eligible:break
  for p in eligible:removed_parameters.append(p.name);assert p.deleteMe()
 for occ in root.occurrences:
  c=occ.component
  if c.partNumber=='CANDIDATE_carrier_master':c.partNumber='carrier_design_master';c.name='Carrier shared design master';occ.isLightBulbOn=False
  elif c.partNumber.startswith('CANDIDATE_'):c.partNumber=c.partNumber[len('CANDIDATE_'):];occ.isLightBulbOn=True
  for sk in c.sketches:sk.isLightBulbOn=False
  for plane in c.constructionPlanes:plane.isLightBulbOn=False
  if c.partNumber in oldkeys or c.partNumber=='carrier_design_master':
   c.attributes.add('Tinfox','SourceModelSHA256','7a30dd8d92258b011e043f6fb43992ff9ac718232dd030ec2a7c79b33f68d63a');c.attributes.add('Tinfox','NativeGeometryStatus','Native current geometry, section comparisons and shared-family edit/restores passed; native whole assembly remains open.');c.attributes.add('Tinfox','ManufacturingRelease','False: source fit, strength and complete robot validation remain incomplete.')
 library=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C');specs={'aluminum':('Aluminum 6061',2700),'steel':('Steel',7850),'rubber':('Rubber',1150),'petg':('PET Plastic',1270)};mats={}
 for key,(template_name,density) in specs.items():
  name={'petg':'PETG'}.get(key,key.capitalize())+' mass estimate ('+str(density)+' kg/m3)';m=d.materials.itemByName(name)
  if not m:m=d.materials.addByCopy(library.materials.itemByName(template_name),name)
  for propid in ['structural_Density','thermal_Density']:
   prop=core.FloatProperty.cast(m.materialProperties.itemById(propid))
   if prop:prop.value=density
  mats[key]=m
 appearance_lib=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140');plastic=appearance_lib.appearances.itemByName('Plastic - Matte (White)');metal=d.appearances.itemByName('Steel - Satin') or plastic;appearances={}
 for role,hexcolor in COLORS.items():
  name='Tinfox '+role;appearance=d.appearances.itemByName(name) or d.appearances.addByCopy(metal if role=='metal' else plastic,name);rgb=[int(hexcolor[i:i+2],16) for i in [1,3,5]]
  for propid in ['opaque_albedo','surface_albedo','metal_f0']:
   prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(propid))
   if prop:prop.value=core.Color.create(*rgb,255)
  appearances[role]=appearance
 rows=[]
 for occ in root.occurrences:
  c=occ.component;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features),(c.partNumber,[f.errorOrWarningMessage for f in c.features if f.healthState!=fusion.FeatureHealthStates.HealthyFeatureHealthState]);row={'part':c.partNumber,'features':c.features.count,'sketches':c.sketches.count,'bodies':c.bRepBodies.count}
  if c.bRepBodies.count:
   assert c.partNumber in MATERIALS,c.partNumber;kind=MATERIALS[c.partNumber];role=ROLES[c.partNumber];mass=0
   for b in c.bRepBodies:
    b.material=mats[kind];b.appearance=appearances[role];p=b.getPhysicalProperties(fusion.CalculationAccuracy.VeryHighCalculationAccuracy);assert abs(p.mass-p.volume*specs[kind][1]*1e-6)<1e-6;mass+=p.mass
   row.update({'material':mats[kind].name,'appearance_role':role,'mass_kg':mass})
  rows.append(row)
 assert d.computeAll();folder=os.path.join(tempfile.gettempdir(),'tinfox-native');path=os.path.join(folder,'Tinfox-Leg-native-checkpoint.f3d');assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path));previous=doc.dataFile.versionNumber;assert doc.save('Current 28 mm knee drive and compact motor carriers; shared native linkage/sleeve/foot parameters. Retired obsolete histories and applied source mass materials. Geometry, sections, parameter edits and fixed interfaces checked; complete assembly and manufacturing release remain open.')
 print(json.dumps({'previous_version':previous,'save_requested':True,'removed_parts':removed,'removed_unused_parameter_count':len(removed_parameters),'unrelated_geometry_unchanged':len(before),'parts':rows,'paths':[path],'editable_files':len(limits.editableFiles),'source_of_truth_changed':False,'manufacturing_ready':False}))
'''
for token,value in [('KEYS',keys),('MATERIALS',materials),('ROLES',roles),('COLORS',palette['colors'])]:s=s.replace(token,repr(value))
r=rpc(s,'cohesive-leg-interface-checkpoint',timeout=360);assert r[0]['success'],r;record=json.loads(r[0]['message']);record['retired_v6_archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest();(ROOT/'audits/cohesive-leg-interface-checkpoint.json').write_text(json.dumps(record,indent=2));print({k:v for k,v in record.items() if k not in ['removed_parts','parts']})
for path in record['paths']:fetch(path,Path(path).name)
