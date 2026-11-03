"""Model backends. Ollama (local, free) is the default; Claude is optional.

Settings come from environment variables or local/swarm.env (KEY=value lines):
  OLLAMA_HOST        default http://127.0.0.1:11434
  OLLAMA_MODEL       default qwen2.5:14b
  OLLAMA_THINK       default false (turns off Qwen3-style thinking; "auto" leaves the model default)
  OLLAMA_JSON        default auto (strict JSON mode, dropped automatically if the model starts repeating)
  ANTHROPIC_API_KEY  enables the claude backend
  CLAUDE_MODEL       default claude-sonnet-5-5
local/.env is NOT used here: it holds only the Neo4j password.
"""
import json, os, re, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_FILE = ROOT / 'local' / 'swarm.env'


def settings():
    values = {}
    if SETTINGS_FILE.exists():
        for line in SETTINGS_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                values[k.strip()] = v.strip().strip('"').strip("'")
    for k in ('OLLAMA_HOST', 'OLLAMA_MODEL', 'OLLAMA_THINK', 'OLLAMA_JSON', 'ANTHROPIC_API_KEY', 'CLAUDE_MODEL', 'MANIM_BIN'):
        if os.environ.get(k):
            values[k] = os.environ[k]
    values.setdefault('OLLAMA_HOST', 'http://127.0.0.1:11434')
    values.setdefault('OLLAMA_MODEL', 'qwen2.5:14b')
    values.setdefault('CLAUDE_MODEL', 'claude-sonnet-5-5')
    return values


class LLMError(RuntimeError):
    pass


class Stats:
    def __init__(self):
        self.calls = 0
        self.prompt_tokens = 0
        self.output_tokens = 0
        self.seconds = 0.0

    def add(self, prompt, output, seconds):
        self.calls += 1
        self.prompt_tokens += prompt
        self.output_tokens += output
        self.seconds += seconds

    def as_dict(self):
        return {'calls': self.calls, 'prompt_tokens': self.prompt_tokens,
                'output_tokens': self.output_tokens, 'seconds': round(self.seconds, 1)}


def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors='replace')[:400]
        raise LLMError(f'{url} returned HTTP {e.code}: {detail}') from None
    except urllib.error.URLError as e:
        raise LLMError(f'cannot reach {url}: {e.reason}') from None


class Ollama:
    name = 'ollama'

    def __init__(self, model=None, host=None, ctx=16384):
        s = settings()
        self.model = model or s['OLLAMA_MODEL']
        self.host = (host or s['OLLAMA_HOST']).rstrip('/')
        self.ctx = ctx
        self.stats = Stats()
        think = s.get('OLLAMA_THINK', 'false').strip().lower()
        self.think = None if think in ('', 'auto', 'default') else think in ('1', 'true', 'yes', 'on')
        strict = s.get('OLLAMA_JSON', 'auto').strip().lower()
        self.strict_json = strict not in ('0', 'false', 'no', 'off', 'loose')

    def label(self):
        return f'ollama:{self.model}'

    def check(self):
        try:
            with urllib.request.urlopen(self.host + '/api/tags', timeout=5) as r:
                tags = [m['name'] for m in json.load(r).get('models', [])]
        except Exception as e:
            return False, f'Ollama not reachable at {self.host} ({e}). Install from https://ollama.com and open it.'
        base = self.model if ':' in self.model else self.model + ':latest'
        if self.model not in tags and base not in tags:
            return False, f'model {self.model} not pulled. Run: ollama pull {self.model}'
        return True, f'Ollama {self.host}, model {self.model}'

    def _body(self, system, user, json_mode, max_tokens, temperature):
        loose = json_mode and not self.strict_json
        if loose:
            system += ('\nRespond with a single JSON object only: no prose before or after it, no code fences, '
                       'and do not repeat yourself.')
        options = {'temperature': temperature, 'num_ctx': self.ctx, 'num_predict': max_tokens}
        if loose:
            options.update({'temperature': max(temperature, 0.5), 'repeat_penalty': 1.1, 'repeat_last_n': 256})
        body = {'model': self.model, 'stream': False, 'options': options,
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}]}
        if json_mode and self.strict_json:
            body['format'] = 'json'
        if self.think is not None:
            body['think'] = self.think
        return body

    def complete(self, system, user, json_mode=True, max_tokens=3000, temperature=0.3):
        t = time.time()
        r = None
        for attempt in range(4):
            body = self._body(system, user, json_mode, max_tokens, temperature)
            try:
                r = _post(self.host + '/api/chat', body, {'Content-Type': 'application/json'}, timeout=900)
                break
            except LLMError as e:
                msg = str(e)
                if 'think' in body and re.search(r'HTTP 400.*think', msg, re.I | re.S):
                    self.think = None
                elif re.search(r'repeat limit|repetition', msg, re.I) and attempt < 3:
                    if self.strict_json and json_mode:
                        self.strict_json = False
                    else:
                        temperature = min(temperature + 0.2, 0.9)
                else:
                    raise
        self.stats.add(r.get('prompt_eval_count', 0), r.get('eval_count', 0), time.time() - t)
        content = re.sub(r'<think>.*?(</think>|$)', '', r['message'].get('content', ''), flags=re.S).strip()
        if not content and r.get('eval_count', 0) >= max_tokens:
            raise LLMError(f'{self.model} used its whole {max_tokens}-token budget without answering '
                           '(it is probably thinking). Set OLLAMA_THINK=false in local/swarm.env or pick another model.')
        return content


