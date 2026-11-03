"""The agent roles and the per-family pipeline.

untangler -> intuitor -> visualizer -> critic (-> reviser -> critic) -> animator (Manim, optional)
"""
import gzip, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
from . import SCHEMA
from .llm import ask_json, LLMError
from .safety import validate_widget, check_manim

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
OUT = DIST / 'explainers'

TEAM = ('ROLE: {role}\nYou are one member of a team that explains research mathematics to curious, '
        'knowledge-hungry learners on Mathematical Universe. Rules: be faithful to the SOURCE; never '
        'invent theorems, constants, numbers, names or citations that the source does not support; when '
        'the source is too thin to be sure, say so plainly. Write math in LaTeX between single dollar signs '
        'like $x^2$. Plain, warm, precise English. Output JSON only.')


def load_concepts():
    data = json.loads((DIST / 'foundations.json').read_text())
    return [(n['id'], n['title']) for n in data['nodes'] if n.get('kind') == 'Concept']


def family_ids():
    cat = json.loads((DIST / 'catalogue.json').read_text())
    return sorted(n['id'] for n in cat['nodes'] if n.get('kind') == 'Family')


def _rank(node):
    t = (node.get('title') or '').lower()
    score = 0
    for i, key in enumerate(('thm', 'theorem', 'main', 'prop', 'def', 'lem', 'cor')):
        if key in t:
            score = max(score, 10 - i)
    if node.get('kind') == 'Definition':
        score = max(score, 6)
    return score


def build_context(fid, budget=11000):
    graph = json.loads(gzip.open(DIST / 'graphs' / f'{fid}.json.gz').read())
    details = {}
    dpath = DIST / 'details' / f'{fid}.json.gz'
    if dpath.exists():
        details = json.loads(gzip.open(dpath).read())
    nodes = graph['nodes']
    fam = next(n for n in nodes if n['id'] == fid)
    parts = [f'FAMILY {fid}: {fam.get("title", "")}', f'Subject: {fam.get("subject", "")}',
             'Catalogue summary: ' + (details.get(fid) or fam.get('summary', '')).strip()]
    for m in (n for n in nodes if n.get('kind') == 'Manuscript'):
        parts.append(f'Manuscript "{m.get("title", "")}": {(details.get(m["id"]) or m.get("summary", ""))[:900]}')
    picks = sorted((n for n in nodes if n.get('kind') in ('Statement', 'Definition')), key=_rank, reverse=True)
    used = sum(len(p) for p in parts)
    for n in picks:
        text = (details.get(n['id']) or n.get('summary') or '').strip()
        piece = f'[{n.get("kind")} {n.get("title", "")}] {text[:1100]}'
        if used + len(piece) > budget:
            continue
        parts.append(piece)
        used += len(piece)
    return {'id': fid, 'title': fam.get('title', ''), 'subject': fam.get('subject', ''),
            'url': fam.get('url', ''), 'text': '\n\n'.join(parts)}


def _need(obj, keys):
    problems = []
    if not isinstance(obj, dict):
        return ['answer must be a JSON object']
    for k, kind in keys.items():
        v = obj.get(k)
        if kind is str and not (isinstance(v, str) and v.strip()):
            problems.append(f'"{k}" must be a non-empty string')
        if kind is list and not isinstance(v, list):
            problems.append(f'"{k}" must be a list')
    return problems


def untangle(llm, ctx, concepts):
    ids = [c[0] for c in concepts]
    system = TEAM.format(role='untangler') + '''
Your job: untangle the central result into its parts so a newcomer can read it.
Return JSON with exactly these keys:
{"headline": "<=12 plain words saying what was shown",
 "core_statement": "the main result in 1-3 plain sentences, then the precise version",
 "key_equation": "the single most important formula or object in LaTeX without dollar signs, or \\"\\"",
 "symbols": [{"symbol": "LaTeX without dollars", "meaning": "plain meaning"}],
 "given": ["each assumption or setting, plainly"],
 "concludes": ["each conclusion, plainly"],
 "foundations": ["2-6 concept ids from the CONCEPTS list that a learner needs first"],
 "difficulty": "high school | college | graduate | research"}'''
    user = f'CONCEPTS: {json.dumps(concepts)}\n\nSOURCE:\n{ctx["text"]}'

    def check(o):
        p = _need(o, {'headline': str, 'core_statement': str, 'symbols': list, 'given': list,
                      'concludes': list, 'foundations': list, 'difficulty': str})
        if isinstance(o, dict):
            bad = [f for f in o.get('foundations') or [] if f not in ids]
            if bad:
                p.append(f'foundations must be ids from CONCEPTS; not valid: {bad}')
            for s in o.get('symbols') or []:
                if not (isinstance(s, dict) and isinstance(s.get('symbol'), str) and isinstance(s.get('meaning'), str)):
                    p.append('each symbol needs string "symbol" and "meaning"')
                    break
            o.setdefault('key_equation', '')
        return p
    return ask_json(llm, system, user, check)


