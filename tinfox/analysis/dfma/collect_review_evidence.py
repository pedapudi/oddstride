"""Read-only design inventory for the manufacturing and assembly review."""
from pathlib import Path
import json,hashlib,collections,math,gzip
ROOT=Path(__file__).resolve().parents[2]/'proposals/sculpted/model'
OUT=Path(__file__).resolve().parent
candidate=ROOT/'output/closed-thigh-work'
raw=(candidate/'model.json').read_bytes();model=json.loads(raw)
stamp=hashlib.sha256(raw).hexdigest()
if (OUT/'inventory.json').exists():
 assert json.loads((OUT/'inventory.json').read_text())['model_sha256']==stamp,'Use a new review folder for another CAD revision.'
(OUT/'review-model.json.gz').write_bytes(gzip.compress(raw,mtime=0))
parts=model['parts'];families=[]
for key in sorted({p['mesh'] for p in parts}):
 ps=[p for p in parts if p['mesh']==key];p=ps[0]
 if p.get('service_role') or p['material'] not in ['petg','aluminum','rubber']:continue
 families.append({'key':key,'quantity':len(ps),'material':p['material'],'mass_one_kg':p['mass_kg'],'bounds_mm':p['bounds_mm'],'note':p.get('note','')})
physical=[p for p in parts if p.get('service_role') not in ['keepout','withdrawal']]
by_material=collections.Counter()
for p in physical:by_material[p['material']]+=p['mass_kg']
files={}
for name in ['build.py','slim_limb.py','seamless_limb.py','cohesive_limb.py','cohesive_chassis.py','closed_thigh.py','service_design.py','printed_carrier.py','low_sensor_saddle.py']:
 file=ROOT/name;files[name]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'path':str(file)}
report={'model_path':str(candidate/'model.json'),'model_sha256':hashlib.sha256(raw).hexdigest(),'physical_component_count':len(physical),'custom_material_families':families,'mass_sum_by_material_kg':dict(by_material),'parameters':model['parameters'],'source_files':files,'scope':'Inventory and documented dimensions only. Reference envelopes can have assigned masses; this is not a BOM cost, stock verification or physical qualification.'}
(OUT/'inventory.json').write_text(json.dumps(report,indent=2))
print('Model',report['model_sha256'],'physical parts',len(physical),'families',len(families))
