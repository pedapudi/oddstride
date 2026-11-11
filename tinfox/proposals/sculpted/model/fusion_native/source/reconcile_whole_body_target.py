"""Reuse qualified body/head evidence only where the frozen mesh geometry is unchanged."""
import json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
whole_manifest=read(ROOT/'manifests/whole-robot-integration-target.json');whole=read(ROOT/whole_manifest['reference_model']);body_manifest=read(ROOT/'manifests/current-body-target.json');body=read(ROOT/body_manifest['reference_model']);targets=read(ROOT/'manifests/current-targets.json');print('current targets schema',targets.keys());rows=[]
for p in whole['parts']:
 if p.get('leg')is not None:continue
 old=next((q for q in body['parts']if q['name']==p['name']),None)
 rows.append({'instance':p['name'],'mesh':p['mesh'],'body_target_present':old is not None,'geometry_hash':digest(whole['meshes'][p['mesh']]),'body_target_geometry_hash':digest(body['meshes'][old['mesh']])if old else None,'geometry_unchanged':bool(old and whole['meshes'][p['mesh']]==body['meshes'][old['mesh']]),'frame_unchanged':bool(old and (p.get('leg'),p.get('group'))==(old.get('leg'),old.get('group')))})
report={'whole_target_sha256':whole_manifest['model_sha256'],'body_target_sha256':body_manifest['source_model_sha256'],'body_head_instances':len(rows),'unchanged_geometry':sum(x['geometry_unchanged']for x in rows),'rows':rows,'scope':'Reference-geometry identity only. Reuse saved native shape evidence where source geometry matches; current native placement/assembly checks remain separate.'};(ROOT/'audits/whole-current-body-target-reconciliation.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items()if k!='rows'});print('changed',[r['instance']for r in rows if not r['geometry_unchanged']])
