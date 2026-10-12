"""Static translation checks only. Never import or execute benchmark tasks."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LANGUAGES=('en','hi','hinglish')
OUTPUT_CONTRACT='\n\nBenchmark output contract: Write prose deliverables in English. Preserve the specified filenames, commands, identifiers, JSON keys, enum values, headings, and exact output strings.\n'
COMMON_CLARIFICATIONS={
    '048-release-note-changelog':'\n\nBenchmark clarification: Produce all five listed output files: out/CHANGELOG.md, out/release_summary.json, out/upgrade_notes.md, out/release_decisions.json, and out/release_audit.json.\n',
    '067-canary-release-check':'\n\nBenchmark clarification: Produce both listed output files: out/canary_decision.json and out/metric_evidence.csv.\n',
    '068-product-launch-ops':'\n\nBenchmark clarification: audience.json contains four segments. Mention all listed segments, including the unavailable segment only to explain its exclusion.\n',
}

def digest(data): return hashlib.sha256(data).hexdigest()

def protected(text):
    return {
        'placeholders': Counter(re.findall(r'\$[A-Z][A-Z0-9_]*',text)),
        'backtick_literals': Counter(re.findall(r'`([^`\n]+)`',text)),
        'fenced_blocks': Counter(re.findall(r'```[^\n]*\n.*?```',text,re.S)),
        'double_quoted_literals': Counter(re.findall(r'"[^"\n]*"|“[^”\n]*”',text)),
        'numbers': Counter(re.findall(r'(?<![\w])\d+(?:[.:/-]\d+)*(?![\w])',text)),
    }

def check_translations():
    manifest=json.loads((ROOT/'dataset/task_manifest.json').read_text(encoding='utf-8'))
    review_path=ROOT/'dataset/translation_reviews.json'
    reviews=json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else {}
    entries=[]; errors=[]
    for task in manifest:
        if not task['pilot_candidate']: continue
        task_id=task['task_id']
        for name in task['source_prompt_files']:
            source=ROOT/'vendor/harnessbench/tasks'/task_id/name
            original=source.read_text(encoding='utf-8')
            original_checks=protected(original)
            row={'task_id':task_id,'prompt_file':name,'source_sha256':digest(source.read_bytes()),'languages':{}}
            for lang in LANGUAGES:
                path=ROOT/'tasks'/task_id/'prompts'/lang/name
                errs=[]
                if not path.is_file():
                    errs.append('missing_prompt')
                else:
                    data=path.read_bytes()
                    try: text=data.decode('utf-8')
                    except UnicodeDecodeError: text=''; errs.append('invalid_utf8')
                    suffix=COMMON_CLARIFICATIONS.get(task_id,'')+OUTPUT_CONTRACT
                    if not text.endswith(suffix): errs.append('common_output_contract_missing_or_changed')
                    body=text[:-len(suffix)] if text.endswith(suffix) else text
                    if lang=='en' and body!=original: errs.append('english_source_body_changed')
                    if lang!='en':
                        if body==original: errs.append('untranslated_source_copy')
                        for kind, values in original_checks.items():
                            other=protected(body)[kind]
                            if other!=values:
                                errs.append({'protected_literal_mismatch':kind,
                                    'missing':list((values-other).elements()),'extra':list((other-values).elements())})
                        if lang=='hi' and not re.search(r'[\u0900-\u097f]',body): errs.append('no_devanagari')
                        if lang=='hinglish' and re.search(r'[\u0900-\u097f]',body): errs.append('hinglish_must_use_roman_script')
                    row['languages'][lang]={'sha256':digest(data),'errors':errs}
                if lang not in row['languages']: row['languages'][lang]={'sha256':None,'errors':errs}
                if errs: errors.append({'task_id':task_id,'prompt_file':name,'language':lang,'errors':errs})
            entries.append(row)
        review=reviews.get(task_id,{})
        criteria=['requirements','negations','numbers_and_dates','round_order','no_new_hints',
                  'technical_literals','hindi_naturalness','hinglish_naturalness','backtranslation_comparison']
        if review.get('reviewer')!='AI self-review' or review.get('independent_human_review') is not False:
            errors.append({'task_id':task_id,'errors':['review_provenance_missing']})
        if any(review.get('checks',{}).get(x) is not True for x in criteria):
            errors.append({'task_id':task_id,'errors':['semantic_review_incomplete']})
    result={'scope':'Static prompt literal/provenance checks; semantic correctness is self-reviewed, not independently verified.',
            'task_count':sum(t['pilot_candidate'] for t in manifest),'unique_prompt_count':len(entries),
            'expected_prompt_files':len(entries)*3,'passed':not errors,'errors':errors,'prompts':entries,
            'oracle_validation_completed':False,'pilot_authorized_by_this_check':False}
    out=ROOT/'reports/translation_check.json'; out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    result=check_translations()
    print(json.dumps({k:v for k,v in result.items() if k!='prompts'},indent=2,ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
