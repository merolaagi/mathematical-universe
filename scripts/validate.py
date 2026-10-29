import json,collections,gzip
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'dist'
catalogue=json.loads((root/'catalogue.json').read_text());nodes={};edges={}
for f in (root/'graphs').glob('*.json.gz'):
 g=json.loads(gzip.decompress(f.read_bytes()));nodes.update((n['id'],n) for n in g['nodes']);edges.update(((e['source'],e['target'],e['type']),e) for e in g['edges'])
for e in catalogue['edges']:edges[(e['source'],e['target'],e['type'])]=e
assert catalogue['meta']['counts']['Manuscript']==721
assert catalogue['meta']['counts']['Family']==373
assert len(nodes)==sum(catalogue['meta']['counts'].values())
assert len(edges)==catalogue['meta']['edges']
assert all(a in nodes and b in nodes for a,b,t in edges)
for n in nodes.values():
 assert n['url'].startswith('https://github.com/openai/math/blob/'+catalogue['meta']['commit']+'/')
for f in (root/'details').glob('*.json.gz'):
 assert all(k in nodes for k in json.loads(gzip.decompress(f.read_bytes())))
print(f'PASS: {len(nodes):,} nodes, {len(edges):,} edges; complete catalog, resolved endpoints, pinned provenance, valid detail IDs.')
