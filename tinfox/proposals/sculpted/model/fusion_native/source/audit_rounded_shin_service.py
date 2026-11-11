"""Audit current native shin seats and access with frozen standard hardware."""
import hashlib,json,sys
from pathlib import Path
from functools import cache
import cadquery as cq
from audit_part import volume
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent));import build as b
target=json.loads((ROOT/'manifests/latest-shin-reference-hardware.json').read_text());refs={}
@cache
def solid(key):
 if key in ['shin_inner','shin_outer']:path=ROOT/'exports'/('rounded-native-'+key+'.step')
 else:
  row=target['parts'][key];path=ROOT/row['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
 refs[key]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};shape=cq.importers.importStep(str(path)).val();assert shape.isValid()and len(shape.Solids())==1;return shape
rows=[]
def fit(label,a,c):
 overlap=max(0,volume(a.intersect(c))[0]);rows.append({'check':label,'overlap_mm3':overlap,'passed':overlap<.001})
fit('Structural half separation',solid('shin_inner'),solid('shin_outer'))
hardware=[key for key in target['parts']if not key.startswith('thigh_')]
for side in ['inner','outer']:
 shin=solid('shin_'+side);direction=-1 if side=='inner'else 1
 for key in hardware:fit(side+' / '+key,shin,solid(key))
 for travel in [0,.1,.5,1,2,4,8,12,20,35]:fit(side+' bearing extraction '+str(travel),shin,solid('bearing_'+side).translate((0,direction*travel,0)))
 for x in[-12.7,12.7]:fit(side+' extraction punch '+str(x),shin,b.cyl(1,16,(x,61,0)))
 for travel in[.1,1,5,15,40,70]:fit(side+' shell separation '+str(travel),shin.translate((0,direction*travel,0)),solid('shin_outer'if side=='inner'else'shin_inner'))
 for position in['37','105']:
  washer=solid('shin_clamp_washer_'+position+'_'+side);probe=washer.translate((0,-direction*.1,0));contact=max(0,volume(shin.intersect(probe))[0]);rows.append({'check':side+' washer '+position+' bearing floor','probe_depth_mm':.1,'contact_probe_volume_mm3':contact,'passed':contact>4})
record={'source_model_sha256':target['model_sha256'],'checks':rows,'passed':all(row['passed']for row in rows),'references':refs,'scope':'Native shell interfaces with current bearing, shoulder screw, bushing, clamp and washer geometry. Sampled bearing/shell extraction and shallow washer contact probes. Excludes structural strength, preload, process fit qualification and continuous swept-volume proof.'}
(ROOT/'audits/rounded-shin-service.json').write_text(json.dumps(record,indent=2));print({'passed':record['passed'],'checks':len(rows),'failed':[r for r in rows if not r['passed']]})
