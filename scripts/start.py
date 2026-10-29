import secrets,os,subprocess,time
from db import ROOT,query
env=ROOT/'local/.env';env.parent.mkdir(exist_ok=True)
if not env.exists():
 fd=os.open(env,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as f:f.write('NEO4J_PASSWORD='+secrets.token_urlsafe(32)+'\n')
subprocess.run(['docker','compose','--env-file',str(env),'-p','mathematical-universe-standalone','up','-d'],cwd=ROOT,check=True)
for _ in range(90):
 try:query('RETURN 1');break
 except Exception:time.sleep(2)
else:raise SystemExit('Neo4j did not become ready; inspect docker compose logs.')
print('Neo4j ready on localhost:18474. Credentials stored only in local/.env.')
