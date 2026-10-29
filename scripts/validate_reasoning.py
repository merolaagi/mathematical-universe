"""Integrity checks, deliberately not a mathematical proof checker."""
import json,gzip
from pathlib import Path
r=Path(__file__).resolve().parents[1]/'dist'
d=json.loads((r/'reasoning.json').read_text());source=json.loads(gzip.decompress((r/'graphs/f005.json.gz').read_bytes()))
ids={n['id'] for f in ['catalogue.json','foundations.json','reasoning.json'] for n in json.loads((r/f).read_text())['nodes']}
assert len({n['id'] for n in d['nodes']})==len(d['nodes'])
assert all(e['source'] in ids and e['target'] in ids for e in d['edges'])
assert len({(e['source'],e['target'],e['type']) for e in d['edges']})==len(d['edges'])
sourceids={n['id'] for n in source['nodes']}
for n in d['nodes']:
 if n['id'].startswith('reason:'):
  assert n['assumptions'] and n['conclusion'] and n['justification'] and n['status']
 else: assert n['id'] in sourceids
adj={n['id']:[e['target'] for e in d['edges'] if e['source']==n['id'] and e['type']=='USES_RESULT'] for n in d['nodes']}
def visit(id,path):
 assert id not in path, 'Circular declared argument'
 for dep in adj[id]:visit(dep,path+[id])
for id in adj:visit(id,[])
assert 'reason:nonzero' in adj['reason:lower']
assert 'reason:nonzero' in adj['reason:upper']
assert len([e for e in d['edges'] if e['source']=='reason:sum' and e['type']=='ALTERNATIVE_PROOF'])==2
print('PASS: contract fields, source endpoints, alternative routes, nonvanishing requirements, and acyclic declared dependencies.')
