import json
import re
import sys
sys.path.append('.')
from app import app


def normalize_url(url):
    if not url:
        return ''
    url = url.lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    url = url.split('#')[0]
    url = url.split('?')[0]
    return url


def is_duplicate(result1, result2):
    url1 = normalize_url(result1.get('link'))
    url2 = normalize_url(result2.get('link'))
    if url1 and url1 == url2:
        return True
    title1 = (result1.get('title') or '').strip().lower()
    title2 = (result2.get('title') or '').strip().lower()
    if title1 and title1 == title2:
        domain1 = url1.split('/')[0] if url1 else ''
        domain2 = url2.split('/')[0] if url2 else ''
        if domain1 and domain1 == domain2:
            return True
    return False


source_priority = {
    'Universal Search': 3,
    'Social Searcher Style': 2,
    'Google CSE': 1,
    'Unknown': 0
}


def add_result(combined, result, source, priority=0):
    if not result.get('source'):
        result['source'] = source
    priority = priority or source_priority.get(source, 0)
    for idx, existing in enumerate(combined):
        if is_duplicate(existing, result):
            existing_priority = existing.get('mergePriority', 0)
            existing_source_priority = source_priority.get(existing.get('source'), 0)
            if priority > existing_priority or (priority == existing_priority and priority > existing_source_priority):
                result['mergePriority'] = priority
                combined[idx] = result
                return True, True, True
            return False, True, False
    result['mergePriority'] = priority
    combined.append(result)
    return True, False, False


with app.test_client() as client:
    uni_resp = client.post('/api/universal-search', json={'name': 'MARGUTIN'})
    uni_data = uni_resp.get_json()
    universal_results = [
        {
            'title': item.get('title') or 'No Title',
            'link': item.get('link') or '#',
            'snippet': item.get('snippet') or '',
            'source': 'Universal Search'
        }
        for item in uni_data['data'].get('organic_results', [])
    ]

    social_resp = client.post('/api/social-media-search', json={'name': 'MARGUTIN', 'type': 'web'})
    social_data = social_resp.get_json()
    social_results = social_data['data'].get('web', [])
    for item in social_results:
        if not item.get('source'):
            item['source'] = 'Google CSE'

combined = []
added_uni = skipped_uni = 0
for res in universal_results:
    added, dup, _ = add_result(combined, res, 'Universal Search', 3)
    if added and not dup:
        added_uni += 1
    elif dup:
        skipped_uni += 1

added_google = skipped_google = replaced_google = 0
for res in social_results:
    added, dup, replaced = add_result(combined, res, res.get('source', 'Google CSE'), 1)
    if added and not dup:
        added_google += 1
    elif dup:
        skipped_google += 1
        if replaced:
            replaced_google += 1

print('Universal results total:', len(universal_results))
print('Added universal:', added_uni, 'Skipped universal duplicates:', skipped_uni)
print('Google results total:', len(social_results))
print('Added google:', added_google, 'Duplicates:', skipped_google, 'Replaced:', replaced_google)
print('Combined total:', len(combined))
source_counts = {}
for r in combined:
    source_counts[r.get('source')] = source_counts.get(r.get('source'), 0) + 1
print('Source breakdown:', source_counts)
print('Sample combined first 5:', json.dumps([{k: v for k, v in r.items() if k in ('title', 'link', 'source')} for r in combined[:5]], indent=2))
