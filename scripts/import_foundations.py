"""Idempotently add the curated learning layer to the local Neo4j graph."""
import json
from db import ROOT,query
data=json.loads((ROOT/'dist/foundations.json').read_text())
query('UNWIND $rows AS row MERGE (n:MathEntity {id:row.id}) SET n += row',{'rows':data['nodes']})
for kind in ['LEARNING_PREREQUISITE','SUGGESTED_BACKGROUND']:
 rows=[e for e in data['edges'] if e['type']==kind]
 query(f'UNWIND $rows AS row MATCH (a:MathEntity {{id:row.source}}),(b:MathEntity {{id:row.target}}) MERGE (a)-[r:{kind}]->(b) SET r.evidence=row.evidence',{'rows':rows})
print(query("MATCH (n:MathEntity {kind:'Concept'}) RETURN count(n)"))
