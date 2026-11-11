"""Instance native master parts in the frozen V0 assembly without geometry copies.

Run only while the native worker is stopped. This creates an editable occurrence
hierarchy; joint and motion validation remain separate migration requirements.
"""
import gzip,json,sys,math
from pathlib import Path
import numpy as np
from run_native import rpc
ROOT=Path(__file__).resolve().parents[1]

def transforms(parameters,pose):
 def translation(x=0,y=0,z=0):
  m=np.eye(4);m[:3,3]=(x,y,z);return m
 def rotation(axis,angle):
  a=math.radians(angle);c,s=math.cos(a),math.sin(a);m=np.eye(4)
  m[:3,:3]=[[1,0,0],[0,c,-s],[0,s,c]] if axis=='x' else [[c,0,s],[0,1,0],[-s,0,c]]
  return m
 result={}
 for leg,(front,side) in {'FL':(1,1),'FR':(1,-1),'RL':(-1,1),'RR':(-1,-1)}.items():
  roll,hip,knee=pose[leg];p=parameters;a=knee+p['crank_phase_deg']
  result[leg]={
   'mount':translation(front*p['hip_x'],side*p['roll_y'],0).tolist(),
   'roll':rotation('x',side*roll).tolist(),
   'thigh':(translation(0,side*p['pitch_offset'],0)@rotation('y',hip)).tolist(),
   'knee':(translation(0,0,-p['thigh'])@rotation('y',knee)).tolist(),
   'crank':rotation('y',a).tolist(),
   'rod':translation(p['crank_radius']*math.cos(math.radians(a)),0,-p['crank_radius']*math.sin(math.radians(a))).tolist()}
 return result

def assemble(allow_partial=False):
 manifest=json.loads((ROOT/'manifests/parts.json').read_text())
 model=json.loads(gzip.decompress((ROOT/manifest.get('reference_model','snapshots/reference-model.json.gz')).read_bytes()))
 pose=model['poses']['stand'];frames=transforms(model['parameters'],pose)
 instances=[{'key':part['id'],**instance} for part in manifest['parts'] for instance in part['instances']]
 reference_manifest=ROOT/'manifests/hardware-references.json'
 if reference_manifest.exists():
  references=json.loads(reference_manifest.read_text())
  instances.extend({'key':'REF_'+part['key'],'name':part['name'],'leg':part['leg'],'kinematic_group':part['kinematic_group'],'reference_geometry':True} for part in references['source_instances'])
 else:assert allow_partial,'Install explicitly marked hardware references before the complete assembly'
 script='''import adsk.core as core,adsk.fusion as fusion,json
def run(_context: str):
 app=core.Application.get();d=fusion.Design.cast(app.activeProduct)
 assert app.activeDocument.name.startswith('Tinfox - Native Master Assembly')
 root=d.rootComponent
 assert not any(o.component.partNumber=='TINFOX_V0_ASSEMBLY' for o in root.occurrences),'V0 assembly already exists'
 library={}
 for group in root.occurrences:
  for occurrence in group.component.occurrences:
   c=occurrence.component
   if (c.bRepBodies.count or c.meshBodies.count) and c.partNumber:library[c.partNumber]=c
 missing=sorted(set(row['key'] for row in INSTANCES)-set(library))
 assert ALLOW_PARTIAL or not missing,('Native masters missing',missing)
 def matrix(rows):
  values=[]
  for i,row in enumerate(rows):values+=row[:3]+[row[3]*.1 if i<3 else row[3]]
  m=core.Matrix3D.create();m.setWithArray(values);return m
 start=d.timeline.count
 assembly_occ=root.occurrences.addNewComponent(core.Matrix3D.create());assembly=assembly_occ.component
 assembly.name='Robot assembly - V0';assembly.partNumber='TINFOX_V0_ASSEMBLY'
 assembly.attributes.add('Tinfox','NativeAssemblyStatus','Incomplete validation; not a manufacturing release')
 body_occ=assembly.occurrences.addNewComponent(core.Matrix3D.create());body_occ.component.name='Chassis and electronics'
 groups={};group_records=[]
 for leg,frames in FRAMES.items():
  mount=assembly.occurrences.addNewComponent(matrix(frames['mount']));mount.component.name=leg+' shoulder datum';groups[(leg,'mount')]=mount.component
  hierarchy=[('roll','mount'),('thigh','roll'),('knee','thigh'),('crank','thigh'),('rod','thigh')]
  for name,parent in hierarchy:
   occurrence=groups[(leg,parent)].occurrences.addNewComponent(matrix(frames[name]));occurrence.component.name=leg+' '+name+' motion frame';groups[(leg,name)]=occurrence.component
   occurrence.component.attributes.add('Tinfox','KinematicFrame',leg+':'+name)
   group_records.append({'leg':leg,'frame':name,'parent':parent,'local_transform_mm':frames[name]})
 mapping=[]
 for row in INSTANCES:
  if row['key'] not in library:continue
  parent=groups[(row['leg'],row['kinematic_group'])] if row['leg'] else body_occ.component
  occurrence=parent.occurrences.addExistingComponent(library[row['key']],core.Matrix3D.create())
  occurrence.attributes.add('Tinfox','SourceInstance',row['name'])
  mapping.append({'source_instance':row['name'],'native_path':occurrence.fullPathName,'master_part':row['key'],'leg':row['leg'],'frame':row['kinematic_group'],'reference_geometry':row.get('reference_geometry',False)})
 for occurrence in root.occurrences:
  if occurrence!=assembly_occ:occurrence.isLightBulbOn=False
 d.timeline.timelineGroups.add(start,d.timeline.count-1).name='V0 native assembly instances'
 app.activeDocument.save('V0 native occurrence assembly; shape and motion migration audits remain open.')
 app.activeViewport.fit()
 print(json.dumps({'instances':mapping,'motion_frames':group_records,'missing_native_masters':missing,'pose':'stand','joint_validation_complete':False,'migration_gate_passed':False}))
'''
 for token,value in [('INSTANCES',instances),('FRAMES',frames),('ALLOW_PARTIAL',allow_partial)]:script=script.replace(token,repr(value))
 result=rpc(script,'assembly',timeout=900)
 if not result[0].get('success',True):return False
 (ROOT/'manifests/assembly.json').write_text(json.dumps(json.loads(result[0]['message']),indent=2))
 return True
if __name__=='__main__':sys.exit(0 if assemble('--partial' in sys.argv) else 1)
