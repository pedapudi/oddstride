"""Export printed, hybrid and metal limb construction studies with explicit scope."""
import copy,csv,hashlib,json,math,zipfile
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from mesh_cleanup import clean_mesh
from kinematics import ROOT,LEGS,POSES,matrix
from build import box,cyl,ring,hex_nut,motor_envelope,POD_TIE_ANGLES
import engineering as engineering
OUT=ROOT/'output';DEST=OUT/'limb-variants';DEST.mkdir(exist_ok=True)
raw=(OUT/'model.json').read_bytes();main=json.loads(raw);stamp=hashlib.sha256(raw).hexdigest()
custom_prefixes=('roll_cartridge','motor_carrier','hip_hub','motor_mount_ring','thigh_inner','thigh_outer','shin_inner','shin_outer','knee_head','input_crank','pushrod','shoulder_cover')
def is_custom(p):return p.get('leg') and p['mesh'].startswith(custom_prefixes)
def keybase(key):return key.removesuffix('_right')
shapes={p['mesh']:cq.importers.importStep(str(OUT/'step-parts'/f"{p['mesh']}.step")).val() for p in main['parts'] if is_custom(p)}
def nut_modification(shape,key,side):
 if key not in ['knee_head','input_crank']:return shape
 a=math.radians(main['parameters']['crank_phase_deg'])
 x,z=(22,0) if key=='input_crank' else (22*math.cos(a),-22*math.sin(a))
 pocket=hex_nut(8.2,4.3,x,55.6,z,0.01).fuse(cyl(2.8,6.4,(x,55.6,z)))
 if side<0:pocket=pocket.mirror('XZ')
 return shape.cut(pocket).clean()
def printed_shape(shape,p):
 if p['mesh'].endswith('_right'):
  left=copy.deepcopy(p);left['mesh']=p['mesh'].removesuffix('_right');left['leg']=p['leg'][:-1]+'L'
  return printed_shape(shapes[left['mesh']],left).mirror('XZ')
 key=keybase(p['mesh']);front,side=LEGS[p['leg']]
 shape=nut_modification(shape,key,side)
 if key=='hip_hub':
  pad=ring(48,6,3,5)
  for a in range(0,360,60):
   x,z=12*math.cos(math.radians(a)),12*math.sin(math.radians(a))
   pad=pad.cut(cyl(2.2,13,(x,0,z))).cut(cyl(3.8,4.5,(x,3.7,z)))
  for a in [90,210,330]:pad=pad.cut(cyl(1.7,8,(43.5*math.cos(math.radians(a)),0,43.5*math.sin(math.radians(a)))))
  if side<0:pad=pad.mirror('XZ')
  shape=shape.fuse(pad,tol=1e-5).clean()
 if key.startswith('roll_cartridge'):
  pad=cyl(37.1,16.3,(-front*70.3,0,0),(front,0,0)).cut(cyl(33.1,18,(-front*71,0,0),(front,0,0)))
  for z in [-12,24]:pad=pad.cut(cyl(1.7,30,(-front*59.5,side*7,z),(0,side,0)))
  shape=shape.fuse(pad,tol=1e-5).clean()
 if key=='pushrod':
  # Wider printed web preserves the eyes and their purchased bushing interface.
  pad=box(10,6,146,(0,side*70,-85),1)
  shape=shape.fuse(pad,tol=1e-5).clean()
 return shape

def relief(s,key):
 if key=='thigh_inner':
  cut=cyl(43.7,34,(0,10,0))
  for a in POD_TIE_ANGLES:
   x,z=43.5*math.cos(math.radians(a)),43.5*math.sin(math.radians(a));cut=cut.cut(cyl(6,38,(x,8,z)))
  s=s.cut(cut)
 if key=='thigh_outer':
  cut=ring(46.5,42,14.2,56.8)
  for a in POD_TIE_ANGLES:
   x,z=43.5*math.cos(math.radians(a)),43.5*math.sin(math.radians(a));cut=cut.cut(cyl(6,20,(x,54,z)))
  s=s.cut(cut).cut(cyl(38,4.7,(0,88,0)))
 if key=='hip_hub':
  for a in [30,150,270]:
   x,z=31*math.cos(math.radians(a)),31*math.sin(math.radians(a));s=s.cut(cyl(12,5,(x,4,z)))
 if key.startswith('motor_carrier'):
  front=-1 if '-1' in key else 1
  # Open annular pocket from the journal end; preserve the output bolt circle.
  cut=cyl(21,10,(-front*67.4,0,0),(front,0,0)).cut(cyl(17.5,12,(-front*68.4,0,0),(front,0,0)))
  s=s.cut(cut)
 if key.startswith('shoulder_cover'):
  front=-1 if '-1' in key else 1
  s=ring(43.5,42.3,44.4,-48.4).fuse(ring(43.5,12,1.2,-48.4))
  s=s.fuse(ring(52.2,51,45.4,-2.2),ring(52.2,41.5,2.2,-4.4)).cut(box(20,54,46,(-front*45,-24,0),2))
 return s.clean()

