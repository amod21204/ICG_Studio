# Compiler Construction Studio

An interactive, end-to-end Compiler Design and Multi-Pass Optimization Studio with a rich web dashboard and pure Python backend.

**Technology Stack:**
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Backend:** Python 3 (100% Standard Library — **Zero `pip install` required**)

---

## 🌟 Architecture & Features

1. **Lexical Analysis (Scanner)**:
   - Full support for identifiers (`a`, `x`, `student_name`), numbers (`0`, `10`, `100`), operators (`+`, `-`, `*`, `/`, `%`), relational operators (`==`, `!=`, `<`, `>`, `<=`, `>=`), assignment (`=`), keywords (`if`, `else`, `while`), symbols (`(`, `)`, `{`, `}`, `;`), and comments (`//`).
   - Generates a searchable **Tokens Table** with Type, Lexeme, Line, and Column.

2. **Syntax Analysis & AST Visualizer**:
   - Operator precedence parsing: Parentheses > Unary Minus > `*`, `/`, `%` > `+`, `-` > Relational > Assignment.
   - Dynamic hierarchical **Abstract Syntax Tree (AST)** visualization.

3. **Three-Address Code (TAC)**:
   - Dynamic temporary generation (`t1`, `t2`, ...) and label generation (`L1`, `L2`, ...).
   - Dedicated **"Why This Instruction?"** pedagogical breakdowns for every TAC statement.

4. **Intermediate Representations**:
   - **Quadruples Table**: `(op, arg1, arg2, result)`
   - **Triples Table**: `(index, op, arg1, arg2)` with index back-references `(0)`, `(1)`

5. **Basic Blocks & Control Flow Graph (CFG)**:
   - Textbook leader detection (Entry, Jump targets, Post-jump instructions).
   - Visual **Directed CFG Graph** with SVG connector arrows and conditional/fallthrough transitions.

6. **Multi-Pass Code Optimizer**:
   - **Constant Folding**: Evaluates compile-time operations (e.g. `10 + 20` -> `30`).
   - **Constant Propagation**: Propagates known constants across straight-line blocks.
   - **Algebraic Identities**: Simplifies `x + 0`, `x - 0`, `x * 1`, `x / 1`, `x * 0`.
   - **Common Subexpression Elimination (CSE)**: Reuses computed temporary results.
   - **Dead Code Elimination (DCE)**: Eliminates unreferenced temporary calculations while preserving user variables.
   - **Dynamic Optimization Report**: Shows before/after lines, count removed, % reduction, and applied pass badges.

7. **Educational Target-like Pseudo-Assembly**:
   - Converts TAC into assembly instructions (`MOV`, `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `CMP`, `JMP`, `JE`, `JNE`, `JL`, `JG`, `JLE`, `JGE`).

8. **Runtime Execution & Memory Store**:
   - Step-by-step emulation of TAC instructions with memory state tracker (`a = 10`, `b = 20`, `c = 50`, `d = 45`).

---

## 🚀 How to Run the Project

No dependencies to install! Run directly using Python 3:

```powershell
python server.py
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 🧪 Automated Testing

To run the full automated verification test suite:

```powershell
python test_suite.py
```

All 7 test cases (Precedence, Parentheses, If-Else CFG, While Loop CFG, Multi-Pass Optimization, Syntax Error, and Zero Division) will execute and report `[PASS]`.

---

## 👥 Developers

- **Amod Pathak**: Compiler Logic & Full-Stack Development
  - *Responsibilities:* Intermediate Code Generation, Parser/compiler grammar logic, Multi-pass optimization engine, Backend server integration.
- **Utkarsh Kuchankar**: Frontend & System Development
  - *Responsibilities:* UI architecture, AST & Directed CFG visualizers, Frontend integration, Test scenarios & presentation.
