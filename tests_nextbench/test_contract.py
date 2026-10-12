import copy
import unittest

from nextbench.contract import completion, request_payload, stream_chunks, retry_delay

PROFILE = {'model': 'nemotron-3-super', 'thinking': True, 'provider_reasoning_effort': 'high',
           'context_window': 65536, 'provider_context_window': 262144,
           'response_model_aliases': ['nemotron-3-super']}


class ContractTests(unittest.TestCase):
    def test_boolean_thinking_is_explicit_and_unknown_provider_extensions_are_removed(self):
        request = {'model': PROFILE['model'], 'messages': [{'role': 'user', 'content': 'हिन्दी ठीक है।'}],
                   'reasoning_effort': 'medium', 'temperature': 1, 'stream': True, 'unsafe_url': 'https://example.com'}
        payload = request_payload(request, PROFILE)
        self.assertEqual(payload['reasoning_effort'], 'high')
        self.assertEqual(payload['temperature'], 0)
        self.assertFalse(payload['stream'])
        self.assertNotIn('unsafe_url', payload)
        self.assertEqual(payload['messages'], request['messages'])

    def test_reasoning_is_separate_unicode_and_tool_arguments_remain_exact(self):
        data = {'model': PROFILE['model'], 'choices': [{'message': {'role': 'assistant', 'content': None,
                'reasoning': 'यह विचार है।', 'tool_calls': [{'id': 'call_1', 'type': 'function',
                'function': {'name': 'exec', 'arguments': '{"command":"printf हिन्दी"}'}}]}, 'finish_reason': 'tool_calls'}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'completion_tokens_details': {'reasoning_tokens': 3}}}
        original = copy.deepcopy(data)
        normalized, calls, errors = completion(data, PROFILE)
        self.assertEqual((calls, errors), (1, 0))
        self.assertEqual(data, original)
        self.assertEqual(normalized['choices'][0]['message']['reasoning_content'], 'यह विचार है।')
        self.assertIsNone(normalized['choices'][0]['message']['content'])
        chunks = list(stream_chunks(normalized, 'c' * 32))
        self.assertEqual(chunks[0]['choices'][0]['delta']['tool_calls'][0]['index'], 0)
        self.assertEqual(chunks[-1]['usage']['completion_tokens'], 5)
        self.assertNotIn('index', normalized['choices'][0]['message']['tool_calls'][0])

    def test_length_reason_and_empty_final_answer_are_never_fabricated_as_success(self):
        data = {'model': PROFILE['model'], 'choices': [{'message': {'role': 'assistant', 'content': '',
                'reasoning_content': 'unfinished thought', 'tool_calls': None}, 'finish_reason': 'length'}]}
        normalized, _, _ = completion(data, PROFILE)
        chunks = list(stream_chunks(normalized, 'c' * 32))
        self.assertEqual(chunks[0]['choices'][0]['delta']['content'], '')
        self.assertEqual(chunks[1]['choices'][0]['finish_reason'], 'length')
        self.assertNotIn('tool_calls', chunks[0]['choices'][0]['delta'])

    def test_generated_bad_json_arguments_are_counted_without_infra_reclassification(self):
        data = {'model': PROFILE['model'], 'choices': [{'message': {'role': 'assistant', 'content': None,
                'tool_calls': [{'id': 'call_1', 'type': 'function', 'function': {'name': 'exec', 'arguments': '{bad'}}]},
                'finish_reason': 'tool_calls'}]}
        normalized, calls, errors = completion(data, PROFILE)
        self.assertEqual((calls, errors), (1, 1))
        self.assertEqual(normalized['choices'][0]['message']['tool_calls'][0]['function']['arguments'], '{bad')

    def test_missing_or_different_model_identity_and_multimodal_requests_are_rejected(self):
        for model in (None, 'gpt-oss:20b', 'nemotron-3-nano:30b'):
            with self.subTest(model=model), self.assertRaises(ValueError):
                completion({'model': model, 'choices': [{'message': {'content': 'ok'}}]}, PROFILE)
        with self.assertRaises(ValueError):
            request_payload({'model': PROFILE['model'], 'messages': [{'role': 'user', 'content': [{'type': 'image_url'}]}]}, PROFILE)

    def test_retry_after_numeric_http_date_and_invalid_headers_are_bounded(self):
        for value in ('2', 'Wed, 01 Oct 2036 00:00:00 GMT', 'invalid', '-3'):
            self.assertTrue(1 <= retry_delay({'Retry-After': value}) <= 30)


if __name__ == '__main__':
    unittest.main()
