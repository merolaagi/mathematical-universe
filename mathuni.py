#!/usr/bin/env python3
"""Mathematical Universe command-line entry point.

  python3 mathuni.py doctor            check this machine and the install
  python3 mathuni.py start             start the app (Neo4j if Docker is running, else snapshot)
  python3 mathuni.py start --snapshot  bundled data only, no Docker
  python3 mathuni.py start --neo4j     require Neo4j (fails if Docker is not running)
  python3 mathuni.py stop              stop the web app on port 18765 (and --db for Neo4j)
  python3 mathuni.py explain ...       run the explainer swarm (python3 mathuni.py explain -h)
  python3 mathuni.py version
"""
import argparse, json, os, shutil, socket, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = (ROOT / 'VERSION').read_text().strip() if (ROOT / 'VERSION').exists() else 'dev'
PORT = 18765
PROJECT = 'mathematical-universe-standalone'
LABEL = 'com.mathuni.web'
REQUIRED = ['dist/index.html', 'dist/app.js', 'dist/catalogue.json', 'dist/foundations.json',
            'dist/reasoning.json', 'dist/paths.json', 'dist/decomposition.json', 'dist/version.json',
            'scripts/launch.py', 'scripts/serve.py', 'scripts/db.py', 'scripts/start.py',
            'scripts/import_graph.py', 'compose.yaml']

os.environ['PATH'] = os.pathsep.join([str(Path.home() / '.docker/bin'), '/opt/homebrew/bin',
                                      '/usr/local/bin', os.environ.get('PATH', '')])


def port_free(port=PORT):
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def running_build(port=PORT):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/version.json', timeout=2) as r:
            return json.load(r).get('build')
    except Exception:
        return None


def local_build():
    try:
        return json.loads((ROOT / 'dist/version.json').read_text()).get('build')
    except Exception:
        return None


def docker_state():
    if not shutil.which('docker'):
        return 'missing'
    ok = subprocess.run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    return 'running' if ok else 'stopped'


