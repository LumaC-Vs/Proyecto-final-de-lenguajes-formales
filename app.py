"""
Punto de entrada del proyecto de Lenguajes Formales.

Integra el ITEM 1 (FIRST/FOLLOW, ya implementado) con el ITEM 2
(parsers LL(1) y SLR(1)).

Uso ejemplos:
    python app.py --grammar gramatica.txt --sets
    python app.py --grammar gramatica.txt --input "id+id" --ll1 --step
    python app.py --grammar gramatica.txt --input "id*id" --slr1 --step
    python app.py --grammar gramatica.txt --clasificar

Formato del archivo de gramatica:
    Linea 1: numero n de no terminales
    Lineas siguientes: <no_terminal> -> <alternativas>
    Ejemplo:
        5
        E -> T E'
        E' -> + T E' | e
        T -> F T'
        T' -> * F T' | e
        F -> ( E ) | id
"""

import argparse
import sys
import subprocess
import os

from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow
from parser_engine import ll1, slr1
from collections import deque

END = '$'


def load_grammar_from_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return Grammar(lines)


def print_sets(grammar, first, follow):
    print("=== CONJUNTOS FIRST ===")
    for nt in sorted(grammar.non_terminals):
        items = sorted(list(first[nt]))
        print(f"First({nt}) = {{{', '.join(items)}}}")

    print("\n=== CONJUNTOS FOLLOW ===")
    for nt in sorted(grammar.non_terminals):
        items = sorted(list(follow[nt]), key=lambda x: (x != END, x))
        print(f"Follow({nt}) = {{{', '.join(items)}}}")


def print_ll1_table(grammar, table):
    terminals = sorted(ll1.get_real_terminals(grammar) | {END})
    non_terminals = sorted(grammar.non_terminals)

    # Ancho de columnas
    col_width = max([len(t) for t in terminals] + [4])
    header = " " * 12 + " | " + " | ".join(t.center(col_width) for t in terminals)
    sep = "-" * len(header)
    print("\n=== TABLA PREDICTIVA LL(1) M[A, a] ===")
    print(header)
    print(sep)
    for A in non_terminals:
        row_cells = []
        for a in terminals:
            cell = table.get(A, {}).get(a, [])
            if not cell:
                row_cells.append("".center(col_width))
            else:
                prods = []
                for alt in cell:
                    body = 'e' if alt == ['e'] or alt == [] else ' '.join(alt)
                    prods.append(f"{A}->{body}")
                cell_str = "; ".join(prods)
                if len(cell) > 1:
                    cell_str += "  [CONFLICTO LL(1)]"
                row_cells.append(cell_str.center(col_width))
        print(f"{A:<10} | " + " | ".join(row_cells))


def print_ll1_result(grammar, first, follow, tables=None):
    es_ll1, conflicts = ll1.is_ll1(grammar, first, follow)
    print("\n=== CLASIFICACION LL(1) ===")
    print(f"Es LL(1): {'SI' if es_ll1 else 'NO'}")
    if conflicts:
        print("Conflictos encontrados:")
        for c in conflicts:
            pi = ' '.join(c['prod_i']) if c['prod_i'] else 'e'
            pj = ' '.join(c['prod_j']) if c['prod_j'] else 'e'
            syms = ', '.join(c['symbols'])
            print(f"  - En '{c['non_terminal']}': "
                  f"'{pi}' vs '{pj}' -> simbolos en conflicto: {{{syms}}} [{c['type']}]")
    else:
        print("No hay conflictos. La gramatica cumple la condicion LL(1).")
    return es_ll1


def print_slr_result(grammar, first, follow, tables=None):
    if tables is None:
        tables = slr1.build_slr_tables(grammar, first, follow)
    print("\n=== CLASIFICACION SLR(1) ===")
    print(f"Es SLR(1): {'SI' if tables['is_slr1'] else 'NO'}")
    if tables['conflicts']:
        print("Conflictos detectados en las tablas ACTION:")
        for c in tables['conflicts']:
            print(f"  - Estado {c['state']}, simbolo '{c['symbol']}': "
                  f"{c['existing']} vs {c['new']} -> {c['type']}")
    else:
        print("No hay conflictos. La gramatica es SLR(1).")
    return tables['is_slr1']


