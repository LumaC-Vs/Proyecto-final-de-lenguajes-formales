
def compute_first(grammar):
    """
    Calcula el conjunto FIRST(X) para cada símbolo gramatical (terminal y no terminal).
    Basado en las reglas de la Sección 4.4.2 del libro de Aho et al.[cite: 15].
    """
    # Inicializar conjuntos FIRST
    first = {nt: set() for nt in grammar.non_terminals}
    for t in grammar.terminals:
        first[t] = {t}
    first['e'] = {'e'} # Épsilon siempre se pertenece a sí mismo

    changed = True
    # Iterar hasta alcanzar un punto fijo (cuando ya no se añaden más elementos)
    while changed:
        changed = False
        for A, alts in grammar.productions.items():
            for alt in alts:
                before_len = len(first[A])
                
                # Regla 3: Si A -> e, añadir 'e' a FIRST(A)
                if alt == ['e']:
                    first[A].add('e')
                else:
                    # Regla 2: Para producciones X1 Y1 ... Yk
                    all_derives_epsilon = True
                    for symbol in alt:
                        symbol_first = first.get(symbol, {symbol})
                        
                        # Añadir todo lo de FIRST(symbol) excepto épsilon a FIRST(A)
                        non_eps = symbol_first - {'e'}
                        if not non_eps.issubset(first[A]):
                            first[A].update(non_eps)
                            changed = True
                        
                        # Si el símbolo actual no deriva épsilon, rompemos la cadena
                        if 'e' not in symbol_first:
                            all_derives_epsilon = False
                            break
                    
                    # Si toda la cadena deriva épsilon, añadimos 'e' a FIRST(A)
                    if all_derives_epsilon:
                        if 'e' not in first[A]:
                            first[A].add('e')
                            changed = True
                
                if len(first[A]) > before_len:
                    changed = True
                    
    return first


def compute_follow(grammar, first):
    """
    Calcula el conjunto FOLLOW(A) para cada no terminal A.
    Basado en las reglas de la Sección 4.4.2 del libro[cite: 15].
    """
    follow = {nt: set() for nt in grammar.non_terminals}
    
    # Regla 1 de FOLLOW: Colocar el marcador de fin '$' en el FOLLOW del símbolo inicial
    follow[grammar.start_symbol].add('$')

    changed = True
    while changed:
        changed = False
        for A, alts in grammar.productions.items():
            for alt in alts:
                for i, symbol in enumerate(alt):
                    # Solo aplicamos FOLLOW a los No Terminales
                    if symbol in grammar.non_terminals:
                        before_len = len(follow[symbol])
                        
                        # Todo lo que está después del símbolo actual se denota como beta (trailer)
                        trailer = alt[i+1:]
                        
                        if trailer:
                            # Calcular el FIRST de la cadena posterior (trailer)
                            trailer_first = set()
                            all_eps = True
                            for sym in trailer:
                                sym_first = first.get(sym, {sym})
                                trailer_first.update(sym_first - {'e'})
                                if 'e' not in sym_first:
                                    all_eps = False
                                    break
                            if all_eps:
                                trailer_first.add('e')
                            
                            # Regla 2 de FOLLOW: Añadir FIRST(beta) - {e} al FOLLOW(B)
                            follow[symbol].update(trailer_first - {'e'})
                            
                            # Regla 3a de FOLLOW: Si beta deriva épsilon, añadir FOLLOW(A) al FOLLOW(B)
                            if 'e' in trailer_first:
                                follow[symbol].update(follow[A])
                        else:
                            # Regla 3b de FOLLOW: Si es el último símbolo (A -> alpha B), 
                            # añadir todo el FOLLOW(A) al FOLLOW(B)
                            follow[symbol].update(follow[A])
                        
                        if len(follow[symbol]) > before_len:
                            changed = True
                            
    return follow