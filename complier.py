def skip_space(s, idx):
    while True:
        save = idx
        while idx < len(s) and s[idx].isspace():
            idx += 1
        if idx < len(s) and s[idx] ==';':
            idx += 1
            while idx < len(s) and s[idx] != '\n':
                idx+=1
        if idx == save:
            break
    return idx
def parse_atom(s):
    import json
    try: 
        return ['val', json.loads(s)]
    except json.JSONDecodeError:
            return s
def parse_expr(s: str, idx: int):
    idx = skip_space(s, idx)
    if s[idx] == '(':
        idx += 1
        l = []
        while True:
            idx = skip_space(s, idx)
            if idx >= len(s):
                raise Exception('Unbalanced parenthesis')
            if s[idx] == ')':
                idx += 1
                break
            idx, v = parse_expr(s, idx)
            l.append(v)
        return idx, l
    elif s[idx] == ')':
        raise Exception('Bad parenthesis')
    else:
        start = idx
        while idx < len(s) and (not s[idx].isspace()) and s[idx] not in '()':
            idx +=1
        if start == idx:
            raise Exception('Bad token')
        return idx, parse_atom(s[start: idx])
def pl_parse(s):
    idx, node = parse_expr(s,0)
    idx = skip_space(s, idx)
    if idx < len(s):
        raise ValueError('trailing garbage')
    return node
def pl_eval(node):
    if len(node) ==  0:
        raise ValueError('empty expression')
    if len(node) == 2 and node[0] == 'val':
        return node[1]
    import operator
    binops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        'eq': operator.eq,
        'ne': operator.ne,
        'lt': operator.lt,
        'le': operator.le,
        'gt': operator.gt,
        'ge': operator.ge,
        'and': operator.and_,
        'or': operator.or_,
    }
    if len(node) == 3 and node[0] in binops:
        op = binops[node[0]]
        return op(pl_eval(node[1]), pl_eval(node[2]))
    unops =  {
        '-': operator.neg,
        'not': operator.not_,
    }
    if len(node) == 2 and node[0] in unops:
        op = unops[node[0]]
        return op(pl_eval(node[1]))
    if len(node) == 4 and node[0] == '?':
        _, cond, yes, no = node
        if pl_eval(cond):
            return pl_eval(yes)
        else:
            return pl_eval(no)
    if(node[0] == 'print'):
        return print(*(pl_eval(val) for val in node[1:]))
    raise ValueError('invalid expression')