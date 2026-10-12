import unittest
from bench.translations import protected

class LiteralTests(unittest.TestCase):
    def test_duplicates_are_counted(self):
        p=protected('Use $WORKSPACE and $WORKSPACE, write `out/a.json`.')
        self.assertEqual(p['placeholders']['$WORKSPACE'],2)
        self.assertEqual(p['backtick_literals']['out/a.json'],1)
    def test_exact_quotes_and_numeric_limits(self):
        p=protected('Write "OK" before 2026-05-20. Keep at most 30 rows and 0.05 error.')
        self.assertEqual(p['double_quoted_literals']['"OK"'],1)
        self.assertEqual(p['numbers']['2026-05-20'],1)
        self.assertEqual(p['numbers']['30'],1)
        self.assertEqual(p['numbers']['0.05'],1)
    def test_changed_literal_is_detected(self):
        self.assertNotEqual(protected('Save `out/report.json`'),protected('Save `out/report.csv`'))

if __name__=='__main__': unittest.main()
