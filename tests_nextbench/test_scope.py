import copy
import json
import unittest
from pathlib import Path

from nextbench.scope import validate_scope


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.scope = json.loads((self.root / 'campaigns/shared/report_matched_scope.json').read_text(encoding='utf-8'))

    def test_saved_scope_matches_authoritative_report_and_all_shared_input_hashes(self):
        result = validate_scope(self.root, self.scope)
        self.assertEqual((result['tasks'], result['conditions'], result['prompt_files']), (46, 138, 156))

    def test_task_loss_or_language_reordering_is_rejected(self):
        for mutation in ('task_loss', 'reordering'):
            scope = copy.deepcopy(self.scope)
            if mutation == 'task_loss':
                scope['conditions'].pop()
            else:
                scope['conditions'][0], scope['conditions'][1] = scope['conditions'][1], scope['conditions'][0]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_scope(self.root, scope)


if __name__ == '__main__':
    unittest.main()
