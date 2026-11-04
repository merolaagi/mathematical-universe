"""Run the explainer swarm over mathuni families.

  python3 mathuni.py explain --families f005                 one family
  python3 mathuni.py explain --families f001-f050            a range
  python3 mathuni.py explain --families all                  everything (resumes; skips finished)
  python3 mathuni.py explain --estimate 2                    time 2 families, project the full run
  python3 mathuni.py explain --backend claude --families f005
  python3 mathuni.py explain --escalate claude               redo low-scoring local drafts with Claude
  python3 mathuni.py explain --rescore-below 6 --backend claude   redo existing low scorers
"""
import argparse, json, os, sys, threading, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from . import SCHEMA
from .llm import make, LLMError
from .agents import OUT, ROOT, explain_family, family_ids, load_concepts, manim_tools

LOG = ROOT / 'local' / 'swarm.log'
FAILS = ROOT / 'local' / 'swarm-failures.json'
_lock = threading.Lock()


def log(msg):
    line = time.strftime('%H:%M:%S ') + msg
    with _lock:
        print(line, flush=True)
        LOG.parent.mkdir(exist_ok=True)
        with open(LOG, 'a') as f:
            f.write(line + '\n')


def select(spec, all_ids):
    if spec in (None, '', 'all'):
        return all_ids
    chosen = []
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-', 1)
            chosen += [i for i in all_ids if a <= i <= b]
        elif part in all_ids:
            chosen.append(part)
        else:
            raise SystemExit(f'unknown family {part}')
    return sorted(set(chosen))


def write_index(out):
    index = {}
    for p in sorted(out.glob('f*.json')):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        index[d['id']] = {'headline': d['untangled'].get('headline', ''), 'score': d['critic']['score'],
                          'model': d['model'], 'video': bool(d.get('video')), 'difficulty': d['untangled'].get('difficulty', '')}
    (out / 'index.json').write_text(json.dumps({'schema': SCHEMA, 'updated': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                                'families': index}, indent=0))
    return index


def fmt(sec):
    sec = int(sec)
    return f'{sec // 3600}h{sec % 3600 // 60:02d}m' if sec >= 3600 else f'{sec // 60}m{sec % 60:02d}s'


