from __future__ import annotations
import io
import json
import tarfile
import uuid
from pathlib import Path
from bench.security import (docker,restricted_args,validate_container,create_workspace_volume,
    create_internal_network,remove_owned,bounded_docker,workspace_archive,validated_archive,SecurityError)

ROOT=Path(__file__).resolve().parents[1]

class Containers:
    def __init__(self,journal=None,run_id=None):
        self.images=json.loads((ROOT/'config/images.json').read_text())
        self.resources=[]; self.journal=journal; self.run_id=run_id
        self.identities={}
    def name(self,role): return 'ihb-'+role+'-'+uuid.uuid4().hex[:12]
    def record(self,kind,name):
        self.resources.append((kind,name))
        if self.journal: self.journal.resource(kind,name,self.run_id)
    def workspace(self):
        name=self.name('work'); self.record('volume',name); create_workspace_volume(name); self.bind('volume',name); return name
    def internal(self):
        name=self.name('net'); self.record('network',name); create_internal_network(name); self.bind('network',name); return name
    def bind(self,kind,name):
        info=json.loads(docker([kind,'inspect',name]))[0]
        ident=info['Name'] if kind=='volume' else info['Id']
        self.identities[(kind,name)]=ident
        if self.journal: self.journal.resource_bound(kind,name,ident)
        return ident
    def create(self,role,*,network='none',volume=None,command=('sleep','900'),extra=()):
        name=self.name(role); self.record('container',name)
        docker(['create',*restricted_args(name,network=network,workspace_volume=volume),*extra,self.images[role]['id'],*command])
        self.bind('container',name)
        validate_container(json.loads(docker(['inspect',name]))[0],network=network,workspace_volume=volume)
        docker(['start',name]); return name
    def invoke(self,container,request,*,timeout=90,program='/opt/ihb/grader.py'):
        data=bounded_docker(['exec','-i',container,'python',program],input_bytes=(json.dumps(request,ensure_ascii=False)+'\n').encode(),
                           max_bytes=4*1024*1024,timeout=timeout)
        return json.loads(data.decode().strip().splitlines()[-1])
    def import_archive(self,container,data):
        tar,members=validated_archive(data)
        # Rebuild headers: source UID, file modes and PAX metadata are untrusted.
        out=io.BytesIO()
        with tarfile.open(fileobj=out,mode='w') as clean:
            for m in members:
                info=tarfile.TarInfo(m.name); info.type=tarfile.DIRTYPE if m.isdir() else tarfile.REGTYPE
                info.mode=0o770 if m.isdir() else 0o660; info.uid=info.gid=10001; info.size=0 if m.isdir() else m.size
                clean.addfile(info,None if m.isdir() else tar.extractfile(m))
        tar.close()
        # Extraction runs non-root IN Docker, after complete host-side header validation.
        docker(['exec','-i',container,'tar','-xf','-','-C','/workspace','--no-same-owner'],input_bytes=out.getvalue())
    def prepared(self,task):
        c=self.create('grader')
        state=self.invoke(c,{'action':'prepare','task':task})['state']
        # Docker cp omits direct container tmpfs mounts on this engine. This trusted
        # fixture-only container has no agent/submitted code; archive inside its namespace.
        data=bounded_docker(['exec',c,'tar','-c','-C','/workspace','.'],max_bytes=68*1024*1024)
        tar,members=validated_archive(data); tar.close()
        return data,state
    def grade(self,task,data,*,action='grade',state=None,round_index=0,ok=True):
        c=self.create('grader'); self.import_archive(c,data)
        return self.invoke(c,{'action':action,'task':task,'state':state or {},'round':round_index,'ok':ok},timeout=240)
    def cleanup(self):
        errors=[]
        for kind,name in reversed(self.resources):
            try:
                # Only names recorded by this controller, with matching ownership labels.
                remove_owned(kind,name,expected_id=self.identities.get((kind,name)))
                if self.journal: self.journal.resource_removed(kind,name)
            except Exception:
                exists=docker([kind,'ls','--format','{{json .}}'])
                if name.encode() in exists: errors.append({'kind':kind,'name':name,'error':'owned_resource_cleanup_failed'})
        self.resources=[]
        if errors: raise SecurityError(json.dumps(errors))

def emergency_stop(journal):
    stopped=[]
    for r in journal.resources():
        if r['kind']!='container': continue
        name=r['id']
        try:
            inspected=json.loads(docker(['inspect',name]))[0]
            from bench.security import LABEL,LABEL_VALUE,resource_name
            resource_name(name)
            if inspected['Config'].get('Labels',{}).get(LABEL)!=LABEL_VALUE: raise SecurityError('Ownership mismatch')
            if r.get('object_id') and inspected['Id']!=r['object_id']: raise SecurityError('Recorded container ID mismatch')
            if inspected['State']['Running']: docker(['kill',inspected['Id']])
            stopped.append(name)
        except SecurityError:
            listing=docker(['container','ls','-a','--filter','name=^/'+name+'$','--format','{{.ID}}'])
            if listing.strip(): raise
            journal.event(r['run_id'],'emergency_stop_check',{'container':name,'status':'absent'})
    journal.event(None,'emergency_stop',{'stopped':stopped})
    return stopped
