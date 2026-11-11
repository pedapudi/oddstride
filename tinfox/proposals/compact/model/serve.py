"""Local-only 3D review and mesh collision service."""
import json, threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from kinematics import ROOT, LEGS, P
from collision import Checker

checker=Checker();lock=threading.Lock();model_stamp=(ROOT/'output'/'model.json').stat().st_mtime_ns

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path in ['/studio.png','/studio-view.png','/reference.png','/body-before.png']:
            name={'/studio.png':'09-cad-studio.png','/studio-view.png':'12-studio-view.png','/reference.png':'studio-reference.png','/body-before.png':'studio-reference.png'}[path]
            payload=(ROOT.parent/'design'/name).read_bytes()
            self.send_response(200);self.send_header('Content-Type','image/png')
            self.send_header('Content-Length',str(len(payload)));self.end_headers()
            self.wfile.write(payload);return
        super().do_GET()

    def do_POST(self):
        global checker,model_stamp
        if self.path!='/api/collision':self.send_error(404);return
        try:
            data=json.loads(self.rfile.read(min(int(self.headers.get('Content-Length',0)),16384)))
            q=data['poses']
            assert set(q)==set(LEGS)
            assert all(len(v)==3 and all(isinstance(x,(int,float)) and -360<=x<=360 for x in v) for v in q.values())
            limits=P['joint_limits_deg']
            for leg,v in q.items():
                ranges=[limits['roll'],limits['hip_front' if leg.startswith('F') else 'hip_rear'],limits['knee']]
                assert all(lo<=angle<=hi for angle,(lo,hi) in zip(v,ranges))
            with lock:
                current=(ROOT/'output'/'model.json').stat().st_mtime_ns
                if current!=model_stamp:
                    checker=Checker();P.clear();P.update(checker.data['parameters']);model_stamp=current
                result=checker.check(q)
            body=json.dumps(result).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        except (ValueError,KeyError,AssertionError):self.send_error(400,'Invalid pose')
    def log_message(self,*args):pass

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',8767),partial(Handler,directory=str(ROOT)))
    print('Tinfox review: http://127.0.0.1:8767/review/',flush=True)
    server.serve_forever()
