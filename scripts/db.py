import json,base64,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def query(statement,parameters=None):
 password=(ROOT/'local/.env').read_text().strip().split('=',1)[1]
 auth=base64.b64encode(('neo4j:'+password).encode()).decode()
 req=urllib.request.Request('http://127.0.0.1:18474/db/neo4j/tx/commit',data=json.dumps({'statements':[{'statement':statement,'parameters':parameters or {}}]}).encode(),headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'})
 result=json.load(urllib.request.urlopen(req,timeout=180))
 if result.get('errors'):raise RuntimeError(str(result['errors']))
 return result['results'][0]['data']
