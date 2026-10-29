"""Local launcher. No account, API key, or remote application required."""
import argparse, json, os, shutil, socket, subprocess, sys, threading, webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--snapshot',action='store_true',help='Use bundled data without Docker/Neo4j')
 parser.add_argument('--no-browser',action='store_true')
 args=parser.parse_args()
 if sys.version_info<(3,10):raise SystemExit('Install Python 3.10 or newer: https://www.python.org/downloads/macos/')
 os.environ['PATH']=os.pathsep.join([str(Path.home()/'.docker/bin'),'/opt/homebrew/bin','/usr/local/bin',os.environ.get('PATH','')])
 with socket.socket() as sock:
  try:sock.bind(('127.0.0.1',18765))
  except OSError:raise SystemExit('Port 18765 is already in use. If the app is running, open http://127.0.0.1:18765. Otherwise stop the program using that port.')
 if not args.snapshot:
  if not shutil.which('docker'):raise SystemExit('Install Docker Desktop and open it first. Or use Start Snapshot.command without Neo4j.')
  ready=subprocess.run(['docker','info'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if ready.returncode:raise SystemExit('Open Docker Desktop, wait until it is running, and try again.')
  subprocess.run([sys.executable,str(ROOT/'scripts/start.py')],check=True)
  from db import query
  meta=json.loads((ROOT/'dist/catalogue.json').read_text())['meta']
  done=query('MATCH (s:UniverseSnapshot {id:$id}) RETURN s.complete',{'id':meta['commit']})
  if not done or not done[0]['row'][0]:
   print('First run: importing the full graph into Neo4j. This can take several minutes.',flush=True)
   subprocess.run([sys.executable,str(ROOT/'scripts/import_graph.py')],check=True)
   count=query('MATCH (n:MathEntity) RETURN count(n)')[0]['row'][0]
   relationships=query('MATCH (:MathEntity)-[r]->(:MathEntity) RETURN count(r)')[0]['row'][0]
   learning=json.loads((ROOT/'dist/foundations.json').read_text())
   reasoning=json.loads((ROOT/'dist/reasoning.json').read_text())
   added=sum(n['id'].startswith('reason:') for n in reasoning['nodes'])
   if count!=sum(meta['counts'].values())+len(learning['nodes'])+added or relationships!=meta['edges']+len(learning['edges'])+len(reasoning['edges']):raise SystemExit('Import counts do not match the bundled snapshot. See README.md.')
   query('MERGE (s:UniverseSnapshot {id:$id}) SET s.complete=true',{'id':meta['commit']})
  subprocess.run([sys.executable,str(ROOT/'scripts/import_foundations.py')],check=True)
  subprocess.run([sys.executable,str(ROOT/'scripts/import_reasoning.py')],check=True)
 else:print('Using bundled graph data; Neo4j is optional in this mode.',flush=True)
 from serve import Handler
 from http.server import ThreadingHTTPServer
 server=ThreadingHTTPServer(('127.0.0.1',18765),Handler)
 print('\nOpen http://127.0.0.1:18765 in Safari, Chrome, or Firefox.\nKeep this window open. Press Control-C to stop the web app.',flush=True)
 if not args.no_browser:threading.Timer(.5,lambda:webbrowser.open('http://127.0.0.1:18765')).start()
 try:server.serve_forever()
 except KeyboardInterrupt:print('\nWeb app stopped. Run Stop Database.command to stop Neo4j too.')
 finally:server.server_close()
if __name__=='__main__':
 try:main()
 except subprocess.CalledProcessError as e:raise SystemExit(f'Setup failed (exit {e.returncode}). Read the message above, fix the issue, then run again.')
