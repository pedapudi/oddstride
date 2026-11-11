"""Apply the shared palette without changing geometry or physical materials."""
import json,gzip,re,sys
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1];palette=json.loads((ROOT.parents[3]/'design/appearance.json').read_text());targets=json.loads((ROOT/'manifests/current-targets.json').read_text());model=json.loads(gzip.decompress((ROOT/targets['targets']['low']['reference_model']).read_bytes()));parts={p['name']:p for p in model['parts'] if p.get('material')};meshparts={p['mesh']:p for p in parts.values()};rows={}
for key,p in (parts|meshparts).items():
 role=palette['material_defaults'].get(p['material'],'charcoal')
 if p['material']!='steel':
  for rule in palette['rules']:
   if re.search(rule['pattern'],key):role=rule['role'];break
 rows[key]={'role':role,'source_material':p['material'],'mass_kg':p.get('mass_kg'),'nonphysical':key=='electronics_clearance'}
role=sys.argv[1];file_id=json.loads((ROOT/'manifests/subsystems.json').read_text())['subsystems'][role]['file_id']
s='''import adsk.core as core,adsk.fusion as fusion,json

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id==FILE_ID;d=fusion.Design.cast(app.activeProduct);library=app.materialLibraries.itemById('BA5EE55E-9982-449B-9D66-9F036540E140');template=library.appearances.itemByName('Plastic - Matte (White)');appearances={}
 for role,hexcolor in COLORS.items():
  name='Tinfox '+role;appearance=d.appearances.itemByName(name) or d.appearances.addByCopy(template,name);rgb=tuple(int(hexcolor[i:i+2],16) for i in [1,3,5])
  for key in ['opaque_albedo','surface_albedo']:
   prop=core.ColorProperty.cast(appearance.appearanceProperties.itemById(key))
   if prop:prop.value=core.Color.create(*rgb,255)
  appearances[role]=appearance
 changed=[]
 for c in d.allComponents:
  key=c.partNumber if c.partNumber in PARTS else c.name
  if key not in PARTS or not c.bRepBodies.count:continue
  row=PARTS[key]
  for b in c.bRepBodies:b.appearance=appearances[row['role']]
  c.attributes.add('Tinfox','AppearanceRole',row['role']);c.attributes.add('Tinfox','SourceMaterialRole',row['source_material']);c.attributes.add('Tinfox','SourceEstimatedMassKg',str(row['mass_kg']));c.attributes.add('Tinfox','MassStatus','Source estimate, not a measurement or physical material density override');changed.append({'part':key,'role':row['role'],'bodies':c.bRepBodies.count})
 root=d.rootComponent;root.attributes.add('Tinfox','MassMetrology','Do not use global Fusion mass as a qualified robot mass. Reference envelopes carry source estimated masses in attributes; curved custom solids require converged export integration.');print(json.dumps({'saved':False,'parts':changed,'physical_materials_changed':False,'palette':'Tinfox / warm fox'}))
'''.replace('FILE_ID',repr(file_id)).replace('COLORS',repr(palette['colors'])).replace('PARTS',repr(rows))
r=rpc(s,'apply-shared-appearance-'+role,timeout=180);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits'/('shared-appearance-'+role+'.json')).write_text(json.dumps(record,indent=2));print({'parts':len(record['parts']),'physical_materials_changed':False})
