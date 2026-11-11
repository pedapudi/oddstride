"""Rounded enclosure concept, separate from the audited migration reference."""
import json,math,hashlib,copy
from pathlib import Path
from functools import cache
import cadquery as cq
import numpy as np
from scipy.spatial.transform import Rotation
import build as b
import service_design as sd
from kinematics import ROOT,P,LEGS,POSES,matrix
BASE=ROOT/'output/service-design';OUT=ROOT/'output/rounded-design'
for folder in ['', 'step','stl','print-stl']:(OUT/folder).mkdir(parents=True,exist_ok=True)
box,cyl,ring=b.box,b.cyl,b.ring

def source(key):
 path=BASE/'step'/f'{key}.step'
 if not path.exists():path=ROOT/'output/step-parts'/f'{key}.step'
 return cq.importers.importStep(str(path)).val()

def oval_loft(sections,inset=0):
 wires=[]
 for z,cx,cy,w,d in sections:
  wires.append(cq.Workplane('XY',origin=(cx,cy,z)).ellipse(w/2-inset,d/2-inset).val())
 return cq.Solid.makeLoft(wires,ruled=False)

@cache
def shin_shell(outer):
 sections=[(-18, b.shin_center(-18),83,38,34),(-42,b.shin_center(-42),83,34,33),(-66,b.shin_center(-66),83,30.5,31),(-90,b.shin_center(-90),83,28,30),(-114,b.shin_center(-114),83,25.5,29),(-136,b.shin_center(-136),83,24,28)]
 blank=oval_loft(sections)
 # Preserve the bearing/rocker envelope and seats from the service design.
 for yy in [67,91]:blank=blank.fuse(ring(24.5,19.2,8,yy))
 cavity=oval_loft([(-24,b.shin_center(-24),83,37,33),*sections[1:-1],(-130,b.shin_center(-130),83,24.5,28.5)],4)
 shell=blank.cut(cavity).fuse(b.integrated_knee_head(),box(16.6,16.8,37.4,(-2,83,-30.5),3.2))
 for yy in [67,90]:shell=shell.fuse(ring(19.4,14,11,yy))
 shell=shell.fuse(ring(19.4,8.2,3,78),ring(19.4,8.2,3,87))
 for yy in [66,90]:shell=shell.cut(cyl(14,12,(0,yy,0)))
 for zz in [-30,-105]:
  shell=shell.fuse(box(20,27,15,(2,83,zz),2).intersect(blank))
  shell=shell.cut(cyl(4.05,18,(2,74,zz))).cut(cyl(2.2,42,(2,62,zz)))
  shell=shell.cut(cyl(3.7,13,(2,92,zz))).cut(b.hex_nut(7.2,14,2,60,zz,.01))
 x=22*math.cos(math.radians(P['crank_phase_deg']));z=-22*math.sin(math.radians(P['crank_phase_deg']))
 shell=shell.cut(b.hex_nut(8.2,4.3,x,71.6,z,.01)).cut(cyl(2.8,6.4,(x,71.6,z)))
 shell=shell.cut(cyl(3.025,4.1,(x,77.9,z))).cut(cyl(3.05,8.2,(x,90,z)))
 shell=shell.cut(cyl(6.3,8.4,(x,81.8,z))).cut(cyl(5.3,6,(x,98,z)))
 shell=shell.cut(cyl(8.2,48,(0,60,0))).cut(sd.rod_clearance())
 for xx in [-12.7,12.7]:shell=shell.cut(cyl(1.3,16,(xx,77,0)))
 half=shell.intersect(box(120,60,240,(0,113 if outer else 53,-85)))
 for zz in [-60,-120]:
  # Locate tongue at the oval's widest lateral section on the split plane.
  widths={-60:31.3,-120:25.2};xx=b.shin_center(zz)+widths[zz]/2-2
  tongue=box(4,4,10,(xx,83,zz),.6)
  if outer:half=half.cut(box(4.4,4.4,10.4,(xx,83,zz),.6))
  else:half=half.fuse(tongue.intersect(blank))
 return half.clean().translate((0,-16,0))

