import io
import json
import unittest
from nextbench_repair.upstream import assemble, IncompleteStream


class Response(io.BytesIO):
    headers = {'Content-Type':'text/event-stream'}


def stream(chunks, done=True):
    text = ''.join('data: '+json.dumps(c,ensure_ascii=False)+'\n\n' for c in chunks)
    if done: text += 'data: [DONE]\n\n'
    return Response(text.encode())


class StreamingTests(unittest.TestCase):
    def test_reasoning_unicode_fragmented_tools_finish_and_authoritative_usage(self):
        chunks=[{'id':'a','model':'nemotron-3-super','choices':[{'index':0,'delta':{'role':'assistant','reasoning':'सोच','tool_calls':[{'index':0,'id':'call','type':'function','function':{'name':'write','arguments':'{"text":"'}}]}}]},
                {'id':'a','model':'nemotron-3-super','choices':[{'index':0,'delta':{'reasoning':' पूर्ण','tool_calls':[{'index':0,'function':{'arguments':'नमस्ते"}'}}]},'finish_reason':'tool_calls'}]},
                {'id':'a','model':'nemotron-3-super','choices':[],'usage':{'prompt_tokens':9,'completion_tokens':4,'completion_tokens_details':{'reasoning_tokens':2}}}]
        data,timing=assemble(stream(chunks))
        self.assertEqual(data['choices'][0]['message']['reasoning'],'सोच पूर्ण')
        self.assertEqual(data['choices'][0]['message']['tool_calls'][0]['function']['arguments'],'{"text":"नमस्ते"}')
        self.assertEqual(data['usage']['completion_tokens_details']['reasoning_tokens'],2)
        self.assertEqual(data['choices'][0]['finish_reason'],'tool_calls')
        self.assertEqual(timing['events'],3)

    def test_empty_final_length_is_preserved_without_fabricated_success(self):
        data,_=assemble(stream([{'id':'a','model':'nemotron-3-super','choices':[{'index':0,'delta':{'reasoning_content':'unfinished'},'finish_reason':'length'}]},
                               {'choices':[],'usage':{'prompt_tokens':2,'completion_tokens':8}}]))
        self.assertEqual(data['choices'][0]['message']['content'],'')
        self.assertEqual(data['choices'][0]['finish_reason'],'length')

    def test_truncated_stream_or_missing_usage_never_releases_reservation(self):
        c={'id':'a','model':'nemotron-3-super','choices':[{'index':0,'delta':{'content':'partial'},'finish_reason':'stop'}]}
        for response in (stream([c],done=False),stream([c])):
            with self.assertRaises(IncompleteStream): assemble(response)

    def test_model_identity_changes_and_unbounded_tool_indices_fail_closed(self):
        with self.assertRaises(ValueError):
            assemble(stream([{'id':'a','model':'one','choices':[]},{'id':'a','model':'two','choices':[]}]))
        with self.assertRaises(ValueError):
            assemble(stream([{'choices':[{'delta':{'tool_calls':[{'index':1000000}]}}]}]))

    def test_keepalive_comments_do_not_become_model_content(self):
        c={'id':'a','model':'nemotron-3-super','choices':[{'index':0,'delta':{'content':'OK'},'finish_reason':'stop'}],'usage':{'prompt_tokens':2,'completion_tokens':1}}
        response=stream([c]); response=Response(b': keepalive\n\n'+response.getvalue())
        data,_=assemble(response); self.assertEqual(data['choices'][0]['message']['content'],'OK')


if __name__=='__main__': unittest.main()
