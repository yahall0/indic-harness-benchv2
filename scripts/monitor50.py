"""Read-only loopback scoreboard for the existing study extended to 50 tasks."""
import argparse,csv,json,os
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from extension50.common import ROOT,NEM,SHARED,TASKS,read
from bench.durable import atomic_json

PAGE='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Indic Harness Bench · 50 tasks</title>
<style>body{font:15px system-ui;background:#f1f5f8;color:#16283e;margin:0}main{max-width:1200px;margin:auto;padding:24px}h1{font-size:27px;margin:0}p{color:#50677c}.cards{display:flex;gap:12px;flex-wrap:wrap}.card{background:white;padding:16px;border-radius:9px;min-width:150px}.big{font-size:27px;font-weight:700}.tag{font-size:12px;background:#deedf1;padding:4px;border-radius:4px}input{padding:9px;margin:16px 0;width:270px;border:1px solid #c9d6df;border-radius:5px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;background:white}th,td{padding:10px;border-bottom:1px solid #e8eef2;text-align:center;font-variant-numeric:tabular-nums}th{background:#172e46;color:white;font-size:12px;position:sticky;top:0}td:first-child,th:first-child{text-align:left;min-width:230px}.small{font-size:12px;color:#6b7d8c}.new{background:#ecf7f4}.good{color:#02715d;font-weight:600}#active{padding:14px;background:#dceaf3;border-radius:8px;margin:15px 0}.held{background:#ffead8!important}a{color:#165d92}</style>
<main><h1>Indic Harness Bench</h1><p>Same study, extended from 46 to 50 matched tasks · GPT-OSS-20B and Nemotron 3 Super</p>
<div class="cards"><div class="card"><div class="big" id="primary">—</div>new primaries saved / 24</div><div class="card"><div class="big" id="resolved">—</div>new scored conditions / 24</div><div class="card"><div class="big" id="tries">—</div>new attempts, incl. INFRA retries</div><div class="card"><div class="big" id="calls">—</div>new physical transmissions</div></div>
<div id="active">Waiting for launch</div><div class="small" id="stamp"></div><input id="search" placeholder="Filter task name or ID"><label><input type="checkbox" id="new" style="width:auto"> Four additions only</label>
<div class="scroll"><table><thead><tr><th>Task</th><th colspan="3">GPT-OSS-20B</th><th colspan="3">Nemotron 3 Super</th></tr><tr><th>Score / 100</th><th>English</th><th>Hindi</th><th>Hinglish</th><th>English</th><th>Hindi</th><th>Hinglish</th></tr></thead><tbody id="rows"></tbody></table></div><p class="small">Read-only. Earlier results are retained. Scores use the first scored attempt after any infrastructure failure; low scores and budget stops are outcomes. Hover a score for status and attempt number. New task rows are shaded.</p></main>
<script>let state;function render(){if(!state)return;const q=document.querySelector('#search').value.toLowerCase(),only=document.querySelector('#new').checked;document.querySelector('#rows').innerHTML=state.tasks.filter(t=>(!only||t.added)&&t.id.toLowerCase().includes(q)).map(t=>'<tr class="'+(t.added?'new':'')+'"><td>'+t.id+'</td>'+['oss','nemotron'].flatMap(m=>['en','hi','hinglish'].map(l=>{let x=t[m][l];if(!x)return '<td class="small">queued</td>';let s=x.score==null?x.status:(100*x.score).toFixed(1);return '<td title="'+x.status+' · attempt '+x.attempt+'" class="'+(x.score>=.9999?'good':'')+'">'+s+'</td>'})).join('')+'</tr>').join('')}
async function refresh(){try{state=await(await fetch('/api',{cache:'no-store'})).json();let c=state.counts;for(let [id,v] of Object.entries({primary:c.primary_terminal,resolved:c.resolved_conditions,tries:c.total_attempts,calls:state.accounting.transmissions}))document.getElementById(id).textContent=v;let a=state.active;let e=document.getElementById('active');e.textContent=state.complete?'All 24 new conditions resolved. Combined 50-task PDF report is ready.':state.hold?'Admissions held: '+state.hold.reason:a?'Working on '+a.model+' · '+a.task+' · '+a.language+' · attempt '+a.attempt_number:'Local checks complete; waiting for new primaries';e.className=state.hold?'held':'';document.getElementById('stamp').textContent='Observed '+state.observed+' · last saved '+(state.updated_utc||'not launched')+' · no controls or model calls';render()}catch(e){document.getElementById('stamp').textContent='Refresh failed; prior snapshot retained'}}document.querySelector('#search').oninput=render;document.querySelector('#new').onchange=render;refresh();setInterval(refresh,6000);</script>'''

def data():
    progress=read(SHARED/'results/progress.json') if (SHARED/'results/progress.json').exists() else {}
    oldoss=list(csv.DictReader((ROOT/'pdf/report_data/included_condition_metrics.csv').open(encoding='utf-8-sig')))
    oldnem=read(NEM/'results/exports/user_requested_resolved_metrics.json')
    mapping={m:{(r['task_id'],r['language']):r for r in rows} for m,rows in [('oss',oldoss),('nemotron',oldnem)]}
    for m,vals in progress.get('models',{}).items(): mapping[m].update({(r['task_id'],r['language']):r for r in vals['resolved']})
    tasks=[]
    for tid in read(SHARED/'config/selection.json')['original_matched_task_ids']+TASKS:
        t={'id':tid,'added':tid in TASKS}
        for m in mapping:
            t[m]={}
            for l in ['en','hi','hinglish']:
                r=mapping[m].get((tid,l))
                if r:
                    score=r.get('original_score');score=float(score) if score not in [None,''] and r['status'] in ['completed','agent_failed','budget_exhausted','timeout','integrity_failed'] else None
                    t[m][l]={'score':score,'status':r['status'],'attempt':r.get('attempt_number',1)}
        tasks.append(t)
    return dict(tasks=tasks,counts=progress.get('counts',dict(primary_terminal=0,resolved_conditions=0,total_attempts=0)),accounting=progress.get('accounting',dict(transmissions=0)),active=read(SHARED/'results/active.json') if (SHARED/'results/active.json').exists() else None,hold=read(SHARED/'results/hold.json') if (SHARED/'results/hold.json').exists() else None,complete=read(SHARED/'results/completion.json').get('complete') if (SHARED/'results/completion.json').exists() else False,observed=datetime.now(timezone.utc).isoformat(),updated_utc=progress.get('updated_utc'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path not in ['/','/api']: self.send_error(404);return
        body=PAGE.encode() if self.path=='/' else json.dumps(data(),ensure_ascii=False).encode()
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8' if self.path=='/' else 'application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=0);args=parser.parse_args()
    s=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);url='http://127.0.0.1:'+str(s.server_port)+'/'
    atomic_json(SHARED/'results/browser_monitor.json',{'pid':os.getpid(),'url':url,'started_utc':datetime.now(timezone.utc).isoformat(),'module':'scripts.monitor50','read_only':True})
    print(url,flush=True);s.serve_forever()
