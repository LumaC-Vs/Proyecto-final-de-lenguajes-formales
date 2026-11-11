"""
Capa de reporte estructurado para el ITEM 3 (SDD).

Este modulo NO reimplementa el evaluador ni modifica la logica academica de
`parser_engine.sdd`. Reutiliza sus funciones y clases:

    - construir_arbol
    - numerar_nodos
    - GrafoDependencias
    - instanciar_reglas

y expone en estructuras JSON todo lo que el evaluador original calcula
internamente (arbol, arbol anotado, grafo de dependencias, orden topologico,
traza de evaluacion y ciclo). La evaluacion sigue exactamente el mismo orden
topologico y las mismas funciones lambda definidas en sdd.SDD; solo se
instrumenta para registrar los valores usados en cada paso.
"""

from parser_engine import sdd


# ---------------------------------------------------------------------------
# Metadatos descriptivos de la SDD del proyecto (documentacion, no resultados)
# ---------------------------------------------------------------------------
ATTR_MEANINGS = {
    ('S', 'val'): ('string', 'Resultado final del SDD: representacion textual de la lista.'),
    ('L', 'num'): ('int', 'Indice inicial del primer identificador de la lista.'),
    ('L', 'val'): ('string', 'Cadena formateada de la lista, o cadena vacia para e.'),
    ('M', 'num'): ('int', 'Indice del identificador actual.'),
    ('M', 'val'): ('string', 'Cadena formateada de los elementos desde el actual.'),
    ('R', 'num'): ('int', 'Indice del siguiente identificador del sufijo.'),
    ('R', 'val'): ('string', 'Cadena formateada del sufijo de elementos.'),
}

EXPRESSIONS = {
    ('S', 'L'): [
        'L.num = 1',
        'S.val = L.val',
    ],
    ('L', '[ M ]'): [
        'M.num = L.num',
        'L.val = "[" + M.val + "]"',
    ],
    ('L', 'e'): [
        'L.val = ""',
    ],
    ('M', 'id R'): [
        'R.num = M.num + 1',
        'M.val = M.num + ":" + id.lexval + R.val',
    ],
    ('M', 'e'): [
        'M.val = ""',
    ],
    ('R', '; id R'): [
        'R3.num = R.num + 1',
        'R.val = "; " + R3.num + ":" + id.lexval + R3.val',
    ],
    ('R', 'e'): [
        'R.val = ""',
    ],
}

_NATURE_ORDER = {'sintetizado': 0, 'heredado': 1, 'sintetizado (lexico)': 2}


def _body_list(body_str):
    return [] if body_str == 'e' else body_str.split()


def _rule_key_text(head, body_str):
    return f"{head} -> {body_str}"


# ---------------------------------------------------------------------------
# Tabla de atributos y reglas semanticas (derivadas de sdd.SDD)
# ---------------------------------------------------------------------------
def attribute_catalog(grammar=None):
    """
    Deriva la naturaleza (sintetizado/heredado) de cada atributo a partir de
    las reglas reales de sdd.SDD:
        - posicion 0  -> atributo sintetizado del lado izquierdo
        - posicion >0 -> atributo heredado del hijo en esa posicion
    """
    catalog = {}
    for (head, body_str), rules in sdd.SDD.items():
        body = _body_list(body_str)
        for rule in rules:
            pos, attr = rule['define']
            symbol = head if pos == 0 else body[pos - 1]
            nature = 'sintetizado' if pos == 0 else 'heredado'
            entry = catalog.setdefault(
                (symbol, attr),
                {'nature': nature, 'productions': set()},
            )
            entry['productions'].add(_rule_key_text(head, body_str))

    if grammar is not None:
        for terminal in sorted(getattr(grammar, 'terminals', set())):
            if terminal == 'e':
                continue
            catalog.setdefault(
                (terminal, 'lexval'),
                {'nature': 'sintetizado (lexico)', 'productions': set()},
            )
    return catalog


def attribute_table(grammar=None):
    """Tabla de atributos lista para serializar."""
    catalog = attribute_catalog(grammar)
    rows = []
    for (symbol, attr), info in catalog.items():
        attr_type, meaning = ATTR_MEANINGS.get(
            (symbol, attr),
            ('string' if attr == 'lexval' else 'desconocido', ''),
        )
        if attr == 'lexval':
            meaning = 'Lexema del token reconocido por el analizador lexico.'
        rows.append({
            'symbol': symbol,
            'attribute': attr,
            'type': attr_type,
            'nature': info['nature'],
            'meaning': meaning,
            'productions': sorted(info.get('productions', [])),
        })
    rows.sort(key=lambda r: (
        r['symbol'],
        r['attribute'],
    ))
    return rows


