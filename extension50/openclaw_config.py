from extension50.contract import validate_profile


def configuration(token, profile, limits):
    validate_profile(profile)
    model = profile['model']
    thinking = profile['agent_thinking']
    return {
        'models': {'mode': 'replace', 'providers': {'ihb': {
            'baseUrl': 'http://ihb-relay:8080/v1', 'apiKey': token,
            'api': 'openai-completions', 'timeoutSeconds': limits['attempt_timeout_sec'], 'models': [{
                'id': model, 'name': model, 'reasoning': profile['thinking'], 'input': ['text'],
                'contextWindow': profile['context_window'], 'maxTokens': limits['max_response_tokens'],
                'cost': {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0}}]}}},
        'agents': {'defaults': {'workspace': '/workspace',
            'model': {'primary': 'ihb/' + model, 'fallbacks': []},
            'models': {'ihb/' + model: {'params': {'temperature': 0}}},
            'thinkingDefault': thinking, 'timeoutSeconds': limits['attempt_timeout_sec'],
            'skipBootstrap': True, 'compaction': {'memoryFlush': {'enabled': False}},
            'sandbox': {'mode': 'off'}}},
        'tools': {'allow': ['read', 'write', 'edit', 'exec', 'process'],
                  'elevated': {'enabled': False}, 'exec': {'host': 'gateway', 'security': 'full', 'ask': 'off'}},
        'channels': {}, 'plugins': {'enabled': False}, 'browser': {'enabled': False},
        'update': {'checkOnStart': False}, 'gateway': {'mode': 'local', 'bind': 'loopback'},
    }
