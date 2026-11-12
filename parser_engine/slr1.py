"""
Parser SLR(1) (LR simple).

Implementa, segun el libro (Aho et al.):
  - Gramatica aumentada: S' -> S
  - Items LR(0) (produccion + posicion del punto)
  - Algoritmo CLOSURE(I) (LR(0))
  - Algoritmo GOTO(I, X)
  - Coleccion canonica LR(0) de estados
  - Construccion de tablas ACTION y GOTO (SLR(1), usando FOLLOW del ITEM 1)
  - Deteccion de conflictos Shift/Reduce y Reduce/Reduce
  - Analizador LR (Seccion 4.6.3): desplazamiento (SHIFT), reduccion (REDUCE), aceptacion (ACCEPT)

Reutiliza compute_follow del ITEM 1 (parser_engine.first_follow).

Convenciones del repositorio:
  - epsilon (e) se representa como 'e' (una produccion A -> e se trata como cuerpo vacio)
  - '$' es el marcador de fin de entrada
  - se genera un simbolo inicial aumentado S' que no colisiona con simbolos existentes
"""

from collections import deque

from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_follow

EPSILON = 'e'
END = '$'


class Item:
    """
    Item LR(0): [A -> alpha . beta]
    - head: no terminal a la izquierda
    - rhs: tupla de simbolos del cuerpo (vacia () para producciones epsilon)
    - dot: posicion del punto (0 .. len(rhs))
    """

    __slots__ = ('head', 'rhs', 'dot')

    def __init__(self, head, rhs, dot):
        self.head = head
        self.rhs = tuple(rhs)
        self.dot = dot

    def symbol_after_dot(self):
        if self.dot < len(self.rhs):
            return self.rhs[self.dot]
        return None

    def is_complete(self):
        return self.dot >= len(self.rhs)

    def __eq__(self, other):
        return (isinstance(other, Item) and
                self.head == other.head and
                self.rhs == other.rhs and
                self.dot == other.dot)

    def __hash__(self):
        return hash((self.head, self.rhs, self.dot))

    def __repr__(self):
        before = ' '.join(self.rhs[:self.dot])
        after = ' '.join(self.rhs[self.dot:])
        return f"[{self.head} -> {before} . {after}]".strip()


def symbol_order_by_first_appearance(grammar):
    """
    Devuelve una lista ordenada de simbolos (no terminales y terminales)
    segun su primera aparicion recorriendo grammar.producciones.
    Esto hace que la numeracion de estados (I0, I1, I2...) sea determinista.
    """
    seen = []
    for head, alts in grammar.productions.items():
        if head not in seen:
            seen.append(head)
        for alt in alts:
            for sym in alt:
                if sym != EPSILON and sym not in seen:
                    seen.append(sym)
    return seen


def _augmented_start_symbol(grammar):
    """
    Genera un simbolo inicial aumentado S' que no colisione con ningun
    simbolo existente (no terminales ni terminales).
    """
    existing = set(grammar.non_terminals) | set(grammar.terminals)
    candidate = "S'"
    while candidate in existing:
        candidate += "'"
    return candidate


def _normalize_rhs(alt):
    """
    Convierte una alternativa del repositorio (lista de simbolos, epsilon=['e'])
    en una tupla de cuerpo LR(0). Una produccion A -> e se representa como
    cuerpo vacio () porque epsilon no consume simbolos en la pila de estados.
    """
    if alt == [EPSILON] or alt == []:
        return ()
    return tuple(alt)


def closure(items, grammar):
    """
    CLOSURE(I) para items LR(0).

    - Parte de los items de I.
    - Para cada item [A -> alpha . B beta] donde B es no terminal,
      agrega [B -> . gamma] por cada produccion B -> gamma.
    - Repite hasta punto fijo; evita duplicados (usa un conjunto).
    """
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(closure_set):
            sym = item.symbol_after_dot()
            if sym is not None and sym in grammar.non_terminals:
                for prod_rhs in grammar.productions.get(sym, []):
                    new_item = Item(sym, _normalize_rhs(prod_rhs), 0)
                    if new_item not in closure_set:
                        closure_set.add(new_item)
                        changed = True
    return frozenset(closure_set)


def goto(items, symbol, grammar):
    """
    GOTO(I, X) para items LR(0).

    - Busca items cuyo punto precede al simbolo X.
    - Avanza el punto una posicion.
    - Aplica CLOSURE al conjunto resultante.
    """
    moved = set()
    for item in items:
        if item.symbol_after_dot() == symbol:
            moved.add(Item(item.head, item.rhs, item.dot + 1))
    if not moved:
        return None
    return closure(moved, grammar)


