"""
ITEM 3: evaluador de la SDD (Pasos 5 y 6).

Lee una gramatica en el formato de la Seccion 2.2, luego lee cadenas una por
linea hasta una linea vacia. Para cada cadena imprime "no" si no pertenece al
lenguaje; en caso contrario imprime el arbol anotado, el orden de evaluacion
y el valor del atributo principal de S.

Uso:
    python sdd_app.py gramaticas/gram_sdd.txt
    python sdd_app.py        (la gramatica se lee por entrada estandar)
"""

import sys

from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow
from parser_engine import ll1, sdd

def leer_gramatica(ruta = None):
    if ruta is not None:
        with open(ruta, 'r', encoding ='utf-8') as f:
            lineas = f.readlines()
    else:
        n = int(input().strip())
        lineas = [str(n)] + [input() for _ in range(n)]
    return Grammar(lineas)

def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    grammar = leer_gramatica(ruta)
    first = compute_first(grammar)
    follow = compute_follow(grammar, first)

    es_ll1, _ = ll1.is_ll1(grammar, first, follow)
    if not es_ll1:
        print("La gramatica no es LL(1): no se puede evaluar la SDD.")
        return 1
    table, _ = ll1.build_ll1_table(grammar, first, follow)

    while True:
        try:
            cadena = input()
        except EOFError:
            break
        if cadena.strip() == "":
            break

        aceptada, raiz, orden = sdd.evaluar_sdd(grammar, table, cadena)

        if not aceptada:
            print("no")
        elif orden is None:
            print("La SDD es circular.")
        else:
            print("--- ARBOL ANOTADO ---")
            sdd.imprimir_arbol(raiz)
            print("--- ORDEN DE EVALUACION ---")
            print(" -> ".join(orden))
            print(f"--- VALOR DE S.val: {raiz.atributos['val']}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
