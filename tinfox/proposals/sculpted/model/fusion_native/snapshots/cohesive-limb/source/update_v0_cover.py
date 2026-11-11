"""Publish an existing rounded cover on V0 without regenerating unchanged CAD."""
import copy
import hashlib
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
start = time.perf_counter()
base = ROOT / 'output/service-design'
rounded = ROOT / 'output/rounded-design'
out = ROOT / 'output/v0-rounded-body'
out.mkdir(exist_ok=True)
raw = (base / 'model.json').read_bytes()
model = json.loads(raw)
candidate_raw = (rounded / 'model.json').read_bytes()
candidate = json.loads(candidate_raw)
analysis = json.loads((ROOT / 'output/enclosure-review/audit.json').read_text())
hashes = {'v0':hashlib.sha256(raw).hexdigest(), 'rounded':hashlib.sha256(candidate_raw).hexdigest()}
assert analysis['source_hashes'] == hashes, 'Rerun enclosure review for changed source geometry'
key = 'body_center_0'
model['meshes'][key] = candidate['meshes'][key]
replacement = next(p for p in candidate['parts'] if p['name'] == key)
model['parts'] = [copy.deepcopy(replacement) if p['name'] == key else p for p in model['parts']]
model['status'] = 'V0 with the rounded body cover. Existing limbs and carriers retained. Preview: fixed cover/frame and hardware contacts require fit review; deep-fold and combined-pose collisions remain.'
model['source_model_sha256'] = hashes['v0']
model['cover_source_model_sha256'] = hashes['rounded']
updated = json.dumps(model, separators=(',', ':')).encode()
(out / 'model.json').write_bytes(updated)
stamp = hashlib.sha256(updated).hexdigest()
audit = json.loads((base / 'audit.json').read_text())
audit['model_sha256'] = stamp
audit['reused_reference_hash'] = hashes['v0']
checks = {row['pose']: row for row in analysis['rounded_cover_on_v0']}
for row in audit['motion_samples']:
    hits = [pair for pair in row['hits'] if key not in pair]
    hits.extend(sorted([key, name]) for name in checks[row['pose']]['intersections'] if name.startswith(('FL_', 'FR_', 'RL_', 'RR_')))
    row['hits'] = sorted(hits)
    row['passed'] = not hits
audit['fixed_cover_contacts_for_review'] = [n for n in checks['stand']['intersections'] if not n.startswith(('FL_', 'FR_', 'RL_', 'RR_'))]
audit['scope'] = 'Preview. Unchanged limb checks are reused from the hashed V0 reference. The transferred cover was checked against V0 at 35 poses. Fixed cover contacts are listed separately and are unresolved. No full manufacturing release or loaded-motion qualification.'
(out / 'audit.json').write_text(json.dumps(audit, indent=2))
for ext in ['step', 'stl']:
    (out / ext).mkdir(exist_ok=True)
    shutil.copy2(rounded / ext / f'{key}.{ext}', out / ext / f'{key}.{ext}')
report = {'model_sha256':stamp, 'source_hashes':hashes, 'changed_parts':[key],
          'unchanged_parts':len(model['parts'])-1, 'elapsed_seconds':time.perf_counter()-start,
          'assembly_step':'Not regenerated for this preview. Download the individual cover STEP; earlier whole-robot STEP files do not contain this revision.'}
(out / 'update.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