def main(argv=None):
    p = argparse.ArgumentParser(prog='mathuni.py explain', description='Explainer swarm')
    p.add_argument('--families', default='all')
    p.add_argument('--backend', choices=['ollama', 'claude', 'mock'], help='default: SWARM_BACKEND setting')
    p.add_argument('--model', help='override the model name for the backend')
    p.add_argument('--escalate', choices=['claude', 'none'], help='redo drafts scoring below --min-score (default: SWARM_ESCALATE setting)')
    p.add_argument('--min-score', type=float, help='default: SWARM_MIN_SCORE setting')
    p.add_argument('--rescore-below', type=float, help='only redo existing explainers scoring below this')
    p.add_argument('--videos', dest='videos', action='store_true', default=None)
    p.add_argument('--no-videos', dest='videos', action='store_false')
    p.add_argument('--force', action='store_true', help='regenerate even if an explainer exists')
    p.add_argument('--workers', type=int, help='parallel families (default 1 for ollama, 4 for claude)')
    p.add_argument('--estimate', type=int, metavar='N', help='time N families into local/estimate and project the full run')
    p.add_argument('--check', action='store_true', help='only check backends and tools')
    a = p.parse_args(argv)
    from .settings import load as load_settings
    cfg = load_settings()
    a.backend = a.backend or cfg['SWARM_BACKEND']
    a.escalate = a.escalate or cfg['SWARM_ESCALATE']
    a.escalate = None if a.escalate in (None, '', 'none') or a.escalate == a.backend else a.escalate
    a.min_score = a.min_score if a.min_score is not None else float(cfg['SWARM_MIN_SCORE'])
    if a.videos is None and cfg['SWARM_VIDEOS'] in ('on', 'off'):
        a.videos = cfg['SWARM_VIDEOS'] == 'on'
    if not a.workers and int(float(cfg['SWARM_WORKERS'] or 0)):
        a.workers = int(float(cfg['SWARM_WORKERS']))
    print(f'Settings: backend {a.backend}, escalate {a.escalate or "none"}, min score {a.min_score:g}, '
          f'videos {"auto" if a.videos is None else ("on" if a.videos else "off")} (change with the app\'s Settings panel '
          'or python3 mathuni.py settings)')

    llm = make(a.backend, a.model)
    ok, msg = llm.check()
    print(('OK   ' if ok else 'FAIL ') + msg)
    esc = None
    if a.escalate:
        esc = make(a.escalate)
        eok, emsg = esc.check()
        print(('OK   ' if eok else 'FAIL ') + 'escalation: ' + emsg)
        if not eok:
            esc = None
    cmd, latex = manim_tools()
    print(('OK   manim ' + cmd[0]) if cmd else 'INFO manim not found: videos will be skipped (see README "Explainer swarm")')
    print(('OK   ' if latex else 'INFO ') + ('LaTeX found: animations may use MathTex' if latex else 'LaTeX not found: animations use plain Text formulas'))
    if a.check or not ok:
        return 0 if ok else 1
    videos = bool(cmd) if a.videos is None else (a.videos and bool(cmd))

    concepts = load_concepts()
    all_ids = family_ids()
    out = OUT
    if a.estimate:
        out = ROOT / 'local' / 'estimate'
        ids = select(a.families, all_ids)[:a.estimate] if a.families != 'all' else ['f005', 'f107', 'f362', 'f014'][:a.estimate]
        a.force = True
    else:
        ids = select(a.families, all_ids)
    out.mkdir(parents=True, exist_ok=True)
    if a.estimate:
        for old in out.glob('f*.json'):
            old.unlink()

    todo = []
    for fid in ids:
        path = out / f'{fid}.json'
        if path.exists() and not a.force:
            try:
                d = json.loads(path.read_text())
            except Exception:
                d = None
            if d and d.get('schema') == SCHEMA:
                if a.rescore_below is None or d['critic']['score'] >= a.rescore_below:
                    continue
        elif a.rescore_below is not None and not path.exists():
            continue
        todo.append(fid)
    workers = a.workers or (1 if a.backend == 'ollama' else 4)
    log(f'swarm start: {len(todo)} of {len(ids)} families to do, backend {llm.label()}, videos {"on" if videos else "off"}, workers {workers}')
    fails = json.loads(FAILS.read_text()) if FAILS.exists() and not a.estimate else {}
    t0, done, scores, durations = time.time(), 0, [], []

    def one(fid):
        start = time.time()
        result = explain_family(fid, llm, concepts, videos=videos, min_score=a.min_score, log=log, out=out)
        if esc and result['critic']['score'] < a.min_score:
            log(f'  {fid} scored {result["critic"]["score"]}; escalating to {esc.label()}')
            try:
                better = explain_family(fid, esc, concepts, videos=videos and not result.get('video'), min_score=a.min_score,
                                        log=log, out=out)
                if not better.get('video') and result.get('video'):
                    better['video'] = result['video']
                if better['critic']['score'] >= result['critic']['score']:
                    result = better
            except LLMError as e:
                log(f'  {fid} escalation failed, keeping the local draft: {str(e)[:160]}')
        tmp = out / f'{fid}.json.tmp'
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=1))
        os.replace(tmp, out / f'{fid}.json')
        return result, time.time() - start

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, fid): fid for fid in todo}
        try:
            for fut in as_completed(futures):
                fid = futures[fut]
                done += 1
                try:
                    result, sec = fut.result()
                    durations.append(sec)
                    scores.append(result['critic']['score'])
                    fails.pop(fid, None)
                    status = f'score {result["critic"]["score"]}' + (', video' if result.get('video') else '')
                except Exception as e:
                    fails[fid] = f'{type(e).__name__}: {e}'
                    status = f'FAILED {type(e).__name__}: {str(e)[:160]}'
                    if not isinstance(e, LLMError):
                        log(traceback.format_exc().strip().splitlines()[-1])
                elapsed = time.time() - t0
                eta = elapsed / done * (len(todo) - done)
                log(f'[{done}/{len(todo)}] {fid} {status} · elapsed {fmt(elapsed)} · eta {fmt(eta)}')
                if not a.estimate:
                    FAILS.write_text(json.dumps(fails, indent=1))
                    if done % 5 == 0:
                        write_index(out)
        except KeyboardInterrupt:
            log('interrupted; finished families are saved. Rerun the same command to resume.')
            pool.shutdown(cancel_futures=True)
            raise SystemExit(130)
    index = write_index(out)
    stats = llm.stats.as_dict()
    log(f'swarm done: {len(scores)} ok, {len([f for f in todo if f in fails])} failed, '
        f'mean score {sum(scores) / len(scores):.1f}' if scores else 'swarm done: nothing generated')
    log(f'model usage: {stats}')
    if a.estimate and durations:
        per = sum(durations) / len(durations) / workers
        total = len(all_ids)
        tps = stats['output_tokens'] / stats['seconds'] if stats['seconds'] else 0
        print(f'\nESTIMATE on this machine with {llm.label()} (videos {"on" if videos else "off"}):')
        print(f'  {sum(durations) / len(durations):.0f} s per family, {tps:.0f} output tokens/s')
        print(f'  all {total} families: about {fmt(per * total)} with {workers} worker(s); cost $0 for local models')
        print(f'  per night (10 h): about {int(36000 / per)} families')
        print(f'  output kept in {out} for review; nothing was published')
    elif not a.estimate:
        print(f'\n{len(index)} explainers in {out}. Publish with: python3 scripts/release.py')
    return 0
