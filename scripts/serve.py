import json,urllib.parse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from db import ROOT,query
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'dist'),**kw)
 def do_GET(self):
  path=urllib.parse.urlparse(self.path)
  if path.path.startswith('/api/'):
   try:
    if path.path=='/api/health':data={'mode':'Neo4j','nodes':query('MATCH (n:MathEntity) RETURN count(n)')[0]['row'][0]}
    elif path.path=='/api/neighbors':
     id=urllib.parse.parse_qs(path.query).get('id',[''])[0]
     rows=query('MATCH (n:MathEntity {id:$id})-[r]-(m:MathEntity) RETURN properties(m), startNode(r).id, endNode(r).id, type(r), r.evidence LIMIT 1000',{'id':id})
     data={'nodes':[r['row'][0] for r in rows],'edges':[dict(source=r['row'][1],target=r['row'][2],type=r['row'][3],evidence=r['row'][4] or '') for r in rows]}
    else:self.send_error(404);return
    self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(data).encode())
   except Exception:
    self.send_response(503);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"error":"Neo4j unavailable. Start the local database."}')
  else:super().do_GET()
if __name__=='__main__':
 print('Mathematical Universe: http://127.0.0.1:18765',flush=True)
 ThreadingHTTPServer(('127.0.0.1',18765),Handler).serve_forever()