def canonical_collection(grammar):
    """
    Construye la coleccion canonica LR(0) partiendo de
    CLOSURE({[S' -> . S]}).

    Retorna:
      - states: lista de frozensets de Item (estados, sin duplicados)
      - transitions: dict {(estado_i, simbolo): estado_j}
      - aug_start: simbolo inicial aumentado
    """
    aug_start = _augmented_start_symbol(grammar)

    # Estado inicial: CLOSURE({[S' -> . S]})
    start_item = Item(aug_start, (grammar.start_symbol,), 0)
    states = [closure({start_item}, grammar)]
    state_index = {states[0]: 0}

    # Lista ordenada de simbolos (determinista: primera aparicion en la gramatica)
    all_symbols = symbol_order_by_first_appearance(grammar)

    transitions = {}
    # Cola FIFO para descubrir estados en orden de llegada (BFS)
    worklist = deque([0])

    while worklist:
        i = worklist.popleft()
        for sym in all_symbols:
            g = goto(states[i], sym, grammar)
            if g is None:
                continue
            if g not in state_index:
                state_index[g] = len(states)
                states.append(g)
                worklist.append(state_index[g])
            transitions[(i, sym)] = state_index[g]

    return states, transitions, aug_start


def build_slr_tables(grammar, first=None, follow=None):
    """
    Construye las tablas ACTION y GOTO SLR(1).

    Reglas:
      - Si existe [A -> alpha . a beta] y GOTO(Ii, a) = Ij:
            ACTION[i, a] = shift j
      - Si existe [A -> alpha .] (completo) y A no es el simbolo inicial aumentado:
            ACTION[i, b] = reduce A -> alpha  para cada b en FOLLOW(A)
      - Si existe [S' -> S .]: ACTION[i, '$'] = accept
      - Para no terminales: GOTO[i, A] = j segun las transiciones

    Detecta y documenta conflictos Shift/Reduce y Reduce/Reduce sin
    sobrescribir silenciosamente entradas conflictivas.

    Retorna un diccionario con:
      - states, transitions, aug_start
      - ACTION: {(estado, terminal): accion}  (accion = ('shift', j) | ('reduce', head, rhs) | ('accept',))
      - GOTO: {(estado, no_terminal): estado}
      - conflicts: lista de conflictos detectados
      - is_slr1: True si no hay conflictos
    """
    from parser_engine.first_follow import compute_first

    if follow is None:
        first = compute_first(grammar)
        follow = compute_follow(grammar, first)

    states, transitions, aug_start = canonical_collection(grammar)

    grammar_terminals = set()
    for alts in grammar.productions.values():
        for alt in alts:
            for sym in alt:
                if sym != EPSILON and sym not in grammar.non_terminals:
                    grammar_terminals.add(sym)

    ACTION = {}
    GOTO_TAB = {}
    conflicts = []

    for i, state in enumerate(states):
        # Transiciones hacia no terminales -> tabla GOTO
        for nt in grammar.non_terminals:
            j = transitions.get((i, nt))
            if j is not None:
                GOTO_TAB[(i, nt)] = j

        for item in state:
            sym = item.symbol_after_dot()

            # Caso 1: [A -> alpha . a beta] con a terminal -> shift
            if sym is not None and sym in grammar_terminals:
                j = transitions.get((i, sym))
                if j is not None:
                    action = ('shift', j)
                    key = (i, sym)
                    cell = ACTION.setdefault(key, [])
                    if action not in cell:
                        if cell:
                            existing = cell[0]
                            if existing[0] == 'shift' and action[0] == 'shift':
                                ctype = 'shift/shift'
                            else:
                                ctype = 'shift/reduce'
                            conflicts.append({
                                'state': i,
                                'symbol': sym,
                                'existing': list(cell),
                                'new': action,
                                'type': ctype,
                            })
                        cell.append(action)

            # Caso 2: [A -> alpha .] completo
            elif item.is_complete():
                if item.head == aug_start:
                    # [S' -> S .] -> accept en '$'
                    action = ('accept',)
                    key = (i, END)
                    cell = ACTION.setdefault(key, [])
                    if action not in cell:
                        if cell:
                            existing = cell[0]
                            conflicts.append({
                                'state': i,
                                'symbol': END,
                                'existing': list(cell),
                                'new': action,
                                'type': 'reduce/accept',
                            })
                        cell.append(action)
                else:
                    # Reduccion A -> alpha para cada b en FOLLOW(A)
                    for b in follow.get(item.head, set()):
                        action = ('reduce', item.head, item.rhs)
                        key = (i, b)
                        cell = ACTION.setdefault(key, [])
                        if action not in cell:
                            if cell:
                                existing = cell[0]
                                if existing[0] == 'shift' and action[0] == 'reduce':
                                    ctype = 'shift/reduce'
                                elif existing[0] == 'reduce' and action[0] == 'shift':
                                    ctype = 'shift/reduce'
                                elif existing[0] == 'reduce' and action[0] == 'reduce':
                                    ctype = 'reduce/reduce'
                                else:
                                    ctype = 'reduce/reduce'
                                conflicts.append({
                                    'state': i,
                                    'symbol': b,
                                    'existing': list(cell),
                                    'new': action,
                                    'type': ctype,
                                })
                            cell.append(action)

    is_slr1 = len(conflicts) == 0

    return {
        'states': states,
        'transitions': transitions,
        'aug_start': aug_start,
        'ACTION': ACTION,
        'GOTO': GOTO_TAB,
        'conflicts': conflicts,
        'is_slr1': is_slr1,
    }


