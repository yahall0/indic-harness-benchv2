import unittest
from bench.metrics import compare

class MetricsTests(unittest.TestCase):
    def test_paired_estimates_and_infrastructure_exclusion(self):
        rows=[]
        for task,status,scores in [('A','completed',(1,.5,0)),('B','completed',(1,1,.5)),('C','infrastructure_failed',(1,0,0))]:
            for language,score in zip(('en','hi','hinglish'),scores):
                eligible=status=='completed'
                rows.append({'run_id':task+language,'task_id':task,'language':language,'category':'files','status':status,
                    'original_score':score,'full_completion':int(score==1) if eligible else None,'agent_outcome':eligible,
                    'score_available_for_analysis':eligible,'first_context_prompt_tokens':100 if language=='en' else 200})
        report=compare(rows)
        self.assertEqual(report['complete_triplets'],2)
        self.assertEqual(len(report['incomplete_triplets']),1)
        hi=next(r for r in report['estimates'] if r['category']=='all' and r['contrast']=='English minus hi')
        self.assertEqual(hi['score_difference_pp'],25)
        self.assertEqual(hi['completion_difference_pp'],50)
        self.assertEqual(hi['mean_first_context_token_ratio'],2)
        self.assertEqual(hi['score_bootstrap_95_percent_interval_pp'],[0,50])
    def test_no_results_is_not_zero_performance(self):
        r=compare([])
        self.assertEqual(r['complete_triplets'],0)
        self.assertTrue(all(e['score_difference_pp'] is None for e in r['estimates']))

if __name__=='__main__': unittest.main()
