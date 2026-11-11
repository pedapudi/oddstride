"""Export the revised whole robot while preserving unchanged source solids."""
import json,hashlib,math
import cadquery as cq
import numpy as np
from scipy.spatial.transform import Rotation
from kinematics import ROOT,POSES,matrix,LEGS
from service_design import OUT,port_box
from build import motor_envelope
source=cq.Assembly.importStep(str(ROOT/'output/tinfox-assembly.step'))
data=json.loads((OUT/'model.json').read_text());assembly=cq.Assembly(name='Tinfox_bearing_connector_revision');count=0;volume=0;shapes={}
for p in data['parts']:
 if p.get('service_role') in ['keepout','withdrawal']:continue
 key=p['mesh'];path=OUT/'step'/f'{key}.step'
 if p['name'].endswith('_motor'):
  family=p['name'].split('_')[1];front,side=LEGS[p['leg']];face=54.4 if family=='knee' else 0
  s=motor_envelope((0,face,0))
  for sign in [-1,1]:s=s.cut(port_box(16,6,15,face,sign,-7))
  if family=='roll':
   s=s.rotate((0,0,0),(0,0,1),-90).translate((-67.3,0,0))
   if front<0:s=s.mirror('YZ')
  if side<0:s=s.mirror('XZ')
 elif path.exists():
  if key not in shapes:shapes[key]=cq.importers.importStep(str(path)).val()
  s=shapes[key]
 else:s=source.objects[p['name']].obj
 assert isinstance(s,cq.Shape) and s.isValid(),p['name']
 m=matrix(p,POSES['stand']);rv=Rotation.from_matrix(m[:3,:3]).as_rotvec();a=np.linalg.norm(rv);axis=rv/a if a>1e-12 else np.array([1,0,0])
 loc=cq.Location(cq.Vector(*m[:3,3]),cq.Vector(*axis),math.degrees(a));color=p['color'];rgb=tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
 assembly.add(s,name=p['name'],loc=loc,color=cq.Color(*rgb));count+=1;volume+=s.Volume()
assembly.export(str(OUT/'updated-robot.step'));assembly.export(str(OUT/'updated-robot.glb'))
check=cq.Assembly.importStep(str(OUT/'updated-robot.step'));assert len(check.children)==count,(count,len(check.children))
actual=sum(x.obj.Volume() for x in check.children);err=abs(actual-volume)/volume;assert err<1e-5,err
(OUT/'assembly-export.json').write_text(json.dumps({'model_sha256':hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),'physical_components':count,'reopened_components':len(check.children),'relative_volume_error':err,'omitted':['Translucent clearance and withdrawal reservations'],'scope':'Nominal geometry; manufacturing fits and structural strength unqualified.'},indent=2));print('Full assembly STEP/GLB exported and reopened:',count,err,flush=True)
