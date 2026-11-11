"""Resolve one retained STEP section diagnostic using native boundary metrology."""
import hashlib
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from audit_sections import section, sample

ROOT=Path(__file__).resolve().parents[1]


def distance(points, lines):
    starts=np.asarray([a for line in lines for a in line[:-1]])
    ends=np.asarray([b for line in lines for b in line[1:]])
    delta=ends-starts
    denom=np.maximum(np.einsum('ij,ij->i',delta,delta),1e-30)
    greatest=0.
    for point in points:
        t=np.clip(np.einsum('ij,ij->i',point-starts,delta)/denom,0,1)
        greatest=max(greatest,float(np.linalg.norm(starts+t[:,None]*delta-point,axis=1).min()))
    return greatest


def main():
    path=ROOT/'exports/current-outer-native-section-pair.json'
    raw=path.read_bytes();capture=json.loads(raw)
    mapping=json.loads((ROOT/'manifests/whole-native-component-map-candidate.json').read_text())['parts']
    parts={p['part']:p for p in capture['parts']}
    assert set(parts)=={'thigh_outer','thigh_outer_right'}
    assert all(p['native_boundary_check_passed']for p in parts.values())
    for key,part in parts.items():
        assert part['reference_native_step_sha256']==mapping[key]['native_step_sha256']
        assert part['component_part_number']==mapping[key]['component_part_number']
    left,right=parts['thigh_outer'],parts['thigh_outer_right']
    assert left['offset_mm']==75 and right['offset_mm']==-75
    a=[[[p[0],-p[1],p[2]]for p in curve['points_mm']]for curve in left['curves']]
    b=[curve['points_mm']for curve in right['curves']]
    error=max(distance([p for line in a for p in line],b),distance([p for line in b for p in line],a))
    lengths=[sum(c['length_mm']for c in part['curves'])for part in [left,right]]
    perimeter_error=abs(lengths[0]-lengths[1])/lengths[0]
    step_path=ROOT/mapping['thigh_outer_right']['native_step']
    step_cut=section(cq.importers.importStep(str(step_path)).val(),1,-75)
    step_lines=sample(step_cut)
    native_to_exact_step=max(step_cut.distance(cq.Vertex.makeVertex(*p))for line in b for p in line)
    step_to_native=distance([p for line in step_lines for p in line],b)
    export_error=max(native_to_exact_step,step_to_native)
    export_length=sum(edge.Length()for edge in step_cut.Edges())
    export_perimeter_error=abs(export_length-lengths[1])/lengths[1]
    primary_path=ROOT/'audits/whole-mirror-check-thigh_outer_right-sections.json'
    primary=json.loads(primary_path.read_text());failed=[s for s in primary['sections']if not s['pass']]
    assert len(failed)==1 and failed[0]['axis']=='Y' and abs(failed[0]['offset_mm']+75)<1e-9
    passed=error<.05 and perimeter_error<.002 and export_error<.05 and export_perimeter_error<.002
    out={'part':'thigh_outer_right','native_step_sha256':mapping['thigh_outer_right']['native_step_sha256'],
         'qualified_parent_native_sha256':mapping['thigh_outer']['native_step_sha256'],
         'native_capture_sha256':hashlib.sha256(raw).hexdigest(),
         'saved_version':capture['saved_version'],'working_modified':capture['working_modified'],
         'preserved_primary_report':str(primary_path.relative_to(ROOT)),
         'preserved_primary_report_sha256':hashlib.sha256(primary_path.read_bytes()).hexdigest(),
         'preserved_failed_plane':failed[0],
         'other_eight_step_planes_passed':all(s['pass']for s in primary['sections']if s not in failed),
         'native_mirrored_pair_maximum_distance_mm':error,
         'native_mirrored_pair_relative_perimeter_error':perimeter_error,
         'right_step_to_actual_native_section_maximum_distance_mm':export_error,
         'native_to_exact_step_section_maximum_distance_mm':native_to_exact_step,
         'step_to_native_stroked_section_maximum_distance_mm':step_to_native,
         'right_step_to_actual_native_relative_perimeter_error':export_perimeter_error,
         'native_boundary_metrology_passed':True,
         'native_fingerprints':{key:p['native_fingerprint']for key,p in parts.items()},
         'section_gate_passed':passed,'passed':passed,
         'tolerances':{'section_distance_mm':.05,'relative_perimeter':.002,'native_curve_stroke_mm':.001,'native_boundary_bracket_mm':.0049,'native_trimmed_face_distance_mm':.005},
         'scope':'The original external self-boundary failure remains failed. This check evaluates the same plane through actual native Fusion boundary sections, their handed congruence and the right STEP section. Native points use distance to exact STEP curves; STEP samples use the 0.001 mm native stroke. No geometry or thresholds changed. Final saved-document and current-definition fingerprint binding remain separate.'}
    destination=ROOT/'audits/current-outer-native-section-resolution.json'
    if destination.exists():
        original=destination.read_bytes();archived=destination.with_name('current-outer-native-section-coarse-polyline-diagnostic.json');assert not archived.exists();archived.write_bytes(original)
        out['preserved_coarse_polyline_diagnostic']={'path':str(archived.relative_to(ROOT)),'sha256':hashlib.sha256(original).hexdigest(),'reason':'The earlier comparison used up to 2 mm STEP sample chords as distance targets. Their sagitta produced an artificial 0.1387 mm distance. The corrected comparison measures native points against exact STEP curves, retaining the existing 0.05 mm gate.'}
    destination.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items()if k not in ['preserved_failed_plane','native_fingerprints']},indent=2))


if __name__=='__main__':main()
