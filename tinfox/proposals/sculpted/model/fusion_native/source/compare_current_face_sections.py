"""Compare direct Fusion face sections with independently reconstructed source cuts."""
import json,hashlib
from pathlib import Path
import numpy as np
import cadquery as cq
from planar_sections import section_by_faces
from audit_sections import sample
ROOT=Path(__file__).resolve().parents[1];raw=ROOT/'exports/current-face-native-sections.json';r=json.loads(raw.read_text());source=cq.importers.importStep(str(ROOT/'snapshots/current-targets/integrated-low-face.step')).val();rows=[]
for record in r['sections']:
 axis='XYZ'.index(record['axis']);cut,_=section_by_faces(source,axis,record['offset_mm']);lines=[c['points_mm'] for c in record['curves']];seg=np.array([(a,b) for line in lines for a,b in zip(line,line[1:])]);start=seg[:,0];delta=seg[:,1]-start;denom=np.maximum((delta*delta).sum(1),1e-30);errors=[]
 for p in [p for line in sample(cut) for p in line]:
  p=np.asarray(p);t=np.clip(((p-start)*delta).sum(1)/denom,0,1);errors.append(float(np.linalg.norm(start+t[:,None]*delta-p,axis=1).min()))
 reverse=[cut.distance(cq.Vertex.makeVertex(*p)) for line in lines for p in line];lengths=[sum(e.Length() for e in cut.Edges()),sum(c['length_mm'] for c in record['curves'])];relative=abs(lengths[0]-lengths[1])/lengths[0];rows.append({'axis':record['axis'],'offset_mm':record['offset_mm'],'source_to_native_mm':max(errors),'native_to_source_mm':max(reverse),'relative_perimeter_error':relative,'boundary_bracket_failed_count':len(record['boundary_failed']),'comparison_passed':max(errors+reverse)<.05 and relative<.002,'boundary_gate_passed':not record['boundary_failed']})
report={'native_section_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'sections':rows,'passed':all(r['comparison_passed'] and r['boundary_gate_passed'] for r in rows),'scope':'Native curves at nine original planes. Direct section boundary consistency failures remain explicit.'};(ROOT/'audits/current-face-direct-native-section-comparison.json').write_text(json.dumps(report,indent=2));print(report)
