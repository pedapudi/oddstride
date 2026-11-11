"""Report build evidence without confusing geometry checks with migration release."""
import json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def report():
 manifest=json.loads((ROOT/'manifests/parts.json').read_text());rows=[]
 for p in manifest['parts']:
  key=p['id'];native=ROOT/'exports'/f'{key}.step';sha=hashlib.sha256(native.read_bytes()).hexdigest() if native.exists() else None
  row={'part':key,'native_export_available':native.exists(),'geometry':'not_checked','sections':'not_checked','editability':'not_checked','assembly':'not_checked','migration_gate_passed':False}
  for suffix,label,gate in [('geometry','geometry','geometric_gate_passed'),('sections','sections','section_gate_passed')]:
   path=ROOT/'audits'/f'{key}-{suffix}.json'
   if path.exists():
    evidence=json.loads(path.read_text())
    source_current=evidence.get('source_step_sha256')==p.get('source_step_sha256') and evidence.get('source_brep_sha256')==p.get('source_brep_sha256')
    row[label]='stale_export_hash' if evidence['native_step_sha256']!=sha else 'stale_source_reference' if not source_current else 'pass' if evidence[gate] else 'fail'
  rows.append(row)
 result={'updated_utc':datetime.datetime.now(datetime.UTC).isoformat(),'design_revision':'V0','authoritative_source':'CadQuery V0','migration_gate_passed':False,'counts':{'custom_geometry_entries':len(rows),'native_exports':sum(r['native_export_available'] for r in rows),'geometry_pass':sum(r['geometry']=='pass' for r in rows),'geometry_fail':sum(r['geometry']=='fail' for r in rows),'sections_pass':sum(r['sections']=='pass' for r in rows),'sections_fail':sum(r['sections']=='fail' for r in rows),'both_geometry_gates_pass':sum(r['geometry']=='pass' and r['sections']=='pass' for r in rows)},'parts':rows}
 current=ROOT/'manifests/current-rpc.json'
 if current.exists():result['last_tracked_rpc']=json.loads(current.read_text())
 probes=ROOT/'audits/readiness-probes.jsonl'
 if probes.exists():result['last_read_only_probe']=json.loads(probes.read_text().splitlines()[-1])
 (ROOT/'manifests/audit-status.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['counts'],indent=2));return result
if __name__=='__main__':report()
