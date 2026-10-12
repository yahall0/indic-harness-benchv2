import tempfile
import unittest
from pathlib import Path
from bench.durable import Journal
from bench.metrics import attempt_metrics

class BudgetPolicyTests(unittest.TestCase):
    def test_revised_cap_admits_request_blocked_by_old_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            j=Journal(Path(tmp)/'journal.sqlite3')
            try:
                j.plan(['canary'],'test');run=j.runs()[0]['id'];j.start(run)
                limits={'attempt_timeout_sec':600,'max_requests':30,'max_input_tokens':100000,'max_output_tokens':16000,'max_response_tokens':4096}
                j.reserve(run,'a'*32,65000,4096,limits)
                j.settle('a'*32,{'usage':{'prompt_tokens':63000,'completion_tokens':2000}})
                with self.assertRaisesRegex(ValueError,'input budget exhausted'):
                    j.reserve(run,'b'*32,45000,4096,limits)
                self.assertEqual(j.get(run)['requests'],1)
                larger={**limits,'max_input_tokens':200000}
                j.reserve(run,'b'*32,45000,4096,larger)
                self.assertEqual(j.get(run)['requests'],2)
                metric=attempt_metrics(j,j.get(run),'canary')
                self.assertIsNone(metric['input_tokens'])
                self.assertEqual(metric['known_input_tokens'],63000)
                self.assertEqual(metric['unaccounted_input_reserved'],45000)
                with self.assertRaisesRegex(ValueError,'input budget exhausted'):
                    j.reserve(run,'c'*32,100000,4096,larger)
                self.assertEqual(j.get(run)['requests'],2)
            finally:j.close()

if __name__=='__main__': unittest.main()
