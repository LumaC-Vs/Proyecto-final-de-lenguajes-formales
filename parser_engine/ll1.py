"""
Parser LL(1) no recursivo.

Implementa, segun el libro (Aho et al.):
  - Seccion 4.4.3: verificacion exacta de la condicion LL(1).
  - Seccion 4.4.4: construccion de la tabla predictiva M[A, a].
  - Seccion 4.4.4: algoritmo de analisis predictivo no recursivo dirigido por tabla.

Reutiliza las funciones del ITEM 1 (parser_engine.first_follow):
  - compute_first(grammar)  -> FIRST de simbolos y de cadenas
  - compute_follow(grammar, first) -> FOLLOW de no terminales

Convenciones del repositorio:
  - epsilon (e) se representa como 'e'
  - '$' es el marcador de fin de entrada
  - los no terminales se identifican por pertencia a grammar.non_terminals
"""

from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow

EPSILON = 'e'
END = '$'


def get_real_terminals(grammar):
    """
    Devuelve el conjunto de terminales reales de la gramatica.
    Un simbolo es terminal si aparece en alguna produccion, no es epsilon
    y no pertenece al conjunto de no terminales.

    Nota: se calcula por pertenencia a non_terminals en lugar de confiar
    directamente en grammar.terminales, porque en el parsing del ITEM 1
    los no terminales con prima (p. ej. E') pueden acabar etiquetados como
    terminales por error. Asi se evitan columnas incorrectas en la tabla.
    """
    non_terminals = grammar.non_terminals
    terminals = set()
    for alts in grammar.productions.values():
        for alt in alts:
            for sym in alt:
                if sym != EPSILON and sym not in non_terminals:
                    terminals.add(sym)
    return terminals


def first_of_string(symbols, first):
    """
    Calcula FIRST de una cadena completa de simbolos (lista/tupla).
    Regla: FIRST(X1...Xk) incluye FIRST(Xi) - {e} mientras todos los
    simbolos previos deriven epsilon; si toda la cadena deriva epsilon,
    se añade 'e'.
    """
    result = set()
    all_derive_epsilon = True
    for sym in symbols:
        sym_first = first.get(sym, {sym})
        result.update(sym_first - {EPSILON})
        if EPSILON not in sym_first:
            all_derive_epsilon = False
            break
    if all_derive_epsilon:
        result.add(EPSILON)
    return result


def is_ll1(grammar, first, follow):
    """
    Verifica la condicion LL(1) (Seccion 4.4.3) sin transformar la gramatica.

    Para cada no terminal A con producciones A -> alpha1 | ... | alphan:
      - FIRST(alphai) INTERSECCION FIRST(alphaj) = vacio   (i != j)
      - Si epsilon pertenece a FIRST(alphai):
            FIRST(alphaj) INTERSECCION FOLLOW(A) = vacio
      - Si epsilon pertenece a FIRST(alphaj):
            FIRST(alphai) INTERSECCION FOLLOW(A) = vacio

    Retorna (es_ll1, conflictos) donde conflictos es una lista de diccionarios
    que describen cada conflicto encontrado. No se elimina recursión izquierda
    ni se realiza factorizacion izquierda.
    """
    conflicts = []
    for A, alts in grammar.productions.items():
        n = len(alts)
        for i in range(n):
            for j in range(i + 1, n):
                alpha_i = alts[i]
                alpha_j = alts[j]
                first_i = first_of_string(alpha_i, first)
                first_j = first_of_string(alpha_j, first)

                # Condicion 1: FIRST(ai) interseccion FIRST(aj) = vacio
                inter = first_i & first_j
                if inter:
                    conflicts.append({
                        'non_terminal': A,
                        'prod_i': list(alpha_i),
                        'prod_j': list(alpha_j),
                        'symbols': sorted(inter),
                        'type': 'FIRST/FIRST',
                    })

                # Condicion 2: si epsilon en FIRST(ai) -> FIRST(aj) interseccion FOLLOW(A) = vacio
                if EPSILON in first_i:
                    inter_follow = first_j & follow.get(A, set())
                    if inter_follow:
                        conflicts.append({
                            'non_terminal': A,
                            'prod_i': list(alpha_i),
                            'prod_j': list(alpha_j),
                            'symbols': sorted(inter_follow),
                            'type': 'FIRST/FOLLOW',
                        })

                # Condicion 3: si epsilon en FIRST(aj) -> FIRST(ai) interseccion FOLLOW(A) = vacio
                if EPSILON in first_j:
                    inter_follow = first_i & follow.get(A, set())
                    if inter_follow:
                        conflicts.append({
                            'non_terminal': A,
                            'prod_i': list(alpha_i),
                            'prod_j': list(alpha_j),
                            'symbols': sorted(inter_follow),
                            'type': 'FOLLOW/FIRST',
                        })

    return (len(conflicts) == 0), conflicts


