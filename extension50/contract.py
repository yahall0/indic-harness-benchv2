"""Explicit Nemotron/OpenAI wire contract, also copied into the restricted relay."""
from __future__ import annotations

import copy
import email.utils
import json
import time


def validate_profile(profile):
    if not isinstance(profile,dict) or profile.get('model') not in ('gpt-oss:20b','nemotron-3-super'):
        raise ValueError('Only the two frozen models; no fallback')
    expected='medium' if profile['model']=='gpt-oss:20b' else 'high'
    if profile.get('thinking') is not True or profile.get('provider_reasoning_effort')!=expected or profile.get('agent_thinking')!=expected:
        raise ValueError('Original model-specific reasoning settings required')
    if profile.get('context_window')!=65536 or profile.get('provider_context_window',0)<65536:
        raise ValueError('Fixed supported context required')
    if profile.get('response_model_aliases')!=[profile['model']]: raise ValueError('Pinned identity required')
    return profile


def request_payload(request, profile):
    validate_profile(profile)
    if request.get('model') != profile['model']:
        raise ValueError('Configured model only; no fallback')
    if not isinstance(request.get('messages'), list) or not request['messages']:
        raise ValueError('Messages required')
    for message in request['messages']:
        if not isinstance(message, dict) or message.get('role') not in {'system', 'developer', 'user', 'assistant', 'tool'}:
            raise ValueError('Invalid chat message')
        content = message.get('content')
        if content is not None and not isinstance(content, str):
            if not isinstance(content, list) or any(not isinstance(p, dict) or p.get('type') != 'text'
                                                   or not isinstance(p.get('text'), str) for p in content):
                raise ValueError('Text-only messages required')
    payload = {key: copy.deepcopy(request[key]) for key in ('messages', 'tools', 'tool_choice', 'stop') if key in request}
    payload.update(model=profile['model'], temperature=0,
                   reasoning_effort=profile['provider_reasoning_effort'], stream=False)
    return payload


def completion(data, profile):
    validate_profile(profile)
    if not isinstance(data, dict) or not isinstance(data.get('choices'), list) or not data['choices']:
        raise ValueError('Invalid completion envelope')
    if data.get('model') not in profile['response_model_aliases']:
        raise ValueError('Unverified provider model identity')
    normalized = copy.deepcopy(data)
    tool_count, schema_errors = 0, 0
    for choice in normalized['choices']:
        if not isinstance(choice, dict) or not isinstance(choice.get('message'), dict):
            raise ValueError('Invalid completion choice')
        message = choice['message']
        if message.get('content') is not None and not isinstance(message.get('content'), str):
            raise ValueError('Non-text completion content')
        # OpenClaw's installed OpenAI client consumes reasoning_content. Keep the
        # raw upstream trace intact and never merge reasoning into the final answer.
        if 'reasoning_content' not in message and isinstance(message.get('reasoning'), str):
            message['reasoning_content'] = message.pop('reasoning')
        tools = message.get('tool_calls')
        if tools is None:
            message.pop('tool_calls', None)
        elif not isinstance(tools, list):
            raise ValueError('Invalid completion tool list')
        else:
            tool_count += len(tools)
            for tool in tools:
                function = tool.get('function', {}) if isinstance(tool, dict) else {}
                if not isinstance(function, dict):
                    function = {}
                try:
                    args = function.get('arguments')
                    if (not isinstance(tool, dict) or tool.get('type') != 'function'
                            or not isinstance(tool.get('id'), str) or not tool['id']
                            or not isinstance(function.get('name'), str)
                            or not isinstance(args, str) or not isinstance(json.loads(args), dict)):
                        schema_errors += 1
                except (ValueError, TypeError):
                    schema_errors += 1
                # Generated malformed arguments stay unchanged for agent-level
                # handling; they never become an infrastructure recovery reason.
    return normalized, tool_count, schema_errors


def stream_chunks(data, call_id):
    for choice in data['choices']:
        delta = copy.deepcopy(choice['message'])
        for index, tool in enumerate(delta.get('tool_calls', [])):
            if isinstance(tool, dict):
                tool['index'] = index
        chunk = {'id': data.get('id', call_id), 'object': 'chat.completion.chunk',
                 'created': data.get('created', int(time.time())), 'model': data['model'],
                 'choices': [{'index': choice.get('index', 0), 'delta': delta, 'finish_reason': None}]}
        yield chunk
        yield {**chunk, 'choices': [{'index': choice.get('index', 0), 'delta': {},
                                    'finish_reason': choice.get('finish_reason')}]}
    yield {'id': data.get('id', call_id), 'object': 'chat.completion.chunk',
           'created': data.get('created', int(time.time())), 'model': data['model'],
           'choices': [], 'usage': data.get('usage')}


def retry_delay(headers):
    value = headers.get('Retry-After', '0')
    try:
        seconds = float(value)
    except (ValueError, TypeError):
        try:
            seconds = email.utils.parsedate_to_datetime(value).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            seconds = 1
    return min(30, max(1, int(seconds)))
