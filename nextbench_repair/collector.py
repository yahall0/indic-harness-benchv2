"""Authenticated, bounded accounting API; no command or filesystem endpoints."""
from __future__ import annotations
import hmac
import json
import secrets
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from bench.durable import encode,atomic_json

class Collector:
    def __init__(self,journal,run_id,limits,slots,preferred=None,trace_dir=None):
        self.token=secrets.token_hex(32); self.journal=journal; self.run_id=run_id
        self.limits=limits; self.preferred=preferred; self.lock=threading.Lock()
        self.paused=None
        self.trace_dir=Path(trace_dir) if trace_dir else None; self.trace_bytes=0
        journal.slot_init(slots)
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                if not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+owner.token):
                    self.send_error(403); return
                data={}
                try:
                    n=int(self.headers.get('Content-Length','0'))
                    if not 0<n<=8*1024*1024: raise ValueError('Request size')
                    data=json.loads(self.rfile.read(n))
                    if not isinstance(data,dict): raise ValueError('Invalid object')
                    with owner.lock:
                        if self.path=='/reserve':
                            if owner.paused: raise ValueError('Controller paused')
                            result=owner.journal.reserve(owner.run_id,data['call_id'],data['input_bound'],data['output_tokens'],owner.limits)
                            result['slot']=owner.journal.choose_slot(owner.preferred,allowed=slots)
                            owner.preferred=result['slot']
                        elif self.path=='/quota':
                            if data['slot'] not in slots: raise ValueError('Unknown slot')
                            owner.journal.exhaust_slot(data['slot'],'confirmed_quota_exhaustion',owner.run_id)
                            result={'slot':owner.journal.choose_slot(allowed=slots)}
                            owner.preferred=result['slot']
                        elif self.path=='/settle':
                            # Only metadata and usage are accepted; keys/upstream messages never get stored.
                            payload={k:data[k] for k in ('usage','slot','latency_sec','status','classification','retries','rotations','tool_calls','schema_errors') if k in data}
                            settled=owner.journal.settle(data['call_id'],payload)
                            if settled['budget_violation']:
                                owner.paused='budget_integrity_violation'
                                raise ValueError('Provider exceeded reserved inference budget')
                            result={'ok':True}
                        elif self.path=='/rejected':
                            if data.get('classification') not in ('rate_limited','quota_exhausted'): raise ValueError('Ambiguous rejection')
                            owner.journal.rejected_forward(data['call_id']); result={'ok':True}
                        elif self.path=='/trace':
                            import re
                            if not re.fullmatch('[a-f0-9]{24,64}',data['call_id']): raise ValueError('Invalid trace ID')
                            trace={k:data[k] for k in ('call_id','request','response') if k in data}
                            phase=data.get('phase','response')
                            if phase not in {'request','response','error'}: raise ValueError('Invalid trace phase')
                            trace['phase']=phase
                            size=len(encode(trace).encode())
                            existing=owner.trace_dir/(data['call_id']+'.'+phase+'.json') if owner.trace_dir else None
                            if existing and existing.exists():
                                if json.loads(existing.read_text(encoding='utf-8'))!=trace: raise ValueError('Conflicting inference trace')
                            elif owner.trace_dir and owner.trace_bytes+size<=64*1024*1024:
                                atomic_json(owner.trace_dir/(data['call_id']+'.'+phase+'.json'),trace)
                                owner.trace_bytes+=size
                                owner.journal.event(owner.run_id,'inference_trace_saved',{'call_id':data['call_id'],'bytes':size})
                            else:
                                owner.journal.event(owner.run_id,'inference_trace_unavailable',{'call_id':data['call_id'],'reason':'trace_storage_cap_or_disabled'})
                            result={'ok':True}
                        elif self.path=='/event':
                            if data.get('kind') not in {'transport_retry','provider_pause','inference_forwarded','accounting_transport_retry'}: raise ValueError('Event kind')
                            payload={k:data[k] for k in ('slot','status','classification','retry','call_id','stage','error_type','upstream_status','settled','endpoint','local_retries') if k in data}
                            if data['kind']=='inference_forwarded':
                                if owner.paused: raise ValueError('Controller paused')
                                owner.journal.forward(data['call_id'],data['slot'],owner.limits,data.get('transmission_id'))
                            else:
                                owner.journal.event(owner.run_id,data['kind'],payload)
                                if data['kind']=='provider_pause' and owner.paused is None: owner.paused=data.get('classification','provider_pause')
                            result={'ok':True}
                        else: raise ValueError('Unknown accounting endpoint')
                    body=encode(result).encode(); self.send_response(200)
                    self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body)))
                    self.end_headers(); self.wfile.write(body)
                except (ValueError,KeyError,TypeError) as e:
                    owner.paused=str(e)
                    if 'budget' in owner.paused.lower():
                        current=owner.journal.get(owner.run_id)
                        owner.journal.event(owner.run_id,'budget_denied',{
                            'endpoint':self.path,'reason':owner.paused,
                            'next_input_bound':data.get('input_bound'),
                            'charged_input':current['input_bound'],'actual_input':current['input_actual'],
                            'charged_output':current['output_reserved'],'actual_output':current['output_actual'],
                            'requests':current['requests'],
                            'input_limit':owner.limits['max_input_tokens'],
                            'output_limit':owner.limits['max_output_tokens'],
                            'request_limit':owner.limits['max_requests']})
                    body=encode({'error':str(e)}).encode(); self.send_response(409)
                    self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)

    def start(self): self.thread.start(); return self.server.server_port
    def close(self): self.server.shutdown(); self.server.server_close(); self.thread.join(5)