def launch_agent_loaded():
    if sys.platform != 'darwin' or not shutil.which('launchctl'):
        return False
    r = subprocess.run(['launchctl', 'print', f'gui/{os.getuid()}/{LABEL}'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def cmd_doctor(_):
    fatal = 0
    def line(status, msg):
        print(f'  [{status}] {msg}')
    print(f'Mathematical Universe {VERSION} — doctor')
    print(f'  install: {ROOT}')
    v = sys.version_info
    if v >= (3, 10):
        line(' OK ', f'Python {v.major}.{v.minor}.{v.micro}')
    else:
        line('FAIL', f'Python {v.major}.{v.minor} found; 3.10+ required: https://www.python.org/downloads/macos/')
        fatal += 1
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        line('FAIL', 'missing files: ' + ', '.join(missing))
        fatal += 1
    else:
        graphs = len(list((ROOT / 'dist/graphs').glob('*.json.gz'))) if (ROOT / 'dist/graphs').exists() else 0
        line(' OK ', f'bundled data present ({graphs} graph files, build {local_build()})')
    try:
        meta = json.loads((ROOT / 'dist/catalogue.json').read_text())['meta']
        line(' OK ', f"catalogue readable (source commit {meta.get('commit', '?')[:12]})")
    except Exception as e:
        line('FAIL', f'catalogue.json unreadable: {e}')
        fatal += 1
    d = docker_state()
    if d == 'running':
        line(' OK ', 'Docker running — start will use Neo4j mode')
    elif d == 'stopped':
        line('WARN', 'Docker installed but not running — start will use snapshot mode (open Docker Desktop for Neo4j)')
    else:
        line('WARN', 'Docker not installed — start will use snapshot mode')
    env = ROOT / 'local/.env'
    line(' OK ' if env.exists() else 'INFO', 'Neo4j password file local/.env ' +
         ('present' if env.exists() else 'will be created on first Neo4j start'))
    if port_free():
        line(' OK ', f'port {PORT} free')
    else:
        b = running_build()
        if b and b == local_build():
            line('INFO', f'port {PORT} already serving this build ({b}) — start will report it as running')
        elif b:
            line('WARN', f'port {PORT} serving another Mathematical Universe build ({b}); start will replace it')
        else:
            line('WARN', f'port {PORT} in use by another program; run: lsof -nP -iTCP:{PORT} -sTCP:LISTEN')
    if launch_agent_loaded():
        line('INFO', f'LaunchAgent {LABEL} is loaded (it may restart an older copy on port {PORT})')
    try:
        sys.path.insert(0, str(ROOT))
        from swarm.llm import Ollama, Claude
        from swarm.agents import manim_tools, OUT
        ok, msg = Ollama().check()
        line(' OK ' if ok else 'INFO', 'explainer swarm, local model: ' + msg)
        ok, msg = Claude().check()
        line(' OK ' if ok else 'INFO', 'explainer swarm, Claude (optional): ' + msg)
        cmd, latex = manim_tools()
        line(' OK ' if cmd else 'INFO', 'Manim videos: ' + (cmd[0] if cmd else 'not installed (videos skipped)') +
             ('' if not cmd else (', LaTeX found' if latex else ', no LaTeX (Text formulas)')))
        count = len(list(OUT.glob('f*.json'))) if OUT.exists() else 0
        line('INFO', f'explainers generated: {count} of 373')
    except Exception as e:
        line('INFO', f'explainer swarm not checked: {e}')
    print('Doctor: ' + ('FAILED' if fatal else 'ready') + '.')
    return 1 if fatal else 0


def stop_web():
    if launch_agent_loaded():
        subprocess.run(['launchctl', 'bootout', f'gui/{os.getuid()}/{LABEL}'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f'Unloaded LaunchAgent {LABEL}.')
    if shutil.which('lsof'):
        pids = subprocess.run(['lsof', '-t', '-nP', f'-iTCP:{PORT}', '-sTCP:LISTEN'],
                              capture_output=True, text=True).stdout.split()
        for pid in pids:
            subprocess.run(['kill', pid])
        if pids:
            print(f'Stopped process(es) on port {PORT}: {" ".join(pids)}')
    import time
    for _ in range(20):
        if port_free():
            return True
        time.sleep(0.25)
    return port_free()


def cmd_stop(args):
    ok = stop_web()
    if args.db and shutil.which('docker') and (ROOT / 'local/.env').exists():
        subprocess.run(['docker', 'compose', '--env-file', str(ROOT / 'local/.env'), '-p', PROJECT, 'down'], cwd=ROOT)
    print('Stopped.' if ok else f'Port {PORT} is still in use.')
    return 0 if ok else 1


def cmd_start(args):
    if not port_free():
        b = running_build()
        if b and b == local_build() and not args.replace:
            print(f'Mathematical Universe (build {b}) is already running: http://127.0.0.1:{PORT}')
            return 0
        if b or args.replace:
            print(f'Replacing the Mathematical Universe server on port {PORT} (build {b}) with {ROOT.name} {VERSION}.')
            if not stop_web():
                print(f'Could not free port {PORT}. Check: lsof -nP -iTCP:{PORT} -sTCP:LISTEN')
                return 1
        else:
            print(f'Port {PORT} is used by another program. Check: lsof -nP -iTCP:{PORT} -sTCP:LISTEN')
            return 1
    launch = [sys.executable, str(ROOT / 'scripts/launch.py')]
    if args.no_browser:
        launch.append('--no-browser')
    if args.snapshot:
        mode = 'snapshot'
    elif args.neo4j:
        mode = 'neo4j'
    else:
        mode = 'neo4j' if docker_state() == 'running' else 'snapshot'
        if mode == 'snapshot':
            print('Docker is not running; starting in snapshot mode (bundled data). Open Docker Desktop and rerun for Neo4j.')
    if mode == 'snapshot':
        launch.append('--snapshot')
    print(f'Starting Mathematical Universe {VERSION} ({mode} mode) from {ROOT}')
    try:
        return subprocess.call(launch, cwd=ROOT)
    except KeyboardInterrupt:
        return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'explain':
        sys.path.insert(0, str(ROOT))
        from swarm.run import main as explain
        return explain(sys.argv[2:])
    p = argparse.ArgumentParser(prog='mathuni.py', description='Mathematical Universe')
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('doctor', help='check this machine and the install')
    s = sub.add_parser('start', help='start the web app on http://127.0.0.1:18765')
    g = s.add_mutually_exclusive_group()
    g.add_argument('--snapshot', action='store_true', help='bundled data only, no Docker/Neo4j')
    g.add_argument('--neo4j', action='store_true', help='require Neo4j')
    s.add_argument('--no-browser', action='store_true')
    s.add_argument('--replace', action='store_true', help=f'stop whatever is on port {PORT} first')
    t = sub.add_parser('stop', help=f'stop the web app on port {PORT}')
    t.add_argument('--db', action='store_true', help='also stop the Neo4j container (data is kept)')
    sub.add_parser('version')
    args = p.parse_args()
    if args.cmd == 'doctor':
        return cmd_doctor(args)
    if args.cmd == 'start':
        return cmd_start(args)
    if args.cmd == 'stop':
        return cmd_stop(args)
    if args.cmd == 'version':
        print(VERSION)
        return 0
    p.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