def _item_string(item):
    return repr(item)


def format_reduce(head, rhs):
    """Devuelve una reduccion legible: 'A -> alpha' (epsilon como 'e')."""
    if rhs == () or rhs == (EPSILON,):
        body_str = EPSILON
    else:
        body_str = ' '.join(rhs)
    return f"{head} -> {body_str}"


def tokenize(input_string, terminals):
    """
    Convierte una cadena de entrada en lista de terminales.
    Coincide el terminal mas largo disponible en cada posicion.
    """
    tokens = []
    i = 0
    sorted_terms = sorted(terminals, key=len, reverse=True)
    n = len(input_string)
    while i < n:
        matched = False
        for t in sorted_terms:
            if input_string.startswith(t, i):
                tokens.append(t)
                i += len(t)
                matched = True
                break
        if not matched:
            tokens.append(input_string[i])
            i += 1
    return tokens


def slr_parse(grammar, tables, input_string, verbose=True):
    """
    Analizador LR / SLR(1) (Seccion 4.6.3).

    Usa:
      - Pila de estados.
      - Entrada terminada en '$'.
      - Tabla ACTION y tabla GOTO.

    Movimientos fundamentales: SHIFT, REDUCE, ACCEPT.
    Detecta errores sintacticos.

    Retorna (accepted, steps) donde steps es una lista de diccionarios con:
      - step, stack (estadoes), remaining (entrada), action
    """
    terminals = set()
    for alts in grammar.productions.values():
        for alt in alts:
            for sym in alt:
                if sym != EPSILON and sym not in grammar.non_terminals:
                    terminals.add(sym)

    ACTION = tables['ACTION']
    GOTO_TAB = tables['GOTO']

    tokens = tokenize(input_string, terminals) + [END]
    stack = [0]  # pila de estados, estado 0 en el fondo
    ip = 0
    steps = []
    step_no = 0
    # Cota de seguridad para evitar bucles infinitos.
    max_steps = 1000 * (len(tokens) + 1) + 100

    while True:
        if step_no >= max_steps:
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(tokens[ip:]),
                'action': "ERROR: bucle detectado (la gramatica no es SLR(1))",
            })
            return False, steps
        step_no += 1
        s = stack[-1]
        a = tokens[ip]
        remaining = tokens[ip:]

        action_list = ACTION.get((s, a))

        if action_list is None:
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': f"ERROR sintactico: ACTION[{s}, '{a}'] no definida",
            })
            return False, steps

        if len(action_list) > 1:
            # Conflicto en la celda: no se puede decidir una accion univoca
            pasos_accion = ", ".join(str(ac) for ac in action_list)
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': f"ERROR: conflicto en ACTION[{s}, '{a}']: {pasos_accion}",
            })
            return False, steps

        action = action_list[0]

        if action[0] == 'shift':
            j = action[1]
            stack.append(j)
            ip += 1
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': f"SHIFT '{a}', apilar estado {j}",
            })
            continue

        if action[0] == 'reduce':
            _, head, rhs = action
            k = len(rhs) if rhs != () else 0
            if k > 0:
                stack = stack[:-k]
            s2 = stack[-1]
            j = GOTO_TAB.get((s2, head))
            if j is None:
                steps.append({
                    'step': step_no,
                    'stack': list(stack),
                    'remaining': list(remaining),
                    'action': f"ERROR: no hay GOTO[{s2}, '{head}'] tras reduccion",
                })
                return False, steps
            stack.append(j)
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': f"REDUCE {format_reduce(head, rhs)} -> apilar estado {j}",
            })
            continue

        if action[0] == 'accept':
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': 'ACEPTAR: entrada valida',
            })
            return True, steps

        # No deberia llegar aqui
        steps.append({
            'step': step_no,
            'stack': list(stack),
            'remaining': list(remaining),
            'action': f"ERROR: accion desconocida {action}",
        })
        return False, steps