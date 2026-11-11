"""Check the native structural stock before adding functional interfaces."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
import cadquery as cq
import slim_limb as sl
from audit_part import audit
from audit_sections import audit as sections
source_dir=ROOT/'snapshots/latest-leg/thigh-stages';source_dir.mkdir(exist_ok=True)
blank=sl.extrusion(sl.outline(9,3.5),85)
blank=cq.Workplane(obj=blank).faces('>Y').edges().fillet(6).val()
fill=blank.intersect(sl.rounded.cap_mask(500))
underside=sl.b.box(220,94,300,(0,0,-90));root=sl.b.cyl(sl.CASE_OUTER_RADIUS,42,(0,9,0))
for theta in sl.b.POD_TIE_ANGLES:root=root.fuse(sl.b.box(12,19,10,(0,41.5,45),2).rotate((0,0,0),(0,1,0),90-theta))
blank=blank.cut(underside.cut(root.clean())).intersect(sl.rounded.cap_mask(500)).intersect(sl.roof()).clean()
edges=[e for e in blank.Edges() if -150<e.Center().z<-55 and e.Center().y>80 and e.Length()>15]
assert edges;blank=blank.fillet(2,edges).clean()
cavity=sl.extrusion(sl.outline(13,3.5).offset2D(-8)[0].toNURBS(),77).cut(underside.translate((0,6,0))).intersect(sl.rounded.cap_mask(496)).intersect(sl.roof(4,True))
shapes={'slim-thigh-structural-stock':blank.cut(cavity),'slim-thigh-continuous-exterior-stock':fill,'slim-thigh-land-stock':blank}
rows=[]
for key,shape in shapes.items():
 path=source_dir/(key+'.step');cq.exporters.export(shape,str(path))
 ref={'id':key,'source_step':str(path),'absolute_mesh_deflection_mm':.005,'volume_method':'gauss_kronrod_spans','volume_method_reason':'The shared thigh contains nonuniform cubic offset surfaces; compare converged span-aware integration.','functional_clearance_cylinders':[[13.5,0,0,-170,0,1,0]],'functional_clearance_proof':'audits/slim-thigh-cavity-analytic-arc-proof.json'}
 a=audit(key,key,ref);b=sections(key,key,ref);rows.append({'part':key,'geometry':a['geometric_gate_passed'],'sections':b['section_gate_passed']})
report={'rows':rows,'passed':all(r['geometry'] and r['sections'] for r in rows),'source_files':{name:hashlib.sha256((ROOT.parent/name).read_bytes()).hexdigest() for name in ['slim_limb.py','seamless_limb.py']},'scope':'Intermediate construction comparison only; completed shell must still match frozen b968 final parts.'}
(ROOT/'audits/slim-thigh-shell-stock-comparison.json').write_text(json.dumps(report,indent=2));print(report)
