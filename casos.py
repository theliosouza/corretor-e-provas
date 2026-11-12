"""Casos de teste provisórios da atividade de Lógica de Programação."""

import ast, builtins, itertools, re, signal, unicodedata
SAFE = {name: getattr(builtins, name) for name in ('range', 'len', 'int', 'float', 'str', 'list', 'tuple', 'bool', 'set', 'dict', 'min', 'max', 'sum', 'abs', 'round', 'sorted', 'enumerate', 'zip', 'map', 'filter', 'any', 'all', 'reversed', 'isinstance', 'Exception', 'ValueError', 'IndexError', 'TypeError', 'EOFError')}
METHODS = set('append extend insert index count sort reverse remove pop clear copy split strip lower upper casefold join replace startswith endswith isdigit rstrip lstrip items keys values get'.split())


def timeout(*args):
    raise TimeoutError('Tempo excedido')
signal.signal(signal.SIGALRM, timeout)


def clean(s):
    return ''.join((x for x in unicodedata.normalize('NFKD', s.lower()) if not unicodedata.combining(x)))


def numbers(s):
    return [float(x.replace(',', '.')) for x in re.findall('(?<!\\w)[-+]?\\d+(?:[.,]\\d+(?!\\d))?', s)]


def matches(s, expected):
    n = numbers(s)
    it = iter(n)
    return all((any((abs(a - b) < 0.051 for a in it)) for b in expected))


def labeled(s, pat, val):
    return any((re.search(pat, l) and numbers(l) and (abs(numbers(l)[-1] - val) < 0.051) for l in s.splitlines()))


def line_index(t, label, values):
    return any((label in l and any((v in numbers(l) for v in values)) for l in t.splitlines()))


def code_of(source):
    tree = ast.parse(source)
    if not any((not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Constant) for n in tree.body)):
        return (None, 0)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.With, ast.AsyncWith, ast.Global, ast.Nonlocal)):
            raise PermissionError('Construção fora do executor restrito')
        if isinstance(n, ast.Attribute) and n.attr not in METHODS:
            raise PermissionError('Método fora do executor: ' + n.attr)
        if isinstance(n, (ast.Name, ast.arg)) and '__' in (n.id if isinstance(n, ast.Name) else n.arg) and (not (isinstance(n, ast.Name) and n.id == '__name__')):
            raise PermissionError('Identificador fora do executor')
    defs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    return (compile(tree, '<resposta>', 'exec'), len(defs & calls))


def run(code, inputs):
    it = iter(map(str, inputs))
    out = []
    total = 0

    def inp(prompt=''):
        try:
            return next(it)
        except StopIteration:
            raise EOFError('O programa solicitou entradas adicionais') from None

    def output(*args, sep=' ', end='\n'):
        nonlocal total
        s = sep.join(map(str, args)) + end
        total += len(s)
        if total > 20000:
            raise ValueError('Excesso de saída')
        out.append(s)
    env = {'__builtins__': {**SAFE, 'print': output, 'input': inp}, '__name__': '__main__'}
    signal.setitimer(signal.ITIMER_REAL, 0.08)
    try:
        exec(code, env)
        return (clean(''.join(out)), '')
    except Exception as e:
        return (clean(''.join(out)), type(e).__name__ + ': ' + str(e))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
m9 = [2, 5, -3, 7, 3, 11, -2, 8, 9]
m12 = [2, -3, 7, 4, -1, 6, 11, 2, 5, -4, 8, 9]
m16 = [2, 7, -3, 9, 6, 4, 10, 2, 5, -2, 13, 11, -4, 3, 7, 8]
m25 = [2, -3, 4, 7, -2, 5, 8, -1, 0, 3, -2, 9, 0, 11, 4, 7, -1, 5, -9, 2, -3, 4, 6, -7, 1]
names = ['Amora', 'Bento', 'Cecilia', 'Dante', 'Elias', 'Flora']
notes = [4.0, 6.0, 7.0, 8.0, 3.0, 5.0]
n39 = [[3, 5], [7, 5], [7, 7], [7, 9], [2, 4], [3, 7]]
flat = lambda rows: list(itertools.chain.from_iterable(rows))


def chunks(a, n):
    return [a[i:i + n] for i in range(0, len(a), n)]


def fixed(seq, check):
    return [(seq, check)]


def matrix(seq, cols, check):
    return [([seq, [' '.join(map(str, l)) for l in chunks(seq, cols)]], check, 'variants')]