class Claude:
    name = 'claude'

    def __init__(self, model=None, key=None):
        s = settings()
        self.model = model or s['CLAUDE_MODEL']
        self.key = key or s.get('ANTHROPIC_API_KEY')
        self.stats = Stats()

    def label(self):
        return f'claude:{self.model}'

    def check(self):
        if not self.key:
            return False, f'no ANTHROPIC_API_KEY. Put ANTHROPIC_API_KEY=... in {SETTINGS_FILE} (chmod 600)'
        return True, f'Claude API, model {self.model}'

    def complete(self, system, user, json_mode=True, max_tokens=4000, temperature=0.3):
        if json_mode:
            system += '\nRespond with a single JSON object only. No prose before or after it, no code fences.'
        body = {'model': self.model, 'max_tokens': max_tokens, 'temperature': temperature,
                'system': system, 'messages': [{'role': 'user', 'content': user}]}
        headers = {'Content-Type': 'application/json', 'x-api-key': self.key, 'anthropic-version': '2023-06-01'}
        t = time.time()
        for attempt in range(4):
            try:
                r = _post('https://api.anthropic.com/v1/messages', body, headers, timeout=300)
                break
            except LLMError as e:
                if attempt == 3 or not re.search(r'HTTP (429|5\d\d)', str(e)):
                    raise
                time.sleep(5 * (attempt + 1))
        u = r.get('usage', {})
        self.stats.add(u.get('input_tokens', 0), u.get('output_tokens', 0), time.time() - t)
        return ''.join(b.get('text', '') for b in r.get('content', []) if b.get('type') == 'text')


def make(name, model=None):
    if name == 'ollama':
        return Ollama(model)
    if name == 'claude':
        return Claude(model)
    if name == 'mock':
        from .mock import Mock
        return Mock()
    raise SystemExit(f'unknown backend {name}')


def parse_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find('{')
    if start < 0:
        raise ValueError('no JSON object in model output')
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError('unterminated JSON object in model output')


def ask_json(backend, system, user, validate=None, retries=2, max_tokens=3000):
    """Call the model, parse JSON, run validate(obj) -> list of problems; feed problems back."""
    problems = []
    prompt = user
    for attempt in range(retries + 1):
        raw = backend.complete(system, prompt, json_mode=True, max_tokens=max_tokens)
        try:
            obj = parse_json(raw)
            problems = validate(obj) if validate else []
        except (ValueError, json.JSONDecodeError) as e:
            obj, problems = None, [f'output was not valid JSON: {e}']
        if not problems:
            return obj
        prompt = (user + '\n\nYour previous answer had these problems; fix all of them and answer again '
                  'with the complete JSON object:\n- ' + '\n- '.join(problems[:8]))
    raise LLMError('model output still invalid after retries: ' + '; '.join(problems[:4]))
