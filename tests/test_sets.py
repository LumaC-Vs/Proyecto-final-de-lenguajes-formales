# test_sets.py
from parser_engine.grammar import Grammar
from parser_engine.first_follow import compute_first, compute_follow

# Gramática de prueba (Ejemplo 4.28 del libro de Aho)
# S -> T E'
# E' -> + T E' | e
# T -> F T'
# T' -> * F T' | e
# F -> ( E ) | id
raw_grammar_input = [
    "5", # 5 no terminales: E, E', T, T', F
    "E -> T E'",
    "E' -> + T E' | e",
    "T -> F T'",
    "T' -> * F T' | e",
    "F -> ( E ) | id"
]

# 1. Inicializar la gramática
g = Grammar(raw_grammar_input)

# 2. Calcular conjuntos
firsts = compute_first(g)
follows = compute_follow(g, firsts)

# 3. Imprimir resultados ordenados alfabéticamente (como lo pide el proyecto)
print("=== CONJUNTOS FIRST ===")
for nt in sorted(g.non_terminals):
    items = sorted(list(firsts[nt]))
    print(f"First({nt}) = {{{', '.join(items)}}}")

print("\n=== CONJUNTOS FOLLOW ===")
for nt in sorted(g.non_terminals):
    items = sorted(list(follows[nt]), key=lambda x: (x != '$', x)) # Poner '$' al final si aplica
    print(f"Follow({nt}) = {{{', '.join(items)}}}")