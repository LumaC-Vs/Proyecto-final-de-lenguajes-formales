from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow
from parser_engine import ll1, sdd

def probar_ciclo(grammar, table):
    original = sdd.SDD[('M', 'id R')]
    sdd.SDD[('M', 'id R')] = [
        {'define': (2, 'num'), 'usa': [(0, 'val')], 'funcion': lambda v : 1},
        {'define': (0, 'val'), 'usa': [(1, 'lexval'), (2, 'num')], 'funcion': lambda x, n: f"{x}{n}"},
    ]
    
    print ('=' * 50)
    print("PRUEBA DE CICLO: SDD modificada, evaluando '[a]'")
    print('=' * 50)
    try:
        aceptada, raiz, orden = sdd.evaluar_sdd(grammar, table, "[a]")
        if not aceptada:
            print("RESULTADO: NO generada por la gramatica .\n")
        elif orden is None:
            print("Resultado: la SDD es circular. Se detiene la evaluacion.\n")
        else:
            print("ERROR: no se detecto el ciclo.\n")
    finally:
        sdd.SDD[('M', 'id R')] = original


def main():
    gramatica_raw = [
        "4",
        "S -> L",
        "L -> [ M ] | e",
        "M -> id R | e",
        "R -> ; id R | e"
    ]

    grammar = Grammar(gramatica_raw)
    first = compute_first(grammar)
    follow = compute_follow(grammar, first)
    table, _ = ll1.build_ll1_table(grammar, first, follow)

    cadenas = [
        "e",
        "[]",
        "[a]",
        "[a; b; c]",
        "[ab; cd; ef; gh; ij]",
        "[a:]"
    ]

    for cadena in cadenas:
        print('=' * 50)
        print(f"Evaluando: '{cadena}'")
        print('=' * 50)

        aceptada, raiz, orden = sdd.evaluar_sdd(grammar, table, cadena)

        if not aceptada:
            print("Resultado: NO generada por la gramatica .\n")
        elif orden is None:
            print("Resultado: la SDD es circular.\n")
        else:
            print("\n--- ARBOL ANOTADO ---")
            sdd.imprimir_arbol(raiz)
            print("\n--- ORDEN DE EVALUACION ---")
            print(" -> ".join(orden))
            print(f"\nResultado principal (S.val): {raiz.atributos['val']}\n")

    probar_ciclo(grammar, table)

if __name__ == '__main__':
    main()