def build_ll1_table(grammar, first, follow):
    """
    Construye la tabla predictiva LL(1) M[A, a].

    Para cada produccion A -> alpha:
      - Para cada terminal a en FIRST(alpha): M[A, a] += A -> alpha
      - Si epsilon pertenece a FIRST(alpha):
            para cada b en FOLLOW(A): M[A, b] += A -> alpha

    Retorna (table, conflicts) donde:
      - table: dict {A: {a: [producciones]}}; columnas = terminales U {'$'}
      - conflicts: lista de diccionarios con celdas que tienen mas de una
        produccion (conflictos LL(1)).
    """
    terminals = get_real_terminals(grammar) | {END}
    non_terminals = grammar.non_terminals

    table = {A: {a: [] for a in terminals} for A in non_terminals}
    conflicts = []

    for A, alts in grammar.productions.items():
        for alt in alts:
            first_alpha = first_of_string(list(alt), first)

            # Caso general: llenar con los terminales de FIRST(alpha)
            for a in (first_alpha - {EPSILON}):
                cell = table[A][a]
                if cell:
                    # Conflicto: ya existe al menos una produccion en esta celda
                    conflicts.append({
                        'non_terminal': A,
                        'terminal': a,
                        'existing': [list(c) for c in cell],
                        'new': list(alt),
                        'type': 'LL(1) tabla',
                    })
                cell.append(list(alt))

            # Caso epsilon: usar FOLLOW(A)
            if EPSILON in first_alpha:
                for b in follow.get(A, set()):
                    cell = table[A][b]
                    if cell:
                        conflicts.append({
                            'non_terminal': A,
                            'terminal': b,
                            'existing': [list(c) for c in cell],
                            'new': list(alt),
                            'type': 'LL(1) tabla',
                        })
                    cell.append(list(alt))

    return table, conflicts


def format_production(head, body):
    """Devuelve una produccion legible: 'A -> alpha' (epsilon como 'e')."""
    if body == [EPSILON] or body == []:
        body_str = EPSILON
    else:
        body_str = ' '.join(body)
    return f"{head} -> {body_str}"


def tokenize(input_string, terminals):
    """
    Convierte una cadena de entrada en lista de terminales.
    Coincide el terminal mas largo disponible en cada posicion (soporta
    terminales multicaracter como 'id'). Caracteres no reconocidos se
    emiten como un solo simbolo (el parser reportara error sintactico).
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


def ll1_parse(grammar, table, input_string, verbose=True):
    """
    Analizador predictivo no recursivo dirigido por tabla (Seccion 4.4.4).

    Usa una pila (tope al final de la lista) y una entrada terminada en '$'.
    Implementa: inicializacion de pila, comparacion tope/simbolo actual,
    reconocimiento de terminales, consulta de la tabla predictiva,
    aplicacion de producciones, manejo de epsilon, aceptacion y rechazo.

    Retorna (accepted, steps) donde steps es una lista de diccionarios con:
      - step: numero de paso
      - stack: contenido de la pila (fondo -> tope)
      - remaining: entrada restante
      - action: descripcion de la accion ejecutada
    """
    non_terminals = grammar.non_terminals
    terminals = get_real_terminals(grammar)

    tokens = tokenize(input_string, terminals) + [END]
    stack = [END, grammar.start_symbol]  # tope = ultimo elemento
    ip = 0
    steps = []
    step_no = 0
    # Cota de seguridad para evitar bucles infinitos en gramaticas que no
    # son LL(1) (al elegir una produccion de una celda con conflicto).
    max_steps = 1000 * (len(tokens) + 1) + 100

    while True:
        if step_no >= max_steps:
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(tokens[ip:]),
                'action': "ERROR: bucle detectado (la gramatica no es LL(1); no se puede dirigir por tabla)",
            })
            return False, steps
        step_no += 1
        X = stack[-1]
        a = tokens[ip]
        remaining = tokens[ip:]

        # Caso de aceptacion
        if X == END and a == END:
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': 'ACEPTAR: entrada valida',
            })
            return True, steps

        # X es terminal: reconocerlo si coincide con la entrada
        if X in terminals or X == END:
            if X == a:
                stack.pop()
                ip += 1
                steps.append({
                    'step': step_no,
                    'stack': list(stack),
                    'remaining': list(remaining),
                    'action': f"Hacer pop del terminal '{X}' (match)",
                })
                continue
            else:
                steps.append({
                    'step': step_no,
                    'stack': list(stack),
                    'remaining': list(remaining),
                    'action': f"ERROR sintactico: se esperaba '{X}' pero se encontro '{a}'",
                })
                return False, steps

        # X es no terminal: consultar tabla predictiva M[X, a]
        cell = table.get(X, {}).get(a, [])
        if not cell:
            steps.append({
                'step': step_no,
                'stack': list(stack),
                'remaining': list(remaining),
                'action': f"ERROR sintactico: no hay produccion para M[{X}, '{a}'] (celda vacia)",
            })
            return False, steps

        # Si hay mas de una produccion (conflicto), la gramatica no es LL(1);
        # se toma la primera para seguir ejecutando, pero se anota.
        alt = cell[0]
        if len(cell) > 1:
            action_desc = (f"PREDECIR {format_production(X, alt)} "
                           f"[CELDA CON CONFLICTO: {len(cell)} producciones]")
        else:
            action_desc = f"PREDECIR {format_production(X, alt)}"

        stack.pop()
        if alt != [EPSILON]:
            # Empujar el cuerpo en reversa para que alt[0> quede en el tope
            for sym in reversed(alt):
                stack.append(sym)

        steps.append({
            'step': step_no,
            'stack': list(stack),
            'remaining': list(remaining),
            'action': action_desc,
        })
