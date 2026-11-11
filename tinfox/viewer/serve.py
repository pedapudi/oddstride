"""Serve the static review and optional local rigid-part collision checks."""
import argparse
import gzip
import hashlib
import json
import math
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'proposals/sculpted/model'
sys.path.insert(0, str(MODEL))
import numpy as np
import trimesh
from kinematics import P, matrix

PATHS = {'v0': MODEL / 'output/v0-rounded-body/model.json',
         'v1': MODEL / 'output/rounded-design/model.json',
         'v2': MODEL / 'output/integrated-candidate/model.json',
         'v3': MODEL / 'output/raised-head-prototype/model.json',
         'v4': MODEL / 'output/shoulder-head-prototype/model.json',
         'v5': MODEL / 'output/limb-refinement/model.json',
         'v6': MODEL / 'output/compact-thigh-work/model.json',
         'v7': MODEL / 'output/integrated-pitch-work/model.json',
         'v8': MODEL / 'output/seamless-limb-work/model.json',
         'v9': MODEL / 'output/manufacturing-thigh-work/model.json',
         'v10': MODEL / 'output/slim-limb-work/model.json',
         'v11': MODEL / 'output/cohesive-chassis-work/model.json',
         'v12': MODEL / 'output/closed-thigh-work/model.json',
         'v13': MODEL / 'output/clamp-seat-work/model.json',
         'v14': MODEL / 'output/paired-roll-work/model.json'}
ENGINES = {}
LOCK = threading.Lock()


def resolve_design(design):
    """Resolve only catalog-published native models or recorded legacy designs."""
    if design in PATHS:
        return PATHS[design], None
    catalog = json.loads((ROOT/'viewer/catalog.json').read_text())
    entry = next((d for d in catalog['designs'] if d['id'] == design), None)
    if not entry or entry.get('source', {}).get('kind') != 'fusion-native' or entry.get('motion_available') is not True:
        raise ValueError('Design has no approved native motion model')
    path = (ROOT/'viewer'/entry['model']).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
        raise ValueError('Native review model must be a local Tinfox artifact')
    identity = entry.get('model_sha256')
    if not isinstance(identity, str) or len(identity) != 64:
        raise ValueError('Native review model requires its recorded hash')
    return path, identity


