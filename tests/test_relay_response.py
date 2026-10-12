import copy
import unittest
from runtime.relay import normalize_response

class RelayResponseTests(unittest.TestCase):
    def test_null_tool_calls_preserve_hindi_and_original_trace(self):
        original={'choices':[{'message':{'role':'assistant','content':'हिन्दी ठीक है।','tool_calls':None},'finish_reason':'stop'}]}
        saved=copy.deepcopy(original)
        normalized,count=normalize_response(original)
        self.assertEqual(count,0)
        self.assertEqual(normalized['choices'][0]['message']['content'],'हिन्दी ठीक है।')
        self.assertNotIn('tool_calls',normalized['choices'][0]['message'])
        self.assertEqual(original,saved)

    def test_function_arguments_and_unicode_are_unchanged(self):
        tools=[{'id':'call_1','type':'function','function':{'name':'exec','arguments':'{"command":"printf हिन्दी"}'}}]
        data={'choices':[{'message':{'role':'assistant','content':None,'tool_calls':tools}}]}
        normalized,count=normalize_response(data)
        self.assertEqual(count,1)
        self.assertEqual(normalized,data)

    def test_malformed_completion_is_explicitly_rejected(self):
        for data in (None,{'choices':None},{'choices':[{'message':None}]},{'choices':[{'message':{'tool_calls':'invalid'}}]}):
            with self.subTest(data=data):
                with self.assertRaises(ValueError): normalize_response(data)

if __name__=='__main__': unittest.main()
