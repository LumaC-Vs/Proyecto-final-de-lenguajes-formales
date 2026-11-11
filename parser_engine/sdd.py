from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first , compute_follow
from parser_engine import ll1

SDD = {
    ('S', 'L'): [
        {'define': (1, 'num'), 'usa': [],           'funcion': lambda: 1},
        {'define': (0, 'val'), 'usa': [(1, 'val')], 'funcion': lambda v: v},
    ],
    ('L', '[ M ]'): [
        {'define': (2, 'num'), 'usa': [(0, 'num')], 'funcion': lambda n: n},
        {'define': (0, 'val'), 'usa': [(2, 'val')], 'funcion': lambda v: f"[{v}]"},
    ],
    ('L', 'e'): [
        {'define': (0, 'val'), 'usa': [], 'funcion': lambda: ""},
    ],
    ('M', 'id R'): [
        {'define': (2, 'num'), 'usa': [(0, 'num')], 'funcion': lambda n: n + 1},
        {'define': (0, 'val'), 'usa': [(0, 'num'), (1, 'lexval'), (2, 'val')],
         'funcion': lambda n, x, v: f"{n}:{x}{v}"},
    ],
    ('M', 'e'): [
        {'define': (0, 'val'), 'usa': [], 'funcion': lambda: ""},
    ],
    ('R', '; id R'): [
        {'define': (3, 'num'), 'usa': [(0, 'num')], 'funcion': lambda n: n + 1},
        {'define': (0, 'val'), 'usa': [(0, 'num'), (2, 'lexval'), (3, 'val')],
         'funcion': lambda n, x, v: f"; {n}:{x}{v}"},
    ],
    ('R', 'e'): [
        {'define': (0, 'val'), 'usa': [], 'funcion': lambda: ""},
    ],
}

class Nodo:
    def __init__(self, simbolo, produccion = None):
        self.simbolo = simbolo
        self.produccion = produccion 
        self.hijos = []
        self.atributos = {}
        self.indice = 0

    def agregar_hijo(self, nodo):
        self.hijos.append(nodo)

    def __repr__(self):
        return f"nodo({self.simbolo})"

def construir_arbol(grammar, table, input_string):
    if input_string.strip() == 'e':
        input_string = ''
    non_terminals = grammar.non_terminals
    terminals = ll1.get_real_terminals(grammar)
    tokens = ll1.tokenize(input_string, terminals) + ['$']
    
    tokens_limpios = []
    lexemas = []
    for t in tokens:
        if t.isalpha() and t not in non_terminals and t != 'e':
            tokens_limpios.append ('id')
            lexemas.append(t)
        elif t.strip() != "":
            tokens_limpios.append(t)
            lexemas.append(t)
    tokens = tokens_limpios

    raiz = Nodo(grammar.start_symbol)
    stack = [Nodo('$'), raiz]
    ip = 0 

    while True:
        X = stack[-1]
        a = tokens[ip]

        if X.simbolo == '$' and a == '$':
            return raiz, True

        if X.simbolo in terminals or X.simbolo == '$':
            if X.simbolo == a:
                X.atributos['lexval'] = lexemas[ip]
                stack.pop()
                ip += 1
            else:
                return None, False

        elif X.simbolo in non_terminals: 
            cell = table.get(X.simbolo, {}).get(a, [])
            if not cell:
               return None, False

            alt = cell[0]
            X.produccion = (X.simbolo, alt)
            stack.pop()

            if alt != ['e'] and alt != []:
                nodos_hijos = [Nodo(s) for s in alt]
                for h in nodos_hijos:
                    X.agregar_hijo(h)
                for h in reversed(nodos_hijos):
                    stack.append(h)
            else:
                X.agregar_hijo(Nodo('e'))
        else: 
           return None, False

class GrafoDependencias:
    def __init__(self):
        self.aristas = {}

    def agregar_dependencias(self, nodo_origen, attr_origen, nodo_destino, attr_destino):
            origen = (id(nodo_origen), attr_origen)
            destino = (id(nodo_destino), attr_destino)

            if destino not in self.aristas:
                self.aristas[destino] = []
            self.aristas[destino].append(origen)

    def orden_topologico(self, todos_los_atributos):
        visitados = set()
        en_proceso = set()
        orden = []

        def visitar(nodo_attr):
            if nodo_attr in visitados:
                return True
            if nodo_attr in en_proceso:
                return False
            en_proceso.add(nodo_attr)

            for dep in self.aristas.get(nodo_attr, []):
                if not visitar(dep):
                    return False
            en_proceso.discard(nodo_attr)
            visitados.add(nodo_attr)
            orden.append(nodo_attr)
            return True

        for attr in todos_los_atributos:
            if not visitar(attr):
                return None
        return orden

def numerar_nodos(nodo, contador=None):
    if contador is None:
        contador = [0]
    contador[0] += 1
    nodo.indice = contador[0]
    for hijo in nodo.hijos:
        numerar_nodos(hijo, contador)

def instanciar_reglas(nodo, grafo, instancias):
    if not nodo.hijos:
        return

    prod = nodo.produccion
    if not prod:
        return

    cabeza, cuerpo = prod
    prod_str = " ".join(cuerpo) if cuerpo != ['e'] else "e"

    for regla in SDD.get((cabeza, prod_str), []):
        pos, attr = regla['define']
        destino = nodo if pos == 0 else nodo.hijos[pos -1]
        usados = []
        for pos_u, attr_u in regla['usa']:
            origen = nodo if pos_u == 0 else nodo.hijos[pos_u - 1]
            grafo.agregar_dependencias(origen, attr_u, destino, attr)
            usados.append((origen, attr_u))
        instancias[(id(destino), attr)] = {
            'nodo': destino,
            'attr': attr,
            'usa': usados,
            'funcion': regla['funcion'],
        }

    for hijo in nodo.hijos:
        instanciar_reglas(hijo, grafo, instancias)

def evaluar_en_orden(orden, instancias):
    evaluados = []
    for clave in orden:
        inst = instancias.get(clave)
        if inst is None:
            continue
        valores = [n.atributos[a] for n, a in inst['usa']]
        inst['nodo'].atributos[inst['attr']] = inst['funcion'](*valores)
        evaluados.append(f"{inst['nodo'].simbolo}#{inst['nodo'].indice}.{inst['attr']}")
    return evaluados

def imprimir_arbol(nodo, nivel = 0):
    indent = "  " * nivel
    attrs = ", ".join(f"{k}={v}" for k, v in nodo.atributos.items())
    print(f"{indent}{nodo.simbolo}#{nodo.indice} [{attrs}]")
    for hijo in nodo.hijos:
        imprimir_arbol(hijo, nivel + 1)

def evaluar_sdd(grammar, table, input_string):
    raiz, ok = construir_arbol(grammar, table, input_string)
    if not ok:
        return False, None, None

    numerar_nodos(raiz)

    grafo = GrafoDependencias()
    instancias = {}
    instanciar_reglas(raiz, grafo, instancias)

    orden = grafo.orden_topologico(list(instancias.keys()))
    if orden is None:
        return True, raiz, None

    evaluados = evaluar_en_orden(orden, instancias)

    return True, raiz, evaluados
