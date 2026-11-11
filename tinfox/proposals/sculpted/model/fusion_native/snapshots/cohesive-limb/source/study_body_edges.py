import cadquery as cq
s=cq.importers.importStep('tinfox/proposals/sculpted/model/output/body-form-0.step').val()
for x in [-214,-185,185,214,232]:
 candidates=[e for e in s.Edges() if e.BoundingBox().xlen<1e-4 and abs(e.Center().x-x)<.01]
 print(x,[(e.geomType(),round(e.Length(),1),round(e.Center().y,1),round(e.Center().z,1)) for e in candidates],flush=True)
 for mode in ['top','straight','small']:
  edges=[e for e in candidates if (e.Center().z>30 and e.Length()>50) if mode=='top'] if mode=='top' else [e for e in candidates if e.geomType()=='LINE']
  try:
   t=cq.Workplane(obj=s).newObject(edges).fillet(2 if mode=='small' else 5).val();print(mode,'OK',flush=True);s=t;break
  except Exception as e:print(mode,'fail',str(e),flush=True)
cq.exporters.export(s,'tinfox/proposals/sculpted/model/output/body-form-refined.step')
