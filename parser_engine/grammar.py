
class Grammar:
    """
    Clase para representar y almacenar una Gramática Libre de Contexto (GLC)
    según las especificaciones de formato del proyecto (Sección 2.2).
    """
    def __init__(self, raw_lines):
        self.non_terminals = set()  # Conjunto de no terminales (Letras mayúsculas)
        self.terminals = set()      # Conjunto de terminales (Símbolos, dígitos, minúsculas)
        self.productions = {}       # Diccionario de producciones: { 'A': [['B', 'c'], ['e']] }
        self.start_symbol = None    # Se infiere de la primera producción del archivo
        self._parse_input(raw_lines)

    def _parse_input(self, lines):
        """
        Lógica para leer las líneas de entrada de la gramática.
        Formato esperado:
        - Línea 1: Número n de no terminales.
        - Siguientes n líneas: <no_terminal> -> <alternativas separadas por espacios>
        """
        # Limpiar y filtrar líneas vacías
        clean_lines = [line.strip() for line in lines if line.strip()]
        if not clean_lines:
            return

        # La primera línea contiene el número de no terminales
        n = int(clean_lines[0])
        prod_lines = clean_lines[1:n+1]
        
        for line in prod_lines:
            # Separar la cabeza (LHS) del cuerpo (RHS) usando la flecha '->'
            parts = line.split("->")
            lhs = parts[0].strip()
            rhs_alternatives = parts[1].strip().split()
            
            # Registrar el no terminal si es nuevo
            if lhs not in self.productions:
                self.productions[lhs] = []
                self.non_terminals.add(lhs)
                # El simbolo inicial es la cabeza de la primera produccion del archivo
                if self.start_symbol is None:
                    self.start_symbol = lhs
            
            # Procesar las alternativas de derivación (pueden venir separadas por '|' o espacios)
            current_alt = []
            for symbol in rhs_alternatives:
                if symbol == '|':
                    self.productions[lhs].append(current_alt)
                    current_alt = []
                else:
                    current_alt.append(symbol)
            if current_alt:
                self.productions[lhs].append(current_alt)

        # Clasificación automática de terminales y no terminales
        # - Los no terminales son los que aparecen en la cabeza de producciones
        #   (grammar.non_terminals, ya registrados arriba).
        # - La 'e' representa épsilon (ε) y no se cuenta como terminal físico.
        # - El resto de simbolos que aparecen en los cuerpos y no son no
        #   terminales son Terminales.
        for lhs, alts in self.productions.items():
            for alt in alts:
                for symbol in alt:
                    if symbol != 'e' and symbol not in self.non_terminals:
                        self.terminals.add(symbol) 