def spec(q):
    pos = lambda t, p, n: labeled(t, p, n)
    if q == 1:
        a = [-8, 2, 7, 0, 4, 0, 6, 9]
        return fixed(a, lambda t: all((pos(t, k, v) for k, v in [('positiv', 5), ('negativ', 1), ('zero', 2)])) or matches(t, [5, 1, 2]))
    if q == 2:
        return fixed([14, 5, 4, 8, 7, 6, 12, 7, 9, 4], lambda t: matches(t, [14, 4, 12, 3]))
    if q == 3:
        return fixed([8, 9, 11, 2, 5, 1, 6], lambda t: matches(t, [42, 6, 3]))
    if q == 4:
        return fixed([8, 21, 2, 13, 14, -12, 1, 6], lambda t: matches(t, [21, 1, -12, 5]) or matches(t, [-12, 5, 21, 1]))
    if q == 5:
        return fixed([31, -21, 63, 18, 44, 92], lambda t: matches(t, [92, 44, 18, 63, -21, 31]))
    if q == 6:
        return fixed([10, 37, 4, 23, 1, 8, 17, 2], lambda t: matches(t, [37, 23]))
    if q == 7:
        return fixed([4, 29, 6, 3, 29, 2, 2, 5, 29, 1, 29], lambda t: matches(t, [1, 4, 8, 3]) or matches(t, [3, 1, 4, 8]))
    if q == 8:
        return fixed([13, 5, 13, 7, 5, 2, 8, 13, 3, 2], lambda t: matches(t, [13, 5, 7, 2, 8, 3]))
    if q == 9:
        return [([1, 3, 5, 7, 9, 11], lambda t: 'crescente' in t and (not re.search('nao.*crescente', t))), ([1, 3, 5, 5, 7, 8], lambda t: bool(re.search('nao.*crescente|fals', t)))]
    if q == 10:
        return fixed([8, 6, 5, 4, 23, 7, 11, 12], lambda t: matches(t, [4, 23, 19]) or matches(t, [19, 4, 23]))
    if q == 11:
        a = flat(zip(names, notes))
        b = [f'{n}/{v}' for n, v in zip(names, notes)]
        return [([a, b], lambda t: all((n.lower() in t for n in names)) and pos(t, 'media', sum(notes) / 6) and pos(t, 'aprovados', 3) and pos(t, 'aprovados.*media', 3), 'variants')]
    if q == 12:
        return fixed([8, 1, 12, 4, 6, 10, 8], lambda t: matches(t, [7, 8]) or matches(t, [7, 6]))
    if q == 13:
        return fixed([23, 6, 17, 12, 7, 19, 18, 25, 24, 31], lambda t: matches(t, [6, 12, 18, 24, 23, 17, 7, 19, 25, 31]) and 'impar' in t)
    if q == 14:
        return fixed([18, 3, 52, 17, 24, 36, 41], lambda t: matches(t, [41, 18, 3, 52, 17, 24, 36]))
    if q == 15:
        a = [1, 3, 5, 3, 3, 2, 4, 3, 1, 2]
        return fixed(a, lambda t: matches(t, [1, 2, 2, 2, 3, 4, 4, 1, 5, 1]) or matches(t, [2, 2, 4, 1, 1]))
    if q == 16:
        return matrix(m9, 3, lambda t: matches(t, m9))
    if q == 17:
        return matrix(m12[:-1] + [10], 4, lambda t: all((pos(t, 'soma.*linha', v) for v in (10, 18, 19))) and line_index(t, 'maior', (2, 3)) and matches(t, m12[:-1] + [10]))
    if q == 18:
        return matrix(m9, 3, lambda t: matches(t, [7, 16, 17]) and line_index(t, 'maior', (2, 3)))
    if q == 19:
        return matrix(m16, 4, lambda t: matches(t, [2, 4, 13, 8]) and matches(t, [9, 10, -2, -4]) and matches(t, [27, 13]))
    if q == 20:
        return matrix(m16, 4, lambda t: pos(t, 'acima', 36) and pos(t, 'abaixo', 15))
    if q == 21:
        return matrix(m12, 4, lambda t: matches(t, [11, 1, 2]) or matches(t, [11, 2, 3]))
    if q == 22:
        return matrix(m12, 3, lambda t: matches(t, [7, 6, 11, 9, 11]))
    if q == 23:
        return matrix(m12, 3, lambda t: all((pos(t, f'coluna\\s*{i}', n) for i, n in enumerate([3, 2, 1]))) or matches(t, [3, 2, 1]))
    if q == 24:
        a = m16[:-1] + [7]
        return [([a + [7], [' '.join(map(str, l)) for l in chunks(a, 4)] + [7]], lambda t: matches(t, [0, 1, 3, 2, 3, 3, 3]) or matches(t, [1, 2, 4, 3, 4, 4, 3]), 'variants')]
    if q == 25:
        return matrix([1, 0, 0, 0, 1, 0, 0, 0, 1], 3, lambda t: 'identidade' in t and 'nao' not in t) + matrix(m9, 3, lambda t: 'identidade' in t and 'nao' in t)
    if q == 26:
        return matrix([1, 2, 3, 2, 4, 5, 3, 5, 6], 3, lambda t: 'simetrica' in t and 'nao' not in t) + matrix(m9, 3, lambda t: 'simetrica' in t and 'nao' in t)
    if q == 27:
        a = [6, 7, 8, 3, 4, 5, 8, 9, 10, 1, 2, 3, 4, 5, 6]
        return matrix(a, 3, lambda t: matches(t, [7, 4, 9, 2, 5]) and (matches(t, [2, 9]) or matches(t, [3, 9])))
    if q == 28:
        return matrix(m25, 5, lambda t: matches(t, [3, 6, 6]))
    if q == 29:
        l = list(map(sum, chunks(m16, 4)))
        c = list(map(sum, zip(*chunks(m16, 4))))
        return matrix(m16, 4, lambda t: matches(t, l) and matches(t, c) and ('maior' in t))
    if q == 30:
        return matrix([6, 4, 8, 3, 2, 9, 5, 1, 7], 3, lambda t: 'sela' in t and 'nao' not in t and matches(t, [4, 0, 1]) or ('sela' in t and 'nao' not in t and matches(t, [4, 1, 2])))
    if q == 31:
        return fixed([-8, 0, 12, -7, 9, 0], lambda t: all((word in t for word in ['negativo', 'positivo', 'zero'])) and matches(t, [-8, 0, 12, -7, 9, 0]))
    if q == 32:
        return fixed([-8, 21, 2, 13, 14, -12, 1, 6], lambda t: matches(t, [21]))
    if q == 33:
        return fixed([2, 3, 4, 8, 9, 10], lambda t: matches(t, [6, 8, 9, 10]))
    if q == 34:
        return fixed([4, 29, 6, 3, 29, 2, 2, 5, 29, 1, 29], lambda t: matches(t, [3]))
    if q == 35:
        return [([1, 3, 5, 7, 9, 11, 14], lambda t: 'crescente' in t and (not re.search('nao.*crescente', t))), ([1, 3, 5, 5, 7, 8, 9], lambda t: bool(re.search('nao.*crescente|fals', t)))]
    if q == 36:
        return matrix(m9, 3, lambda t: matches(t, [4, 21, 15]) and line_index(t, 'maior', (1, 2)))
    if q == 37:
        return matrix(m12, 4, lambda t: matches(t, [11]))
    if q == 38:
        return fixed([4, 6, 10, 8, 3, 5, 6, 2], lambda t: matches(t, [5.5, 4, 10]))
    if q == 39:
        scalar = flat(((name, *pair) for name, pair in zip(names, n39)))
        grouped = flat(((name, ' '.join(map(str, pair))) for name, pair in zip(names, n39)))
        return [([scalar, grouped], lambda t: all((n.lower() in t for n in names)) and bool(re.search('dante.*8|8.*dante', t)) and ('reprovado' in t) and ('aprovado' in t), 'variants')]
    if q == 40:
        expected = [''.join(('#' if r in (0, 8, 4) or c in (0, 8, 4) or r == c or (r + c == 8) else '.' for c in range(9))) for r in range(9)]
        return fixed([9, 9, 9], lambda t: ''.join(expected) in ''.join((l.replace(' ', '') for l in t.splitlines() if re.fullmatch('[ #.]+', l) and len(l.replace(' ', '')) == 9)))


def grade(q, s):
    if not s:
        return ['Em branco', 'Sem código']
    try:
        code, funcs = code_of(s)
    except SyntaxError as e:
        return ['Erro', f'{e.msg} (linha {e.lineno})']
    except PermissionError as e:
        return ['Rever', str(e)]
    if code is None:
        return ['Em branco', 'Sem instruções executáveis']
    notes = []
    for case in spec(q):
        variants, check = (case[0], case[1]) if len(case) > 2 else ([case[0]], case[1])
        outputs = [run(code, i) for i in variants]
        if not any((not e and check(t) for t, e in outputs)):
            valid = [t for t, e in outputs if not e]
            sample = valid[0] if valid else outputs[0][0]
            err = '' if valid else outputs[0][1]
            notes.append((err, sample))
    if notes:
        return ['Rever', ' / '.join(((e + ' | ' if e else '') + ' '.join(t.split())[:160] for e, t in notes))[:280]]
    if 31 <= q <= 39 and (not funcs):
        return ['Erro', 'Resultado compatível, mas sem uso de função própria']
    return ['Certa', 'Saída compatível com o(s) caso(s) testado(s)']
