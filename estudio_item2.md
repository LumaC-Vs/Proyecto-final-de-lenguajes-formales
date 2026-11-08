# Guía de Estudio — Ítem 2: Parsers LL(1) y SLR(1)

Este documento explica **línea por línea**, de forma detallada y pedagógica, el código del proyecto de Lenguajes Formales (Ítem 1: FIRST/FOLLOW; Ítem 2: parsers LL(1) y SLR(1)).

> **Nota:** Este archivo es únicamente para estudio local. No contiene código ejecutable, sino explicaciones y comandos para ejecutar en la terminal de PowerShell.

---

## Índice

1. [parser_engine/grammar.py](#grammar-py) — Ítem 1: Modelo de la GLC
2. [parser_engine/first_follow.py](#first-follow-py) — Ítem 1: FIRST y FOLLOW
3. [parser_engine/ll1.py](#ll1-py) — Ítem 2A: Parser LL(1)
4. [parser_engine/slr1.py](#slr1-py) — Ítem 2B: Parser SLR(1)
5. [app.py](#app-py) — Punto de entrada y CLI
6. [Trazado manual LL(1)](#trazado-ll1)
7. [Trazado manual SLR(1)](#trazado-slr1)
8. [Pruebas automatizadas](#pruebas)
9. [Preguntas de auto-evaluación](#preguntas)

---

## 1. parser_engine/grammar.py

### ¿Qué hace este archivo?

Define la clase `Grammar` que representa y almacena una **Gramática Libre de Contexto (GLC)** según el formato del proyecto.

### Estructura de datos principal

```python
self.non_terminals = set()   # No terminales (ej: S, E', T, T', F)
self.terminals = set()       # Terminales (ej: +, *, (, ), id)
self.productions = {}        # { 'A': [['B', 'c'], ['e']] }
self.start_symbol = 'S'      # Símbolo inicial (siempre 'S')
```

### Formato de entrada del archivo de gramática

```
Línea 1: número n de no terminales
Líneas siguientes: <no_terminal> -> <alt1> | <alt2>
```

**Ejemplo** (`gramaticas/gram_expr.txt`):
```
5
S -> T E'
E' -> + T E' | e
T -> F T'
T' -> * F T' | e
F -> ( E ) | id
```

### Clasificación de símbolos

- Los no terminales son los que aparecen como **cabeza (LHS)** de producciones (ya registrados en `self.non_terminals`).
- `'e'` representa **épsilon** y NO es terminal físico.
- Cualquier otro símbolo que aparezca en el cuerpo y NO sea no terminal, es **terminal**.

### Corrección realizada (Ítem 1)

| Antes (incorrecto) | Después (correcto) |
|--------------------|--------------------|
| `symbol.isupper() and len(symbol)==1` | `symbol not in self.non_terminals` |

**Por qué:** Los no terminales con prima (`E'`, `T'`) se etiquetaban erróneamente como terminales con la heurística de "letra mayúscula de un solo carácter".

### Comando para ver el archivo

```powershell
type parser_engine\grammar.py
```

---

## 2. parser_engine/first_follow.py

### `compute_first(grammar)` — Líneas 2-50

1. Inicializa `first[nt] = {}` para cada no terminal.
2. Inicializa `first[t] = {t}` para cada terminal.
3. `first['e'] = {'e'}` (épsilon pertenece a sí mismo).
4. Itera hasta **punto fijo** (cuando ya no hay cambios):
   - Para cada producción `A -> α`:
     - Si `α == ['e']`: añadir `'e'` a `FIRST(A)`.
     - Sino: para cada símbolo en `α`:
       - Añadir `FIRST(symbol) - {e}` a `FIRST(A)`.
       - Si el símbolo NO deriva `'e'`, romper la cadena.
     - Si **todos** los símbolos de `α` derivan `'e'`, añadir `'e'` a `FIRST(A)`.

### `compute_follow(grammar, first)` — Líneas 53-103

1. Inicializa `follow[nt] = {}` para cada no terminal.
2. `follow[start_symbol] = {'$'}` (regla 1 de FOLLOW).
3. Itera hasta punto fijo:
   - Para cada producción `A -> ... B ...` donde `B` es no terminal:
     - `trailer` = símbolos después de `B`.
     - Calcular `FIRST(trailer) - {e}`, añadir a `follow[B]`.
     - Si `trailer` deriva `'e'`, añadir `follow[A]` a `follow[B]`.
     - Si `B` es el último símbolo, añadir `follow[A]` a `follow[B]`.

### Ejemplo concreto (`gram_expr.txt`)

```
First(E') = {+, e}
First(F)  = {(, id}
First(S)  = {(, id}
First(T)  = {(, id}
First(T') = {*, e}

Follow(F) = {$, *, +}
Follow(T) = {$, +}
Follow(T') = {$, +}
Follow(S) = {$}
Follow(E') = {$}
```

### Comandos

```powershell
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python tests/test_sets.py
python app.py --grammar gramaticas/gram_expr.txt --sets
```

---

## 3. parser_engine/ll1.py

### 1. `get_real_terminals(grammar)` — Líneas 26-44

- Devuelve terminales reales: símbolos en cuerpos que no son épsilon y no son no terminales.
- **¿Por qué no usar `grammar.terminals`?** Porque `E'` y `T'` podían etiquetarse erróneamente como terminales en el Ítem 1.

### 2. `first_of_string(symbols, first)` — Líneas 47-64

- Calcula `FIRST` de una **cadena completa** de símbolos.
- **Regla:** añadir `FIRST(Xi) - {e}` mientras todos los previos deriven épsilon. Si toda la cadena deriva `'e'`, añadir `'e'`.
- Ejemplo: Para `A -> B C`, si `FIRST(B) = {b, e}` y `FIRST(C) = {c, e}`:
  ```
  FIRST(ABC) = {b, c, e}
  ```

### 3. `is_ll1(grammar, first, follow)` — Líneas 67-127

Verifica la **condición LL(1)** (Sección 4.4.3) sin transformar la gramática (no elimina recursión izquierda ni factoriza).

Para cada par de producciones `αi`, `αj` del mismo no terminal `A`:

| Condición | Requisito |
|-----------|-----------|
| a) | `FIRST(αi) ∩ FIRST(αj) = ∅` |
| b) | Si `e ∈ FIRST(αi)`: `FIRST(αj) ∩ FOLLOW(A) = ∅` |
| c) | Si `e ∈ FIRST(αj)`: `FIRST(αi) ∩ FOLLOW(A) = ∅` |

Retorna `(es_ll1, lista_de_conflictos)`.

### 4. `build_ll1_table(grammar, first, follow)` — Líneas 130-168

Construye la tabla predictiva `M[A, a]`:

- Para cada producción `A -> α`:
  - Para cada terminal `a` en `FIRST(α) - {e}`: `M[A,a] += A -> α`
  - Si `e ∈ FIRST(α)`: para cada `b` en `FOLLOW(A)`: `M[A,b] += A -> α`

**Importante:** Ahora conserva **TODAS** las producciones en celdas conflictivas y registra el conflicto (no sobrescribe silenciosamente).

### 5. `ll1_parse(grammar, table, input_string)` — Líneas 205-308

Analizador predictivo no recursivo dirigido por tabla (Sección 4.4.4):

- **Pila inicial:** `[END, start_symbol]` (tope = último elemento).
- **Entrada:** `tokens + [END]`.

**Ciclo principal:**

| Situación | Acción |
|-----------|--------|
| Tope == `END` y entrada == `END` | **ACEPTAR** |
| Tope es terminal y coincide con entrada | `pop` (match) |
| Tope es terminal y NO coincide | ERROR sintáctico |
| Tope es no terminal | Consultar `M[X, a]`: |
| &nbsp;&nbsp;- Celda vacía | ERROR (no hay producción) |
| &nbsp;&nbsp;- Celda con producción | Predecir, `pop`, empujar cuerpo en reversa |
| &nbsp;&nbsp;- Producción es `'e'` | No empujar nada (manejo de épsilon) |

### Comandos

```powershell
type parser_engine\ll1.py
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python app.py --grammar gramaticas/gram_expr.txt --input "id+id" --ll1 --step --table
```

---

## 4. parser_engine/slr1.py

### Clase `Item` — Líneas 29-64

Representa un **ítem LR(0)**: `[A -> α . β]`

| Atributo | Descripción |
|----------|-------------|
| `head` | Izquierda de la producción |
| `rhs` | Cuerpo como tupla |
| `dot` | Posición del punto |

- `symbol_after_dot()`: retorna el símbolo después del punto, o `None`.
- `is_complete()`: `True` si el punto está al final (producción lista para reducir).
- Implementa `__eq__` y `__hash__` para usar en conjuntos (evitar duplicados).

### `_augmented_start_symbol(grammar)` — Líneas 67-76

Crea `S'` (símbolo inicial aumentado) que no colisione con existentes. Gramática aumentada: `S' -> S`.

### `_normalize_rhs(alt)` — Líneas 79-87

Convierte alternativa del repositorio a tupla LR(0). Una producción `A -> e` se representa como cuerpo vacío `()` (épsilon no consume estados).

### `closure(items, grammar)` — Líneas 90-111

**CLOSURE(I)** para LR(0):

1. Parte de los ítems de `I`.
2. Para cada ítem `[A -> α . B β]` donde `B` es no terminal: agregar `[B -> . γ]` por cada producción `B -> γ`.
3. Repetir hasta punto fijo (no hay nuevos ítems).
4. Usar conjunto para evitar duplicados.

### `goto(items, symbol, grammar)` — Líneas 114-128

**GOTO(I, X)**:

1. Buscar ítems cuyo punto precede a `X`.
2. Avanzar el punto una posición.
3. Aplicar CLOSURE al conjunto resultante.
4. Retornar `None` si no hay ítems que mover.

### `canonical_collection(grammar)` — Líneas 131-172

Construye la **colección canónica LR(0)**:

1. Estado inicial: `CLOSURE({[S' -> . S]})`
2. Para cada estado y cada símbolo, calcular `GOTO`.
3. Asignar ID único a cada estado nuevo.
4. Evitar estados duplicados (usar diccionario `state_index`).
5. Retornar estados, transiciones y símbolo aumentado.

### `build_slr_tables(grammar, first, follow)` — Líneas 175-290

Construye tablas **ACTION** y **GOTO** SLR(1):

| Regla | Condición | Acción |
|-------|-----------|--------|
| a) | `[A -> α . a β]` y `GOTO(Ii, a) = Ij` | `ACTION[i, a] = shift j` |
| b) | `[A -> α .]` completo (`A ≠ S'`) | `ACTION[i, b] = reduce A -> α` para cada `b ∈ FOLLOW(A)` |
| c) | `[S' -> S .]` | `ACTION[i, $] = accept` |
| d) | No terminales | `GOTO[i, A] = j` según transiciones |

**Importante:** Ahora `ACTION` es diccionario de **listas** (conserva múltiples acciones). Detecta conflictos shift/reduce y reduce/reduce **sin sobrescribir** silenciosamente. `is_slr1 = True` solo si no hay conflictos.

### `slr_parse(grammar, tables, input_string)` — Líneas 329-439

Analizador LR (Sección 4.6.3):

- **Pila de estados:** `[0]`.
- **Entrada:** `tokens + [END]`.

**Ciclo:**

| Acción | Qué hace |
|--------|----------|
| `shift j` | Apilar `j`, avanzar entrada. |
| `reduce A -> α` | Desapilar `|α|` estados, consultar `GOTO`, apilar resultado. |
| `accept` | Terminar con éxito. |
| Celda vacía o conflicto múltiple | ERROR sintáctico. |

### Comandos

```powershell
type parser_engine\slr1.py
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python app.py --grammar gramaticas/gram_leftrec.txt --input "id+id+id" --slr1 --step --table
```

---

## 5. app.py

### ¿Qué hace?

Punto de entrada del proyecto. Integra **Ítem 1** (FIRST/FOLLOW) con **Ítem 2** (parsers LL(1) y SLR(1)).

### Argumentos de línea de comandos

| Argumento | Descripción |
|-----------|-------------|
| `--grammar -g` | Ruta al archivo de gramática (requerido salvo `--all`/`--run-tests`) |
| `--input -i` | Cadena de entrada a analizar |
| `--sets` | Mostrar conjuntos FIRST y FOLLOW (Ítem 1) |
| `--ll1` | Ejecutar parser LL(1) |
| `--slr1` | Ejecutar parser SLR(1) |
| `--clasificar` | Clasificar gramática (4 escenarios) |
| `--table` | Mostrar tablas construidas |
| `--step` | Mostrar análisis paso a paso |
| `--run-tests` | Ejecutar pruebas automatizadas |
| `--all` | Ejecutar TODO el Ítem 2 (pruebas + escenarios + parsers + tablas) |

### Flujo principal (`main`)

1. Cargar gramática desde archivo.
2. Calcular FIRST y FOLLOW (Ítem 1).
3. Clasificar: `es_ll1 = is_ll1()`, `es_slr1 = build_slr_tables().is_slr1`.
4. Mostrar escenarios (1: ambos, 2: solo LL(1), 3: solo SLR(1), 4: ninguno).
5. Si `--ll1` o `--slr1`: ejecutar parser correspondiente **solo si califica**.
6. Si `--all` o `--run-tests`: ejecutar pruebas y trazados completos.

> **Importante:** Los parsers **NO se ejecutan** si la gramática no califica (evita bucles infinitos en gramáticas no-LL(1) o no-SLR(1)).

### Comandos

```powershell
type app.py
python app.py --all
```

---

## 6. Trazado Manual LL(1)

**Gramática:** `gram_expr.txt`  
**Entrada:** `'id+id'`

```
Grammatica:
  S -> T E'
  E' -> + T E' | e
  T -> F T'
  T' -> * F T' | e
  F -> ( E ) | id
```

**Tabla predictiva relevante** (`M[A, a]`):
```
M[S, id]   = S -> T E'
M[S, (]    = S -> T E'
M[T, id]   = T -> F T'
M[T, (]    = T -> F T'
M[F, id]   = F -> id
M[F, (]    = F -> ( E )
M[T', +]   = T' -> e
M[T', $]   = T' -> e
M[T', *)   = T' -> * F T'
M[E', +]   = E' -> + T E'
M[E', $]   = E' -> e
```

**Trazado paso a paso:**

| Paso | Pila | Entrada | Acción |
|------|------|---------|--------|
| 1 | `$ E' T` | `id+id$` | PREDECIR `S -> T E'` |
| 2 | `$ E' T' F` | `id+id$` | PREDECIR `T -> F T'` |
| 3 | `$ E' T' id` | `id+id$` | PREDECIR `F -> id` |
| 4 | `$ E' T'` | `id+id$` | match `'id'` |
| 5 | `$ E'` | `+id$` | PREDECIR `T' -> e` |
| 6 | `$ E' T +` | `+id$` | PREDECIR `E' -> + T E'` |
| 7 | `$ E' T` | `+id$` | match `'+'` |
| 8 | `$ E' T' F` | `id$` | PREDECIR `T -> F T'` |
| 9 | `$ E' T' id` | `id$` | PREDECIR `F -> id` |
| 10 | `$ E' T'` | `id$` | match `'id'` |
| 11 | `$ E'` | `$` | PREDECIR `T' -> e` |
| 12 | `$` | `$` | PREDECIR `E' -> e` |
| 13 | `$` | `$` | **ACEPTAR** |

### Ejecutar en terminal

```powershell
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python app.py --grammar gramaticas/gram_expr.txt --input "id+id" --ll1 --step
```

---

## 7. Trazado Manual SLR(1)

**Gramática:** `gram_leftrec.txt`  
**Entrada:** `'id+id+id'`

```
Grammatica:
  S -> S + T | T
  T -> id
```

**Estados relevantes** (colección canónica LR(0)):
```
I0: [S' -> . S], [S -> . S + T], [S -> . T], [T -> . id]
I1: [S -> S . + T], [S' -> S . ]
I2: [S -> T . ]
I3: [T -> id . ]
I4: [S -> S + . T], [T -> . id]
I5: [S -> S + T . ]
```

**Trazado paso a paso:**

| Paso | Estados | Entrada | Acción |
|------|---------|---------|--------|
| 1 | `0 3` | `id+id+id$` | SHIFT `'id'`, estado 3 |
| 2 | `0 1` | `+id+id$` | REDUCE `T -> id`, estado 1 |
| 3 | `0 2` | `+id+id$` | REDUCE `S -> T`, estado 2 |
| 4 | `0 2 4` | `+id+id$` | SHIFT `'+'`, estado 4 |
| 5 | `0 2 4 3` | `id+id$` | SHIFT `'id'`, estado 3 |
| 6 | `0 2 4 5` | `+id$` | REDUCE `T -> id`, estado 5 |
| 7 | `0 2` | `+id$` | REDUCE `S -> S + T`, estado 2 |
| 8 | `0 2 4` | `+id$` | SHIFT `'+'`, estado 4 |
| 9 | `0 2 4 3` | `id$` | SHIFT `'id'`, estado 3 |
| 10 | `0 2 4 5` | `$` | REDUCE `T -> id`, estado 5 |
| 11 | `0 2` | `$` | REDUCE `S -> S + T`, estado 2 |
| 12 | `0 2` | `$` | **ACEPTAR** |

### Ejecutar en terminal

```powershell
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python app.py --grammar gramaticas/gram_leftrec.txt --input "id+id+id" --slr1 --step
```

---

## 8. Pruebas Automatizadas

### Ítem 1 (`--sets`)

```powershell
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python tests/test_sets.py
```

### Ítem 2 (70 pruebas)

```powershell
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"
python tests/test_item2.py
```

**Resultado esperado:** `Pruebas: 70 totales, 0 fallidas`

### Ejecutar todo

```powershell
python app.py --all
```

---

## 9. Preguntas de Auto-Evaluación

1. ¿Por qué `grammar.py` clasifica mal a `E'` y `T'` si se usa `len(symbol)==1`?
2. ¿Cuáles son las 3 condiciones de la condición LL(1) (Sección 4.4.3)?
3. ¿Por qué NO se debe eliminar recursión izquierda antes de verificar LL(1)?
4. ¿Qué representa un ítem LR(0) `[A -> α . β]`?
5. ¿Cuál es la diferencia entre `CLOSURE` y `GOTO` en LR(0)?
6. ¿Cuándo se usa `FOLLOW` en la construcción de la tabla LL(1)?
7. ¿Cuándo se usa `FOLLOW` en la construcción de la tabla ACTION SLR(1)?
8. ¿Qué significa una celda ACTION con múltiples acciones?
9. ¿Por qué SLR(1) puede aceptar gramáticas con recursión izquierda?
10. ¿Cuáles son los 4 escenarios de clasificación y un ejemplo de cada uno?

---

## Comandos Rápidos

```powershell
# Configurar PYTHONPATH (obligatorio en cada terminal nueva)
$env:PYTHONPATH = "C:\Users\shery\OneDrive\Escritorio\finalformales\Proyecto-final-de-lenguajes-formales"

# Ver FIRST y FOLLOW (Ítem 1)
python tests/test_sets.py

# Ver las 70 pruebas del Ítem 2
python tests/test_item2.py

# Trazado LL(1) paso a paso
python app.py --grammar gramaticas/gram_expr.txt --input "id+id" --ll1 --step --table

# Trazado SLR(1) paso a paso
python app.py --grammar gramaticas/gram_leftrec.txt --input "id+id+id" --slr1 --step --table

# Ejecutar TODO el Ítem 2
python app.py --all
```

---

*Fin de la guía de estudio.*