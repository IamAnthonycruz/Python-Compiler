# Skip whitespace and comments
def skip_space(s, idx):
    while True:
        save = idx
        while idx < len(s) and s[idx].isspace():
            idx += 1
        if idx < len(s) and s[idx] == ';':
            idx += 1
            while idx < len(s) and s[idx] != '\n':
                idx += 1
        if idx == save:
            break
    return idx

# Parse atoms into values or symbols
def parse_atom(s):
    import json
    try:
        return ['val', json.loads(s)]
    except json.JSONDecodeError:
        return s

# Recursive S-expression parser
def parse_expr(s, idx):
    idx = skip_space(s, idx)
    if s[idx] == '(':
        idx += 1
        l = []
        while True:
            idx = skip_space(s, idx)
            if idx >= len(s):
                raise Exception('unbalanced parenthesis')
            if s[idx] == ')':
                idx += 1
                break
            idx, v = parse_expr(s, idx)
            l.append(v)
        return idx, l
    elif s[idx] == ')':
        raise Exception('bad parenthesis')
    else:
        start = idx
        while idx < len(s) and (not s[idx].isspace()) and s[idx] not in '()':
            idx += 1
        if start == idx:
            raise Exception('empty program')
        return idx, parse_atom(s[start:idx])

def pl_parse(s):
    idx, node = parse_expr(s, 0)
    idx = skip_space(s, idx)
    if idx < len(s):
        raise ValueError('trailing garbage')
    return node

def pl_parse_prog(s):
    return pl_parse('(do ' + s + ')')

# Variable lookup through env chain
def name_lookup(env, key):
    while env:
        current, env = env
        if key in current:
            return current
    raise ValueError('undefined name')

# Expression evaluator with environment
def pl_eval(env, node):
    if not isinstance(node, list):
        assert isinstance(node, str)
        return name_lookup(env, node)[node]

    if len(node) == 2 and node[0] == 'val':
        return node[1]

    if node[0] in ('do', 'then', 'else') and len(node) > 1:
        new_env = (dict(), env)
        for val in node[1:]:
            val = pl_eval(new_env, val)
        return val

    if node[0] == 'var' and len(node) == 3:
        _, name, val = node
        scope, _ = env
        if name in scope:
            raise ValueError('duplicated name')
        val = pl_eval(env, val)
        scope[name] = val
        return val

    if node[0] == 'set' and len(node) == 3:
        _, name, val = node
        scope = name_lookup(env, name)
        val = pl_eval(env, val)
        scope[name] = val
        return val

    if len(node) in (3, 4) and node[0] == '?':
        _, cond, yes, *no = node
        no = no[0] if no else ['val', None]
        new_env = (dict(), env)
        return pl_eval(new_env, yes) if pl_eval(new_env, cond) else pl_eval(new_env, no)

    if node[0] == 'print':
        return print(*(pl_eval(env, val) for val in node[1:]))
    if len(node) in (3,4) and node[0] in('?' , 'if'):
        _, cond, yes, *no = node
        no = no[0] if no else ['val', None]
        new_env = (dict(), env)
        if pl_eval(new_env, cond):  
            return pl_eval(new_env, yes)
        else:
            return pl_eval(new_env, no)
    if node[0] == 'loop' and len(node) == 3:
        _, cond, body = node
        ret = None
        while True:
            new_env = (dict(), env)
            if not pl_eval(new_env, cond):
                break
            ret = pl_eval(new_env, body)
        return ret
    
    if node[0] == 'loop' and len(node) == 3:
        _, cond, body = node
        ret = None
        while True:
            new_env = (dict(), env)
            if not pl_eval(new_env, cond):
                break
            try:
                ret = pl_eval(new_env, body)
            except LoopBreak:
                break
            except LoopContinue:
                continue
        return ret
    if node[0] == 'break' and len(node) == 1:
        raise LoopBreak
    if node[0] == 'continue' and len(node) == 1:
        raise LoopContinue
    class LoopBreak(Exception):
        def __init__(self):
            super().__init__('break outside a loop')
    class LoopContinue(Exception):
        def __init__(self):
            super().__init__('continue outside a loop')

    import operator
    binops = {
        '+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv,
        'eq': operator.eq, 'ne': operator.ne, 'ge': operator.ge, 'gt': operator.gt,
        'le': operator.le, 'lt': operator.lt, 'and': operator.and_, 'or': operator.or_,
    }
    if len(node) == 3 and node[0] in binops:
        op = binops[node[0]]
        return op(pl_eval(env, node[1]), pl_eval(env, node[2]))

    unops = {
        '-': operator.neg, 'not': operator.not_,
    }
    if len(node) == 2 and node[0] in unops:
        op = unops[node[0]]
        return op(pl_eval(env, node[1]))

    raise ValueError('unknown expression')
    

# Testing helper
def test_eval():
    def f(s):
        return pl_eval(None, pl_parse_prog(s))

    assert f('''
        (var a 1)
        (var b (+ a 1))
        (do
            (var a (+ b 5))
            (set b (+ a 10))
        )
        (* a b)
    ''') == 17

# Run tests
test_eval()


