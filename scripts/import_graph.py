import json,re,gzip
from db import ROOT,query
query('CREATE CONSTRAINT math_entity_id IF NOT EXISTS FOR (n:MathEntity) REQUIRE n.id IS UNIQUE')
files=sorted((ROOT/'dist/graphs').glob('*.json.gz'))
catalogue=json.loads((ROOT/'dist/catalogue.json').read_text())
def ingest_nodes(nodes):
 for i in range(0,len(nodes),300):
  query('UNWIND $rows AS row MERGE (n:MathEntity {id:row.id}) SET n += row',{'rows':nodes[i:i+300]})
def ingest_edges(edges):
 groups={}
 for e in edges:groups.setdefault(e['type'],[]).append(e)
 for kind,rows in groups.items():
  assert re.fullmatch('[A-Z_]+',kind)
  for i in range(0,len(rows),500):
   query(f'UNWIND $rows AS row MATCH (a:MathEntity {{id:row.source}}),(b:MathEntity {{id:row.target}}) MERGE (a)-[r:{kind}]->(b) SET r.evidence=row.evidence',{'rows':rows[i:i+500]})
ingest_nodes(catalogue['nodes']);ingest_edges(catalogue['edges'])
for i,file in enumerate(files):
 data=json.loads(gzip.decompress(file.read_bytes()));ingest_nodes(data['nodes']);ingest_edges(data['edges'])
 if i%25==0:print(f'Imported {i+1}/{len(files)} families',flush=True)
print('Node count:',query('MATCH (n:MathEntity) RETURN count(n)')[0]['row'][0])
print('Edge count:',query('MATCH (:MathEntity)-[r]->(:MathEntity) RETURN count(r)')[0]['row'][0])

learning=ROOT/'dist/foundations.json'
if learning.exists():
 data=json.loads(learning.read_text());ingest_nodes(data['nodes']);ingest_edges(data['edges'])

reasoning=json.loads((ROOT/'dist/reasoning.json').read_text())
ingest_nodes(reasoning['nodes']);ingest_edges(reasoning['edges'])
