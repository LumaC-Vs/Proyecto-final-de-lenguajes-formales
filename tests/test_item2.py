"""
Pruebas automatizadas del ITEM 2 (parsers LL(1) y SLR(1)).

Reutiliza las funciones del ITEM 1 (compute_first / compute_follow) y no
utiliza generadores de parsers ni librerias externas.

Ejecuta con:  python test_item2.py
"""

from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow
from parser_engine import ll1, slr1


def build(lines):
    g = Grammar(lines)
    first = compute_first(g)
    follow = compute_follow(g, first)
    return g, first, follow


# ---------------------------------------------------------------------------
# Gramaticas de prueba (archivos están en la raiz del proyecto; aqui se
# definen inline para que las pruebas sean autocontenidas).
# ---------------------------------------------------------------------------
GRAMS = {
    # Escenario 1: LL(1) y SLR(1) (gramatica de expresiones, Ejemplo 4.28 Aho)
    "expr": [
        "5",
        "E -> T E'",
        "E' -> + T E' | e",
        "T -> F T'",
        "T' -> * F T' | e",
        "F -> ( E ) | id",
    ],
    # Escenario 1: LL(1) y SLR(1), con produccion epsilon
    "epsilon": [
        "2",
        "S -> a A | e",
        "A -> b",
    ],
    # Escenario 2: LL(1), pero NO SLR(1)
    "ll_only": [
        "2",
        "S -> e | A b A",
        "A -> e | a a b",
    ],
    # Escenario 3: SLR(1), pero NO LL(1) (recursividad izquierda)
    "leftrec": [
        "2",
        "S -> S + T | T",
        "T -> id",
    ],
    # Escenario 4: NO LL(1) ni SLR(1) (conflicto shift/reduce, else)
    "dangling": [
        "2",
        "S -> i E t S | i E t S else S | a",
        "E -> b",
    ],
    # Escenario 4: NO LL(1) ni SLR(1) (conflicto reduce/reduce)
    "rr": [
        "3",
        "S -> A | B",
        "A -> a",
        "B -> a",
    ],
}

results = []


def check(name, condition, detail=""):
    status = "OK" if condition else "FALLO"
    results.append((name, condition, detail))
    print(f"[{status}] {name}" + (f"  ({detail})" if detail and not condition else ""))


# ---------------------------------------------------------------------------
# 1. Integracion FIRST/FOLLOW (ITEM 1 sigue funcionando)
# ---------------------------------------------------------------------------
g, first, follow = build(GRAMS["expr"])
check("compute_first devuelve dict", isinstance(first, dict))
check("compute_follow devuelve dict", isinstance(follow, dict))
check("S tiene First", "S" in first)
check("S tiene Follow", "S" in follow)
check("'$' en Follow(S)", "$" in follow[g.start_symbol])
check("epsilon representado como 'e'", ll1.EPSILON == "e")
check("fin de entrada representado como '$'", ll1.END == "$")

# ---------------------------------------------------------------------------
# 2. LL(1)
# ---------------------------------------------------------------------------
# 2a. Gramatica LL(1)
es_ll1, llc = ll1.is_ll1(g, first, follow)
check("expr es LL(1)", es_ll1 is True, f"conflictos={llc}")

# 2b. Gramatica que NO es LL(1)
gl, fll, fow = build(GRAMS["leftrec"])
es_ll1_lr, _ = ll1.is_ll1(gl, fll, fow)
check("leftrec NO es LL(1)", es_ll1_lr is False)

# 2c. Gramatica con produccion epsilon es LL(1)
ge, fee, foe = build(GRAMS["epsilon"])
es_ll1_eps, _ = ll1.is_ll1(ge, fee, foe)
check("epsilon-gram es LL(1)", es_ll1_eps is True)

# 2d. Tabla LL(1) tiene celdas y columnas con '$'
table, tconf = ll1.build_ll1_table(g, first, follow)
check("tabla LL(1) tiene fila S", "S" in table)
check("tabla LL(1) tiene columna $", "$" in table["S"])
check("tabla LL(1) de expr sin conflictos", len(tconf) == 0, f"conflictos={tconf}")

