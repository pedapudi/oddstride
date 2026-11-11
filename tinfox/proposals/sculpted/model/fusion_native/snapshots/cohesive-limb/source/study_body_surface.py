"""Controlled analytic sections with a planar center and normal skin offset."""
import math,cadquery as cq,numpy as np

def section(x,w,top,bottom):
 yy=w/2
 wire=cq.Workplane('YZ',origin=(x,0,0)).polyline([(-yy+18,top),(yy-18,top),(yy,top-18),(yy,bottom+17),(yy-17,bottom),(-yy+17,bottom),(-yy,bottom+17),(-yy,top-18)]).close().val()
 return wire.fillet2D(7,wire.Vertices())

def dims(x):
 side=1 if x>=0 else -1;s=abs(x)
 if s<=132:return 222.4,49.5,-48
 if s<=185:
  f=(1-math.cos(math.pi*(s-132)/53))/2
  return 222.4,49.5+9*f,-48
 end=245.4 if side>0 else 232
 t=(s-185)/(end-185);f=(1-math.cos(math.pi*t))/2
 return (222.4-(20.4 if side>0 else 72.4)*f,58.5-(13 if side>0 else 16)*f,-48+(4 if side>0 else 7)*f)

def form():
 front=[132,138,148,160,172,180,185,192,202,214,226,236,242,245.4]
 back=[-232,-228,-221,-212,-202,-192,-185,-180,-172,-160,-148,-138,-132]
 a=cq.Solid.makeLoft([section(x,*dims(x)) for x in front],ruled=False)
 b=cq.Solid.makeLoft([section(x,*dims(x)) for x in back],ruled=False)
 c=cq.Solid.extrudeLinear(section(-132,*dims(0)),[],cq.Vector(264,0,0))
 s=a.fuse(c).fuse(b).clean()
 print('surface',s.isValid(),len(s.Solids()),len(s.Faces()),flush=True)
 for x,r in [(245.4,5),(-232,4)]:
  es=[e for e in s.Edges() if e.BoundingBox().xlen<1e-4 and abs(e.Center().x-x)<.01]
  s=cq.Workplane(obj=s).newObject(es).fillet(r).val();print('edge rounded',x,flush=True)
 return s
if __name__=='__main__':
 s=form();cq.exporters.export(s,'tinfox/proposals/sculpted/model/output/body-smooth-outer.step')
 skin=s.hollow([],-1.6);print('offset',skin.isValid(),len(skin.Shells()),skin.Volume(),flush=True)
 for sh in skin.Shells():print(sh.BoundingBox().xlen,cq.Solid.makeSolid(sh).Volume(),flush=True)
 cq.exporters.export(skin,'tinfox/proposals/sculpted/model/output/body-smooth-skin.step')
