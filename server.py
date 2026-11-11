"""
Servidor web de demostración para el proyecto de Lenguajes Formales y Compiladores.

Reutiliza los algoritmos originales de parser_engine sin modificarlos:
  - parser_engine.grammar.Gramaica
  - parser_engine.first_follow (compute_first, compute_follow)  -> ITEM 1
  - parser_engine.ll1                                            -> ITEM 2A
  - parser_engine.slr1                                           -> ITEM 2B
  - parser_engine.sdd_report                                     -> ITEM 3

Las gramaticas se leen AUTOMATICAMENTE desde la carpeta gramaticas/
ubicada en la raiz del repositorio (ruta relativa robusta). No se solicita
carga manual de archivos al usuario.
"""

import os
import json
from flask import Flask, request, jsonify, render_template

from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow
from parser_engine import ll1, slr1
from parser_engine import sdd_report

app = Flask(__name__)

END = '$'
EPSILON = 'e'


# ---------------------------------------------------------------------------
# Descubrimiento automatico de gramaticas (ruta relativa a este archivo)
# ---------------------------------------------------------------------------
def _grammar_folder():
    """Devuelve la ruta absoluta a la carpeta gramaticas/ de este repositorio."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gramaticas')


def _safe_grammar_id(nombre_archivo):    # noqa: D401
    """Devuelve un identificador seguro a partir del nombre de archivo."""
    return os.path.splitext(nombre_archivo)[0]


def _load_grammar_file(filename):
    """Lee un archivo de gramatica y devuelve (Grammar, lineas_raw) o None si es invalido."""
    ruta = os.path.join(_grammar_folder(), filename)
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
    except OSError:
        return None
    try:
        g = Grammar(lineas)
    except Exception:
        return None
    if not g.productions or g.start_symbol is None:
        return None
    return g, lineas


def _discover_grammars():
    """Lista todas las gramaticas validas en gramaticas/."""
    carpeta = _grammar_folder()
    if not os.path.isdir(carpeta):
        return []
    resultado = []
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith('.txt'):
            continue
        cargado = _load_grammar_file(nombre)
        if cargado is None:
            continue
        g, _ = cargado
        gid = _safe_grammar_id(nombre)
        try:
            first = compute_first(g)
            follow = compute_follow(g, first)
            es_ll1, _ = ll1.is_ll1(g, first, follow)
            slr_tables = slr1.build_slr_tables(g, first, follow)
            es_slr1 = slr_tables['is_slr1']
        except Exception:
            es_ll1 = None
            es_slr1 = None
        resultado.append({
            'id': gid,
            'nombre': nombre,
            'archivo': nombre,
            'simbolo_inicial': g.start_symbol,
            'no_terminales': sorted(g.non_terminals),
            'terminales': sorted(g.terminals),
            'producciones': {k: [list(a) for a in v] for k, v in g.productions.items()},
            'es_ll1': es_ll1,
            'es_slr1': es_slr1,
        })
    return resultado


# Cache simple: se vuelve a descubrir en cada peticion para detectar
# gramaticas nuevas o modificadas sin reiniciar el servidor.
def listar_gramaticas():
    return _discover_grammars()


def obtener_gramatica(gid):
    for g in listar_gramaticas():
        if g['id'] == gid:
            return g
    return None


def cargar_gramatica_por_id(gid):
    """Devuelve (Grammar, first, follow) para un id, o None si no existe."""
    carpeta = _grammar_folder()
    for nombre in os.listdir(carpeta):
        if _safe_grammar_id(nombre) == gid:
            cargado = _load_grammar_file(nombre)
            if cargado is None:
                return None
            g, _ = cargado
            first = compute_first(g)
            follow = compute_follow(g, first)
            return g, first, follow
    return None


# ---------------------------------------------------------------------------
# Serializadores de resultados de SLR(1) (objetos no nativos de JSON)
# ---------------------------------------------------------------------------
def _item_to_str(item):
    return repr(item)


def _serialize_slr_tables(tables):
    estados = []
    for i, state in enumerate(tables['states']):        # state: frozenset[Item]
        items = [_item_to_str(it) for it in sorted(state, key=lambda it: (it.head, str(it.rhs), it.dot))]
        trans = {sym: j for (st, sym), j in tables['transitions'].items() if st == i}
        trans_desc = {str(k): v for k, v in trans.items()}
        estados.append({
            'indice': i,
            'items': items,
            'transiciones': trans_desc,
        })

    action_serializable = {}
    for (estado, simbolo), acciones in tables['ACTION'].items():
        key = f"{estado}|{simbolo}"
        action_serializable[key] = [_accion_to_str(a) for a in acciones]

    goto_serializable = {}
    for (estado, no_terminal), destino in tables['GOTO'].items():
        key = f"{estado}|{no_terminal}"
        goto_serializable[key] = destino

    return {
        'estados': estados,
        'transiciones': {f"{i}|{sym}": j for (i, sym), j in tables['transitions'].items()},
        'simbolo_aumento': tables['aug_start'],
        'ACTION': action_serializable,
        'GOTO': goto_serializable,
        'conflictos': tables['conflicts'],
        'es_slr1': tables['is_slr1'],
    }


def _accion_to_str(accion):
    tipo = accion[0]
    if tipo == 'shift':
        return {'tipo': 'shift', 'estado': accion[1]}
    if tipo == 'reduce':
        _, head, rhs = accion
        cuerpo = 'e' if rhs == () or rhs == (EPSILON,) else ' '.join(rhs)
        return {'tipo': 'reduce', 'produccion': f"{head} -> {cuerpo}"}
    if tipo == 'accept':
        return {'tipo': 'accept'}
    return {'tipo': str(tipo)}


# ---------------------------------------------------------------------------
# Rutas de vistas (frontend)
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/item1')
def item1():
    return render_template('item1.html')


@app.route('/item2')
def item2():
    return render_template('item2.html')


@app.route('/item3')
def item3():
    return render_template('item3.html')


# ---------------------------------------------------------------------------
# API: gramaticas
# ---------------------------------------------------------------------------
@app.route('/api/grammars', methods=['GET'])
def api_listar_gramaticas():
    return jsonify({'gramaticas': listar_gramaticas()})


@app.route('/api/grammars/<gid>', methods=['GET'])
def api_detalle_gramatica(gid):
    g = obtener_gramatica(gid)
    if g is None:
        return jsonify({'error': f'Gramatica no encontrada: {gid}'}), 404
    return jsonify(g)


# ---------------------------------------------------------------------------
# API: ITEM 1 - FIRST y FOLLOW
# ---------------------------------------------------------------------------
@app.route('/api/first-follow', methods=['POST'])
def api_first_follow():
    data = request.get_json(silent=True) or {}
    gid = data.get('grammar_id')
    cargado = cargar_gramatica_por_id(gid)
    if cargado is None:
        return jsonify({'error': f'Gramatica no encontrada o invalida: {gid}'}), 400
    g, first, follow = cargado

    producciones = []
    for cabeza, alts in g.productions.items():
        for alt in alts:
            cuerpo = 'e' if alt == [] or alt == ['e'] else ' '.join(alt)
            producciones.append({'cabeza': cabeza, 'cuerpo': cuerpo})

    first_serializable = {nt: sorted(list(vals)) for nt, vals in first.items()}
    follow_serializable = {
        nt: sorted(list(vals), key=lambda x: (x != END, x))
        for nt, vals in follow.items()
    }

    return jsonify({
        'gramatica': gid,
        'simbolo_inicial': g.start_symbol,
        'no_terminales': sorted(g.non_terminals),
        'terminales': sorted(g.terminals),
        'producciones': producciones,
        'first': first_serializable,
        'follow': follow_serializable,
    })


# ---------------------------------------------------------------------------
# API: ITEM 2A - LL(1)
# ---------------------------------------------------------------------------
@app.route('/api/ll1', methods=['POST'])
def api_ll1():
    data = request.get_json(silent=True) or {}
    gid = data.get('grammar_id')
    entrada = data.get('input', '')
    cargado = cargar_gramatica_por_id(gid)
    if cargado is None:
        return jsonify({'error': f'Gramatica no encontrada o invalida: {gid}'}), 400
    g, first, follow = cargado

    es_ll1, conflictos = ll1.is_ll1(g, first, follow)
    tabla, conflictos_tabla = ll1.build_ll1_table(g, first, follow)

    # Tabla serializable: {A: {a: [producciones]}}
    tabla_serializable = {}
    for A in sorted(tabla.keys()):
        tabla_serializable[A] = {}
        for a in sorted(tabla[A].keys()):
            celdas = tabla[A][a]
            tabla_serializable[A][a] = [
                ('e' if alt == [] or alt == ['e'] else ' '.join(alt)) for alt in celdas
            ]

    resultado = {
        'gramatica': gid,
        'es_ll1': es_ll1,
        'conflictos': conflictos,
        'tabla': tabla_serializable,
        'terminales': sorted(ll1.get_real_terminals(g) | {END}),
        'no_terminales': sorted(g.non_terminals),
    }

    if entrada is not None:
        aceptado, pasos = ll1.ll1_parse(g, tabla, entrada, verbose=True)
        resultado['simulacion'] = {
            'entrada': entrada,
            'aceptado': aceptado,
            'pasos': pasos,
        }

    return jsonify(resultado)


# ---------------------------------------------------------------------------
# API: ITEM 2B - SLR(1)
# ---------------------------------------------------------------------------
@app.route('/api/slr1', methods=['POST'])
def api_slr1():
    data = request.get_json(silent=True) or {}
    gid = data.get('grammar_id')
    entrada = data.get('input', '')
    cargado = cargar_gramatica_por_id(gid)
    if cargado is None:
        return jsonify({'error': f'Gramatica no encontrada o invalida: {gid}'}), 400
    g, first, follow = cargado

    tablas = slr1.build_slr_tables(g, first, follow)
    resultado = {
        'gramatica': gid,
        'simbolo_aumento': tablas['aug_start'],
        'es_slr1': tablas['is_slr1'],
        'conflictos': tablas['conflicts'],
        'num_estados': len(tablas['states']),
    }
    resultado.update(_serialize_slr_tables(tablas))

    if entrada is not None:
        aceptado, pasos = slr1.slr_parse(g, tablas, entrada, verbose=True)
        resultado['simulacion'] = {
            'entrada': entrada,
            'aceptado': aceptado,
            'pasos': pasos,
        }

    return jsonify(resultado)


# ---------------------------------------------------------------------------
# API: ITEM 3 - SDD
# ---------------------------------------------------------------------------
@app.route('/api/sdd', methods=['POST'])
def api_sdd():
    data = request.get_json(silent=True) or {}
    gid = data.get('grammar_id')
    entrada = data.get('input', '')
    cargado = cargar_gramatica_por_id(gid)
    if cargado is None:
        return jsonify({'error': f'Gramatica no encontrada o invalida: {gid}'}), 400
    g, first, follow = cargado

    # El SDD del proyecto reutiliza la tabla LL(1) para construir el arbol.
    tabla_ll1, _ = ll1.build_ll1_table(g, first, follow)
    reporte = sdd_report.build_report(g, tabla_ll1, entrada)
    reporte['gramatica'] = gid
    reporte['entrada'] = entrada
    reporte['reglas_semanticas'] = sdd_report.semantic_rules()
    reporte['tabla_atributos'] = sdd_report.attribute_table(g)
    return jsonify(reporte)


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
