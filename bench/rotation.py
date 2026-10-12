"""Fail closed for ambiguous provider errors; never use 429 alone as quota evidence."""
from __future__ import annotations
import json
import re

def classify(status, body):
    if status in (200,201): return 'success'
    try:
        obj=json.loads(body) if isinstance(body,(str,bytes)) else body
    except (ValueError,TypeError): obj={}
    err=obj.get('error',{}) if isinstance(obj,dict) else {}
    code=err.get('code','') if isinstance(err,dict) else ''
    msg=err.get('message','') if isinstance(err,dict) else str(err)
    if code in {'insufficient_quota','quota_exceeded','usage_limit_exceeded'} and status in (402,403,429):
        return 'quota_exhausted'
    # Require an explicit allowance/usage exhaustion statement, not a generic rate limit.
    quota = re.search(r'(?:daily|weekly|monthly|free|account|plan) (?:usage|token|credit|quota|allowance)(?: limit)? (?:has been |is )?(?:exhausted|exceeded|reached)',msg,re.I)
    quota = quota or re.search(r'(?:exceeded|reached|exhausted) (?:your |the )?(?:daily|weekly|monthly|free|account|plan) (?:usage|token|credit|quota|allowance)(?: limit)?',msg,re.I)
    quota = quota or re.search(r'(?:usage limit|quota) (?:has been |is )?(?:exhausted|exceeded|reached)',msg,re.I)
    if status in (402,403,429) and quota: return 'quota_exhausted'
    if status==429: return 'rate_limited'
    if status in (408,425,500,502,503,504): return 'transient'
    if status in (401,403): return 'authentication_or_permission'
    return 'provider_error'
