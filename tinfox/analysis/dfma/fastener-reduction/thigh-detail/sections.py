import cadquery as cq,json,hashlib
from pathlib import Path
ROOT=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native/exports/dfma-architecture-v1'); OUT=Path(__file__).parent
parts={k:cq.importers.importStep(str(ROOT/f'dfma-thigh-{k}-round-inboard.step')).val() for k in ['primary','secondary']}
rows=[]; panels=[]
for axis,coords in [('z',[-40,-42,-44,-45.4,-48,-50,-55,-60,-65,-70]),('y',[46.5,48,49,49.1,50,50.4,51,53.5])]:
 for value in coords:
  faces=[]; lines=[]
  for k,shape in parts.items():
   base=(0,0,value) if axis=='z' else (0,value,0); normal=(0,0,1) if axis=='z' else(0,1,0)
   sec=shape.intersect(cq.Face.makePlane(400,400,base,normal))
   for f in sec.Faces():
    b=f.BoundingBox(); faces.append({'part':k,'area':f.Area(),'bounds':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]})
    for e in f.Edges():
     pts,_=e.sample(40); xy=[(p.x,p.y if axis=='z' else -p.z)for p in pts];lines.append((k,xy))
  rows.append({'axis':axis,'value':value,'faces':faces});panels.append((axis,value,lines))
# SVG diagrams, all same scale; axis z use X vs Y, axis y use X vs -Z
for axis in ['z','y']:
 ps=[p for p in panels if p[0]==axis];w=440;h=420 if axis=='z' else 700;svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*4}" height="{h*((len(ps)+3)//4)}" viewBox="0 0 {w*4} {h*((len(ps)+3)//4)}"><rect width="100%" height="100%" fill="white"/>']
 for i,(_,value,lines)in enumerate(ps):
  ox=(i%4)*w+180;oy=(i//4)*h+50;scale=3
  svg.append(f'<text x="{(i%4)*w+10}" y="{(i//4)*h+24}" font-family="sans-serif" font-size="18">{axis} = {value}</text>')
  for part,xy in lines:
   points=' '.join(f'{ox+x*scale:.3f},{oy+y*scale:.3f}'for x,y in xy);color='#d15b16'if part=='primary'else'#1586aa';svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.3"/>')
 svg.append('</svg>');(OUT/f'sections-{axis}.svg').write_text('\n'.join(svg))
 try:
  import cairosvg;cairosvg.svg2png(url=str(OUT/f'sections-{axis}.svg'),write_to=str(OUT/f'sections-{axis}.png'))
 except Exception as e:print(e)
report={'sources':{str(ROOT/f'dfma-thigh-{k}-round-inboard.step'):hashlib.sha256((ROOT/f'dfma-thigh-{k}-round-inboard.step').read_bytes()).hexdigest()for k in parts},'sections':rows};(OUT/'sections.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows[:10],indent=2))
