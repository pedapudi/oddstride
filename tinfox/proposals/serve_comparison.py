"""Serve local CAD comparisons, sources and downloads."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
root=Path(__file__).resolve().parent.parent
if __name__=='__main__':
 print('Tinfox proposals: http://127.0.0.1:8769/proposals/',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8769),partial(SimpleHTTPRequestHandler,directory=str(root))).serve_forever()
