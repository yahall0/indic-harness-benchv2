"""Restricted inference relay. Secrets arrive on stdin, never a mount or image layer."""
from __future__ import annotations
import hashlib
import http.client
import json
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from bench.rotation import classify
from contract import validate_profile,request_payload,completion,stream_chunks,retry_delay

MAX_BODY=2*1024*1024
MAX_RESPONSE=4*1024*1024

def normalize_response(data):
    """Normalize optional null tool lists without changing generated text/arguments."""
    if not isinstance(data,dict) or not isinstance(data.get('choices'),list):
        raise ValueError('Invalid completion envelope')
    normalized={**data,'choices':[]}; count=0
    for choice in data['choices']:
        if not isinstance(choice,dict) or not isinstance(choice.get('message'),dict):
            raise ValueError('Invalid completion choice')
        message=dict(choice['message'])
        tools=message.get('tool_calls')
        if tools is None:
            message.pop('tool_calls',None)
        elif isinstance(tools,list):
            count+=len(tools)
        else:
            raise ValueError('Invalid completion tool list')
        normalized['choices'].append({**choice,'message':message})
    return normalized,count

def main():
    config=json.loads(sys.stdin.readline(65536))
    profile=validate_profile(config['profile'])
    if config['model']!=profile['model']: raise ValueError('Profile model mismatch')
    if config.get('upstream')!='https://ollama.com/v1/chat/completions': raise ValueError('Fixed upstream required')
    slots=config['keys']
    if not 1<=len(slots)<=4 or len(set(slots.values()))!=len(slots): raise ValueError('Configure 1-4 distinct keys')
    lock=threading.Lock()
    paused=threading.Event()
    # Disable environment proxies and redirects: no alternate URL or Location forwarding.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def account(path,data):
        request=urllib.request.Request(config['accounting']+path,json.dumps(data).encode(),
            {'Authorization':'Bearer '+config['accounting_token'],'Content-Type':'application/json'})
        safe=path in {'/reserve','/trace','/settle','/rejected','/quota'} or (path=='/event' and data.get('kind')=='inference_forwarded')
        for attempt in range(3 if safe else 1):
            try:
                with opener.open(request,timeout=15) as r: result=json.load(r)
                if attempt:
                    event={'kind':'accounting_transport_retry','call_id':data.get('call_id'),'endpoint':path,'local_retries':attempt}
                    notification=urllib.request.Request(config['accounting']+'/event',json.dumps(event).encode(),
                        {'Authorization':'Bearer '+config['accounting_token'],'Content-Type':'application/json'})
                    try:
                        with opener.open(notification,timeout=5) as r: r.read()
                    except Exception: pass
                return result
            except urllib.error.HTTPError: raise
            except (urllib.error.URLError,TimeoutError,http.client.HTTPException,OSError):
                if attempt==2 or not safe: raise
                time.sleep(attempt+1)
    def post(slot,payload):
        from upstream import post as stream_post
        request=urllib.request.Request(config["upstream"],json.dumps(payload,ensure_ascii=False).encode(),
            {"Authorization":"Bearer "+slots[slot],"Content-Type":"application/json"})
        try: return stream_post(opener,request)
        except urllib.error.HTTPError as e: return e.code,e.read(65536),e.headers

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,status,obj):
            b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status)
            self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b)))
            self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            if self.path=='/health': self.respond(200,{'ok':True,'model':config['model']})
            else: self.respond(404,{'error':'Endpoint not allowed'})
        def do_POST(self):
            if self.path!='/v1/chat/completions': self.respond(404,{'error':'Endpoint not allowed'}); return
            if self.headers.get('Authorization')!='Bearer '+config['agent_token']:
                self.respond(403,{'error':'Invalid attempt token'}); return
            if paused.is_set(): self.respond(503,{'error':{'code':'benchmark_pause','message':'Attempt paused'}}); return
            if not lock.acquire(blocking=False): self.respond(429,{'error':'One in-flight inference permitted'}); return
            call_id=secrets.token_hex(16); slot=None; usage=None; retries=0; rotations=0; status=0
            classification='relay_error'; begin=time.monotonic(); settled=False
            stage='request_parse'
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=MAX_BODY: raise ValueError('Request size exceeds limit')
                p=json.loads(self.rfile.read(n))
                if p.get('model')!=config['model']: raise ValueError('Configured model only')
                if not isinstance(p.get('messages'),list): raise ValueError('Messages required')
                # Multimodal/URL content and provider extensions are not forwarded.
                for m in p['messages']:
                    c=m.get('content')
                    if c is not None and not isinstance(c,str):
                        if not isinstance(c,list) or any(x.get('type')!='text' for x in c):
                            raise ValueError('Text content only')
                stream=bool(p.get('stream',False))
                payload=request_payload(p,profile)
                payload.update(stream=True,stream_options={"include_usage":True})
                # Conservative UTF-8 byte bound + chat/template allowance, explicitly logged.
                bound=len(json.dumps(payload,ensure_ascii=False).encode())+4096+64*len(p['messages'])
                stage='budget_reservation'
                reservation=account('/reserve',{'call_id':call_id,'input_bound':bound,'output_tokens':config['max_response_tokens']})
                slot=reservation['slot']; payload['max_tokens']=reservation['allowance']
                account('/trace',{'call_id':call_id,'phase':'request','request':payload})
                while True:
                    stage='forward_accounting'
                    account('/event',{'kind':'inference_forwarded','call_id':call_id,'slot':slot,'transmission_id':secrets.token_hex(16)})
                    stage='upstream_transport'
                    try: status,body,headers=post(slot,payload)
                    except (urllib.error.URLError,TimeoutError,http.client.HTTPException,OSError) as transport_error:
                        account('/trace',{'call_id':call_id,'phase':'error','response':{'error_type':type(transport_error).__name__,'stage':stage}})
                        # Uncertain whether inference happened: keep reservation charged. Do not rotate.
                        status=0; body=b'{}'; headers={}; classification='ambiguous_transport'
                        break
                    classification=classify(status,body)
                    if classification=='quota_exhausted':
                        account('/rejected',{'call_id':call_id,'classification':classification})
                        slot=account('/quota',{'slot':slot})['slot']; rotations+=1; continue
                    if classification in ('transient','rate_limited') and retries<2:
                        if classification=='rate_limited': account('/rejected',{'call_id':call_id,'classification':classification})
                        retries+=1
                        account('/event',{'kind':'transport_retry','call_id':call_id,'slot':slot,'status':status,'classification':classification,'retry':retries})
                        delay=retry_delay(headers)
                        time.sleep(delay); continue
                    break
                if classification=='success':
                    stage='response_parse'
                    data=json.loads(body); usage=data.get('usage')
                    stage='trace_save'
                    account('/trace',{'call_id':call_id,'request':payload,'response':data,'phase':'response'})
                    stage='model_identity'
                    if data.get('model') not in profile['response_model_aliases']:
                        account('/settle',{'call_id':call_id,'usage':usage,'slot':slot,'latency_sec':time.monotonic()-begin,
                            'status':status,'classification':'provider_identity_mismatch','retries':retries,'rotations':rotations})
                        settled=True
                        raise ValueError('Upstream model identity mismatch')
                    stage='response_normalization'
                    data,calls,schema_errors=completion(data,profile)
                    stage='settlement'
                    account('/settle',{'call_id':call_id,'usage':usage,'slot':slot,'latency_sec':time.monotonic()-begin,
                        'status':status,'classification':classification,'retries':retries,'rotations':rotations,
                        'tool_calls':calls,'schema_errors':schema_errors})
                    settled=True
                    stage='agent_delivery'
                    if not stream: self.respond(200,data)
                    else:
                        # Buffer until complete and durably accounted, then adapt to OpenAI SSE.
                        self.send_response(200); self.send_header('Content-Type','text/event-stream')
                        self.send_header('Connection','close'); self.end_headers()
                        for chunk in stream_chunks(data,call_id):
                            self.wfile.write(('data: '+json.dumps(chunk,ensure_ascii=False)+'\n\n').encode())
                        self.wfile.write(b'data: [DONE]\n\n'); self.wfile.flush()
                        self.close_connection=True
                else:
                    paused.set()
                    account('/settle',{'call_id':call_id,'usage':None,'slot':slot,'latency_sec':time.monotonic()-begin,
                        'status':status,'classification':classification,'retries':retries,'rotations':rotations})
                    settled=True
                    account('/event',{'kind':'provider_pause','call_id':call_id,'slot':slot,'status':status,'classification':classification})
                    self.respond(503,{'error':{'message':'Benchmark paused: '+classification,'type':'benchmark_pause','code':'benchmark_pause'}})
            except Exception as error:
                paused.set()
                try: account('/event',{'kind':'provider_pause','call_id':call_id,'classification':'relay_accounting_gate',
                    'stage':stage,'error_type':type(error).__name__,'upstream_status':status,'settled':settled})
                except Exception: pass
                # Never echo provider bodies, keys or exception URLs to agent/logs.
                self.respond(503,{'error':{'message':'Benchmark relay/accounting gate stopped the request','code':'benchmark_pause'}})
            finally: lock.release()
    print(json.dumps({'ready':True}),flush=True)
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()

if __name__=='__main__': main()
