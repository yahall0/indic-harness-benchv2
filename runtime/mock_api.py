"""Task 022 adaptation: isolated helper preserves endpoint pagination/retry behavior."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs

attempts={}
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        url=urlparse(self.path); path=url.path
        mapping={'/projects':'projects.json','/users':'users.json','/incidents':'incidents.json'}
        if path not in mapping: self.send_error(404); return
        attempts[self.path]=attempts.get(self.path,0)+1
        log=Path('/workspace/out/api_access.log'); log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('a',encoding='utf-8') as f: f.write(path+'\n')
        print(json.dumps({'path':path,'attempt':attempts[self.path]}),flush=True)
        if path in {'/projects','/incidents'} and attempts[self.path]==1:
            self.send_error(429 if path=='/projects' else 503); return
        page=int(parse_qs(url.query).get('page',['1'])[0]); size=2
        if page<1: self.send_error(400); return
        items=json.loads((Path('/workspace/in/api_data')/mapping[path]).read_text())
        start=(page-1)*size
        b=json.dumps({'items':items[start:start+size],'next_page':page+1 if start+size<len(items) else None},sort_keys=True).encode()
        self.send_response(200); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)

if __name__=='__main__': ThreadingHTTPServer(('0.0.0.0',8081),Handler).serve_forever()
