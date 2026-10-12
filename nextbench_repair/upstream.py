"""Bounded upstream SSE assembly before durable settlement and agent delivery."""
import http.client
import json
import time

MAX_BYTES = 4 * 1024 * 1024
MAX_LINE = 65536


class IncompleteStream(http.client.HTTPException):
    pass


def assemble(response, *, started=None, now=time.monotonic):
    started = now() if started is None else started
    header_elapsed = now() - started
    content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
    if content_type != 'text/event-stream':
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES: raise ValueError('Upstream response size exceeded')
        data = json.loads(body)
        return data, {'mode':'json_fallback','header_sec':header_elapsed,'complete_sec':now()-started,'bytes':len(body)}
    result = {'object':'chat.completion'}
    choices, events = {}, []
    total, event_count, first_event, done, usage = 0, 0, None, False, None
    while True:
        line = response.readline(MAX_LINE + 1)
        total += len(line)
        if len(line) > MAX_LINE or total > MAX_BYTES: raise ValueError('Upstream SSE size exceeded')
        if not line: break
        if line.strip():
            if line.startswith(b'data:'): events.append(line[5:].lstrip().rstrip(b'\r\n'))
            continue
        if not events: continue
        raw = b'\n'.join(events); events = []
        if raw.strip() == b'[DONE]': done = True; break
        chunk = json.loads(raw)
        if first_event is None: first_event = now() - started
        event_count += 1
        for key in ('id','created','model','system_fingerprint'):
            if key in chunk:
                if key in result and key in {'id','model'} and result[key] != chunk[key]:
                    raise ValueError('Upstream SSE identity changed')
                result[key] = chunk[key]
        if isinstance(chunk.get('usage'),dict): usage = chunk['usage']
        for choice in chunk.get('choices',[]):
            index = choice.get('index',0)
            if not isinstance(index,int) or not 0 <= index < 4: raise ValueError('Upstream choice index exceeded')
            row = choices.setdefault(index,{'index':index,'message':{'role':'assistant','content':''},'finish_reason':None})
            message, delta = row['message'], choice.get('delta',{})
            for key in ('content','reasoning','reasoning_content'):
                if isinstance(delta.get(key),str): message[key] = message.get(key,'') + delta[key]
            for call in delta.get('tool_calls',[]) or []:
                i = call.get('index',0)
                if not isinstance(i,int) or not 0 <= i < 64: raise ValueError('Upstream tool index exceeded')
                tools = message.setdefault('tool_calls',[])
                while len(tools) <= i: tools.append({'id':'','type':'function','function':{'name':'','arguments':''}})
                target = tools[i]
                if isinstance(call.get('id'),str): target['id'] += call['id']
                if call.get('type'): target['type'] = call['type']
                for key in ('name','arguments'):
                    value = call.get('function',{}).get(key)
                    if isinstance(value,str): target['function'][key] += value
            if choice.get('finish_reason') is not None: row['finish_reason'] = choice['finish_reason']
    if not done or not choices or any(c['finish_reason'] is None for c in choices.values()):
        raise IncompleteStream('Upstream completion stream ended before complete finish')
    if not isinstance(usage,dict) or not all(isinstance(usage.get(k),int) and usage[k] >= 0 for k in ('prompt_tokens','completion_tokens')):
        raise IncompleteStream('Upstream completion stream omitted authoritative usage')
    result.update(choices=[choices[i] for i in sorted(choices)],usage=usage)
    return result, {'mode':'sse_buffered_until_settled','header_sec':header_elapsed,
                    'first_event_sec':first_event,'complete_sec':now()-started,'events':event_count,'bytes':total}


def post(opener, request):
    started = time.monotonic()
    # Wait for initial headers within the diagnostic-verified allowance. Streaming
    # thereafter supplies liveness; the controller still enforces the original
    # whole-attempt task/600-second deadline and kills the entire container.
    with opener.open(request,timeout=180) as response:
        data, timing = assemble(response,started=started)
        data['_ihb_transport'] = timing
        return response.status,json.dumps(data,ensure_ascii=False).encode(),response.headers
