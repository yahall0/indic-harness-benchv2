"""Fixed task-service adaptations, executed only inside restricted Docker."""
from bench.security import docker

PROXY=r'''from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import urllib.request,urllib.error
class H(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def do_GET(self):
  if self.path.split('?')[0] not in ('/projects','/users','/incidents'): self.send_error(404); return
  try:
   r=urllib.request.urlopen('http://ihb-mock:8081'+self.path,timeout=5); b=r.read(65536); code=r.status
  except urllib.error.HTTPError as e: b=e.read(65536); code=e.code
  self.send_response(code); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
ThreadingHTTPServer(('127.0.0.1',8081),H).serve_forever()
'''

def start_mock(box,agent,network,volume):
    mock=box.create('helper',network=network,volume=volume,command=('python','/opt/ihb/mock_api.py'),extra=('--network-alias','ihb-mock'))
    docker(['exec','-d',agent,'python','-c',PROXY])
    wait=r'''import socket,time
for _ in range(40):
 try:
  socket.create_connection(('ihb-mock',8081),timeout=.3).close()
  socket.create_connection(('127.0.0.1',8081),timeout=.3).close()
  break
 except OSError: time.sleep(.1)
else: raise RuntimeError('Isolated task service unavailable')
'''
    docker(['exec',agent,'python','-c',wait],timeout=10)
    return mock
