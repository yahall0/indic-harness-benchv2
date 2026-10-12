"""Controller-owned journal. Transactions commit before external side effects."""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import time
import threading
from functools import wraps
from pathlib import Path

TERMINAL = {'completed', 'agent_failed', 'timeout', 'budget_exhausted','integrity_failed','infrastructure_failed', 'interrupted', 'quota_paused'}

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as f:
        f.write(encode(value) + '\n'); f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)

class Journal:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY, task TEXT NOT NULL, language TEXT NOT NULL,
            dataset_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'planned',
            started REAL, finished REAL, result TEXT,
            requests INTEGER NOT NULL DEFAULT 0, input_bound INTEGER NOT NULL DEFAULT 0,
            output_reserved INTEGER NOT NULL DEFAULT 0, input_actual INTEGER NOT NULL DEFAULT 0,
            output_actual INTEGER NOT NULL DEFAULT 0, usage_missing INTEGER NOT NULL DEFAULT 0,
            UNIQUE(task,language,dataset_hash));
          CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, at REAL NOT NULL,
            kind TEXT NOT NULL, payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
            reserved_at REAL NOT NULL, input_bound INTEGER NOT NULL, allowance INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'reserved', response TEXT);
          CREATE TABLE IF NOT EXISTS slots (
            id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'eligible', reason TEXT,
            changed REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS resources (
            kind TEXT NOT NULL, id TEXT NOT NULL, run_id TEXT,
            status TEXT NOT NULL DEFAULT 'recorded', PRIMARY KEY(kind,id));
          CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS forwards (
            call_id TEXT NOT NULL, ordinal INTEGER NOT NULL, slot TEXT NOT NULL,
            at REAL NOT NULL, PRIMARY KEY(call_id,ordinal));
        ''')
        if 'object_id' not in {r[1] for r in self.db.execute('PRAGMA table_info(resources)')}:
            self.db.execute('ALTER TABLE resources ADD COLUMN object_id TEXT')

    def close(self): self.db.close()

    def _event(self, run_id, kind, payload):
        self.db.execute('INSERT INTO events(run_id,at,kind,payload) VALUES(?,?,?,?)',
                        (run_id,time.time(),kind,encode(payload)))

    def event(self, run_id, kind, payload):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self._event(run_id,kind,payload); self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def plan(self, tasks, dataset_hash):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            for index, task in enumerate(tasks):
                order = ['en','hi','hinglish']
                order = order[index % 3:] + order[:index % 3]
                for language in order:
                    ident = hashlib.sha256(f'{dataset_hash}:{task}:{language}:1'.encode()).hexdigest()[:24]
                    self.db.execute('INSERT OR IGNORE INTO runs(id,task,language,dataset_hash) VALUES(?,?,?,?)',
                                    (ident,task,language,dataset_hash))
            self._event(None,'plan_created',{'dataset_hash':dataset_hash,'tasks':len(tasks)})
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def runs(self): return [dict(r) for r in self.db.execute('SELECT * FROM runs ORDER BY rowid')]
    def get(self, run_id):
        r=self.db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
        if not r: raise ValueError('Unknown run')
        return dict(r)

    def start(self, run_id):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.get(run_id)
            if row['status'] != 'planned': raise ValueError('Attempt already started; automatic rerun prohibited')
            self.db.execute("UPDATE runs SET status='running',started=? WHERE id=?",(time.time(),run_id))
            self._event(run_id,'attempt_started',{})
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def finish(self, run_id, status, result):
        if status not in TERMINAL: raise ValueError('Invalid final status')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.get(run_id)
            if row['status'] != 'running': raise ValueError('Cannot overwrite a completed attempt')
            self.db.execute('UPDATE runs SET status=?,finished=?,result=? WHERE id=?',
                            (status,time.time(),encode(result),run_id))
            self._event(run_id,'attempt_finished',{'status':status,'result':result})
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def reserve(self, run_id, call_id, input_bound, requested_output, limits):
        """Idempotent reservation; every retry uses the SAME logical call ID."""
        if not re.fullmatch('[a-f0-9]{24,64}',call_id): raise ValueError('Invalid call ID')
        if not isinstance(input_bound,int) or input_bound<1: raise ValueError('Invalid input bound')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            existing=self.db.execute('SELECT * FROM calls WHERE id=?',(call_id,)).fetchone()
            if existing:
                if existing['run_id']!=run_id or existing['input_bound']!=input_bound:
                    raise ValueError('Idempotency key collision')
                if existing['status']!='reserved': raise ValueError('Call already settled; do not repeat inference')
                result=dict(existing)
            else:
                r=self.get(run_id)
                if r['status']!='running': raise ValueError('Attempt inactive')
                if time.time()-r['started'] >= limits['attempt_timeout_sec']: raise ValueError('Attempt timeout')
                allowance=min(requested_output,limits['max_response_tokens'],limits['max_output_tokens']-r['output_reserved'])
                if allowance<1:
                    raise ValueError(f"Attempt output budget exhausted (charged={r['output_reserved']}, limit={limits['max_output_tokens']})")
                if r['requests']>=limits['max_requests']:
                    raise ValueError(f"Attempt request budget exhausted (requests={r['requests']}, limit={limits['max_requests']})")
                if r['input_bound']+input_bound>limits['max_input_tokens']:
                    raise ValueError(f"Attempt input budget exhausted (charged={r['input_bound']}, next_bound={input_bound}, limit={limits['max_input_tokens']})")
                self.db.execute('INSERT INTO calls(id,run_id,reserved_at,input_bound,allowance) VALUES(?,?,?,?,?)',
                                (call_id,run_id,time.time(),input_bound,allowance))
                self.db.execute('UPDATE runs SET requests=requests+1,input_bound=input_bound+?,output_reserved=output_reserved+? WHERE id=?',
                                (input_bound,allowance,run_id))
                result={'id':call_id,'allowance':allowance,'input_bound':input_bound}
                self._event(run_id,'inference_reserved',result)
            self.db.execute('COMMIT'); return result
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def settle(self, call_id, response):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            c=self.db.execute('SELECT * FROM calls WHERE id=?',(call_id,)).fetchone()
            if not c: raise ValueError('Unreserved inference')
            if c['status']=='settled':
                if c['response']!=encode(response): raise ValueError('Conflicting settlement')
                usage=response.get('usage')
                valid=isinstance(usage,dict) and all(isinstance(usage.get(k),int) and usage[k]>=0 for k in ('prompt_tokens','completion_tokens'))
                violation=valid and (usage['prompt_tokens']>c['input_bound'] or usage['completion_tokens']>c['allowance'])
                self.db.execute('COMMIT'); return {'budget_violation':violation}
            usage=response.get('usage')
            missing=not isinstance(usage,dict) or not all(isinstance(usage.get(k),int) and usage[k]>=0 for k in ('prompt_tokens','completion_tokens'))
            inp=0 if missing else usage['prompt_tokens']; out=0 if missing else usage['completion_tokens']
            # Missing/ambiguous usage keeps the FULL reservation charged. Never release it optimistically.
            reclaim=0 if missing else max(0,c['allowance']-out)
            reclaim_input=0 if missing else max(0,c['input_bound']-inp)
            self.db.execute("UPDATE calls SET status='settled',response=? WHERE id=?",(encode(response),call_id))
            self.db.execute('UPDATE runs SET input_actual=input_actual+?,output_actual=output_actual+?,output_reserved=output_reserved-?,input_bound=input_bound-?,usage_missing=usage_missing+? WHERE id=?',
                            (inp,out,reclaim,reclaim_input,int(missing),c['run_id']))
            self._event(c['run_id'],'inference_settled',{'call_id':call_id,**response})
            violation=inp>c['input_bound'] or out>c['allowance']
            if violation:
                self._event(c['run_id'],'budget_integrity_violation',{'call_id':call_id})
            self.db.execute('COMMIT')
            return {'budget_violation':violation}
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def forward(self, call_id, slot, limits, transmission_id=None):
        """Persist every physical upstream request before forwarding, including retries."""
        self.db.execute('BEGIN IMMEDIATE')
        try:
            c=self.db.execute('SELECT * FROM calls WHERE id=?',(call_id,)).fetchone()
            if not c or c['status']!='reserved': raise ValueError('Inactive call')
            r=self.get(c['run_id'])
            if r['status']!='running' or time.time()-r['started']>=limits['attempt_timeout_sec']:
                raise ValueError('Attempt inactive or timed out')
            receipt=None
            if transmission_id is not None:
                if not re.fullmatch('[a-f0-9]{24,64}',transmission_id): raise ValueError('Invalid transmission ID')
                receipt='forward_ack:'+call_id+':'+transmission_id
                prior=self.db.execute('SELECT value FROM metadata WHERE key=?',(receipt,)).fetchone()
                if prior:
                    value=json.loads(prior['value'])
                    if value['slot']!=slot: raise ValueError('Conflicting transmission acknowledgment')
                    self.db.execute('COMMIT'); return value['ordinal']
            count=self.db.execute('SELECT COUNT(*) FROM forwards WHERE call_id=?',(call_id,)).fetchone()[0]
            if count:
                if r['requests']>=limits['max_requests']:
                    raise ValueError('Retry would exceed request budget')
                if r['input_bound']+c['input_bound']>limits['max_input_tokens']:
                    raise ValueError('Retry would exceed input budget')
                if r['output_reserved']+c['allowance']>limits['max_output_tokens']:
                    raise ValueError('Retry would exceed output budget')
                self.db.execute('UPDATE runs SET requests=requests+1,input_bound=input_bound+?,output_reserved=output_reserved+? WHERE id=?',
                    (c['input_bound'],c['allowance'],c['run_id']))
            self.db.execute('INSERT INTO forwards VALUES(?,?,?,?)',(call_id,count+1,slot,time.time()))
            if receipt: self.db.execute('INSERT INTO metadata VALUES(?,?)',(receipt,encode({'slot':slot,'ordinal':count+1})))
            self._event(c['run_id'],'inference_forwarded',{'call_id':call_id,'ordinal':count+1,'slot':slot})
            self.db.execute('COMMIT')
            return count+1
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def rejected_forward(self, call_id):
        """Provider explicitly rejected for rate/quota BEFORE inference; reclaim only this transmission."""
        self.db.execute('BEGIN IMMEDIATE')
        try:
            c=self.db.execute('SELECT * FROM calls WHERE id=?',(call_id,)).fetchone()
            if not c or c['status']!='reserved': raise ValueError('Inactive call')
            count=self.db.execute('SELECT COUNT(*) FROM forwards WHERE call_id=?',(call_id,)).fetchone()[0]
            if not count: raise ValueError('No transmission')
            marker=f'{call_id}:{count}'
            if self.db.execute('SELECT 1 FROM metadata WHERE key=?',('rejected:'+marker,)).fetchone():
                self.db.execute('COMMIT'); return
            self.db.execute('INSERT INTO metadata VALUES(?,?)',('rejected:'+marker,'true'))
            self.db.execute('UPDATE runs SET input_bound=input_bound-?,output_reserved=output_reserved-? WHERE id=?',
                (c['input_bound'],c['allowance'],c['run_id']))
            self._event(c['run_id'],'inference_rejected_without_generation',{'call_id':call_id,'ordinal':count})
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def slot_init(self, slots):
        for s in slots:
            self.db.execute('INSERT OR IGNORE INTO slots(id,changed) VALUES(?,?)',(s,time.time()))

    def slot_state(self): return [dict(r) for r in self.db.execute('SELECT * FROM slots ORDER BY id')]

    def choose_slot(self, preferred=None,allowed=None):
        eligible=[r['id'] for r in self.slot_state() if r['state']=='eligible' and (allowed is None or r['id'] in allowed)]
        if preferred in eligible: return preferred
        if not eligible: raise ValueError('All configured credential slots exhausted or paused')
        return eligible[0]

    def exhaust_slot(self, slot, reason, run_id):
        if reason!='confirmed_quota_exhaustion': raise ValueError('Only confirmed quota exhaustion permits automatic rotation')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self.db.execute("UPDATE slots SET state='exhausted',reason=?,changed=? WHERE id=?",(reason,time.time(),slot))
            self._event(run_id,'credential_exhausted',{'slot':slot,'reason':reason})
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def reactivate_slot(self,slot):
        if slot not in {r['id'] for r in self.slot_state()}: raise ValueError('Unknown credential slot')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self.db.execute("UPDATE slots SET state='eligible',reason='operator_confirmed_allowance_reset',changed=? WHERE id=?",(time.time(),slot))
            self._event(None,'credential_reactivated',{'slot':slot,'reason':'operator_confirmed_allowance_reset'})
            self.db.execute('COMMIT')
        except BaseException: self.db.execute('ROLLBACK'); raise

    def resource(self, kind, ident, run_id):
        self.db.execute('INSERT OR IGNORE INTO resources(kind,id,run_id) VALUES(?,?,?)',(kind,ident,run_id))

    def resource_removed(self,kind,ident):
        self.db.execute("UPDATE resources SET status='removed' WHERE kind=? AND id=?",(kind,ident))

    def resource_bound(self,kind,name,object_id):
        self.db.execute('UPDATE resources SET object_id=? WHERE kind=? AND id=?',(object_id,kind,name))

    def resources(self): return [dict(r) for r in self.db.execute("SELECT * FROM resources WHERE status!='removed'")]

    def recover(self):
        """Call only with exclusive controller ownership, after stopping recorded agents."""
        for r in self.runs():
            if r['status']=='running':
                self.finish(r['id'],'interrupted',{'cause':'controller_restart','automatic_rerun':False,
                            'note':'Unsettled calls retain reservations; spending may be uncertain.'})

    def export(self, destination):
        dest=Path(destination); dest.mkdir(parents=True,exist_ok=True)
        atomic_json(dest/'runs.json',self.runs())
        path=dest/'events.jsonl'; temp=path.with_name(path.name+'.tmp')
        with temp.open('w',encoding='utf-8',newline='\n') as f:
            for r in self.db.execute('SELECT * FROM events ORDER BY seq'):
                d=dict(r); d['payload']=json.loads(d['payload']); f.write(encode(d)+'\n')
            f.flush(); os.fsync(f.fileno())
        os.replace(temp,path)
        # An online SQLite snapshot includes committed WAL pages and is independently reopenable.
        target=sqlite3.connect(dest/'journal-backup.sqlite3')
        try: self.db.backup(target)
        finally: target.close()

def _serialized(method):
    @wraps(method)
    def wrapped(self,*args,**kwargs):
        with self.lock: return method(self,*args,**kwargs)
    return wrapped

# Controller and HTTP accounting threads share one connection; lock complete transactions.
for _name in ('close','event','plan','runs','get','start','finish','reserve','settle','forward',
              'rejected_forward','slot_init','slot_state','choose_slot','exhaust_slot','reactivate_slot','resource',
              'resource_removed','resource_bound','resources','recover','export'):
    setattr(Journal,_name,_serialized(getattr(Journal,_name)))