@cache
def thigh_shell(outer):
 old=source('thigh_outer' if outer else 'thigh_inner')
 sections=[(-53,-.5,69,72,52),(-66,-.5,69,62,51),(-92,-1,69,50,50),(-121,-1,69,44,50),(-144,-1,69,43,51),(-157,0,69,45,52)]
 envelope=oval_loft(sections)
 wall=envelope.cut(oval_loft([(z-2 if z==-157 else z+2 if z==-53 else z,cx,cy,w,d) for z,cx,cy,w,d in sections],4))
 # Open the loft ends into the retained motor and bearing structures.
 wall=wall.cut(oval_loft([(-50,-.5,69,64,44),(-66,-.5,69,54,43),(-92,-1,69,42,42),(-121,-1,69,36,42),(-144,-1,69,35,43),(-160,0,69,37,44)]))
 # Split on the new median mating plane, preserving the joint regions intact.
 wall=wall.intersect(box(140,80,240,(0,109 if outer else 29,-100)))
 # Leave the knee's rotating shin head between the original bearing cheeks.
 wall=wall.cut(cyl(38,44,(0,49.5,-170)))
 # Reserve the shin's flexion sweep inside the structural halves. The outer
 # faces remain curved; the inner edge opens only where the moving shin needs it.
 sweep_blank=oval_loft([(-18,b.shin_center(-18),67,41,37),(-42,b.shin_center(-42),67,37,36),(-90,b.shin_center(-90),67,31,33),(-136,b.shin_center(-136),67,27,31)])
 tools=[sweep_blank.rotate((0,0,0),(0,1,0),q).translate((0,0,-170)) for q in range(-156,-47,6)]
 wall=wall.cut(*tools)
 trim=box(160,160,85,(0,69,-106.5)) # -149 .. -64
 s=old.cut(trim).fuse(wall)
 if outer:
  # Spherical cap, constant radial wall, replaces the flat motor-face center.
  radius=(40.8**2+8.5**2)/(2*8.5);center=cq.Vector(0,100-radius,0)
  outer_s=cq.Solid.makeSphere(radius,center,angleDegrees1=-90,angleDegrees2=90)
  inner_s=cq.Solid.makeSphere(radius-3,center,angleDegrees1=-90,angleDegrees2=90)
  cap=outer_s.cut(inner_s).intersect(cyl(40.8,10,(0,91.5,0)))
  s=s.cut(cyl(35.5,5,(0,91,0))).fuse(cap)
 # The rod needs a continuous opening; retain its complete sampled clearance.
 for knee in np.arange(-156,-47,3):
  a=math.radians(knee+P['crank_phase_deg'])
  x=22*math.cos(a);z=-22*math.sin(a)
  # Link remains parallel to the thigh in this equal-crank mechanism.
  path=box(19,13,189,(x,70,z-85),2)
  s=s.cut(path.intersect(box(150,150,100,(0,69,-106))))
 return s.clean()

@cache
def hip_pod(front):
 stations=[(-51.5,46),(-49,49),(-40,53),(-25,53),(-12,50.5),(-3,48),(1.5,48)]
 outer=cq.Solid.makeLoft([cq.Wire.makeCircle(r,cq.Vector(0,y,0),cq.Vector(0,1,0)) for y,r in stations],ruled=False)
 inner=cq.Solid.makeLoft([cq.Wire.makeCircle(r-2.7,cq.Vector(0,y,0),cq.Vector(0,1,0)) for y,r in [(-48.8,48),*stations[2:-1],(4,48)]],ruled=False)
 s=outer.cut(inner).cut(cyl(13,8,(0,-54,0)))
 # Broad neck opening around the elbow carrier and roll-output coupling.
 s=s.cut(box(36,90,80,(-front*49,-15,0),7))
 # Open neck allows wiring to pass toward the stationary body.
 for sign in [-1,1]:
  s=s.cut(sd.connector_parts(0,sign)[3]).cut(sd.cable_space(0,sign))
 # All cover walls remain clear of the existing metal carrier.
 carrier=source('motor_carrier_'+str(front))
 # Replace the cylindrical shroud with the rounded enclosure, retaining the
 # elbow, bearing journal, motor mounting face and their existing fasteners.
 remove=ring(43.6,41.4,40.8,-45.5).cut(box(40,65,65,(-front*47,-22,0),6))
 carrier=carrier.cut(remove)
 back=ring(46,12,3.6,-50).cut(box(36,90,80,(-front*49,-15,0),7))
 flange=ring(48,27,3,-3.9)
 for a in range(0,360,40):
  flange=flange.cut(cyl(1.7,5,(36.5*math.cos(math.radians(a)),-4.9,36.5*math.sin(math.radians(a)))))
 s=s.fuse(carrier,back,flange)
 for sign in [-1,1]:s=s.cut(sd.connector_parts(0,sign)[3]).cut(sd.cable_space(0,sign))
 return s.clean()

