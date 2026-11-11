"""Independent final tool/service check of the split stationary housing candidate."""
from pathlib import Path
import gzip, hashlib, json, math, shutil, sys
import cadquery as cq
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'proposals/sculpted/model'
sys.path.insert(0,str(ROOT));import build as b
STAMP='b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6'
TARGET=ROOT/'fusion_native/snapshots/paired-bearing-target'/STAMP
raw=gzip.decompress((TARGET/'model.json.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==STAMP
model=json.loads(raw);b.P.update(model['parameters'])
F=HERE/'paired-service-input'/STAMP;F.mkdir(parents=True,exist_ok=True)
shutil.copy2(TARGET/'model.json.gz',F/'model.json.gz')
shutil.copy2(TARGET/'source/paired_roll.py',F/'paired_roll.py')
solids={};hashes={};checks=[]
def read(k):
 if k not in solids:
  p=TARGET/'step'/(k+'.step');dst=F/p.name;shutil.copy2(p,dst)
  hashes[k]=hashlib.sha256(dst.read_bytes()).hexdigest();solids[k]=cq.importers.importStep(str(dst)).val()
 return solids[k]
def vol(s):return max(0,sum(x.Volume() for x in s.Solids()))
def overlap(a,c):
 aa,bb=a.BoundingBox(),c.BoundingBox()
 if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-7 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-7 for k in ['x','y','z']):return 0
 return vol(a.intersect(c))
def clear(name,a,c):
 v=overlap(a,c);checks.append(dict(check=name,kind='rigid_clearance',overlap_mm3=v,passed=v<1e-4))
def contact(name,a,c,d):
 v=overlap(a.translate(tuple(.02*x for x in d)),c);checks.append(dict(check=name,kind='axial_contact',footprint_mm2=v/.02,passed=v>1e-6))
for front,leg in [(1,'FL'),(-1,'RL')]:
 cup=read(f'motor_carrier_{front}');hsg=read(f'roll_cartridge_{front}');rear=read(f'roll_stator_backplate_{front}');ret=read(f'roll_outer_retainer_{front}');cap=read(f'hip_stator_closure_{front}')
 rb=read(f'roll_bearing_6810_{front}_0');fb=read(f'roll_bearing_6810_{front}_1')
 contact(f'{front} rear outer race to removable shoulder',rb,rear,(-front,0,0))
 contact(f'{front} rear plate to main housing',rear,hsg,(front,0,0))
 clear(f'{front} registered rear plate seated',rear,hsg)
 for t in [.1,.5,1,3,5,10,25]:clear(f'{front} rear plate withdrawal {t}',rear.translate((-front*t,0,0)),hsg)
 # Small outer-race press pins and a full annular sleeve are clear through
 # the actual housing once the removable end pieces/shaft are absent.
 for angle in range(0,360,45):
  a=math.radians(angle);pin=b.cyl(.4,60,(-100,32*math.cos(a),32*math.sin(a)),(1,0,0))
  if front<0:pin=pin.mirror('YZ')
  clear(f'{front} outer-race pin access {angle}',pin,hsg)
 sleeve=b.cyl(32.4,65,(-100,0,0),(1,0,0)).cut(b.cyl(31.5,67,(-101,0,0),(1,0,0)))
 if front<0:sleeve=sleeve.mirror('YZ')
 clear(f'{front} full outer-race sleeve through bore',sleeve,hsg)
 # Preserve all earlier race paths, now with a separate rear stator plate.
 for name,a,c,d in [
  ('front outer race',fb,ret,(front,0,0)),
  ('rear inner race',rb,read(f'roll_inner_backplate_{front}'),(-front,0,0)),
  ('front inner race',fb,cup,(front,0,0)),
 ]:contact(f'{front} {name}',a,c,d)
 motor=b.motor_envelope((front*5,0,0))
 for t in (0,1,5,20,50,65):clear(f'{front} motor insertion {t}',motor.translate((0,t,0)),cup)
 for t in (0,.1,1,3,10):clear(f'{front} closure removal {t}',cap.translate((0,t,0)),cup)
 hardware=[]
 for p in model['parts']:
  if p.get('leg')==leg and p.get('material')=='steel' and any(s in p['name'] for s in ['roll_','carrier_closure','hip_stator']):
   file=TARGET/'step'/(p['mesh']+'.step')
   if file.exists():hardware.append((p['name'],read(p['mesh'])))
 fixed=[('cup',cup),('housing',hsg),('rear plate',rear),('retainer',ret),('closure',cap),('motor',motor)]+hardware
 for angle in (90,215,325):
  ha=-15 if front<0 and angle==325 else 15
  a=math.radians(angle)
  head=b.cyl(8,3.8,(0,-16,0));handle=b.box(100,3.8,8,(55,-14.1,0)).rotate((0,0,0),(0,1,0),-ha)
  mouth=b.box(20,6,7.1,(-5.8,-14.1,0));tool=head.fuse(handle).cut(mouth)
  tool=tool.rotate((0,0,0),(0,1,0),-angle).translate((front*5+47*math.cos(a),0,47*math.sin(a)))
  positions=[('axial '+str(y),(8*math.cos(a),y,8*math.sin(a))) for y in (-40,-25,-10,-3,0)]
  positions += [('seating '+str(r),(r*math.cos(a),0,r*math.sin(a))) for r in (8,6,4,2,1)]
  for label,delta in positions:
   moved=tool.translate(delta)
   for name,part in fixed:clear(f'{front} wrench lug{angle} handle{ha} {label} / {name}',moved,part)
 print('Finished',front,'checks',len(checks),'fails',len([c for c in checks if not c['passed']]),flush=True)
report=dict(model_sha256=STAMP,checker='Independent exported STEP check; front/rear canonical left assemblies, actual widened slots and removable stationary rear plate.',
 conditions='Generic16mm wrench head,7.1mm jaw,3.8mm thick,100mm handle,±15degree handle angle; wrench front face0.3mm from nut floor. Axial entry at8mm radial standoff, followed by7mm seating, leaving1mm outward offset while the nut flats remain fully inside the jaw. Motor dimensions match reference envelope. All modeled roll-module steel hardware included in tool check.',
 limitations='Sampled rigid paths only. No particular purchased wrench, actual bearing race/seal internals, tolerance sweep, press force, preload, strength or full robot/hand access qualification. End retainers, shaft and motor released for through-bore extraction.',
 checks=checks,failed_checks=[c for c in checks if not c['passed']],step_sha256=hashes)
(HERE/'paired-service-delta.json').write_text(json.dumps(report,indent=2)+'\n');(F/'manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(json.dumps(dict(checks=len(checks),failed=report['failed_checks']),indent=2))
