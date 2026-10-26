"""Automatisk retting av FY1-03-luftmotstand.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1', 'terminalfart(80, 0.25) skal gi ca. 56.0 m/s', 'naer(terminalfart(80, 0.25), (80*9.81/0.25)**0.5) and naer(terminalfart(100, 1, g=10), 31.6228, rel=1e-4)'),
    ('2_lengde', 'simuler_fall(80, 0.25, 0.1, 10) skal gi lister med 101 elementer', 'all(len(liste) == 101 for liste in simuler_fall(80, 0.25, 0.1, 10))'),
    ('2_forste_steg', 'første Euler-steg skal gi v = g·dt', 'naer(simuler_fall(80, 0.25, 0.01, 1)[1][1], 0.0981, rel=1e-6) and naer(simuler_fall(80, 0.25, 0.01, 1)[1][0], 0)'),
    ('2_terminal', 'farten etter 60 s skal være nesten lik terminalfarten', 'naer(simuler_fall(80, 0.25, 0.01, 60)[1][-1], (80*9.81/0.25)**0.5, rel=2e-3)'),
    ('2_strekning', 'strekningen skal øke med v·dt i hvert steg', 'naer(simuler_fall(80, 0.25, 0.5, 1)[2][-1], 0.5*9.81*0.5, rel=1e-6)'),
    ('3', 'tid_til_andel([0, 1, 2, 3], [0, 5, 9, 9.9], 10, 0.9) skal gi 2', 'naer(tid_til_andel([0, 1, 2, 3], [0, 5, 9, 9.9], 10, 0.9), 2)'),
    ('5', 'eksakt_fart(5, 80, 0.25) skal gi v_T·tanh(g·5/v_T)', "naer(eksakt_fart(5, 80, 0.25), (80*9.81/0.25)**0.5 * __import__('math').tanh(9.81*5/(80*9.81/0.25)**0.5), rel=1e-6)"),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
