import json,sys,urllib.parse,urllib.request
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from db import ROOT,query
sys.path.insert(0,str(ROOT))
LOCAL_HOSTS={'127.0.0.1','localhost','[::1]'}
LOCAL_ORIGINS={'http://127.0.0.1:18765','http://localhost:18765'}
TUNNEL_HEADERS=('CF-Connecting-IP','CF-Ray','CF-Visitor','CDN-Loop','X-Forwarded-For','X-Forwarded-Host','Forwarded')
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'dist'),**kw)
 def end_headers(self):
  if self.path.startswith('/api/settings'):self.send_header('Cache-Control','no-store')
  super().end_headers()
 def local_admin(self):
  """Settings are only for someone sitting at this Mac: the tunnel also connects from 127.0.0.1,
  so require a local Host header and no proxy/Cloudflare headers as well."""
  host=self.headers.get('Host','').rsplit(':',1)[0].lower()
  if host not in LOCAL_HOSTS or self.client_address[0] not in ('127.0.0.1','::1'):return False
  return not any(self.headers.get(h) for h in TUNNEL_HEADERS)
 def send_json(self,code,data):
  body=json.dumps(data).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def settings_view(self):
  from swarm import settings
  from swarm.llm import Ollama,Claude
  from swarm.agents import manim_tools
  cfg=settings.load();models=[]
  try:
   with urllib.request.urlopen(cfg['OLLAMA_HOST'].rstrip('/')+'/api/tags',timeout=3) as r:models=sorted(m['name'] for m in json.load(r).get('models',[]))
  except Exception:pass
  o=Ollama().check();c=Claude().check();cmd,latex=manim_tools()
  return {'local':True,'file':str(settings.FILE),'settings':settings.public(),'ollama_models':models,
          'status':{'ollama':{'ok':o[0],'message':o[1]},'claude':{'ok':c[0],'message':c[1]},
                    'manim':{'ok':bool(cmd),'message':(cmd[0]+(' · LaTeX found' if latex else ' · no LaTeX')) if cmd else 'Manim not installed; videos are skipped'}}}
 def do_GET(self):
  path=urllib.parse.urlparse(self.path)
  if path.path=='/api/settings':
   if not self.local_admin():self.send_error(404);return
   self.send_json(200,self.settings_view());return
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
 def do_POST(self):
  path=urllib.parse.urlparse(self.path).path
  if path not in ('/api/settings','/api/settings/test') or not self.local_admin():self.send_error(404);return
  if self.headers.get('Origin') not in LOCAL_ORIGINS or 'application/json' not in self.headers.get('Content-Type',''):self.send_json(403,{'error':'Settings can only be changed from this Mac at http://127.0.0.1:18765'});return
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length>20000:raise ValueError('request too large')
   body=json.loads(self.rfile.read(length) or b'{}')
  except Exception as e:self.send_json(400,{'error':f'bad request: {e}'});return
  from swarm import settings
  if path=='/api/settings':
   changes=body.get('changes')
   if not isinstance(changes,dict):self.send_json(400,{'error':'send {"changes": {...}}'});return
   try:settings.save({str(k):str(v) for k,v in changes.items()})
   except ValueError as e:self.send_json(400,{'error':str(e)});return
   self.send_json(200,self.settings_view());return
  from swarm.llm import Ollama,Claude,LLMError
  target=body.get('target')
  try:
   if target=='claude':
    c=Claude();ok,msg=c.check()
    if ok:reply=c.complete('Reply with the single word OK.','Test.',json_mode=False,max_tokens=5);msg=f'Claude answered ({c.model}): {reply.strip()[:20]}'
   elif target=='ollama':
    ok,msg=Ollama().check()
   else:self.send_json(400,{'error':'target must be claude or ollama'});return
  except LLMError as e:ok,msg=False,str(e)[:300]
  self.send_json(200,{'ok':ok,'message':msg})
 def log_message(self,fmt,*args):
  if '/api/settings' in str(args[:1]):return
  super().log_message(fmt,*args)
if __name__=='__main__':
 print('Mathematical Universe: http://127.0.0.1:18765',flush=True)
 ThreadingHTTPServer(('127.0.0.1',18765),Handler).serve_forever()
