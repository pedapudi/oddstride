"""Bind cover structure to hip datums while retaining independent hardware fits."""
import json,re
from pathlib import Path
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'audits/current-cover-parameter-inventory.json').read_text());bindings={}
replacements={
 'Roof stiffening rib datum':{'46.75 mm':'cover_roof_z-2.75 mm'},
 'Roof stiffening rib rectangle':{'170 mm':'2*cover_half_width-52.4 mm'},
 'Open mounting boss channel rectangle':{'103.5 mm':'cover_half_width-7.7 mm'},
 'Inner boss release tool rectangle':{'101.5 mm':'cover_half_width-9.7 mm'},
 'Lateral cover screw hole datum':{'101 mm':'cover_half_width-10.2 mm'},
 'Open old roof datum':{'45.8 mm':'cover_roof_z-3.7 mm'},
 'Open old roof outline':{'207 mm':'2*cover_half_length-43.8 mm','139 mm':'2*cover_half_width-83.4 mm'},
 'Display aperture tool datum':{'55 mm':'cover_roof_z+5.5 mm'},
 'Upper half roll cuff section':{'118.8 mm':'cover_hip_x-66.2 mm','128 mm':'cover_hip_x-57 mm','132 mm':'cover_hip_x-53 mm','135 mm':'cover_hip_x-50 mm'},
 'Cuff structural root rectangle':{'121 mm':'cover_hip_x-64 mm'},
 'Crossmember underside clearance rectangle':{'121 mm':'cover_hip_x-64 mm','184 mm':'2*cover_half_width-38.4 mm'},
 'Upper cuff ear tool rectangle':{'125.5 mm':'cover_hip_x-59.5 mm'},
 'Obsolete front lip relief rectangle':{'122 mm':'cover_hip_x-63 mm','204 mm':'2*cover_half_width-18.4 mm'},
 'Former cradle relief rectangle':{'138 mm':'cover_hip_x-47 mm'},
 'Obsolete lidar seat tool datum':{'45 mm':'cover_roof_z-4.5 mm'},
}
for side in ['Left','Right']:
 replacements[side+' rail release tool rectangle']={'264 mm':'2*cover_half_length+13.2 mm'}
 replacements[side+' crossmember release tool rectangle']={'206 mm':'2*cover_half_width-16.4 mm'}
for p in inventory['parameters']:
 expression=p['expression']
 for old,new in replacements.get(p['owner_name'],{}).items():
  expression=re.sub(r'(?<![\d.])'+re.escape(old)+r'(?![\d.])','('+new+')',expression)
 if expression!=p['expression']:bindings[p['name']]={'old':p['expression'],'new':expression,'owner':p['owner_name']}
user={'cover_half_length':'cover_hip_x-59.6 mm','cover_half_width':'cover_roll_y+43.2 mm','cover_boss_x':'cover_half_length-13.4 mm','cover_boss_y':'cover_half_width-4.95 mm','saddle_cover_crossmember_x':'cover_hip_x-64 mm','saddle_cover_rail_y':'cover_half_width-11.7 mm','saddle_cover_service_x':'cover_hip_x-36 mm','saddle_cover_old_seat_x':'cover_hip_x-103 mm','saddle_cover_roof_z':'cover_roof_z+6 mm'}
s='''import adsk.core as core,adsk.fusion as fusion,json,time

def run(_context: str):
 app=core.Application.get();doc=app.activeDocument;assert doc.dataFile.id=='urn:adsk.wipprod:dm.lineage:R7U8KNNBSA6o3YwVNF2ZQQ';d=fusion.Design.cast(app.activeProduct);c=next(c for c in d.allComponents if c.partNumber=='CANDIDATE_current_body_center_0');before=[p.value for p in c.modelParameters];rows=[];tick=time.monotonic()
 for name,expr in USER.items():
  p=d.userParameters.itemByName(name);old=p.expression;value=p.value;p.expression=expr;assert abs(p.value-value)<1e-8,(name,p.value,value);rows.append({'parameter':name,'before':old,'after':expr,'kind':'Family datum'})
 for name,row in BINDINGS.items():
  p=d.allParameters.itemByName(name);assert p.createdBy.name==row['owner'];assert p.expression==row['old'];value=p.value;p.expression=row['new'];assert abs(p.value-value)<1e-8,(name,p.value,value);rows.append({'parameter':name,'before':row['old'],'after':row['new'],'owner':row['owner']})
 assert d.computeAll();assert c.bRepBodies.count==1;assert all(f.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState for f in c.features);after=[p.value for p in c.modelParameters];assert len(before)==len(after) and max(abs(a-b) for a,b in zip(before,after))<1e-8
 print(json.dumps({'passed':True,'saved':False,'bindings':rows,'elapsed_seconds':time.monotonic()-tick,'scope':'Cover family geometry. Other chassis components and vendor hardware remain independent; whole-robot family propagation is a separate gate.'}))
'''.replace('USER',repr(user)).replace('BINDINGS',repr(bindings))
r=rpc(s,'current-cover-family-bindings',timeout=600);assert r[0]['success'],r;record=json.loads(r[0]['message']);(ROOT/'audits/current-cover-family-bindings.json').write_text(json.dumps(record,indent=2));print({'bindings':len(record['bindings']),'elapsed_seconds':record['elapsed_seconds']})
