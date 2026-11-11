"""Package checked geometry for an unpowered single-limb fit prototype."""
import hashlib,json,shutil,zipfile
from kinematics import ROOT
from cad_authority import require_generated_authority
require_generated_authority(ROOT)

OUT=ROOT/'output/paired-roll-work';PACK=OUT/'prototype-limb'
stamp=hashlib.sha256((OUT/'model.json').read_bytes()).hexdigest()
files=['paired-roll-interfaces.json','knee-retention.json','paired-roll-motion.json','foot-clearance.json','body-integration.json','step-roundtrip.json']
reports={}
for name in files:
    d=json.loads((OUT/name).read_text());assert d['model_sha256']==stamp,name;reports[name]=d
for name in ['paired-roll-interfaces.json','knee-retention.json','foot-clearance.json']:assert reports[name]['passed'],name
assert not reports['paired-roll-motion.json']['previously_clear_poses_lost']
assert reports['paired-roll-motion.json']['knee_clear_samples']==109
manifest=json.loads((PACK/'manifest.json').read_text());assert manifest['model_sha256']==stamp
(PACK/'checks').mkdir(exist_ok=True)
for name in files:shutil.copy2(OUT/name,PACK/'checks'/name)
independent=ROOT.parents[2]/'analysis/dfma/paired-service-delta.json'
if independent.exists():
    d=json.loads(independent.read_text());assert d['model_sha256']==stamp and not d['failed_checks']
    shutil.copy2(independent,PACK/'checks/independent-service.json')
    manifest['independent_service_checks']=len(d['checks'])
guide=(ROOT.parents[2]/'design/prototype-limb.md').read_text()
guide=guide.replace('../proposals/sculpted/model/output/paired-roll-work/prototype-limb.zip','.')
(PACK/'README.md').write_text(guide)
manifest['release_scope']='Unpowered bench fit only. Fixed-body integration, preload, process-specific fits and operating strength remain unqualified.'
manifest['checks']={name:{k:v for k,v in d.items() if k in ['passed','previously_clear_poses_lost','knee_clear_samples','continuous_nominal_distance_lower_bound_mm','whole_robot_integration_qualified']} for name,d in reports.items()}
(PACK/'manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(OUT/'prototype-limb.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(PACK.rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(PACK)))
release=dict(model_sha256=stamp,scope=manifest['release_scope'],parts=len(manifest['parts']),coupons=manifest['coupon_count'],
    archive_sha256=hashlib.sha256((OUT/'prototype-limb.zip').read_bytes()).hexdigest(),
    archive_bytes=(OUT/'prototype-limb.zip').stat().st_size)
(OUT/'prototype-release.json').write_text(json.dumps(release,indent=2));print(json.dumps(release),flush=True)
