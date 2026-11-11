"""Exercise controlled body edge blends before assembling the robot."""
import cadquery as cq

def form(inset=0):
 stations=[(-232,150,82),(-214,195,94),(-185,222.4,114),(-132,222.4,96),(132,222.4,96),(185,222.4,114),(214,218,104),(232,210,94),(245.4,202,88)]
 wires=[]
 for i,(x,w,h) in enumerate(stations):
  if i==0:x+=inset
  if i==len(stations)-1:x-=inset
  yy=w/2-inset;top=h/2+1.5-inset;bottom=-min(h,96)/2+inset;bevel=18-inset*.35
  wp=cq.Workplane(cq.Plane(origin=(x,0,0),xDir=(0,1,0),normal=(1,0,0)))
  wire=wp.polyline([(-yy+bevel,top),(yy-bevel,top),(yy,top-18),(yy,bottom+17),(yy-17,bottom),(-yy+17,bottom),(-yy,bottom+17),(-yy,top-18)]).close().val()
  wires.append(wire.fillet2D(7-inset*.5,wire.Vertices()))
 s=cq.Solid.makeLoft(wires,ruled=True).clean()
 print('initial',len(s.Faces()),len(s.Edges()),s.isValid(),flush=True)
 for x,r in [(245.4-inset,5-inset),(-232+inset,4-inset)]:
  edges=[e for e in s.Edges() if e.BoundingBox().xlen<1e-4 and abs(e.Center().x-x)<.01]
  try:s=cq.Workplane(obj=s).newObject(edges).fillet(r).val();print('end',x,len(edges),'OK',flush=True)
  except Exception as e:print('end failed',x,str(e),flush=True)
 for x in [-214,-185,-132,132,185,214,232]:
  edges=[e for e in s.Edges() if e.BoundingBox().xlen<1e-4 and abs(e.Center().x-x)<.01]
  try:s=cq.Workplane(obj=s).newObject(edges).fillet(5-inset*.5).val();print('joint',x,len(edges),'OK',flush=True)
  except Exception as e:print('joint failed',x,len(edges),str(e),flush=True)
 return s
if __name__=='__main__':
 for inset in [0,1.6]:
  s=form(inset);print('final',inset,len(s.Faces()),s.isValid(),flush=True)
  cq.exporters.export(s,'tinfox/proposals/sculpted/model/output/body-form-'+str(inset)+'.step')
