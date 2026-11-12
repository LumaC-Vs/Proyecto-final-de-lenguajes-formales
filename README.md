# Formal Languages and Compilers — Final Project

Web server demonstration integrated with the original project algorithms. Provides interactive visualization of the three required items:

1. **Item 1:** FIRST and FOLLOW sets.
2. **Item 2:** LL(1) and SLR(1) parsers with tables, LR(0) automaton, and step-by-step simulations.
3. **Item 3:** Syntax-Directed Definition (SDD) with syntax tree, annotated tree, dependency graph, topological order, attribute evaluation, and cycle detection.

## Key features

- **Automatic grammar loading:** The server reads `.txt` files directly from the `gramaticas/` folder; the user never needs to upload grammar files manually.
- **Original algorithms:** The code in `parser_engine/` is reused without modifying its academic logic. No parser generators are used (Yacc, Bison, ANTLR, Lark, NLTK, etc.).
- **Web interface:** Flask backend + Jinja2 templates, custom CSS, and vanilla JavaScript. Diagrams are generated as SVG.
- **REST API:** JSON endpoints to query grammars and run the algorithms for each item.

---

## Repository structure

```
Proyecto-final-de-lenguajes-formales/
├── app.py                          # Original CLI (Item 1 + Item 2)
├── server.py                       # Flask web server (new)
├── requirements.txt                # Dependencies (flask>=3.0.0)
├── README.md                       # This file
├── .gitignore                      # Git exclusions
├── sdd_app.py                      # Original Item 3 CLI (pre-existing)
├── test_sets.py                    # Automated tests for Item 1
├── test_item2.py                   # Automated tests for Item 2
├── test_sdd.py                     # Automated tests for Item 3
├── gramaticas/                     # Grammar folder (source of truth)
│   ├── gram_expr.txt               # Arithmetic expressions (E start, LL(1) and SLR(1))
│   ├── gram_epsilon.txt            # Grammar with epsilon (LL(1) and SLR(1))
│   ├── gram_leftrec.txt            # Left recursion (SLR(1) only)
│   ├── gram_ll_not_slr.txt         # LL(1) only
│   ├── gram_dangling.txt           # Dangling-else (none, shift/reduce conflict)
│   ├── gram_rr.txt                 # Reduce/reduce conflict (none)
│   ├── gram_new1.txt               # Additional test grammar
│   ├── gram_new2.txt               # Additional test grammar
│   ├── gram_new3.txt               # Additional test grammar
│   └── gram_sdd.txt                # Grammar for Item 3 (SDD)
├── parser_engine/
│   ├── __init__.py
│   ├── grammar.py                  # CFG model; start_symbol inferred from file
│   ├── first_follow.py             # Item 1: compute_first, compute_follow
│   ├── ll1.py                      # Item 2A: LL(1) parser
│   ├── slr1.py                     # Item 2B: SLR(1) parser
│   ├── sdd.py                      # Item 3: SDD, tree, graph, cycle detection, evaluator
│   └── sdd_report.py               # Item 3: JSON report for the web server
├── templates/                      # Web views (Jinja2)
│   ├── base.html                   # Base layout with navbar and grammar selector
│   ├── index.html                  # Home page
│   ├── item1.html                  # Item 1 module
│   ├── item2.html                  # Item 2 module
│   └── item3.html                  # Item 3 module
└── static/
    ├── css/style.css               # Modern and responsive styles
    └── js/app.js                   # Frontend logic (fetch, SVG, simulations)
```

---

## Grammar file format

Files in `gramaticas/` follow this structure:

```
5                                   # Line 1: number of non-terminals
E -> T E'                           # Following lines: <non_terminal> -> <alternative1> | <alternative2>
E' -> + T E' | e
T -> F T'
T' -> * F T' | e
F -> ( E ) | id
```

**Project conventions:**
- `e` represents epsilon (ε).
- `$` is the end-of-input marker.
- The start symbol is **inferred automatically** from the first production of the file (it does not have to be `S`; for example, `gram_expr.txt` uses `E`).
- Non-terminals are identified by appearing as the head of at least one production.
- Terminals are the remaining symbols that are not non-terminals or `e`.

---

## 1. Web server (recommended for demonstration)

The Flask server provides a complete web interface with grammar selector, navigation between the three items, tables, SVG diagrams, and step-by-step simulations.

### Installation

```bash
# Clone the repository
git clone https://github.com/LumaC-Vs/Proyecto-final-de-lenguajes-formales.git
cd Proyecto-final-de-lenguajes-formales

# (Recommended) Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Run the server

```bash
python server.py
```

The server will be available at: **`http://127.0.0.1:5000`**

### Web navigation