def intuit(llm, ctx, untangled, feedback=None):
    system = TEAM.format(role='intuitor') + '''
Your job: give the intuition behind the result so that a curious person wants to learn more.
Explain WHY it is true or WHY it is hard, not just what it says. Prefer a concrete small example.
Return JSON with exactly these keys:
{"hook": "one question that makes a curious reader lean in",
 "intuition": ["2-4 short paragraphs building the idea step by step from a small example"],
 "analogy": "one honest everyday analogy, with where it breaks down",
 "ladder": [{"level": "curious", "text": "..."}, {"level": "undergraduate", "text": "..."}, {"level": "researcher", "text": "..."}],
 "why_it_matters": "what this unlocks or connects to",
 "misconceptions": ["0-3 tempting wrong readings"],
 "explore": ["2-3 questions a learner could investigate next"]}'''
    user = f'UNTANGLED:\n{json.dumps(untangled)}\n\nSOURCE:\n{ctx["text"]}'
    if feedback:
        user += '\n\nA reviewer found these problems in an earlier draft. Fix every one:\n- ' + '\n- '.join(feedback)

    def check(o):
        p = _need(o, {'hook': str, 'intuition': list, 'analogy': str, 'ladder': list, 'why_it_matters': str})
        if isinstance(o, dict):
            if not (2 <= len(o.get('intuition') or []) <= 5) or not all(isinstance(x, str) for x in o.get('intuition') or []):
                p.append('"intuition" must be 2-4 strings')
            if not all(isinstance(x, dict) and isinstance(x.get('text'), str) and x.get('level') for x in o.get('ladder') or []) or len(o.get('ladder') or []) != 3:
                p.append('"ladder" must be 3 objects with "level" and "text"')
            o.setdefault('misconceptions', [])
            o.setdefault('explore', [])
        return p
    return ask_json(llm, system, user, check)


WIDGET_GUIDE = '''Widget types (use 1-3; choose what genuinely shows the idea; toy cases are fine but say so in the caption):
{"type":"plot","title":"...","caption":"what to notice; say if it is a toy model","expr":"sin(a*x)/x",
 "x":[-10,10],"y":[-1.5,1.5],"params":[{"name":"a","label":"frequency","min":0.5,"max":5,"value":1,"step":0.1}],
 "extra":[{"expr":"1/x","label":"envelope"}]}
{"type":"series","title":"...","caption":"...","term":"(-1)^n/(2*n+1)^2","start":0,"count":40,"limit":0.915965594,"limit_label":"G"}
{"type":"steps","title":"...","caption":"...","steps":[{"latex":"LaTeX line without dollars","note":"why this step"}]}
{"type":"network","title":"...","caption":"...","nodes":[{"id":"a","label":"..."}],"edges":[{"from":"a","to":"b","label":"uses"}]}
Expression grammar for expr/term: numbers, the variable (x for plot, n for series), slider names,
+ - * / ^ %, parentheses, and functions sin cos tan asin acos atan sinh cosh tanh exp log ln log10 log2 sqrt abs floor ceil min max pow gamma factorial; constants pi e.
No other names, no ** (use ^), no implicit multiplication (write 2*x). Only give "limit" when the source or standard knowledge fixes it.'''


