import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'dist'
nodes={};edges=[]
for file in ['catalogue.json','foundations.json','reasoning.json','paths.json']:
 d=json.loads((R/file).read_text());nodes.update((n['id'],n) for n in d['nodes']);edges.extend(d['edges'])
p=json.loads((R/'paths.json').read_text())
assert len({n['id'] for n in p['nodes']})==len(p['nodes'])
assert all(e['source'] in nodes and e['target'] in nodes for e in p['edges'])
assert len({(e['source'],e['target'],e['type']) for e in p['edges']})==len(p['edges'])
for n in p['nodes']:assert all(n.get(k) for k in ['level','course','detail','proof'])
def walk(id,path):
 assert id not in path,('Cycle',path,id)
 n=nodes[id]
 if n.get('level')=='College' or (n['kind']=='Concept' and not n.get('level')):return [id]
 children=[e['target'] for e in edges if e['source']==id and e['type']=='LEARNING_PREREQUISITE']
 assert children,('Unfinished advanced branch',id)
 return [leaf for child in children for leaf in walk(child,path+[id])]
for route in p['paths']:
 leaves=walk(route['start'],[]);assert leaves
 print(route['family'],': every branch reaches a college foundation;',len(set(leaves)),'distinct endpoints')
