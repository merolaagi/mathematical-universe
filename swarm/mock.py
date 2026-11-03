"""Canned backend for testing the pipeline without a model."""
import json, re, time
from .llm import Stats

SCENE = '''from manim import *

class Explainer(Scene):
    def construct(self):
        title = Text("Partial sums settle down", font_size=40).to_edge(UP)
        self.play(Write(title))
        axes = Axes(x_range=[0, 12, 2], y_range=[0, 1.2, 0.2], x_length=10, y_length=5).shift(DOWN * 0.5)
        self.play(Create(axes))
        total = 0
        dots = VGroup()
        for n in range(12):
            total += (-1) ** n / (2 * n + 1) ** 2
            dots.add(Dot(axes.c2p(n, total), color=YELLOW))
        self.play(LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.2))
        line = DashedLine(axes.c2p(0, 0.9159), axes.c2p(12, 0.9159), color=BLUE)
        self.play(Create(line))
        self.wait(1)
'''


class Mock:
    name = 'mock'

    def __init__(self):
        self.stats = Stats()
        self.model = 'mock'

    def label(self):
        return 'mock:canned'

    def check(self):
        return True, 'mock backend (canned answers)'

    def complete(self, system, user, json_mode=True, max_tokens=3000, temperature=0.3):
        self.stats.add(len(user) // 4, 400, 0.01)
        role = re.search(r'ROLE: (\w+)', system).group(1)
        if role == 'untangler':
            return json.dumps({'headline': 'An alternating sum that cannot be a fraction',
                               'core_statement': 'Catalan’s constant $G$ is irrational.',
                               'key_equation': 'G=\\sum_{j\\ge0}\\frac{(-1)^j}{(2j+1)^2}',
                               'symbols': [{'symbol': 'G', 'meaning': 'Catalan’s constant, about 0.9160'}],
                               'given': ['The series defining $G$'], 'concludes': ['$G$ is not $p/q$'],
                               'foundations': ['concept:sequences', 'concept:rational', 'concept:contradiction'],
                               'difficulty': 'research'})
        if role == 'intuitor':
            return json.dumps({'hook': 'Can a sum of simple fractions ever escape being a fraction?',
                               'intuition': ['Add $1-1/9+1/25-\\dots$ and the totals zig-zag toward 0.9160.',
                                             'If $G=p/q$, tiny integer combinations would be forced to be nonzero yet smaller than 1.'],
                               'analogy': 'Like a ruler whose ticks never line up with the target; it breaks down because rulers are finite.',
                               'ladder': [{'level': 'curious', 'text': 'A famous number is shown not to be a fraction.'},
                                          {'level': 'undergraduate', 'text': 'Approximations by rationals are too good to allow $G=p/q$.'},
                                          {'level': 'researcher', 'text': 'Determinant-based linear forms with a certified decay rate.'}],
                               'why_it_matters': 'A long-open question about a classical constant.',
                               'misconceptions': ['Irrational does not mean transcendental.'],
                               'explore': ['Why is $\\pi^2/6$ easier?']})
        if role == 'visualizer':
            return json.dumps({'widgets': [
                {'type': 'series', 'title': 'Partial sums of G', 'caption': 'Each bar adds one term; the totals zig-zag toward G.',
                 'term': '(-1)^n/(2*n+1)^2', 'start': 0, 'count': 30, 'limit': 0.915965594, 'limit_label': 'G'},
                {'type': 'plot', 'title': 'How fast terms shrink', 'caption': 'Toy picture: terms decay like 1/(2x+1)^p.',
                 'expr': '1/(2*x+1)^p', 'x': [0, 10], 'y': [0, 1],
                 'params': [{'name': 'p', 'label': 'power', 'min': 1, 'max': 4, 'value': 2, 'step': 0.1}]},
                {'type': 'steps', 'title': 'The shape of the argument', 'caption': 'Outline only.',
                 'steps': [{'latex': 'G = p/q', 'note': 'Suppose it were a fraction.'},
                           {'latex': '0 < |q\\,L_N| < 1', 'note': 'An integer strictly between 0 and 1.'},
                           {'latex': '\\Rightarrow\\ \\text{contradiction}', 'note': 'No such integer exists.'}]}]})
        if role == 'critic':
            return json.dumps({'score': 7.5, 'issues': [{'where': 'analogy', 'problem': 'loose', 'fix': 'tighten'}],
                               'unsupported_claims': []})
        if role == 'animator':
            return '```python\n' + SCENE + '```'
        raise ValueError(role)