@cache
def body_shell():
 old=source('body_center_0')
 # Raised compound-curved roof loft, keeping the attachment and service edges.
 wires=[];inner=[]
 for z,w,d,r in [(46.8,249.5,201,19),(50,246,195,23),(54,230,174,32),(55.5,212,145,36)]:
  q=cq.Workplane('XY',origin=(0,0,z)).rect(w,d).val();wires.append(q.fillet2D(r,q.Vertices()))
  q=cq.Workplane('XY',origin=(0,0,z-3)).rect(w-6,d-6).val();inner.append(q.fillet2D(r-3,q.Vertices()))
 dome=cq.Solid.makeLoft(wires,ruled=False).cut(cq.Solid.makeLoft(inner,ruled=False))
 s=old.fuse(dome)
 # Avoid a double wall beneath the raised roof, preserving the full edge rim.
 core=cq.Workplane('XY',origin=(0,0,45.8)).rect(207,139).extrude(4).edges('|Z').fillet(32).val()
 s=s.cut(core)
 # Keep display window and lidar separate and their service volumes open.
 s=s.cut(box(50,30,20,(20,0,55),4)).cut(cyl(31.8,20,(82,0,52),(0,0,1)))
 seat=cyl(34,3,(82,0,49),(0,0,1)).cut(cyl(8,5,(82,0,48),(0,0,1)))
 s=s.fuse(seat)
 # Fixed roll cartridges receive rounded cuffs integral to the body cover.
 for front in [-1,1]:
  for side in [-1,1]:
   stations=[(118.8,48,42.5),(128,48,42.5),(132,43,37.5),(135,40.5,37.5)]
   outer=cq.Solid.makeLoft([cq.Wire.makeCircle(ro,cq.Vector(front*x,side*68,0),cq.Vector(1,0,0)) for x,ro,ri in stations],ruled=True)
   inner=cq.Solid.makeLoft([cq.Wire.makeCircle(ri,cq.Vector(front*x,side*68,0),cq.Vector(1,0,0)) for x,ro,ri in stations],ruled=True)
   cuff=outer.cut(inner).intersect(box(400,400,100,(0,0,50)))
   root=box(9,32,5,(front*121,side*68,46.5),1)
   s=s.fuse(cuff,root)
   s=s.cut(box(14,184,4.6,(front*121,0,41.8)))
   for z in [-12,24]:s=s.cut(box(14,16,14,(front*125.5,side*94.5,z),.8))
 # Pitch motion requires an open lower shoulder, including the enlarged oval root.
 for front in [-1,1]:s=s.cut(cyl(67,400,(front*185,-200,0),(0,1,0)))
 return s.clean()

def build():
 model=json.loads((BASE/'model.json').read_text());stamp=hashlib.sha256((BASE/'model.json').read_bytes()).hexdigest()
 exact={};changed={};catalog=[]
 def register(key,shape):
  assert shape.isValid() and len(shape.Solids())==1,(key,shape.isValid(),len(shape.Solids()))
  exact[key]=shape;v,f=shape.tessellate(.09,.09)
  model['meshes'][key]={'vertices':[list(q.toTuple()) for q in v],'faces':[list(q) for q in f]}
 def replace(key,shape,note):
  register(key,shape);changed[key]=shape
  for p in model['parts']:
   if p['mesh']==key:
    bb=shape.BoundingBox();p.update(volume_mm3=shape.Volume(),mass_kg=shape.Volume()*b.DENSITY[p['material']],com_mm=list(shape.Center().toTuple()),bounds_mm=[bb.xlen,bb.ylen,bb.zlen],note=note)
 for outer in [False,True]:
  name='shin_outer' if outer else 'shin_inner';s=shin_shell(outer)
  print(name,len(s.Solids()),s.isValid(),flush=True)
  replace(name,s,'Rounded closed oval shin half. Existing bearing seats, axle and pushrod pivots retained; four-millimetre nominal sidewall with existing clamp and extraction access.')
  replace(name+'_right',s.mirror('XZ'),'Mirrored rounded oval shin half; unchanged bearing and linkage datums.')
  name='thigh_outer' if outer else 'thigh_inner';s=thigh_shell(outer)
  print(name,len(s.Solids()),s.isValid(),flush=True)
  replace(name,s,'Rounded structural thigh half with lofted oval web; existing motor carrier, knee interfaces and joint datums retained. Mating-land closure and printed strength require further detailing.')
  replace(name+'_right',s.mirror('XZ'),'Mirrored rounded structural thigh half.')
 replace('body_center_0',body_shell(),'Rounded roof over the existing body cover; preserved chassis attachment points. Display and lidar openings remain provisional.')
 for front in [-1,1]:
  s=hip_pod(front);name='motor_carrier_'+str(front)
  replace(name,s,'V1 rounded moving hip enclosure integrated with the existing carrier. Motor flange, bearing journal and elbow retained; cylindrical shroud replaced. Printed carrier split and strength require validation.')
  replace(name+'_right',s.mirror('XZ'),'Mirrored integrated rounded carrier enclosure; retained V0 mechanical interfaces.')
 for key,s in changed.items():
  cq.exporters.export(s,str(OUT/'step'/f'{key}.step'));cq.exporters.export(s,str(OUT/'stl'/f'{key}.stl'),tolerance=.08,angularTolerance=.08)
  check=cq.importers.importStep(str(OUT/'step'/f'{key}.step')).val();assert check.isValid() and len(check.Solids())==1,key
  err=abs(check.Volume()-s.Volume())/s.Volume();assert err<1e-4,(key,err)
  catalog.append({'id':key,'step':f'step/{key}.step','stl':f'stl/{key}.stl','volume_mm3':s.Volume(),'roundtrip_volume_error':err})
 model['status']='Tinfox V1 rounded articulated enclosure proposal. Accepted V0 retained as native migration reference. Existing component count and joint datums retained; mating lands, printed carrier split, strength and full motion qualification remain unfinished.'
 model['source_model_sha256']=stamp
 raw=json.dumps(model,separators=(',',':')).encode();(OUT/'model.json').write_bytes(raw)
 (OUT/'parts.json').write_text(json.dumps({'model_sha256':hashlib.sha256(raw).hexdigest(),'parts':catalog,'scope':model['status']},indent=2))
 print('ROUNDED MODEL',len(model['parts']),len(changed),flush=True)
if __name__=='__main__':build()