def semantic_rules():
    """Reglas semanticas reales de sdd.SDD con una expresion legible."""
    result = []
    for (head, body_str), rules in sdd.SDD.items():
        body = _body_list(body_str)
        expressions = EXPRESSIONS.get((head, body_str), [])
        items = []
        for index, rule in enumerate(rules):
            pos, attr = rule['define']
            dest_symbol = head if pos == 0 else body[pos - 1]
            uses = []
            for pos_u, attr_u in rule['usa']:
                src_symbol = head if pos_u == 0 else body[pos_u - 1]
                uses.append({
                    'symbol': src_symbol,
                    'attribute': attr_u,
                    'position': pos_u,
                })
            items.append({
                'define': {
                    'symbol': dest_symbol,
                    'attribute': attr,
                    'position': pos,
                    'nature': 'sintetizado' if pos == 0 else 'heredado',
                },
                'uses': uses,
                'expression': expressions[index] if index < len(expressions) else '',
            })
        result.append({
            'production': _rule_key_text(head, body_str),
            'head': head,
            'body': body,
            'rules': items,
        })
    return result


# ---------------------------------------------------------------------------
# Utilidades de arbol
# ---------------------------------------------------------------------------
def _collect_nodes(node, id_to_node):
    id_to_node[id(node)] = node
    for child in node.hijos:
        _collect_nodes(child, id_to_node)


def _serialize_tree(node, grammar):
    production = None
    if node.produccion:
        head, body = node.produccion
        body = list(body)
        body_str = ' '.join(body) if body != ['e'] else 'e'
        production = {
            'head': head,
            'body': body,
            'text': f"{head} -> {body_str}",
        }
    return {
        'id': node.indice,
        'symbol': node.simbolo,
        'production': production,
        'isTerminal': node.simbolo == 'e' or node.simbolo not in grammar.non_terminals,
        'attributes': {k: v for k, v in node.atributos.items()},
        'children': [_serialize_tree(child, grammar) for child in node.hijos],
    }


def _key_label(key, id_to_node):
    node = id_to_node.get(key[0])
    if node is None:
        return f"?{key[0]}.{key[1]}"
    return f"{node.simbolo}#{node.indice}.{key[1]}"


def _nature_for(symbol, attr, catalog):
    info = catalog.get((symbol, attr))
    if info:
        return info['nature']
    if attr == 'lexval':
        return 'sintetizado (lexico)'
    return 'sintetizado'


# ---------------------------------------------------------------------------
# Grafo de dependencias
# ---------------------------------------------------------------------------
def _serialize_graph(grafo, instancias, catalog, id_to_node):
    keys = set(instancias.keys())
    for dest, origins in grafo.aristas.items():
        keys.add(dest)
        keys.update(origins)

    nodes = []
    for key in keys:
        node = id_to_node.get(key[0])
        if node is None:
            continue
        attr = key[1]
        value = node.atributos.get(attr)
        nodes.append({
            'id': _key_label(key, id_to_node),
            'nodeId': node.indice,
            'symbol': node.simbolo,
            'attribute': attr,
            'nature': _nature_for(node.simbolo, attr, catalog),
            'value': value,
            'defined': key in instancias,
            'isLexical': attr == 'lexval',
        })
    nodes.sort(key=lambda n: (n['nodeId'], n['attribute']))

    seen = set()
    edges = []
    for dest, origins in grafo.aristas.items():
        for origin in origins:
            pair = (_key_label(origin, id_to_node), _key_label(dest, id_to_node))
            if pair in seen:
                continue
            seen.add(pair)
            edges.append({
                'from': pair[0],
                'to': pair[1],
                'label': '',
            })
    edges.sort(key=lambda e: (e['from'], e['to']))
    return {'nodes': nodes, 'edges': edges}


def _find_cycle(grafo):
    """
    Busca un ciclo siguiendo las dependencias (destino -> origenes).
    Devuelve la lista de claves que forman el ciclo, con el nodo inicial
    repetido al final, o None si el grafo es aciclico.
    """
    adj = {k: list(v) for k, v in grafo.aristas.items()}
    all_keys = set(adj.keys())
    for origins in adj.values():
        all_keys.update(origins)

    color = {}
    stack = []
    position = {}

    def dfs(node_key):
        color[node_key] = 1
        position[node_key] = len(stack)
        stack.append(node_key)
        for dep in adj.get(node_key, []):
            if color.get(dep, 0) == 0:
                found = dfs(dep)
                if found:
                    return found
            elif color.get(dep) == 1:
                start = position[dep]
                return stack[start:] + [dep]
        stack.pop()
        position.pop(node_key, None)
        color[node_key] = 2
        return None

    for key in sorted(all_keys, key=lambda k: (str(k[0]), str(k[1]))):
        if color.get(key, 0) == 0:
            found = dfs(key)
            if found:
                return found
    return None