def metal_shape(shape,p,code):
 if p["mesh"].endswith("_right"):
  left=copy.deepcopy(p);left["mesh"]=p["mesh"].removesuffix("_right");left["leg"]=p["leg"][:-1]+"L"
  return metal_shape(shapes[left["mesh"]],left,code).mirror("XZ")
 key=keybase(p["mesh"])
 if code=="cnc" or p["material"]=="aluminum":return relief(shape,key)
 return shape

def oriented(shape,key):
 side=-1 if key.endswith('_right') else 1;base=keybase(key)
 if base.startswith(('motor_carrier','roll_cartridge')):shape=shape.rotate((0,0,0),(0,1,0),90)
 else:shape=shape.rotate((0,0,0),(1,0,0),(-90 if base in ['thigh_outer','shin_outer'] else 90)*side)
 bb=shape.BoundingBox();return shape.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))

variants=[]
for code,title in [('printed','Printed first prototype'),('hybrid','Printed shells with metal joint parts'),('cnc','All-metal custom limb parts')]:
 folder=DEST/code
 for sub in ['step','stl','print-stl']:(folder/sub).mkdir(parents=True,exist_ok=True)
 model=copy.deepcopy(main);model['parts']=[p for p in model['parts'] if p.get('leg')];records=[];assembly=cq.Assembly(name=code+'_front_left_limb')
 for key,source in shapes.items():
  uses=[p for p in model['parts'] if p['mesh']==key];p=uses[0];base=keybase(key)
  shape=printed_shape(source,p) if code=='printed' else metal_shape(source,p,code)
  material='petg' if code=='printed' else ('steel' if base=='pushrod' else 'aluminum') if code=='cnc' else p['material']
  density={'petg':1.27e-6,'aluminum':2.70e-6,'steel':7.85e-6}[material]
  assert shape.isValid() and len(shape.Solids())==1,(code,key)
  path=folder/'step'/f'{key}.step';cq.exporters.export(shape,str(path));reopened=cq.importers.importStep(str(path)).val()
  assert reopened.isValid() and len(reopened.Solids())==1,(code,key,'STEP')
  assert abs(reopened.Volume()-shape.Volume())/shape.Volume()<1e-4,(code,key,'volume')
  cq.exporters.export(shape,str(folder/'stl'/f'{key}.stl'),tolerance=.12,angularTolerance=.1)
  vs,fs=shape.tessellate(.25,.12);model['meshes'][key]={'vertices':[list(v.toTuple()) for v in vs],'faces':[list(f) for f in fs]}
  for part in uses:
   part['material']=material;part['mass_kg']=shape.Volume()*density;part['volume_mm3']=shape.Volume();part['com_mm']=list(shape.Center().toTuple());part['color']='#d9d6cc' if material=='petg' else '#aab0a8'
   if part['leg']=='FL':
    tf=matrix(part,POSES['stand']);from OCP.gp import gp_Trsf
    tr=gp_Trsf();tr.SetValues(*tf[:3,:].flatten());assembly.add(shape,name=part['name'],loc=cq.Location(tr),color=cq.Color(part['color']))
  record={'id':key,'title':key.replace('_',' '),'quantity':len(uses),'material':material,'step':'step/'+key+'.step','stl':'stl/'+key+'.stl','mass_kg':shape.Volume()*density,'volume_mm3':shape.Volume(),'unrelieved_mass_kg':source.Volume()*density,'weight_relief_kg':(source.Volume()-shape.Volume())*density if code!='printed' else 0,'step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'process':'Print and inspect' if material=='petg' else 'CNC manufacturing review'}
  if material=='petg':
   printshape=oriented(shape,key);bb=printshape.BoundingBox();bounds=[bb.xlen,bb.ylen,bb.zlen];assert all(a<=b for a,b in zip(bounds,[305,300,315])),(key,bounds)
   cq.exporters.export(printshape,str(folder/'print-stl'/f'{key}.stl'),tolerance=.12,angularTolerance=.1)
   printpath=folder/'print-stl'/f'{key}.stl'
   printmesh=clean_mesh(trimesh.load_mesh(printpath));printmesh.apply_translation([0,0,-printmesh.bounds[0,2]]);printmesh.export(printpath)
   record.update(print_stl='print-stl/'+key+'.stl',print_bounds_mm=printmesh.extents.tolist())
  record['notes']=('Printed joints and adapters are unqualified. Captive M5 nuts replace printed fork threads; bearing fits require calibration.' if code=='printed' else 'Bearing seats, pin fits and shaft retention require supplier tolerancing; no tolerance class is implied by STEP.')
  records.append(record)
 # Standard M5 nuts retain the existing shoulder pins in the printed forks.
 if code=='printed':
  for leg,(front,side) in LEGS.items():
   for group,base in [('crank','input_crank'),('knee','knee_head')]:
    a=math.radians(main['parameters']['crank_phase_deg']);x,z=(22,0) if group=='crank' else (22*math.cos(a),-22*math.sin(a))
    n=hex_nut(8,4,x,55.8,z,2.5)
    if side<0:n=n.mirror('XZ')
    key=f'{leg}_{group}_M5_nut';vs,fs=n.tessellate(.15,.1);model['meshes'][key]={'vertices':[list(v.toTuple()) for v in vs],'faces':[list(f) for f in fs]}
    model['parts'].append({'name':key,'mesh':key,'leg':leg,'group':group,'material':'steel','mass_kg':n.Volume()*7.85e-6,'com_mm':list(n.Center().toTuple()),'color':'#747b74','check':False,'note':'Purchased M5 nut envelope, AF8 x 4 mm; nominal pocket fit, confirm actual hardware.'})
 # Add purchased hardware and motor envelopes to the single-limb STEP.
 for p in model['parts']:
  if p['leg']!='FL' or is_custom(p):continue
  path=OUT/'step-parts'/f"{p['mesh']}.step"
  if path.exists():shape=cq.importers.importStep(str(path)).val()
  elif p['name'].endswith('_M5_nut'):
   group=p['group'];a=math.radians(main['parameters']['crank_phase_deg']);x,z=(22,0) if group=='crank' else (22*math.cos(a),-22*math.sin(a));shape=hex_nut(8,4,x,55.8,z,2.5)
  elif p['name'].endswith('_hip_motor'):shape=motor_envelope()
  elif p['name'].endswith('_knee_motor'):shape=motor_envelope((0,54.4,0))
  elif p['name'].endswith('_roll_motor'):shape=motor_envelope((-67.3,0,0),(1,0,0))
  else:continue
  tf=matrix(p,POSES['stand']);from OCP.gp import gp_Trsf
  tr=gp_Trsf();tr.SetValues(*tf[:3,:].flatten());assembly.add(shape,name=p['name'],loc=cq.Location(tr))
 assembly.save(str(folder/'front-left-limb.step'))
 # Whole-robot torque estimate keeps the existing chassis and replaces limb masses.
 body=[p for p in main['parts'] if not p.get('leg')];engineering.PARTS=body+model['parts'];budget=engineering.mass_budget();torques=engineering.torques(budget['base_kg'])
 model['variant']={'id':code,'title':title,'scope':'Custom limb parts, from roll cartridge to shin; body and battery design are unchanged. Standard bearings, pins, sleeves, fasteners and motors remain purchased/metal hardware.','status':'Manufacturing study; not load-qualified','base_mass_estimate_kg':budget['base_kg']}
 used={p['mesh'] for p in model['parts']};model['meshes']={k:v for k,v in model['meshes'].items() if k in used}
 (folder/'model.json').write_text(json.dumps(model,separators=(',',':')))
 (folder/'parts.json').write_text(json.dumps({'variant':model['variant'],'parts':records},indent=2))
 (folder/'torque-screen.json').write_text(json.dumps({'parent_model_sha256':stamp,'mass':budget,'cases':torques,'scope':'Prescribed loads with variant CAD mass. Does not establish printed strength, thermal limits or walking performance.'},indent=2))
 with (folder/'inventory.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['part','quantity','material','process','STEP','print STL'])
  for r in records:w.writerow([r['id'],r['quantity'],r['material'],r['process'],r['step'],r.get('print_stl','')])
 variants.append({**model['variant'],'directory':code,'custom_part_geometries':len(records),'custom_parts_per_robot':sum(r['quantity'] for r in records),'print_files':sum('print_stl' in r for r in records),'weight_relief_kg':sum(r['weight_relief_kg']*r['quantity'] for r in records)})
 print(code,len(records),'parts',round(budget['base_kg'],3),'kg',flush=True)
(DEST/'manifest.json').write_text(json.dumps({'parent_model_sha256':stamp,'variants':variants},indent=2))
print('Three limb construction variants exported; run verification before publishing.')