def print_slr_states_tables(grammar, tables):
    print("\n=== COLECCION CANONICA LR(0) (ESTADOS Y ITEMS) ===")
    for i, state in enumerate(tables['states']):
        print(f"\nEstado I{i}:")
        for item in sorted(state, key=_item_sort_key):
            print(f"    {item}")
        # transiciones de este estado
        trans = {sym: j for (st, sym), j in tables['transitions'].items() if st == i}
        if trans:
            trans_desc = ", ".join(f"'{sym}' -> I{j}" for sym, j in sorted(trans.items()))
            print(f"    Transiciones: {trans_desc}")

    print("\n=== TABLAS ACTION Y GOTO SLR(1) ===")
    # Encabezado ACTION: terminales + $
    grammar_terminals = set()
    for alts in grammar.productions.values():
        for alt in alts:
            for sym in alt:
                if sym != ll1.EPSILON and sym not in grammar.non_terminals:
                    grammar_terminals.add(sym)
    action_cols = sorted(grammar_terminals | {END})
    goto_cols = sorted(grammar.non_terminals)

    # Imprimir ACTION
    col_w = 24
    print("\n-- ACTION --")
    header = "Estado".ljust(8) + " | " + " | ".join(a.center(col_w) for a in action_cols)
    print(header)
    print("-" * len(header))
    for i in range(len(tables['states'])):
        cells = []
        for a in action_cols:
            act = tables['ACTION'].get((i, a))
            cells.append(_action_str(act).center(col_w) if act else "".center(col_w))
        print(f"{'I'+str(i):<8} | " + " | ".join(cells))

    print("\n-- GOTO --")
    header = "Estado".ljust(8) + " | " + " | ".join(nt.center(col_w) for nt in goto_cols)
    print(header)
    print("-" * len(header))
    for i in range(len(tables['states'])):
        cells = []
        for nt in goto_cols:
            j = tables['GOTO'].get((i, nt))
            cells.append(str(j).center(col_w) if j is not None else "".center(col_w))
        print(f"{'I'+str(i):<8} | " + " | ".join(cells))


def _item_sort_key(item):
    return (item.head, item.rhs, item.dot)


def _action_str(act):
    if isinstance(act, list):
        return ", ".join(_action_str_single(a) for a in act)
    return _action_str_single(act)


def _action_str_single(a):
    if a[0] == 'shift':
        return f"s{a[1]}"
    if a[0] == 'reduce':
        head, rhs = a[1], a[2]
        body = 'e' if rhs == () or rhs == (ll1.EPSILON,) else ' '.join(rhs)
        return f"r{head}->{body}"
    if a[0] == 'accept':
        return "acc"
    return str(a)


def print_steps(steps):
    print("\n=== PASOS DEL ANALISIS ===")
    print(f"{'Paso':<6} {'Pila':<22} {'Entrada restante':<22} Accion")
    print("-" * 70)
    for s in steps:
        stack_str = ' '.join(str(x) for x in s['stack'])
        rem_str = ' '.join(s['remaining'])
        print(f"{s['step']:<6} {stack_str:<22} {rem_str:<22} {s['action']}")


def run_ll1_parser(grammar, first, follow, input_string, step=False):
    table, conflicts = ll1.build_ll1_table(grammar, first, follow)
    print("\n=== PARSER LL(1) ===")
    accepted, steps = ll1.ll1_parse(grammar, table, input_string, verbose=True)
    print(f"Entrada: '{input_string}' -> {'ACEPTADA' if accepted else 'RECHAZADA'}")
    if step:
        print_steps(steps)
    return accepted


