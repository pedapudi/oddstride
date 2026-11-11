"""Compare Fusion's direct section with frozen source, bypassing STEP trim defects."""
import json
from pathlib import Path
import numpy as np
import cadquery as cq
from audit_sections import section,sample
ROOT=Path(__file__).resolve().parents[1];record=json.loads((ROOT/'audits/nose-direct-native-section.json').read_text());source=cq.importers.importStep(str(ROOT/'snapshots/step/body_nose_surround.step')).val();cut=section(source,2,record['offset_mm'],True)
segments=np.array([(a,b) for curve in record['curves'] for a,b in zip(curve['points_mm'],curve['points_mm'][1:])]);start=segments[:,0];delta=segments[:,1]-start;length2=(delta*delta).sum(1);keep=length2>1e-18;start=start[keep];delta=delta[keep];length2=length2[keep]
source_points=[p for line in sample(cut) for p in line];errors=[]
for p in source_points:
 t=np.clip(((np.array(p)-start)*delta).sum(1)/length2,0,1);errors.append(float(np.linalg.norm(start+t[:,None]*delta-np.array(p),axis=1).min()))
native_errors=[cut.distance(cq.Vertex.makeVertex(*p)) for curve in record['curves'] for p in curve['points_mm']];lengths=[sum(e.Length() for e in cut.Edges()),sum(c['length_mm'] for c in record['curves'])];relative=abs(lengths[1]-lengths[0])/lengths[0]
result={'source_to_native_section_max_mm':max(errors),'native_to_source_section_max_mm':max(native_errors),'source_perimeter_mm':lengths[0],'native_perimeter_mm':lengths[1],'relative_perimeter_error':relative,'native_direct_curves':len(record['curves']),'native_stroke_tolerance_mm':record['stroke_tolerance_mm'],'samples':[len(errors),len(native_errors)],'passed':max(errors+native_errors)<.05 and relative<.002,'method':'Fusion native projectCutEdges; temporary metrology sketch and plane removed. No imported geometry. Exact source BRep section compared bidirectionally with native curves stroked at 0.001 mm.','scope':'Qualifies native geometry at the disputed Z plane. Does not erase the independent STEP trim self-consistency failure.'};(ROOT/'audits/nose-direct-native-section-comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
