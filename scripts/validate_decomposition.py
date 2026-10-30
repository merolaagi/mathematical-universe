"""Check declared structure and visible boundaries, not truth of the mathematics."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'dist'
nodes={};edges=[]
for file in ['catalogue.json','foundations.json','reasoning.json','paths.json','decomposition.json']:
 d=json.loads((R/file).read_text());nodes.update((n['id'],n) for n in d['nodes']);edges.extend(d['edges'])
d=json.loads((R/'decomposition.json').read_text())
assert len({n['id'] for n in d['nodes']})==len(d['nodes'])
assert all(e['source'] in nodes and e['target'] in nodes for e in d['edges'])
adj={n['id']:[e['target'] for e in edges if e['source']==n['id'] and e['type']=='USES_RESULT'] for n in d['nodes']}
for n in d['nodes']:
 assert all(n.get(k) for k in ['assumptions','conclusion','justification','status','boundary'])
 assert bool(adj[n['id']])==(n['boundary']=='Derived step'),n['id']
def visit(id,path):
 assert id not in path,('Circular reasoning',path,id)
 if not adj[id]:return {id}
 return set().union(*(visit(child,path+[id]) for child in adj[id]))
for root in d['roots']:
 ends=visit(root['id'],[]);assert ends
 print(root['title'],':',len(ends),'explicit boundaries')
assert 'reason:deep:source-valuation' in visit('reason:deep:source-nonzero',[])
assert nodes['reason:deep:source-valuation']['status'].startswith('Unverified')
assert 'reason:deep:extreme-value' in visit('reason:deep:gronwall',[])
print('PASS: no hidden leaves, no dependency cycles, source uncertainty retained, shared calculus chain expanded.')
