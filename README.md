# Proyecto-final-lenguajes-formales

Proyecto de compiladores: implementación de analizadores sintácticos **LL(1)** y **SLR(1)** a partir de conjuntos FIRST y FOLLOW.

## Lenguaje y requisitos
- Python 3 (estándar). No se utilizan librerías externas ni generadores de parsers (no Yacc, Bison, ANTLR, Lark, NLTK, etc.).
- Todo el algoritmo se implementa manualmente con la biblioteca estándar.

## Estructura del repositorio
```
app.py                    # Punto de entrada (CLI) del ITEM 1 + ITEM 2
test_sets.py              # Prueba de FIRST/FOLLOW (ITEM 1, ya funcionando)
test_item2.py             # Pruebas automatizadas del ITEM 2
parser_engine/
  grammar.py              # Modelo de la GLC (parsing del formato de entrada)
  first_follow.py         # ITEM 1: compute_first y compute_follow
  ll1.py                  # ITEM 2A: parser LL(1)
  slr1.py                 # ITEM 2B: parser SLR(1)
  sdd.py                  # Reservado para ITEM 3 (no implementado aquí)
templates/
  index.html              # Reservado
README.md
```

## Formato de entrada de una gramática
Archivo de texto con la siguiente estructura:
- Línea 1: número `n` de no terminales.
- Líneas siguientes: `<no_terminal> -> <alternativa1> | <alternativa2>`

Convenciones del proyecto:
- `e` representa épsilon (ε).
- `$` es el marcador de fin de entrada.
- `S` es siempre el símbolo inicial.
- Ejemplo (`gram_expr.txt`):
```
5
S -> T E'
E' -> + T E' | e
T -> F T'
T' -> * F T' | e
F -> ( E ) | id
```

## Ejecución

### Mostrar conjuntos FIRST y FOLLOW (--sets, ITEM 1)
```bash
python app.py --grammar gram_expr.txt --sets
```

### Clasificar la gramática (LL(1) y/o SLR(1))
```bash
python app.py --grammar gram_expr.txt --clasificar
```

### Parser LL(1) (no recursivo, dirigido por tabla)
```bash
python app.py --grammar gram_expr.txt --input "id+id" --ll1 --step
python app.py --grammar gram_expr.txt --input "id+" --ll1 --step   # cadena invalida
```
Mostrar también la tabla predictiva:
```bash
python app.py --grammar gram_expr.txt --ll1 --table
```

### Parser SLR(1) (LR con tablas ACTION/GOTO)
```bash
python app.py --grammar gram_expr.txt --input "id+id" --slr1 --step
python app.py --grammar gram_leftrec.txt --input "id+id+id" --slr1 --step  # recursión izquierda
```
Mostrar estados LR(0) y tablas ACTION/GOTO:
```bash
python app.py --grammar gram_expr.txt --slr1 --table
```

### Opciones de `app.py`
- `--grammar -g` (requerido): ruta al archivo de gramática.
- `--input -i`: cadena de entrada a analizar.
- `--sets`: imprime FIRST y FOLLOW (ITEM 1).
- `--ll1`: ejecuta el parser LL(1).
- `--slr1`: ejecuta el parser SLR(1).
- `--clasificar`: imprime el escenario (LL/SLR/ambos/ninguno).
- `--table`: imprime la(s) tabla(s) construida(s).
- `--step`: muestra el análisis paso a paso (pila, entrada restante, acción).

## ITEM 2 — Parser LL(1)
**Algoritmos utilizados** (Aho et al., Secciones 4.4.3 y 4.4.4):
1. Verificación de la condición LL(1) sobre la gramática original (sin eliminar recursión izquierda ni factorizar):
   - `FIRST(αi) ∩ FIRST(αj) = ∅` para producciones distintas.
   - Si `ε ∈ FIRST(αi)` entonces `FIRST(αj) ∩ FOLLOW(A) = ∅`.
   - Si `ε ∈ FIRST(αj)` entonces `FIRST(αi) ∩ FOLLOW(A) = ∅`.
2. Construcción de la tabla predictiva `M[A, a]` usando `FIRST` de la producción y `FOLLOW(A)` cuando la producción deriva épsilon; se detectan celdas con conflicto (más de una producción).
3. Análisis predictivo no recursivo con pila y entrada terminada en `$`: inicialización, comparación tope/símbolo actual, reconocimiento de terminales, consulta de tabla, aplicación de producciones, manejo de `ε`, aceptación y rechazo con mensajes de error.

**Integración con el ITEM 1:** reutiliza `compute_first` y `compute_follow` de `parser_engine.first_follow`.

## ITEM 2 — Parser SLR(1)
**Algoritmos utilizados** (Aho et al., Sección 4.6):
1. Gramática aumentada `S' -> S` con símbolo inicial nuevo que no colisiona con los existentes.
2. Ítems LR(0) (producción + posición del punto + símbolo tras el punto).
3. `CLOSURE(I)` y `GOTO(I, X)` para LR(0).
4. Colección canónica LR(0): estados a partir de `CLOSURE({S' -> . S})`, transiciones únicas sin duplicados.
5. Tablas `ACTION` y `GOTO` SLR(1) usando `FOLLOW` del ITEM 1:
   - `[A -> α . a β]` y `GOTO(Ii, a) = Ij` → `ACTION[i, a] = shift j`.
   - `[A -> α .]` completo (A no aumentado) → `ACTION[i, b] = reduce A -> α` para cada `b ∈ FOLLOW(A)`.
   - `[S' -> S .]` → `ACTION[i, $] = accept`.
6. Detección de conflictos **shift/reduce** y **reduce/reduce** sin sobrescribir silenciosamente; si hay conflictos, la gramática no es SLR(1).
7. Analizador LR con pila de estados: desplazamiento (`SHIFT`), reducción (`REDUCE`) y aceptación (`ACCEPT`), más detección de errores sintácticos.

## Clasificaciones verificadas (4 escenarios)
| Escenario | Ejemplo | Resultado |
|-----------|---------|-----------|
| LL(1) y SLR(1) | `gram_expr.txt` | Ambos |
| Solo LL(1) | `gram_ll_not_slr.txt` | LL(1) sí, SLR(1) no |
| Solo SLR(1) | `gram_leftrec.txt` | SLR(1) sí, LL(1) no |
| Ninguno | `gram_dangling.txt` / `gram_rr.txt` | Ni LL(1) ni SLR(1) |

## Pruebas
Ejecutar el conjunto automatizado:
```bash
python test_item2.py
```
Cubre: integración FIRST/FOLLOW, producciones ε, gramática LL(1) y no LL(1), conflictos en tabla, cadenas válidas e inválidas para LL(1) y SLR(1), conflicto shift/reduce, conflicto reduce/reduce y los cuatro escenarios de clasificación.