def run_slr_parser(grammar, first, follow, input_string, step=False, tables=None):
    if tables is None:
        tables = slr1.build_slr_tables(grammar, first, follow)
    print("\n=== PARSER SLR(1) ===")
    accepted, steps = slr1.slr_parse(grammar, tables, input_string, verbose=True)
    print(f"Entrada: '{input_string}' -> {'ACEPTADA' if accepted else 'RECHAZADA'}")
    if step:
        print_steps(steps)
    return accepted


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Parsers LL(1) y SLR(1) - Proyecto Lenguajes Formales (ITEM 2)"
    )
    parser.add_argument('--grammar', '-g', default=None,
                        help='Ruta al archivo de gramatica')
    parser.add_argument('--input', '-i', default=None,
                        help='Cadena de entrada a analizar')
    parser.add_argument('--sets', action='store_true',
                        help='Mostrar conjuntos FIRST y FOLLOW (ITEM 1)')
    parser.add_argument('--ll1', action='store_true',
                        help='Ejecutar parser LL(1)')
    parser.add_argument('--slr1', action='store_true',
                        help='Ejecutar parser SLR(1)')
    parser.add_argument('--clasificar', action='store_true',
                        help='Clasificar la gramatica como LL(1) y/o SLR(1)')
    parser.add_argument('--table', action='store_true',
                        help='Mostrar la(s) tabla(s) construida(s)')
    parser.add_argument('--step', action='store_true',
                        help='Mostrar el analisis paso a paso')
    parser.add_argument('--run-tests', action='store_true',
                        help='Ejecutar todas las pruebas automatizadas (ITEM 1 y ITEM 2)')
    parser.add_argument('--all', action='store_true',
                        help='Ejecutar TODO lo relacionado con el ITEM 2: pruebas, '
                             'clasificacion de los 4 escenarios, parsers paso a paso y tablas')
    args = parser.parse_args(argv)

    # Si solo se ejecutan pruebas, no se requiere archivo de gramatica
    if args.run_tests or args.all:
        # Saltar carga de gramatica; se ejecuta despues
        pass
    elif args.grammar is None:
        print("ERROR: Se requiere --grammar -g <archivo> (o use --run-tests / --all)")
        return 1
    else:
        # Cargar gramatica y calcular conjuntos (ITEM 1)
        grammar = load_grammar_from_file(args.grammar)
        first = compute_first(grammar)
        follow = compute_follow(grammar, first)

        # Siempre clasificar (escenarios del ITEM 2, fase 3)
        es_ll1 = ll1.is_ll1(grammar, first, follow)[0]
        slr_tables = slr1.build_slr_tables(grammar, first, follow)
        es_slr1 = slr_tables['is_slr1']

        if args.sets:
            print_sets(grammar, first, follow)

        print("\n" + "=" * 60)
        print("CLASIFICACION DE LA GRAMATICA")
        print("=" * 60)
        print(f"LL(1):  {'SI' if es_ll1 else 'NO'}")
        print(f"SLR(1): {'SI' if es_slr1 else 'NO'}")

        if es_ll1 and es_slr1:
            print("\nEscenario 1: La gramatica es LL(1) y SLR(1).")
        elif es_ll1 and not es_slr1:
            print("\nEscenario 2: La gramatica es LL(1), pero NO SLR(1).")
        elif not es_ll1 and es_slr1:
            print("\nEscenario 3: La gramatica es SLR(1), pero NO LL(1).")
        else:
            print("\nEscenario 4: La gramatica NO es LL(1) ni SLR(1).")

        # Detalles LL(1)
        if args.ll1 or args.table:
            print_ll1_result(grammar, first, follow)
            if args.table:
                table, _ = ll1.build_ll1_table(grammar, first, follow)
                print_ll1_table(grammar, table)

        # Detalles SLR(1)
        if args.slr1 or args.table:
            print_slr_result(grammar, first, follow, slr_tables)
            if args.table:
                print_slr_states_tables(grammar, slr_tables)

        # Analisis de cadena de entrada (se permite cadena vacia, que deriva epsilon)
        if args.input is not None:
            run_ll1 = args.ll1 and not args.slr1
            run_slr1 = args.slr1 and not args.ll1
            if not args.ll1 and not args.slr1:
                # Por defecto, probar con el/los parser(es) aplicable(s)
                run_ll1 = es_ll1
                run_slr1 = es_slr1

            if run_ll1:
                if not es_ll1:
                    print("\n=== PARSER LL(1) ===")
                    print("La gramatica no es LL(1): no se ejecuta el parser predictivo LL(1).")
                else:
                    run_ll1_parser(grammar, first, follow, args.input, step=args.step)

            if run_slr1:
                if not es_slr1:
                    print("\n=== PARSER SLR(1) ===")
                    print("La gramatica no es SLR(1): no se ejecuta el parser LR/SLR(1).")
                else:
                    run_slr_parser(grammar, first, follow, args.input, step=args.step, tables=slr_tables)

            if not run_ll1 and not run_slr1 and not (es_ll1 or es_slr1):
                print("\nLa gramatica no es LL(1) ni SLR(1): no se puede parsear con estos parsers.")

    # -----------------------------------------------------------------------
    # Ejecutar todas las pruebas automatizadas (--run-tests o --all)
    # -----------------------------------------------------------------------
    if args.run_tests or args.all:
        print("\n" + "=" * 60)
        print("EJECUTANDO PRUEBAS AUTOMATIZADAS")
        print("=" * 60)
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        tests_dir = os.path.join(ruta_base, "tests")
        env = os.environ.copy()
        env["PYTHONPATH"] = ruta_base
        for test_file in ["test_sets.py", "test_item2.py"]:
            test_path = os.path.join(tests_dir, test_file)
            print(f"\n>>> Ejecutando: {test_file}")
            resultado = subprocess.run([sys.executable, test_path],
                                       capture_output=True, text=True,
                                       cwd=ruta_base, env=env)
            print(resultado.stdout)
            if resultado.stderr:
                print(resultado.stderr, file=sys.stderr)
            if resultado.returncode != 0:
                print(f"ERROR: {test_file} fallo con codigo {resultado.returncode}",
                      file=sys.stderr)
                return resultado.returncode

    # -----------------------------------------------------------------------
    # Ejecutar TODO el ITEM 2 (--all)
    # -----------------------------------------------------------------------
    if args.all:
        print("\n" + "=" * 60)
        print("EJECUCION COMPLETA DEL ITEM 2")
        print("=" * 60)
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        env = os.environ.copy()
        env["PYTHONPATH"] = ruta_base

        # Lista de (archivo, descripcion del escenario)
        escenarios = [
            ("gramaticas/gram_expr.txt", "Escenario 1: LL(1) y SLR(1)"),
            ("gramaticas/gram_ll_not_slr.txt", "Escenario 2: Solo LL(1)"),
            ("gramaticas/gram_leftrec.txt", "Escenario 3: Solo SLR(1)"),
            ("gramaticas/gram_dangling.txt", "Escenario 4: Ninguno (shift/reduce)"),
            ("gramaticas/gram_rr.txt", "Escenario 4: Ninguno (reduce/reduce)"),
        ]

        for archivo, desc in escenarios:
            print(f"\n{'='*60}")
            print(f"--- {desc} ---")
            print(f"Archivo: {archivo}")
            print(f"{'='*60}")

            def run_app(args_list):
                return subprocess.run([sys.executable, "app.py"] + args_list,
                                      capture_output=True, text=True,
                                      cwd=ruta_base, env=env)

            # Clasificar
            r1 = run_app(["--grammar", archivo, "--clasificar"])
            print(r1.stdout)
            if r1.stderr:
                print(r1.stderr, file=sys.stderr)

            # Tablas
            r2 = run_app(["--grammar", archivo, "--table"])
            print(r2.stdout)
            if r2.stderr:
                print(r2.stderr, file=sys.stderr)

            # Parser paso a paso segun el escenario
            if "Escenario 1" in desc:
                # LL(1) y SLR(1) ambos aplican
                r3 = run_app(["--grammar", archivo, "--input", "id+id",
                              "--ll1", "--step"])
                print(r3.stdout)
                r4 = run_app(["--grammar", archivo, "--input", "id+id",
                              "--slr1", "--step"])
                print(r4.stdout)
            elif "Escenario 2" in desc:
                # Solo LL(1)
                r3 = run_app(["--grammar", archivo, "--input", "ab",
                              "--ll1", "--step"])
                print(r3.stdout)
            elif "Escenario 3" in desc:
                # Solo SLR(1)
                r3 = run_app(["--grammar", archivo, "--input", "id+id+id",
                              "--slr1", "--step"])
                print(r3.stdout)
            # Escenario 4: no hay parser valido
                print(r3.stdout)
            elif "Escenario 3" in desc:
                # Solo SLR(1)
                r3 = subprocess.run([sys.executable, "app.py", "--grammar", archivo,
                                     "--input", "id+id+id", "--slr1", "--step"],
                                    capture_output=True, text=True)
                print(r3.stdout)
            # Escenario 4: no hay parser valido

    return 0


if __name__ == '__main__':
    sys.exit(main())