# ---------------------------------------------------------------------------
# Evaluacion instrumentada (mismo orden y mismas funciones que sdd)
# ---------------------------------------------------------------------------
def _serialize_topo_order(orden, instancias, catalog, id_to_node):
    result = []
    step = 0
    for key in orden:
        node = id_to_node.get(key[0])
        if node is None:
            continue
        defined = key in instancias
        if defined:
            step += 1
        result.append({
            'attribute': _key_label(key, id_to_node),
            'nodeId': node.indice,
            'symbol': node.simbolo,
            'attributeName': key[1],
            'nature': _nature_for(node.simbolo, key[1], catalog),
            'defined': defined,
            'evaluationStep': step if defined else None,
            'value': node.atributos.get(key[1]),
        })
    return result


def _evaluate_with_trace(orden, instancias, catalog, id_to_node):
    trace = []
    step = 0
    for key in orden:
        instance = instancias.get(key)
        if instance is None:
            continue
        step += 1
        node = instance['nodo']
        depends = []
        values = []
        for dep_node, dep_attr in instance['usa']:
            value = dep_node.atributos.get(dep_attr)
            values.append(value)
            depends.append({
                'attribute': _key_label((id(dep_node), dep_attr), id_to_node),
                'nodeId': dep_node.indice,
                'symbol': dep_node.simbolo,
                'attributeName': dep_attr,
                'value': value,
            })
        result = instance['funcion'](*values)
        node.atributos[instance['attr']] = result
        trace.append({
            'step': step,
            'attribute': _key_label(key, id_to_node),
            'nodeId': node.id if hasattr(node, 'id') else node.indice,
            'symbol': node.simbolo,
            'attributeName': instance['attr'],
            'nature': _nature_for(node.simbolo, instance['attr'], catalog),
            'dependsOn': depends,
            'valuesUsed': values,
            'result': result,
        })
    return trace


# ---------------------------------------------------------------------------
# Punto de entrada del reporte
# ---------------------------------------------------------------------------
def build_report(grammar, table, input_string):
    """
    Ejecuta el pipeline del SDD reutilizando sdd.construir_arbol,
    sdd.numerar_nodos, sdd.GrafoDependencias, sdd.instanciar_reglas y
    sdd.GrafoDependencias.orden_topologico, y devuelve un reporte completo.
    """
    raiz, ok = sdd.construir_arbol(grammar, table, input_string)
    if not ok or raiz is None:
        return {
            'accepted': False,
            'circular': False,
            'message': 'La cadena no pertenece al lenguaje generado por la gramatica.',
            'tree': None,
            'graph': {'nodes': [], 'edges': []},
            'topoOrder': [],
            'trace': [],
            'finalValue': None,
            'cycle': [],
        }

    sdd.numerar_nodos(raiz)

    grafo = sdd.GrafoDependencias()
    instancias = {}
    sdd.instanciar_reglas(raiz, grafo, instancias)

    id_to_node = {}
    _collect_nodes(raiz, id_to_node)

    catalog = attribute_catalog(grammar)
    order_keys = list(instancias.keys())
    orden = grafo.orden_topologico(order_keys)

    if orden is None:
        cycle_keys = _find_cycle(grafo) or []
        cycle_labels = [_key_label(key, id_to_node) for key in cycle_keys]
        graph = _serialize_graph(grafo, instancias, catalog, id_to_node)
        return {
            'accepted': True,
            'circular': True,
            'message': (
                'El grafo de dependencias contiene un ciclo: la SDD es circular '
                'para este arbol. La evaluacion se detiene.'
            ),
            'tree': _serialize_tree(raiz, grammar),
            'graph': graph,
            'topoOrder': [],
            'evaluationOrder': [],
            'trace': [],
            'finalValue': None,
            'cycle': cycle_labels,
            'cycleMessage': ' -> '.join(cycle_labels) if cycle_labels else '',
        }

    trace = _evaluate_with_trace(orden, instancias, catalog, id_to_node)
    graph = _serialize_graph(grafo, instancias, catalog, id_to_node)
    topo_order = _serialize_topo_order(orden, instancias, catalog, id_to_node)
    evaluation_order = [item['attribute'] for item in topo_order if item['defined']]

    return {
        'accepted': True,
        'circular': False,
        'message': 'El grafo de dependencias es aciclico; la evaluacion se completo.',
        'tree': _serialize_tree(raiz, grammar),
        'graph': graph,
        'topoOrder': topo_order,
        'evaluationOrder': evaluation_order,
        'trace': trace,
        'finalValue': raiz.atributos.get('val'),
        'finalAttribute': f"{raiz.simbolo}.val",
        'cycle': [],
        'cycleMessage': '',
        'ruleCount': len(instancias),
    }
