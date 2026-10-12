"""Local Windows DPAPI secret store. No API calls and no secret output."""
from __future__ import annotations
import base64
import ctypes
import csv
import getpass
import io
import json
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path
from bench.durable import atomic_json

ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'config/credentials.dpapi.json'

class Blob(ctypes.Structure):
    _fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_ubyte))]

def crypt(data,decrypt=False):
    if os.name!='nt': raise RuntimeError('Windows DPAPI is required for local key storage')
    buf=ctypes.create_string_buffer(data); source=Blob(len(data),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)))
    output=Blob(); library=ctypes.WinDLL('crypt32',use_last_error=True)
    if decrypt:
        ok=library.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(output))
    else:
        ok=library.CryptProtectData(ctypes.byref(source),'Indic Harness Bench',None,None,None,1,ctypes.byref(output))
    if not ok: raise ctypes.WinError(ctypes.get_last_error())
    try: return ctypes.string_at(output.pbData,output.cbData)
    finally:
        # WinDLL prototypes prevent pointer truncation in 64-bit Windows.
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.LocalFree.argtypes=[ctypes.c_void_p]; kernel.LocalFree.restype=ctypes.c_void_p
        kernel.LocalFree(output.pbData)

def configure():
    if not sys.stdin.isatty(): raise RuntimeError('Run key setup in your interactive PowerShell terminal; piped secret input is disabled')
    if STORE.exists():
        print('A key store already exists. Setup will replace it; existing results and exhausted-slot records remain unchanged.')
    print('Enter up to four eligible Ollama Cloud keys. Input is hidden. Blank finishes setup.')
    keys={}
    for i in range(1,5):
        value=getpass.getpass(f'Ollama key {i}: ').strip()
        if not value: break
        if value in keys.values(): raise ValueError('Duplicate key entered; store was not changed')
        if any(c.isspace() for c in value) or len(value)<16: raise ValueError('Invalid key format; store was not changed')
        keys[f'slot-{i}']=value
    if not keys: raise ValueError('No keys entered; store was not changed')
    ciphertext=crypt(json.dumps(keys).encode())
    atomic_json(STORE,{'version':1,'protection':'Windows DPAPI current-user','slots':list(keys),
                       'ciphertext':base64.b64encode(ciphertext).decode()})
    # Restrict file ACL to current user's SID, with no inherited entries.
    p=subprocess.run(['whoami','/user','/fo','csv','/nh'],capture_output=True,text=True,check=True)
    sid=list(csv.reader(io.StringIO(p.stdout)))[0][1]
    subprocess.run(['icacls',str(STORE),'/inheritance:r','/grant:r',f'*{sid}:(F)'],capture_output=True,check=True)
    print(f'Saved {len(keys)} encrypted slots. No provider calls were made. Keys are never included in reports.')

def load_keys():
    if STORE.exists():
        meta=json.loads(STORE.read_text(encoding='utf-8'))
        keys=json.loads(crypt(base64.b64decode(meta['ciphertext']),decrypt=True))
    else:
        keys={f'slot-{i}':os.environ[f'INDIC_OLLAMA_KEY_{i}'] for i in range(1,5) if os.environ.get(f'INDIC_OLLAMA_KEY_{i}')}
    if not keys: raise ValueError('No keys configured. Run scripts/configure_keys.py in an interactive terminal.')
    if len(set(keys.values()))!=len(keys): raise ValueError('Duplicate credentials configured')
    return keys

def status():
    try:
        keys=load_keys()
        return {'configured_slots':list(keys),'count':len(keys),'key_values_disclosed':False,'model_calls':0}
    except Exception:
        return {'configured_slots':[],'count':0,'status':'not_configured_or_cannot_decrypt','model_calls':0}

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='configure': configure()
    else: print(json.dumps(status(),indent=2))
