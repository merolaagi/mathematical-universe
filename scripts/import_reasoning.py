"""Import curated contracts without asserting that their claims are verified."""
import json,re
from db import ROOT,query
data=json.loads((ROOT/'dist/reasoning.json').read_text())
query('UNWIND $rows AS row MERGE (n:MathEntity {id:row.id}) SET n += row',{'rows':data['nodes']})
for kind in sorted({e['type'] for e in data['edges']}):
 assert re.fullmatch('[A-Z_]+',kind)
 rows=[e for e in data['edges'] if e['type']==kind]
 query(f'UNWIND $rows AS row MATCH (a:MathEntity {{id:row.source}}),(b:MathEntity {{id:row.target}}) MERGE (a)-[r:{kind}]->(b) SET r.evidence=row.evidence',{'rows':rows})
print('Imported curated proof contracts and declared dependencies.')