def visualize(llm, ctx, untangled, intuition):
    system = TEAM.format(role='visualizer') + '\nYour job: design interactive pictures that make the intuition visible.\n' + \
        WIDGET_GUIDE + '\nReturn JSON: {"widgets": [ ... ]}'
    user = f'UNTANGLED:\n{json.dumps(untangled)}\n\nINTUITION:\n{json.dumps(intuition)}\n\nSOURCE (for accuracy):\n{ctx["text"][:5000]}'

    def check(o):
        if not isinstance(o, dict) or not isinstance(o.get('widgets'), list) or not 1 <= len(o['widgets']) <= 3:
            return ['return {"widgets": [...]} with 1-3 widgets']
        p = []
        for i, w in enumerate(o['widgets']):
            p += [f'widget {i + 1}: {x}' for x in validate_widget(w)]
        return p
    return ask_json(llm, system, user, check, retries=3)['widgets']


def critique(llm, ctx, draft):
    system = TEAM.format(role='critic') + '''
Your job: check the draft explainer against the SOURCE like a careful referee and a good teacher.
Look for: claims the source does not support, wrong math, misleading pictures or analogies,
jargon left unexplained, and missing honesty about what is not shown.
Return JSON: {"score": 0-10 (10 = accurate and illuminating; below 6 = needs revision),
 "issues": [{"where": "headline|core_statement|intuition|analogy|widget N|...", "problem": "...", "fix": "..."}],
 "unsupported_claims": ["exact phrases not supported by the source"]}'''
    user = f'DRAFT:\n{json.dumps(draft)}\n\nSOURCE:\n{ctx["text"]}'

    def check(o):
        p = _need(o, {'issues': list})
        if isinstance(o, dict) and not (isinstance(o.get('score'), (int, float)) and 0 <= o['score'] <= 10):
            p.append('"score" must be a number 0-10')
        if isinstance(o, dict):
            o.setdefault('unsupported_claims', [])
        return p
    return ask_json(llm, system, user, check)


def revise_untangled(llm, ctx, untangled, issues, concepts):
    system = TEAM.format(role='untangler') + '\nRevise this untangled summary to fix the reviewer issues. Keep the same JSON keys.'
    user = (f'CONCEPTS: {json.dumps(concepts)}\n\nCURRENT:\n{json.dumps(untangled)}\n\nISSUES:\n- ' + '\n- '.join(issues) +
            f'\n\nSOURCE:\n{ctx["text"]}')
    ids = {c[0] for c in concepts}

    def check(o):
        p = _need(o, {'headline': str, 'core_statement': str, 'symbols': list, 'given': list, 'concludes': list, 'foundations': list})
        if isinstance(o, dict):
            o['foundations'] = [f for f in o.get('foundations') or [] if f in ids]
            o.setdefault('key_equation', untangled.get('key_equation', ''))
            o.setdefault('difficulty', untangled.get('difficulty', 'research'))
        return p
    return ask_json(llm, system, user, check)


def manim_tools():
    """Return (manim command list or None, latex available)."""
    from .llm import settings
    s = settings()
    custom = s.get('MANIM_BIN') or os.environ.get('MANIM_BIN')
    venv = ROOT.parent / '.venv-manim' / 'bin' / 'manim'
    for cand in [custom, str(venv), shutil.which('manim')]:
        if cand and Path(cand).exists():
            return [cand], bool(shutil.which('latex'))
    return None, bool(shutil.which('latex'))


ANIM_GUIDE = '''Write a Manim Community Edition script (version 0.18 or newer).
Requirements:
- Start with: from manim import *   (you may also import math, numpy as np, random)
- Exactly one scene: class Explainer(Scene) with def construct(self).
- 25-50 seconds total. Tell a visual story: setup -> key move -> payoff. Use self.wait() so viewers can read.
- Keep everything inside the 16:9 frame (x in [-7,7], y in [-4,4]); scale long text down; at most ~12 words on screen at once.
- Use Axes, NumberPlane, Dot, Line, Arrow, Circle, Square, Polygon, VGroup, ValueTracker, always_redraw, Transform, FadeIn, Create, Write, Indicate.
- {latex_rule}
- No files, images, sounds, config changes, os/sys, while loops, or private attributes.
Answer with only the Python code in one ```python block.'''