# 2e. Cadenas validas e invalidas (LL(1))
ok, steps = ll1.ll1_parse(g, table, "id+id")
check("LL(1) acepta 'id+id'", ok is True)
ok, _ = ll1.ll1_parse(g, table, "(E)")
check("LL(1) acepta '(E)'", ok is True)
ok, _ = ll1.ll1_parse(g, table, "id+(E)")
check("LL(1) acepta 'id+(E)'", ok is True)
ok, _ = ll1.ll1_parse(g, table, "id+")
check("LL(1) rechaza 'id+'", ok is False)
ok, _ = ll1.ll1_parse(g, table, "id id")
check("LL(1) rechaza 'id id'", ok is False)

# 2f. Paso a paso produce pasos con stack/remaining/accion
table_e, _ = ll1.build_ll1_table(ge, fee, foe)
ok, steps = ll1.ll1_parse(ge, table_e, "ab")
check("LL(1) pasos contienen claves esperadas",
      all({"step", "stack", "remaining", "action"} <= set(s.keys()) for s in steps))
check("LL(1) acepta 'ab' (epsilon-gram)", ok is True)
ok, _ = ll1.ll1_parse(ge, table_e, "")
check("LL(1) acepta cadena vacia (epsilon)", ok is True)
ok, _ = ll1.ll1_parse(ge, table_e, "b")
check("LL(1) rechaza 'b' (epsilon-gram)", ok is False)

# ---------------------------------------------------------------------------
# 3. SLR(1)
# ---------------------------------------------------------------------------
# 3a. Gramatica SLR(1)
gs, fgs, fogs = build(GRAMS["expr"])
ts = slr1.build_slr_tables(gs, fgs, fogs)
check("expr es SLR(1)", ts["is_slr1"] is True, f"conflictos={ts['conflicts']}")
check("coleccion canonica tiene estados", len(ts["states"]) > 0)
check("estado inicial es CLOSURE(S'->.S)", len(ts["states"][0]) > 0)

# 3b. Conflicto shift/reduce (dangling-else)
gd, fgd, fogd = build(GRAMS["dangling"])
td = slr1.build_slr_tables(gd, fgd, fogd)
check("dangling NO es SLR(1)", td["is_slr1"] is False)
check("dangling tiene conflicto shift/reduce",
      any(c["type"] == "shift/reduce" for c in td["conflicts"]),
      f"conflictos={td['conflicts']}")

# 3c. Conflicto reduce/reduce
gr, fgr, frogr = build(GRAMS["rr"])
tr = slr1.build_slr_tables(gr, fgr, frogr)
check("rr NO es SLR(1)", tr["is_slr1"] is False)
check("rr tiene conflicto reduce/reduce",
      any(c["type"] == "reduce/reduce" for c in tr["conflicts"]),
      f"conflictos={tr['conflicts']}")

# 3d. Gramatica con epsilon es SLR(1)
te = slr1.build_slr_tables(ge, fee, foe)
check("epsilon-gram es SLR(1)", te["is_slr1"] is True, f"conflictos={te['conflicts']}")

# 3e. Cadenas validas e invalidas (SLR(1))
ok, steps = slr1.slr_parse(gs, ts, "id+id")
check("SLR(1) acepta 'id+id'", ok is True)
ok, _ = slr1.slr_parse(gs, ts, "(E)")
check("SLR(1) acepta '(E)'", ok is True)
ok, _ = slr1.slr_parse(gs, ts, "id+(E)")
check("SLR(1) acepta 'id+(E)'", ok is True)
ok, _ = slr1.slr_parse(gs, ts, "id+")
check("SLR(1) rechaza 'id+'", ok is False)
ok, _ = slr1.slr_parse(gs, ts, "")
check("SLR(1) rechaza cadena vacia (expr)", ok is False)

# 3f. Paso a paso SLR
ok, steps = slr1.slr_parse(gs, ts, "id+id")
check("SLR pasos contienen claves esperadas",
      all({"step", "stack", "remaining", "action"} <= set(s.keys()) for s in steps))
acciones = [s["action"] for s in steps]
check("SLR usa SHIFT", any("SHIFT" in a for a in acciones))
check("SLR usa REDUCE", any("REDUCE" in a for a in acciones))
check("SLR usa ACCEPT", any("ACEPTAR" in a for a in acciones))

