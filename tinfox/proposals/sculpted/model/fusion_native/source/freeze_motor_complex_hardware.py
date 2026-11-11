"""Freeze purchased reference bodies separately from native custom structure."""
import gzip,json,hashlib,math,sys
from pathlib import Path
import cadquery as cq,numpy as np
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT.parent;sys.path.insert(0,str(MODEL));import build as b
base=ROOT/'snapshots/paired-bearing-target/b968fea927022ba467e05eb52ab602a680e14fd7295c263eefcb95a58a90cdc6';model=json.loads(gzip.decompress((base/'model.json.gz').read_bytes()));old={p['key']:p for p in json.loads((ROOT/'manifests/current-exact-hardware-references.json').read_text())['parts']};folder=ROOT/'snapshots/motor-complex-reference-hardware';folder.mkdir(exist_ok=True);assembly=cq.Assembly(name='Purchased motor complex references');rows=[]
def add(name,shape,provenance,role='standard_hardware'):
 assert shape.isValid();assembly.add(shape,name=name);bounds=shape.BoundingBox();rows.append({'name':name,'role':role,'provenance':provenance,'bounds_mm':[bounds.xmin,bounds.ymin,bounds.zmin,bounds.xmax,bounds.ymax,bounds.zmax],'volume_mm3':shape.Volume()})
for name,key,shift in [('Roll motor','roll_motor_1',(-11.2,0,0)),('Hip pitch motor','hip_motor',(0,0,0)),('Knee pitch motor','knee_motor',(0,0,0))]:
 entry=old[key];path=ROOT/entry['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];shape=cq.importers.importStep(str(path)).val().translate(shift);part=next(p for p in model['parts']if p['name']=='FL_'+('roll_motor'if key=='roll_motor_1'else key));vertices=np.array(model['meshes'][part['mesh']]['vertices']).reshape(-1,3);vertices+=np.array([-5,0,0])if key!='knee_motor'else 0;surface=cq.Compound.makeCompound(shape.Faces());errors=[surface.distance(cq.Vertex.makeVertex(*v))for v in vertices];assert max(errors)<.001,(key,max(errors));add(name,shape,{'source_step':str(path.relative_to(ROOT)),'sha256':entry['sha256'],'translation_mm':shift,'frozen_motor_vertex_samples':len(errors),'max_vertex_error_mm':max(errors)},'vendor_motor')
for p in model['parts']:
 if p.get('leg')!='FL':continue
 key=p['mesh'];name=p['name'];group=p['group'];role=None
 if '_port_'in name and name.endswith(('_socket','_plug','_boot','_cable')):role='connector_'+name.rsplit('_',1)[1]
 elif name.startswith(('FL_roll_bearing_6810','FL_roll_stator_bolt','FL_roll_retainer_','FL_carrier_closure_','FL_hip_stator_bolt','FL_roll_output_bolt')):role='standard_hardware'
 elif name.startswith(('FL_thigh_clamp_nut','FL_thigh_clamp_washer'))or name in ['FL_bolt_0','FL_bolt_1']:role='standard_hardware'
 if not role:continue
 path=base/'step'/(key+'.step')
 if not path.exists():
  assert key in old,key;path=ROOT/old[key]['path']
 shape=cq.importers.importStep(str(path)).val();shift=(-5,0,0)if group in['mount','roll']else(0,0,0);shape=shape.translate(shift);add(name,shape,{'source_step':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'translation_mm':shift},role)
# Ordinary fastener geometry follows the independently checked final assembly,
# including corrected sixty-millimeter ties rather than obsolete references.
for angle in [90,210,330]:
 a=math.radians(angle);x,z=43.5*math.cos(a),43.5*math.sin(a);add(f'Pod M3x60 screw {angle}',b.cyl(1.5,60,(x,1,z)).fuse(b.cyl(2.75,3,(x,61,z))),{'spec':'M3x60 socket screw; underhead Y61'});add(f'Pod M3 nut {angle}',b.hex_nut(5.5,2.4,x,2.6,z,1.5),{'spec':'M3 ordinary 5.5 AF nut; Y2.6..5'})
for angle in range(0,360,60):
 a=math.radians(angle);x,z=12*math.cos(a),12*math.sin(a)
 for label,shaft,y,length,head in [('Hip output M4x8',2,-4.3,8,3.7),('Knee output M4x12',2,49,12,61)]:add(f'{label} {angle}',b.cyl(shaft,length,(x,y,z)).fuse(b.cyl(3.5,4,(x,head,z))),{'spec':label,'source':'Final independent motor-complex release checker'})
for angle in range(20,380,40):
 a=math.radians(angle);x,z=36.5*math.cos(a),36.5*math.sin(a);add(f'Knee stator M3x8 {angle}',b.cyl(1.5,8,(x,45.5,z)).fuse(b.cyl(2.75,3,(x,53.5,z))),{'spec':'M3x8 socket screw; underhead Y53.5'})
path=folder/'motor-complex-purchased-references.step';assembly.save(str(path));report={'source_model_sha256':base.name,'geometry_role':'Purchased hardware/vendor references only. No custom structure is imported. Exact stock and physical fit remain to be measured.','path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parts':rows,'motors':sum(r['role']=='vendor_motor'for r in rows),'connectors':sum(r['role'].startswith('connector_')for r in rows)};assert report['motors']==3 and report['connectors']==24;(ROOT/'manifests/motor-complex-hardware.json').write_text(json.dumps(report,indent=2)+'\n');print({'parts':len(rows),'motors':3,'connectors':24,'sha256':report['sha256']})