| Route | Content |
|-------|---------|
| `/` | Home page with project description |
| `/item1` | Item 1: FIRST and FOLLOW |
| `/item2` | Item 2: LL(1) and SLR(1) |
| `/item3` | Item 3: SDD |

In each module, select a grammar from the dropdown menu (loaded automatically from `gramaticas/`) and run the desired algorithms.

### REST API endpoints

The server exposes a REST API returning JSON:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/grammars` | GET | List all grammars available in `gramaticas/` |
| `/api/grammars/<id>` | GET | Details of a specific grammar |
| `/api/first-follow` | POST | Run FIRST and FOLLOW (Item 1) |
| `/api/ll1` | POST | Run LL(1) parser with predictive table and simulation (Item 2A) |
| `/api/slr1` | POST | Run SLR(1) parser with ACTION/GOTO tables and simulation (Item 2B) |
| `/api/sdd` | POST | Run SDD evaluator with tree, graph, and topological order (Item 3) |

Example usage with `curl` (Item 1):

```bash
curl -X POST http://127.0.0.1:5000/api/first-follow \
  -H "Content-Type: application/json" \
  -d '{"grammar_id": "gram_expr"}'
```

---

## 2. Command-line interface (original CLI)

The file `app.py` is the original project entry point. It allows running the algorithms directly from the terminal without a web server.

### Usage examples

```bash
# Item 1: show FIRST and FOLLOW
python app.py --grammar gramaticas/gram_expr.txt --sets

# Item 2: classify grammar (LL(1) and/or SLR(1))
python app.py --grammar gramaticas/gram_expr.txt --clasificar

# Item 2: LL(1) parser with predictive table
python app.py --grammar gramaticas/gram_expr.txt --ll1 --table

# Item 2: LL(1) parser step-by-step with input string (valid)
python app.py --grammar gramaticas/gram_expr.txt --input "id+id" --ll1 --step

# Item 2: LL(1) parser step-by-step with input string (invalid)
python app.py --grammar gramaticas/gram_expr.txt --input "id+" --ll1 --step

# Item 2: SLR(1) parser with ACTION/GOTO tables
python app.py --grammar gramaticas/gram_expr.txt --slr1 --table

# Item 2: SLR(1) parser step-by-step with input string (valid)
python app.py --grammar gramaticas/gram_expr.txt --input "id+id" --slr1 --step

# Item 2: SLR(1) parser step-by-step with input string (left recursion)
python app.py --grammar gramaticas/gram_leftrec.txt --input "id+id+id" --slr1 --step

