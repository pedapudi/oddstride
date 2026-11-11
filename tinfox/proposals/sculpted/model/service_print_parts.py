"""Export bearing-fit coupons and the updated two-piece printed carrier mockups."""
import json,hashlib
import cadquery as cq
from kinematics import ROOT
from build import ring,cyl,box
from printed_carrier import split_carrier
from service_design import OUT,hip_port_cut
rows=[]
for front in [-1,1]:
 source=cq.importers.importStep(str(OUT/'step'/f'motor_carrier_{front}.step')).val()
 pieces,hardware=split_carrier(source,front)
 for kind,s in pieces.items():
  s=hip_port_cut(s);assert s.isValid() and len(s.Solids())==1,(front,kind)
  name=f'printed_carrier_{front}_{kind}'
  cq.exporters.export(s,str(OUT/'step'/f'{name}.step'))
  # Put each perpendicular interface on the bed independently.
  axis=(1,0,0) if kind=='flange' else (0,1,0)
  orient=s.rotate((0,0,0),axis,90);bb=orient.BoundingBox()
  orient=orient.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
  cq.exporters.export(orient,str(OUT/'print-stl'/f'{name}.stl'),tolerance=.08,angularTolerance=.1)
  rows.append({'id':name,'step':f'step/{name}.step','print_stl':f'print-stl/{name}.stl','scope':'Unloaded fit mockup. Keyed two-part carrier with connector windows; printed strength and screw preload unqualified.'})
# Each coupon has an 8 mm seat and a 3 mm rear shoulder with extraction holes.
# These are CAD diameter candidates, not recommended interference values.
for diameter in [27.9,28.0,28.1,28.2]:
 s=ring(19.4,diameter/2,8,0).fuse(ring(19.4,8.2,3,8))
 for xx in [-12.7,12.7]:s=s.cut(cyl(1.3,4,(xx,7.5,0)))
 name='bearing_coupon_'+str(diameter).replace('.','p')
 # Outer face down reproduces the orientation of the complete shin seat.
 s=s.rotate((0,0,0),(1,0,0),90);bb=s.BoundingBox();s=s.translate((0,0,-bb.zmin))
 cq.exporters.export(s,str(OUT/'print-stl'/f'{name}.stl'),tolerance=.05,angularTolerance=.08)
 rows.append({'id':name,'print_stl':f'print-stl/{name}.stl','cad_bore_diameter_mm':diameter,'scope':'Print in the same material/profile as the shin. Assess fit against the selected bearing; do not assume this diameter establishes a production fit.'})
(OUT/'print-extras.json').write_text(json.dumps({'model_sha256':hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest(),'parts':rows},indent=2));print('PRINT EXTRAS READY',len(rows))
