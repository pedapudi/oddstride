import cadquery as cq,math,json
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/sunil/git/oddstride/tinfox/proposals/sculpted/model/fusion_native/exports/dfma-architecture-v1');OUT=Path(__file__).parent
shape=cq.importers.importStep(str(ROOT/'dfma-thigh-secondary-round-inboard.step')).val();d=cq.Vector(.5,0,-math.sqrt(3)/2);n=cq.Vector(math.sqrt(3)/2,0,.5)
fig,axs=plt.subplots(1,3,figsize=(15,7));rows=[]
for ax,t in zip(axs,[-4,0,4]):
 sec=shape.intersect(cq.Face.makePlane(500,500,n.multiply(t),n));segments=[]
 for f in sec.Faces():
  for e in f.Edges():
   pts,_=e.sample(80);rs=[p.dot(d)for p in pts];ys=[p.y for p in pts];ax.plot(rs,ys,color='#1586aa',linewidth=1);segments.append(list(zip(rs,ys)))
 ax.axhline(49,color='r',linestyle='--');ax.axhline(50.4,color='g',linestyle='--');ax.set(xlim=(20,52),ylim=(42,90),aspect='equal',title=f'300° section: tangential offset {t} mm',xlabel='radial r, mm',ylabel='Y, mm');ax.grid()
 rows.append({'tangential_offset':t,'segments':segments})
fig.tight_layout();fig.savefig(OUT/'300-root.png',dpi=130);(OUT/'300-root.json').write_text(json.dumps(rows))
