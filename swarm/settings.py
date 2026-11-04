"""Settings for the explainer swarm, stored in local/swarm.env (KEY=value, chmod 600).

Edited from the app's Settings panel (http://127.0.0.1:18765 only) or with
  python3 mathuni.py settings                 show
  python3 mathuni.py settings KEY=value ...   change
Environment variables with the same names override the file for one run.
"""
import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / 'local' / 'swarm.env'

# name: (kind, default, choices or (min, max), label, help)
FIELDS = {
    'SWARM_BACKEND': ('choice', 'ollama', ['ollama', 'claude'], 'Main model', 'Who writes the explainers by default.'),
    'SWARM_ESCALATE': ('choice', 'none', ['none', 'claude'], 'Second opinion', 'Redo drafts that score below the threshold with Claude.'),
    'SWARM_MIN_SCORE': ('number', '6', (0, 10), 'Revision threshold', 'Critic score below which a draft is revised (and escalated).'),
    'SWARM_VIDEOS': ('choice', 'auto', ['auto', 'on', 'off'], 'Manim videos', 'auto = make videos when Manim is installed.'),
    'SWARM_WORKERS': ('number', '0', (0, 16), 'Parallel families', '0 = automatic (1 for Ollama, 4 for Claude).'),
    'OLLAMA_HOST': ('url', 'http://127.0.0.1:11434', None, 'Ollama address', 'Where Ollama is running.'),
    'OLLAMA_MODEL': ('text', 'qwen2.5:14b', None, 'Ollama model', 'Any model shown by `ollama list`.'),
    'OLLAMA_THINK': ('choice', 'false', ['false', 'true', 'auto'], 'Ollama thinking', 'false is faster and avoids empty answers from Qwen3-style models.'),
    'OLLAMA_JSON': ('choice', 'auto', ['auto', 'loose'], 'Ollama JSON mode', 'loose skips strict JSON mode (helps models that repeat themselves).'),
    'ANTHROPIC_API_KEY': ('secret', '', None, 'Claude API key', 'Stored only on this Mac in local/swarm.env.'),
    'CLAUDE_MODEL': ('text', 'claude-sonnet-5-5', None, 'Claude model', 'e.g. claude-sonnet-5-5, claude-opus-5-5, claude-haiku-5-5.'),
    'MANIM_BIN': ('path', '', None, 'Manim command', 'Leave empty to find ../.venv-manim or manim on PATH.'),
}


def _read_file():
    values, lines = {}, []
    if FILE.exists():
        lines = FILE.read_text().splitlines()
        for line in lines:
            s = line.strip()
            if s and not s.startswith('#') and '=' in s:
                k, v = s.split('=', 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    return values, lines


def load():
    """Effective settings: defaults < file < environment."""
    values, _ = _read_file()
    out = {k: f[1] for k, f in FIELDS.items()}
    out.update({k: v for k, v in values.items() if v != '' or k not in FIELDS})
    for k in FIELDS:
        if os.environ.get(k):
            out[k] = os.environ[k]
    return out


def validate(key, value):
    if key not in FIELDS:
        raise ValueError(f'unknown setting {key}')
    kind, default, extra, label, _ = FIELDS[key]
    value = str(value).strip()
    if '\n' in value or '\r' in value or len(value) > 400:
        raise ValueError(f'{label}: value too long or contains a line break')
    if value == '':
        return ''
    if kind == 'choice' and value not in extra:
        raise ValueError(f'{label}: choose one of {", ".join(extra)}')
    if kind == 'number':
        try:
            n = float(value)
        except ValueError:
            raise ValueError(f'{label}: must be a number') from None
        if not extra[0] <= n <= extra[1]:
            raise ValueError(f'{label}: must be between {extra[0]} and {extra[1]}')
        value = str(int(n)) if n == int(n) else str(n)
    if kind == 'url' and not re.match(r'^https?://[A-Za-z0-9.\-]+(:\d+)?/?$', value):
        raise ValueError(f'{label}: use a form like http://127.0.0.1:11434')
    if kind == 'text' and not re.match(r'^[A-Za-z0-9._:\-/]+$', value):
        raise ValueError(f'{label}: letters, digits and . _ : - / only')
    if kind == 'secret' and not re.match(r'^[A-Za-z0-9_\-]{20,300}$', value):
        raise ValueError(f'{label}: that does not look like an API key')
    if kind == 'path' and not value.startswith('/'):
        raise ValueError(f'{label}: give an absolute path')
    return value


def save(changes):
    """Validate and write changes; '' resets a setting to its default. Returns the public view."""
    clean = {k: validate(k, v) for k, v in changes.items()}
    values, lines = _read_file()
    out, seen = [], set()
    for line in lines:
        s = line.strip()
        k = s.split('=', 1)[0].strip() if '=' in s and not s.startswith('#') else None
        if k in clean:
            seen.add(k)
            if clean[k] != '':
                out.append(f'{k}={clean[k]}')
        else:
            out.append(line)
    for k, v in clean.items():
        if k not in seen and v != '':
            out.append(f'{k}={v}')
    FILE.parent.mkdir(exist_ok=True)
    tmp = FILE.with_suffix('.env.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write('\n'.join(out).strip() + '\n')
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)
    return public()


def mask(v):
    return ('set · ends in ' + v[-4:]) if v else ''


def public():
    """Settings safe to show in a browser: secrets are masked, never returned."""
    eff = load()
    rows = []
    for k, (kind, default, extra, label, help_) in FIELDS.items():
        v = eff.get(k, '')
        rows.append({'key': k, 'kind': kind, 'label': label, 'help': help_, 'default': default,
                     'choices': extra if kind == 'choice' else None,
                     'range': list(extra) if kind == 'number' else None,
                     'value': mask(v) if kind == 'secret' else v,
                     'is_set': bool(v) if kind == 'secret' else None,
                     'from_env': bool(os.environ.get(k))})
    return rows


def cli(argv):
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__)
        print('\n'.join(f'  {k:18} {f[3]}: {f[4]}' for k, f in FIELDS.items()))
        return 0
    if argv:
        changes = {}
        for a in argv:
            if '=' not in a:
                raise SystemExit(f'use KEY=value (got {a!r}); see python3 mathuni.py settings --help')
            k, v = a.split('=', 1)
            changes[k.strip()] = v
        try:
            save(changes)
        except ValueError as e:
            raise SystemExit(str(e))
        print('Saved to', FILE)
    for r in public():
        flag = ' (from environment)' if r['from_env'] else ''
        print(f"  {r['key']:18} {r['value'] or '-'}{flag}")
    return 0
