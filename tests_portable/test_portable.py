import tempfile,unittest
from pathlib import Path
from scripts.portable import LANGS,MODELS,check,ROOT,safe_path,summary,validate_rows

class PortableTests(unittest.TestCase):
    def rows(self):
        return [{'model':m,'task_id':t,'language':l,'status':'completed','original_score':'.5',
                 'full_completion':'0'} for t in ('one','two') for m in MODELS for l in LANGS]
    def test_public_checkout_has_frozen_bytes_and_all_300_conditions(self):
        result=check(ROOT)
        self.assertTrue(result['passed']);self.assertEqual((result['tasks'],result['scored_conditions']),(50,300))
        self.assertEqual(result['model_calls'],0)
    def test_duplicate_or_missing_condition_is_rejected(self):
        for rows in (self.rows()[:-1],self.rows()[:-1]+[self.rows()[0]]):
            with self.assertRaises(ValueError):validate_rows(rows,expected_tasks=2)
    def test_infra_and_nonfinite_scores_are_rejected(self):
        for change in ({'status':'infrastructure_failed'},{'original_score':'nan'},{'original_score':'1.1'}):
            rows=self.rows();rows[0].update(change)
            with self.assertRaises(ValueError):validate_rows(rows,expected_tasks=2)
    def test_summary_uses_the_saved_fractional_scores(self):
        result=summary(validate_rows(self.rows(),expected_tasks=2))
        self.assertEqual(result['mean_scores_out_of_100']['oss']['hi'],50)
        self.assertEqual(result['overall_model_gain_pp'],0)
    def test_manifest_paths_are_portable_and_cannot_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(safe_path(root,'tasks/one/prompt.txt'),root/'tasks/one/prompt.txt')
            for name in ('../outside','/outside','C:/Users/example/file','tasks\\one',''):
                with self.assertRaises(ValueError):safe_path(root,name)

if __name__=='__main__':unittest.main()