# ---------------------------------------------------------------------------
# 3g. Conservacion de acciones originales tras conflicto (no sobrescritura)
# ---------------------------------------------------------------------------
# LL(1): gram_leftrec tiene conflicto FIRST/FIRST en S (producciones S->S+T y S->T)
table_lr, conflicts_lr = ll1.build_ll1_table(gl, fll, fow)
cell_s_id = table_lr['S'].get('id', [])
check("LL(1) conserva ambas producciones en celda conflictiva M[S,id]",
      len(cell_s_id) == 2,
      f"celda={cell_s_id}")
check("LL(1) registra conflicto en M[S,id]",
      any(c['terminal'] == 'id' and c['non_terminal'] == 'S'
          for c in conflicts_lr),
      f"conflictos={conflicts_lr}")

# SLR(1): gram_dangling tiene conflicto shift/reduce en estado con 'else'
# Buscar la celda conflictiva en cualquier estado (la numeracion depende del orden del set)
cell_dangling = None
for (st, sym), actions in td['ACTION'].items():
    if sym == 'else' and len(actions) == 2:
        cell_dangling = actions
        break
check("SLR(1) conserva shift y reduce en celda conflictiva",
      cell_dangling is not None and len(cell_dangling) == 2,
      f"celda={cell_dangling}")
acciones_tipos = {a[0] for a in cell_dangling}
check("SLR(1) celda conflictiva tiene shift y reduce",
      acciones_tipos == {'shift', 'reduce'},
      f"tipos={acciones_tipos}")
check("SLR(1) registra conflicto shift/reduce",
      any(c['type'] == 'shift/reduce' for c in td['conflicts']),
      f"conflictos={td['conflicts']}")

# SLR(1): gram_rr tiene conflicto reduce/reduce
# Buscar la celda conflictiva en cualquier estado (la numeracion depende del orden del set)
cell_rr = None
for (st, sym), actions in tr['ACTION'].items():
    if len(actions) == 2 and all(a[0] == 'reduce' for a in actions):
        cell_rr = actions
        break
check("SLR(1) conserva ambas reducciones en celda conflictiva",
      cell_rr is not None and len(cell_rr) == 2,
      f"celda_encontrada={cell_rr}")
check("SLR(1) registra conflicto reduce/reduce",
      any(c['type'] == 'reduce/reduce' for c in tr['conflicts']),
      f"conflictos={tr['conflicts']}")

# ---------------------------------------------------------------------------
# 4. Clasificacion: los cuatro escenarios
# ---------------------------------------------------------------------------
def clasificar(lines):
    gx, fx, fwx = build(lines)
    ll, _ = ll1.is_ll1(gx, fx, fwx)
    slr = slr1.build_slr_tables(gx, fx, fwx)["is_slr1"]
    return ll, slr

scenarios = {
    "ambos (expr)": clasificar(GRAMS["expr"]),
    "solo LL(1) (ll_only)": clasificar(GRAMS["ll_only"]),
    "solo SLR(1) (leftrec)": clasificar(GRAMS["leftrec"]),
    "ninguno (dangling)": clasificar(GRAMS["dangling"]),
    "ninguno (rr)": clasificar(GRAMS["rr"]),
}
for nombre, (ll, slr) in scenarios.items():
    check(f"clasificacion: {nombre} -> LL={ll}, SLR={slr}", True)

check("escenario 1: expr es LL y SLR", scenarios["ambos (expr)"] == (True, True))
check("escenario 2: ll_only es LL y no SLR", scenarios["solo LL(1) (ll_only)"] == (True, False))
check("escenario 3: leftrec es SLR y no LL", scenarios["solo SLR(1) (leftrec)"] == (False, True))
check("escenario 4: dangling no es ni LL ni SLR", scenarios["ninguno (dangling)"] == (False, False))

# ---------------------------------------------------------------------------
# 5. No se usan librerias prohibidas (verificacion estatica de imports)
# ---------------------------------------------------------------------------
prohibidas = ["yacc", "bison", "antlr", "lark", "nltk"]
for fname in ["parser_engine/ll1.py", "parser_engine/slr1.py", "app.py"]:
    with open(fname, encoding="utf-8") as fh:
        contenido = fh.read().lower()
    for p in prohibidas:
        check(f"{fname} no importa {p}", p not in contenido)

print("\n" + "=" * 50)
fails = [r for r in results if not r[1]]
print(f"Pruebas: {len(results)} totales, {len(fails)} fallidas")
if fails:
    print("FALLOS:")
    for n, c, d in fails:
        print("  -", n, d)
    raise SystemExit(1)
print("Todas las pruebas pasaron.")