# Run all automated tests
python app.py --run-tests
```

Available options:

| Option | Description |
|--------|-------------|
| `--grammar -g` | Path to the grammar file (required) |
| `--input -i` | Input string to analyze |
| `--sets` | Show FIRST and FOLLOW sets (Item 1) |
| `--ll1` | Run LL(1) parser |
| `--slr1` | Run SLR(1) parser |
| `--clasificar` | Classify as LL(1) and/or SLR(1) |
| `--table` | Show constructed table(s) |
| `--step` | Show step-by-step analysis |
| `--run-tests` | Run automated tests |
| `--all` | Run all Item 2 scenarios |

---

## 3. Item 1 — FIRST and FOLLOW

Implemented in `parser_engine/first_follow.py` following Aho et al. (Section 4.4.2).

- `compute_first(grammar)`: computes FIRST(X) for each symbol.
- `compute_follow(grammar, first)`: computes FOLLOW(A) for each non-terminal.

**Special handling:**
- `e` (epsilon) propagates correctly through productions.
- `$` is placed in FOLLOW of the start symbol.
- Grammars with empty productions (`e`) are handled without issues.

### Example output (gram_expr)

```
First(E) = {(, id}
Follow(E) = {$, )}
First(E') = {+, e}
Follow(E') = {$, )}
```

---

## 4. Item 2 — LL(1) and SLR(1) Parsers

Implemented in `parser_engine/ll1.py` and `parser_engine/slr1.py` following Aho et al.

### Item 2A — LL(1) Parser

- LL(1) condition verification without transforming the grammar (no left-recursion elimination or left-factoring).
- Predictive parsing table construction `M[A, a]`.
- LL(1) conflict detection (cells with more than one production).
- Non-recursive predictive parsing with stack and input terminated by `$`.
- Step-by-step simulation: step number, stack, remaining input, action executed.

### Item 2B — SLR(1) Parser

- Augmented grammar `S' -> S`.
- LR(0) items with dot position.
- `CLOSURE(I)` and `GOTO(I, X)` algorithms.
- Canonical LR(0) collection of states.
- `ACTION` and `GOTO` tables using FOLLOW from Item 1.
- **Shift/Reduce** and **Reduce/Reduce** conflict detection.
- LR parser with state stack: shift, reduce, and accept.
- LR(0) automaton visualizable in SVG.
- Step-by-step simulation with state stack.

### Four verified classification scenarios

| Scenario | File | Result |
|----------|------|--------|
| LL(1) and SLR(1) | `gram_expr.txt` | Both |
| LL(1) only | `gram_ll_not_slr.txt` | LL(1) yes, SLR(1) no |
| SLR(1) only | `gram_leftrec.txt` | SLR(1) yes, LL(1) no |
| None | `gram_dangling.txt` / `gram_rr.txt` | Neither LL(1) nor SLR(1) |

---

## 5. Item 3 — Syntax-Directed Definition (SDD)

Implemented in `parser_engine/sdd.py` and `parser_engine/sdd_report.py` following Aho et al. (Chapter 5).

### Components

- **Syntax tree:** built from the LL(1) predictive table and the input string.
- **Attribute table:** symbol, name, type, nature (synthesized/inherited/lexical), meaning.
- **Semantic rules:** associated with each SDD production.
- **Annotated syntax tree:** attributes calculated on each node (SVG).
- **Dependency graph:** vertices = node attributes, edges = dependencies, color differentiation (synthesized = blue, inherited = orange, lexical = green).
- **Topological order:** real sequence of attribute evaluation.
- **Attribute evaluation:** step-by-step trace with values used and result.
- **Cycle detection:** evaluation stops if a circular definition is found.

### Test grammar (`gram_sdd.txt`)

```
4
S -> L
L -> [ M ] | e
M -> id R | e
R -> ; id R | e
```

### Example execution (web or CLI)

Input: `[id;id]`

Expected result: `S.val = [1:id; 2:id]`

**CLI commands for Item 3 (SDD):**

```bash
# Run the interactive SDD driver
python sdd_app.py gramaticas/gram_sdd.txt
# (Type one string per line, use e for epsilon, and press Enter on an empty line to finish).

# Run automated SDD and circularity tests
python -m tests.test_sdd
```

The SDD numbers identifiers by their position in the list.

### Cycle detection

If the dependency graph contains a cycle, evaluation stops and an explanatory message is displayed identifying the circular definition.

---

## 6. Automatic grammar loading

The web server automatically detects `.txt` files in the `gramaticas/` folder using a robust relative path:

```python
os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gramaticas')
```

This guarantees that:
- No manual grammar file upload is requested from the user.
- The grammar folder is not duplicated.
- No absolute paths dependent on a specific computer are used.
- When grammars are added or modified, the server detects them on each request (no restart needed).
- Only files inside `gramaticas/` are read (prevents arbitrary file reading outside the authorized folder).

---

## 7. Automated tests

The project includes three test suites:

```bash
# Item 1: FIRST and FOLLOW
python test_sets.py

# Item 2: LL(1) and SLR(1) (70 tests)
python test_item2.py

# Item 3: SDD and cycle detection
python -m tests.test_sdd
```

All tests should pass with result `OK`.

---

## 8. Instructions to clone and run in another environment

```bash
# 1. Clone the repository
git clone https://github.com/LumaC-Vs/Proyecto-final-de-lenguajes-formales.git
cd Proyecto-final-de-lenguajes-formales

# 2. Create and activate virtual environment (recommended but optional)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the web server
python server.py

# 5. Open the browser at http://127.0.0.1:5000
```

It is not necessary to configure local paths or manually load grammar files: the server discovers them automatically from `gramaticas/`.

---

## 9. Changes made to the original project

All original algorithms were preserved without modifying their academic logic. The changes were:

- **`parser_engine/grammar.py`**: `start_symbol` is no longer hardcoded to `'S'`; it is inferred from the first production of the file (supports both `S` and `E`).
- **`parser_engine/sdd.py`**: recovered the Item 3 implementation (it was empty in the original repository).
- **`parser_engine/sdd_report.py`**: new file with JSON report layer for the web server (reuses `sdd.py` without modifying its logic).
- **`app.py`**: only the example docstring was updated to reflect that `gram_expr.txt` uses `E` as start symbol.
- **`gramaticas/gram_expr.txt`**: restored to the original version with `E -> T E'`.
- **New files:** `server.py`, `requirements.txt`, `static/`, `templates/` (base, index, item1, item2, item3), `.gitignore`.

---

## 10. System requirements

- **Python 3** (tested with Python 3.14.4)
- **Flask 3.1.3** (installed via `requirements.txt`)
- No external parser libraries or automatic generators are required.

---

## 11. License and academic use

This project was developed as the final work for the Formal Languages and Compilers course. All algorithms are implemented manually from scratch following Aho et al. (Compilers: Principles, Techniques, and Tools).