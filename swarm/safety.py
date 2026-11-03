"""Guards for model output: a tiny expression grammar for widgets, and an AST
allowlist for generated Manim scripts (which run on the Mac)."""
import ast, math, re

FUNCS = {'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'asin': math.asin, 'acos': math.acos,
         'atan': math.atan, 'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh, 'exp': math.exp,
         'log': math.log, 'ln': math.log, 'log10': math.log10, 'log2': math.log2, 'sqrt': math.sqrt,
         'abs': abs, 'floor': math.floor, 'ceil': math.ceil, 'min': min, 'max': max,
         'pow': pow, 'gamma': math.gamma, 'factorial': lambda v: math.gamma(v + 1)}
CONSTS = {'pi': math.pi, 'e': math.e}
NAME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9]{0,11}$')
_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)


def compile_expr(expr, variables):
    """Return f(**values) or raise ValueError. Grammar: numbers, variables, + - * / ^ %,
    parentheses and the functions in FUNCS. Shared with dist/explain.js."""
    if not isinstance(expr, str) or not expr.strip() or len(expr) > 240:
        raise ValueError('expression must be a non-empty string under 240 characters')
    if re.search(r'[^0-9a-zA-Z_+\-*/^%().,\s]', expr) or '**' in expr or '_' in expr:
        raise ValueError(f'expression {expr!r} uses characters outside the grammar (use ^ for powers)')
    try:
        tree = ast.parse(expr.replace('^', '**'), mode='eval')
    except SyntaxError:
        raise ValueError(f'expression {expr!r} is not well formed; write multiplication explicitly (2*x) and balance parentheses') from None
    allowed = set(variables) | set(CONSTS)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Expression, ast.Load)) or isinstance(node, _OPS):
            continue
        if isinstance(node, ast.BinOp) and isinstance(node.op, _OPS):
            continue
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            continue
        if isinstance(node, (ast.USub, ast.UAdd)):
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            continue
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
            continue
        if isinstance(node, ast.Name) and (node.id in allowed or node.id in FUNCS):
            continue
        if isinstance(node, ast.Name):
            raise ValueError(f'unknown name {node.id!r} in {expr!r}; allowed variables: {sorted(variables)}')
        raise ValueError(f'unsupported syntax {type(node).__name__} in {expr!r}')
    code = compile(tree, '<expr>', 'eval')
    env = {'__builtins__': {}, **FUNCS, **CONSTS}

    def f(**values):
        return eval(code, env, values)
    return f


def finite_fraction(f, samples):
    good = 0
    for values in samples:
        try:
            v = f(**values)
            if isinstance(v, complex):
                continue
            if math.isfinite(v):
                good += 1
        except (ValueError, ZeroDivisionError, OverflowError, TypeError):
            pass
    return good / max(len(samples), 1)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate_widget(w):
    problems = []
    if not isinstance(w, dict):
        return ['each widget must be an object']
    t = w.get('type')
    for k in ('title', 'caption'):
        if not isinstance(w.get(k), str) or not w.get(k).strip():
            problems.append(f'{t} widget needs a non-empty "{k}"')
    if t == 'plot':
        params = w.get('params') or []
        names = []
        if not isinstance(params, list) or len(params) > 4:
            problems.append('plot "params" must be a list of at most 4 sliders')
            params = []
        for p in params:
            if not isinstance(p, dict) or not NAME_RE.match(str(p.get('name', ''))) or p.get('name') in ('x', 'pi', 'e') or p.get('name') in FUNCS:
                problems.append(f'bad slider name in {p!r}')
                continue
            if not all(_num(p.get(k)) for k in ('min', 'max', 'value')) or not p['min'] < p['max'] or not p['min'] <= p['value'] <= p['max']:
                problems.append(f'slider {p.get("name")} needs numbers with min < max and min <= value <= max')
                continue
            names.append(p['name'])
        xr = w.get('x')
        if not (isinstance(xr, list) and len(xr) == 2 and all(map(_num, xr)) and xr[0] < xr[1]):
            problems.append('plot "x" must be [min, max] with min < max')
            xr = [-1, 1]
        yr = w.get('y')
        if yr is not None and not (isinstance(yr, list) and len(yr) == 2 and all(map(_num, yr)) and yr[0] < yr[1]):
            problems.append('plot "y" must be [min, max] or omitted')
        curves = [{'expr': w.get('expr')}] + [c for c in (w.get('extra') or []) if isinstance(c, dict)]
        if len(curves) > 4:
            problems.append('at most 3 "extra" curves')
        for c in curves:
            try:
                f = compile_expr(c.get('expr'), ['x'] + names)
                base = {p['name']: p['value'] for p in params if p.get('name') in names}
                xs = [xr[0] + (xr[1] - xr[0]) * i / 40 for i in range(41)]
                if finite_fraction(f, [dict(base, x=x) for x in xs]) < 0.6:
                    problems.append(f'curve {c.get("expr")!r} is undefined on most of x range {xr}')
            except (ValueError, SyntaxError) as e:
                problems.append(str(e))
    elif t == 'series':
        try:
            f = compile_expr(w.get('term'), ['n'])
            start, count = w.get('start', 0), w.get('count', 30)
            if not (isinstance(start, int) and isinstance(count, int) and 3 <= count <= 200 and 0 <= start <= 10):
                problems.append('series needs integer "start" in 0..10 and "count" in 3..200')
            elif finite_fraction(f, [{'n': n} for n in range(start, start + count)]) < 0.95:
                problems.append(f'series term {w.get("term")!r} is not finite for n from {start}')
        except (ValueError, SyntaxError) as e:
            problems.append(str(e))
        if w.get('limit') is not None and not _num(w.get('limit')):
            problems.append('series "limit" must be a number or null')
    elif t == 'steps':
        steps = w.get('steps')
        if not (isinstance(steps, list) and 2 <= len(steps) <= 10):
            problems.append('steps widget needs 2-10 "steps"')
        else:
            for s in steps:
                if not isinstance(s, dict) or not isinstance(s.get('latex'), str) or not isinstance(s.get('note'), str):
                    problems.append('each step needs string "latex" and "note"')
                    break
    elif t == 'network':
        nodes, edges = w.get('nodes'), w.get('edges')
        if not (isinstance(nodes, list) and 2 <= len(nodes) <= 14):
            problems.append('network needs 2-14 "nodes"')
        else:
            ids = {n.get('id') for n in nodes if isinstance(n, dict)}
            if len(ids) != len(nodes) or any(not isinstance(n.get('label'), str) for n in nodes if isinstance(n, dict)):
                problems.append('network nodes need unique "id" and string "label"')
            for e in edges if isinstance(edges, list) else []:
                if not isinstance(e, dict) or e.get('from') not in ids or e.get('to') not in ids:
                    problems.append(f'edge {e!r} must connect existing node ids')
                    break
    else:
        problems.append(f'unknown widget type {t!r}; use plot, series, steps or network')
    return problems


