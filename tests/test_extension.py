import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing
from bench.durable import Journal,atomic_json
from bench.extension import check_extension,ordered_tasks
from bench.readiness import freeze


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='ihb-extension-test-')
        self.root=Path(self.temp.name).resolve()
        self.old_ids=[f'{n:03d}-fixture' for n in range(1,41)]
        self.new_ids=[f'{n:03d}-fixture' for n in range(41,55)]
        self.base=self.root/'provenance/initial-40'
        manifest=[{'task_id':t,'pilot_candidate':True,'status':'validated','validation':{'release_eligible':True}} for t in self.old_ids]
        expanded=manifest+[{'task_id':t,'pilot_candidate':True,'validation':{'release_eligible':False}} for t in self.new_ids]
        protocol={'model':'gpt-oss:20b','max_requests':30,'max_input_tokens':200000,
            'target_tasks':40,'target_task_language_versions':120,'planned_runs':120,'pilot_status':'frozen'}
        images={kind:{'id':kind+'-fixed'} for kind in ('agent','relay','helper','grader')}
        reviews={t:{'reviewer':'AI self-review'} for t in self.old_ids}
        for relative,value in [('dataset/task_manifest.json',manifest),('dataset/translation_reviews.json',reviews),
            ('config/protocol.json',protocol),('config/images.json',images)]:atomic_json(self.base/relative,value)
        prompt=self.root/'tasks/001-fixture/prompts/en/prompt.txt';prompt.parent.mkdir(parents=True);prompt.write_bytes(b'Original prompt\n')
        previous={'task_ids':self.old_ids,'file_hashes':{'tasks/001-fixture/prompts/en/prompt.txt':hashlib.sha256(prompt.read_bytes()).hexdigest()},
            'study_id':'preserved-study','dataset_hash':'original-freeze','runtime_revision':5}
        atomic_json(self.base/'dataset/freeze.json',previous);atomic_json(self.root/'dataset/freeze.json',previous)
        protocol={**protocol,'target_tasks':54,'target_task_language_versions':162,'planned_runs':162,'pilot_status':'pending'}
        for relative,value in [('dataset/task_manifest.json',expanded),('dataset/translation_reviews.json',reviews),
            ('config/protocol.json',protocol),('config/images.json',images),
            ('dataset/pilot_plan.json',{'execution_task_ids':self.old_ids+self.new_ids,'planned_runs':162}),
            ('dataset/extension_selection.json',{'selected_task_ids':self.new_ids,'original_task_ids':self.old_ids})]:atomic_json(self.root/relative,value)
        runs=[];hashes={}
        (self.root/'results').mkdir()
        with closing(sqlite3.connect(self.root/'results/journal.sqlite3')) as db,db:
            db.execute('CREATE TABLE runs(id TEXT,status TEXT,result TEXT)')
            for n in range(120):
                row={'id':str(n),'status':'completed','result':'saved'};runs.append(row)
                db.execute('INSERT INTO runs VALUES(?,?,?)',tuple(row.values()))
                p=self.root/'results/runs'/str(n)/'run.json';atomic_json(p,row)
                hashes[str(n)]={'run_json_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        atomic_json(self.base/'runs.json',runs);atomic_json(self.base/'terminal_hashes.json',hashes)

    def tearDown(self):
        # Only this explicitly allocated temporary test directory is cleaned up.
        assert self.root==Path(self.temp.name).resolve()
        self.temp.cleanup()

    def edit(self,path,fn):
        p=self.root/path;data=json.loads(p.read_text(encoding='utf-8'));fn(data);atomic_json(p,data)

    def test_only_count_metadata_and_private_grader_may_change(self):
        self.edit('config/images.json',lambda d:d['grader'].update(id='extended-private-grader'))
        r=check_extension(self.root);self.assertTrue(r['passed']);self.assertEqual(r['original_attempts_unchanged'],120)

    def test_original_execution_order_cannot_change(self):
        self.edit('dataset/pilot_plan.json',lambda d:d['execution_task_ids'].reverse())
        with self.assertRaisesRegex(ValueError,'original execution order'):check_extension(self.root)

    def test_budget_change_rejected(self):
        self.edit('config/protocol.json',lambda d:d.update(max_requests=31))
        with self.assertRaisesRegex(ValueError,'budgets'):check_extension(self.root)

    def test_prompt_change_rejected(self):
        (self.root/'tasks/001-fixture/prompts/en/prompt.txt').write_bytes(b'Changed')
        with self.assertRaisesRegex(ValueError,'Original prompt'):check_extension(self.root)

    def test_translation_review_change_rejected(self):
        self.edit('dataset/translation_reviews.json',lambda d:d['001-fixture'].update(reviewer='different'))
        with self.assertRaisesRegex(ValueError,'translation review'):check_extension(self.root)

    def test_original_result_change_rejected(self):
        with closing(sqlite3.connect(self.root/'results/journal.sqlite3')) as db,db:db.execute("UPDATE runs SET status='planned' WHERE id='0'")
        with self.assertRaisesRegex(ValueError,'attempt records'):check_extension(self.root)

    def test_missing_translations_block_without_mutating_metadata(self):
        files=['dataset/freeze.json','dataset/task_manifest.json','dataset/pilot_plan.json']
        before={name:(self.root/name).read_bytes() for name in files}
        with patch('bench.readiness.ROOT',self.root),patch('bench.readiness.check_extension',lambda:check_extension(self.root)),patch('bench.readiness.readiness',return_value={'ready':False,'blocking_gates':['translations_and_review']}):
            with self.assertRaisesRegex(ValueError,'translations_and_review'):freeze(extend=True)
        self.assertEqual(before,{name:(self.root/name).read_bytes() for name in files})

    def test_duplicate_or_missing_execution_tasks_rejected(self):
        with self.assertRaises(ValueError):ordered_tasks([{'task_id':'a','pilot_candidate':True}],{'execution_task_ids':['a','a']})

    def test_append_freeze_keeps_study_id_and_existing_task_entries(self):
        with patch('bench.readiness.ROOT',self.root),patch('bench.readiness.check_extension',lambda:check_extension(self.root)),patch('bench.readiness.readiness',return_value={'ready':True}),patch('bench.readiness.frozen_files',return_value={'prepared':'new-hash'}):
            result=freeze(extend=True)
        self.assertEqual(result['study_id'],'preserved-study')
        self.assertEqual(result['task_ids'],self.old_ids+self.new_ids)
        self.assertEqual(result['task_count'],54);self.assertEqual(result['planned_runs'],162)
        self.assertEqual(result['runtime_revision'],6)
        self.assertTrue(check_extension(self.root)['passed'])

    def test_regular_freeze_cannot_silently_change_started_study(self):
        p=self.root/'dataset/freeze.json';before=p.read_bytes()
        with patch('bench.readiness.ROOT',self.root),patch('bench.readiness.frozen_files',return_value={'prepared':'new-hash'}):
            with self.assertRaisesRegex(ValueError,'extend-freeze'):freeze()
        self.assertEqual(before,p.read_bytes())

    def test_journal_appends_42_without_replaying_original_results(self):
        j=Journal(self.root/'results/append-test.sqlite3')
        try:
            j.plan(self.old_ids,'same-study')
            for row in j.runs():j.start(row['id']);j.finish(row['id'],'completed',{'saved_result':row['id']})
            before=j.runs();j.plan(self.old_ids+self.new_ids,'same-study');after=j.runs()
            self.assertEqual(after[:120],before);self.assertEqual(len(after),162)
            self.assertTrue(all(r['status']=='planned' for r in after[120:]))
            self.assertEqual([r['language'] for r in after[120:123]],['hi','hinglish','en'])
        finally:j.close()


if __name__=='__main__':unittest.main()
