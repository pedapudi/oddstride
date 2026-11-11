"""Compare nine exact planar cuts and write an overlaid visual section sheet."""
import json,sys,math,hashlib,html
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln,gp_Pnt,gp_Dir
from audit_part import source_shape
from periodic_boundary_distance import BoundaryDistance
ROOT=Path(__file__).resolve().parents[1]

def section(shape,axis,offset,approximation=False):
 origin=[0.,0.,0.];origin[axis]=offset;normal=[0.,0.,0.];normal[axis]=1.
 operation=BRepAlgoAPI_Section(shape.wrapped,gp_Pln(gp_Pnt(*origin),gp_Dir(*normal)),False)
 # Explicit surface p-curves keep trimmed NURBS intersections on the parent
 # face. Without them OCC can return phantom curves outside that same solid.
 operation.ComputePCurveOn1(True);operation.Approximation(approximation);operation.Build()
 assert operation.IsDone(),'Section operation failed'
 return cq.Shape.cast(operation.Shape())

def sample(shape):
 rows=[]
 for edge in shape.Edges():
  count=max(5,min(101,math.ceil(edge.Length()/2)+1))
  rows.append([edge.positionAt(float(t)).toTuple() for t in np.linspace(0,1,count)])
 return rows

def audit(key, export_label=None, reference_override=None):
 label=export_label or key
 record=reference_override or next(p for p in json.loads((ROOT/'manifests/parts.json').read_text())['parts'] if p['id']==key)
 source_path=ROOT/record['source_step'];native_path=ROOT/'exports'/f'{label}.step'
 source=source_shape(record);native=cq.importers.importStep(str(native_path)).val();boundary=[BoundaryDistance(source),BoundaryDistance(native)]
 vertices,_=source.tessellate(.02,.05);points=np.array([v.toTuple() for v in vertices]);low=points.min(0);high=points.max(0)
 rows=[];panels=[]
 for axis in range(3):
  for index,fraction in enumerate([.25,.5,.75]):
   offset=float(low[axis]+fraction*(high[axis]-low[axis]));attempts=[]
   for approximation in [False,True]:
    a=section(source,axis,offset,approximation);b=section(native,axis,offset,approximation);curves=[sample(a),sample(b)]
    self_errors=[max((distance(point) for polyline in polylines for point in polyline),default=0) for polylines,distance in zip(curves,boundary)]
    attempts.append({'approximation':approximation,'section_to_own_solid_max_mm':self_errors})
    if max(self_errors)<.005:break
   errors=[]
   for polylines,target in [(curves[0],b),(curves[1],a)]:
    for polyline in polylines:errors.extend(target.distance(cq.Vertex.makeVertex(*point)) for point in polyline)
   lengths=[sum(e.Length() for e in s.Edges()) for s in [a,b]]
   error=max(errors,default=0);relative=abs(lengths[0]-lengths[1])/max(lengths[0],1e-12)
   if error>=.05 or relative>=.002 or max(self_errors)>=.005:
    from planar_sections import section_by_faces
    original={'error_mm':error,'perimeters_mm':lengths,'self_errors_mm':self_errors}
    a,ad=section_by_faces(source,axis,offset);b,bd=section_by_faces(native,axis,offset);curves=[sample(a),sample(b)]
    self_errors=[max((distance(p) for line in lines for p in line),default=0) for distance,lines in zip(boundary,curves)]
    errors=[target.distance(cq.Vertex.makeVertex(*p)) for lines,target in [(curves[0],b),(curves[1],a)] for line in lines for p in line]
    lengths=[sum(e.Length() for e in q.Edges()) for q in [a,b]];error=max(errors,default=0);relative=abs(lengths[0]-lengths[1])/max(lengths[0],1e-12)
    attempts.append({'method':'analytical planar-face intervals plus surface intersections','original_boolean_result':original,'source_planar_faces':ad,'native_planar_faces':bd,'section_to_own_solid_max_mm':self_errors})
   rows.append({'axis':'XYZ'[axis],'offset_mm':offset,'source_edges':len(a.Edges()),'native_edges':len(b.Edges()),'source_perimeter_mm':lengths[0],'native_perimeter_mm':lengths[1],'relative_perimeter_error':relative,'symmetric_sampled_error_max_mm':error,'section_to_own_solid_max_mm':self_errors,'samples':len(errors),'kernel_attempts':attempts,'pass':bool(error<.05 and relative<.002 and max(self_errors)<.005)})
   coordinates=[k for k in range(3) if k!=axis];span=max(high[coordinates]-low[coordinates]);scale=210/max(span,1)
   x0=axis*300;y0=index*280;paths=[]
   for color,polylines in zip(['#007f87','#e65a27'],curves):
    for polyline in polylines:
     projected=[((p[coordinates[0]]-low[coordinates[0]])*scale+x0+25,y0+240-(p[coordinates[1]]-low[coordinates[1]])*scale) for p in polyline]
     paths.append('<polyline fill="none" stroke="'+color+'" stroke-width="0.7" points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in projected)+'"/>')
   panels.append(f'<text x="{x0+15}" y="{y0+18}" font-size="12">{"XYZ"[axis]} = {offset:.2f} mm; max {error:.4f} mm</text>'+''.join(paths))
 result={'part':key,'source_step_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),'source_brep_sha256':record.get('source_brep_sha256'),'source_reference_note':record.get('source_reference_note'),'native_step_sha256':hashlib.sha256(native_path.read_bytes()).hexdigest(),'sections':rows,'periodic_surface_projection_recoveries':{'source':boundary[0].recoveries,'native':boundary[1].recoveries},'section_gate_passed':all(r['pass'] for r in rows),'section_algorithm':{'compute_parent_pcurves':True,'primary_approximation':False,'fallback_approximation':True,'fallback_condition':'Retry approximation for off-parent curves. If discrepancy remains, independently reconstruct analytical planar-face intervals from trim roots and inside-face classification, retaining original results. Same sample planes and pass thresholds.'},'tolerances':{'sampled_distance_mm':.05,'relative_perimeter':.002,'section_to_own_solid_mm':.005},'scope':'Nine sampled planar cuts supplement the full-surface comparison. They do not replace functional datums, service-path or editability audits.'}
 (ROOT/'audits'/f'{label}-sections.json').write_text(json.dumps(result,indent=2))
 svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 890"><rect width="900" height="890" fill="#faf9f5"/><g font-family="sans-serif" fill="#222">'+f'<text x="15" y="25" font-size="17">{html.escape(key)} - V0 section comparison</text><text x="15" y="45" font-size="12">Teal: frozen source. Orange: native Fusion export. Units: mm.</text><g transform="translate(0,55)">'+''.join(panels)+'</g></g></svg>'
 (ROOT/'audits'/f'{label}-sections.svg').write_text(svg)
 print(key,'section gate',result['section_gate_passed'],'maximum deviation',max(r['symmetric_sampled_error_max_mm'] for r in rows),flush=True)
 return result
if __name__=='__main__':audit(sys.argv[1])