BANNED_CALLS = {'open', 'exec', 'eval', 'compile', '__import__', 'globals', 'locals', 'vars', 'getattr',
                'setattr', 'delattr', 'input', 'breakpoint', 'exit', 'quit', 'help', 'memoryview', 'type',
                'os', 'sys', 'subprocess', 'shutil', 'pathlib', 'Path', 'tempconfig', 'logger', 'console',
                'importlib', 'builtins', 'socket', 'urllib', 'requests'}
BANNED_ATTRS = {'system', 'popen', 'remove', 'unlink', 'rmtree', 'rename', 'write', 'write_text', 'write_bytes',
                'load', 'save', 'savez', 'savez_compressed', 'savetxt', 'loadtxt', 'fromfile', 'tofile', 'memmap',
                'genfromtxt', 'ctypeslib', 'lib', 'f2py', 'DataSource', 'file_writer', 'renderer', 'save_image',
                'config', 'add_sound', 'environ', 'mkdir', 'open'}
ALLOWED_IMPORTS = {'manim', 'math', 'numpy', 'random', 'itertools', 'functools'}
BANNED_MANIM = {'ImageMobject', 'SVGMobject', 'VideoMobject', 'Code', 'config', 'ThreeDScene'}


def check_manim(code, allow_latex):
    """Return a list of problems; empty means the script may be rendered."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f'Python syntax error line {e.lineno}: {e.msg}']
    problems, scene = [], False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split('.')[0] not in ALLOWED_IMPORTS:
                    problems.append(f'import {a.name} is not allowed')
        elif isinstance(node, ast.ImportFrom):
            if (node.module or '').split('.')[0] not in ALLOWED_IMPORTS or node.level:
                problems.append(f'from {node.module} import is not allowed')
        elif isinstance(node, ast.Attribute) and (node.attr.startswith('_') or node.attr in BANNED_ATTRS):
            problems.append(f'attribute .{node.attr} is not allowed')
        elif isinstance(node, ast.Name):
            if node.id in BANNED_CALLS or node.id.startswith('__'):
                problems.append(f'name {node.id} is not allowed')
            if node.id in BANNED_MANIM:
                problems.append(f'{node.id} is not allowed (no files, sounds or config changes)')
            if not allow_latex and node.id in ('MathTex', 'Tex', 'SingleStringMathTex', 'Matrix', 'DecimalMatrix', 'IntegerMatrix'):
                problems.append(f'{node.id} needs LaTeX, which is not installed; use Text instead')
        elif isinstance(node, (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await)):
            problems.append(f'{type(node).__name__} is not allowed')
        elif isinstance(node, ast.ClassDef) and node.name == 'Explainer':
            scene = True
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) > 2000:
            problems.append('string literal too long')
        elif isinstance(node, ast.While):
            problems.append('while loops are not allowed; use for loops over range()')
    if not scene:
        problems.append('define class Explainer(Scene) with a construct(self) method')
    if len(code) > 12000:
        problems.append('script longer than 12000 characters')
    return sorted(set(problems))