class Engine:
    def __init__(self, path, expected_sha256=None):
        self.stamp = path.stat().st_mtime_ns
        raw = path.read_bytes()
        if path.suffix == '.gz':
            raw = gzip.decompress(raw)
        self.source_sha256 = hashlib.sha256(raw).hexdigest()
        if expected_sha256 and self.source_sha256 != expected_sha256:
            raise ValueError('Native review geometry hash does not match its published catalog')
        self.data = json.loads(raw)
        self.parts = {p['name']: p for p in self.data['parts']
                      if p.get('service_role') not in ['keepout', 'withdrawal']}
        self.reference_contacts = {}
        if expected_sha256:
            for rule in self.data.get('validated_reference_contacts', []):
                pair = tuple(sorted(rule['pair']))
                accepted = False
                for leg in ('FL', 'FR', 'RL', 'RR'):
                    for axis, screw, engagement in [('hip', 'hip_output_bolt', 4.3), ('knee', 'input_bolt', 5.4)]:
                        for angle in range(0, 360, 60):
                            if pair == tuple(sorted([f'{leg}_{axis}_motor', f'{leg}_{screw}_{angle}'])):
                                accepted = (rule['classification'] == 'verified_motor_output_thread_envelope'
                                            and rule['shaft_radius_mm'] == 2
                                            and rule['penetration_mm'] == engagement)
                if not accepted or not all(name in self.parts for name in pair) or pair in self.reference_contacts:
                    raise ValueError('Unrecognized or duplicate native reference-contact classification')
                self.reference_contacts[pair] = rule
        self.manager = trimesh.collision.CollisionManager()
        meshes = {}
        for name, part in self.parts.items():
            key = part['mesh']
            if key not in meshes:
                m = self.data['meshes'][key]
                meshes[key] = trimesh.Trimesh(vertices=m['vertices'], faces=m['faces'], process=False)
            self.manager.add_object(name, meshes[key])

    def check(self, poses):
        P.clear()
        P.update(self.data['parameters'])
        for name, part in self.parts.items():
            self.manager.set_transform(name, matrix(part, poses))
        _, pairs = self.manager.in_collision_internal(return_names=True)
        hits = []
        for a, b in pairs:
            p, q = self.parts[a], self.parts[b]
            if '_port_' in a and '_port_' in b and a.rsplit('_', 1)[0] == b.rsplit('_', 1)[0]:
                continue
            if p['leg'] == q['leg']:
                ends = {a.split('_', 1)[-1], b.split('_', 1)[-1]}
                if ends in [{'roll_motor', 'motor_carrier'}, {'motor_carrier', 'roll_bearing'}, {'hip_motor', 'hip_hub'}, {'knee_motor', 'input_crank'}]:
                    continue
                # These contacts are bearing race abutments or threads entering
                # the simplified motor envelope. Separate solid audits check
                # the housing, journal, race lands and fastener clearance.
                if 'roll_motor' in ends and any(e=='roll_inner_backplate' or e.startswith('roll_output_bolt_') for e in ends):
                    continue
                if any(e.startswith('roll_bearing_6810_') for e in ends) and any(e in ['motor_carrier','roll_inner_backplate','roll_inner_spacer'] for e in ends):
                    continue
                if not (p.get('service_role') or q.get('service_role')):
                    if p['group'] == q['group']:
                        continue
                    if any(ends=={axle,bearing} for axle in ['knee_axle','knee_inner_spacer'] for bearing in ['bearing_inner','bearing_outer']):
                        continue
            if p['group'] in ['body', 'mount'] and q['group'] in ['body', 'mount']:
                continue
            hits.append(sorted([a, b]))
        classified = [pair for pair in hits if tuple(pair) in self.reference_contacts]
        material_hits = [pair for pair in hits if tuple(pair) not in self.reference_contacts]
        return {'pairs': sorted(material_hits), 'raw_motion_pairs': sorted(hits),
                'model_sha256': self.source_sha256,
                'reference_contact_pairs': sorted(classified),
                'reference_contact_evidence': [self.reference_contacts[tuple(pair)] for pair in sorted(classified)],
                'checked_components': len(self.parts),
                'scope': 'All modeled physical hardware is included. Listed mating interfaces and rigidly attached pairs are excluded. Flexible cables, tolerances, deflection and loaded motion are not validated.'}

class Handler(SimpleHTTPRequestHandler):
    def json_response(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/health':
            self.json_response(200, {'collision_checks': True})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != '/api/check':
            self.json_response(404, {'error': 'Unknown endpoint'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                raise ValueError('Invalid request size')
            payload = json.loads(self.rfile.read(length))
            design, poses = payload['design'], payload['poses']
            if set(poses) != {'FL', 'FR', 'RL', 'RR'}:
                raise ValueError('Unknown design or leg set')
            for values in poses.values():
                if len(values) != 3 or any(type(v) not in [int, float] or not math.isfinite(v) or abs(v) > 360 for v in values):
                    raise ValueError('Each leg requires three finite angles in degrees')
            with LOCK:
                path, expected_hash = resolve_design(design)
                if expected_hash and payload.get('model_sha256') != expected_hash:
                    raise ValueError('The native review geometry changed. Reload the viewer before checking this pose.')
                if design not in ENGINES or ENGINES[design].stamp != path.stat().st_mtime_ns or (expected_hash and ENGINES[design].source_sha256 != expected_hash):
                    ENGINES[design] = Engine(path, expected_hash)
                result = ENGINES[design].check(poses)
            self.json_response(200, result)
        except (ValueError, KeyError, TypeError) as error:
            self.json_response(400, {'error': str(error)})
        except Exception as error:
            print('Collision check failed:', repr(error), file=sys.stderr, flush=True)
            self.json_response(500, {'error': 'Collision check unavailable; this pose remains unchecked.'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8770)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT)))
    print(f'Tinfox review: http://127.0.0.1:{args.port}/viewer/', flush=True)
    server.serve_forever()