def animate(llm, ctx, draft, fid, out_dir, log, tries=3):
    cmd, has_latex = manim_tools()
    if not cmd:
        return None, 'manim not installed'
    latex_rule = ('Use MathTex for formulas.' if has_latex else
                  'LaTeX is NOT installed: never use MathTex, Tex or Matrix; write formulas with Text using unicode (x², π, ∑, √).')
    system = TEAM.format(role='animator').replace('Output JSON only.', '') + '\n' + ANIM_GUIDE.format(latex_rule=latex_rule)
    brief = {k: draft[k] for k in ('untangled', 'intuition') if k in draft}
    user = f'Animate the core intuition of this explainer for a curious newcomer.\n\nEXPLAINER:\n{json.dumps(brief)}'
    error = ''
    for attempt in range(tries):
        prompt = user if not error else user + f'\n\nYour previous script failed:\n{error[-1800:]}\nFix it and return the full script.'
        raw = llm.complete(system, prompt, json_mode=False, max_tokens=3500, temperature=0.4)
        m = re.search(r'```(?:python)?\s*\n(.*?)```', raw, re.S)
        code = (m.group(1) if m else raw).strip()
        problems = check_manim(code, has_latex)
        if problems:
            error = 'Safety/structure check: ' + '; '.join(problems)
            log(f'  {fid} animator attempt {attempt + 1}: {error[:160]}')
            continue
        with tempfile.TemporaryDirectory(prefix=f'mathuni-{fid}-') as tmp:
            script = Path(tmp) / 'scene.py'
            script.write_text(code)
            env = {'PATH': os.environ.get('PATH', ''), 'HOME': tmp, 'LANG': 'en_US.UTF-8',
                   'TMPDIR': tmp}
            try:
                r = subprocess.run(cmd + ['-ql', '--disable_caching', '--media_dir', tmp + '/media',
                                          '-o', fid, str(script), 'Explainer'],
                                   cwd=tmp, env=env, capture_output=True, text=True, timeout=420)
            except subprocess.TimeoutExpired:
                error = 'Rendering took longer than 7 minutes; make the scene shorter and simpler.'
                log(f'  {fid} animator attempt {attempt + 1}: timeout')
                continue
            videos = list(Path(tmp).rglob(f'{fid}.mp4'))
            if r.returncode == 0 and videos:
                out_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(videos[0], out_dir / f'{fid}.mp4')
                (out_dir / f'{fid}.py').write_text(code)
                return f'explainers/video/{fid}.mp4', None
            error = (r.stderr or r.stdout)[-2500:]
            log(f'  {fid} animator attempt {attempt + 1}: render failed ({error.strip().splitlines()[-1][:140] if error.strip() else "no output"})')
    return None, error[-600:]


def explain_family(fid, llm, concepts, videos=True, min_score=6, log=print, out=OUT, video_llm=None):
    t0 = time.time()
    ctx = build_context(fid)
    untangled = untangle(llm, ctx, concepts)
    intuition = intuit(llm, ctx, untangled)
    widgets = visualize(llm, ctx, untangled, intuition)
    draft = {'untangled': untangled, 'intuition': intuition, 'widgets': widgets}
    review = critique(llm, ctx, draft)
    rounds = 0
    if review['score'] < min_score:
        rounds = 1
        issues = [f'{i.get("where", "")}: {i.get("problem", "")} -> {i.get("fix", "")}' for i in review['issues'] if isinstance(i, dict)]
        issues += [f'unsupported: {c}' for c in review.get('unsupported_claims', [])]
        untangled = revise_untangled(llm, ctx, untangled, issues, concepts)
        intuition = intuit(llm, ctx, untangled, feedback=issues)
        widgets = visualize(llm, ctx, untangled, intuition)
        draft = {'untangled': untangled, 'intuition': intuition, 'widgets': widgets}
        review = critique(llm, ctx, draft)
    video, video_error = None, None
    if videos:
        video, video_error = animate(video_llm or llm, ctx, draft, fid, out / 'video', log)
    result = {'schema': SCHEMA, 'id': fid, 'title': ctx['title'], 'subject': ctx['subject'], 'source': ctx['url'],
              'model': llm.label(), 'generated': time.strftime('%Y-%m-%dT%H:%M:%S'), 'seconds': round(time.time() - t0, 1),
              'critic': {'score': review['score'], 'issues': review['issues'][:8],
                         'unsupported_claims': review.get('unsupported_claims', [])[:8], 'revisions': rounds},
              **draft, 'video': video, 'video_error': video_error if videos and not video else None}
    return result
