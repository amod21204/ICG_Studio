"""
Automated Test Suite for Compiler Construction Project
Executes all 7 critical tests specified in Technical Audit.
"""

from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.icg import ICG, build_triples, build_basic_blocks
from compiler.optimizer import Optimizer
from compiler.target_code import generate_target_code
from compiler.interpreter import Interpreter

def run_pipeline(code, passes=None):
    tokens = tokenize(code)
    parser = Parser(tokens)
    ast = parser.parse()
    icg = ICG()
    instructions = icg.generate(ast)
    quads = [i.to_quadruple() for i in instructions]
    triples = build_triples(instructions)
    blocks = build_basic_blocks(instructions)
    opt = Optimizer(instructions)
    opt_instrs, logs, passes_applied = opt.run_all(passes)
    target_code = generate_target_code(opt_instrs)
    interp = Interpreter(opt_instrs)
    exec_res = interp.run()

    return {
        "tokens": tokens,
        "ast": ast,
        "instructions": instructions,
        "tac": [i.to_tac() for i in instructions],
        "quads": quads,
        "triples": triples,
        "blocks": blocks,
        "opt_tac": [i.to_tac() for i in opt_instrs],
        "target_code": target_code,
        "exec": exec_res,
        "passes_applied": passes_applied
    }

def test_1():
    print("\n--- TEST 1: Arithmetic Precedence ---")
    code = "a = 10;\nb = 20;\nc = a + b * 2;"
    res = run_pipeline(code)
    print("TAC:")
    for t in res["tac"]: print(" ", t)
    print("Execution Variables:", res["exec"]["final_variables"])
    assert res["exec"]["final_variables"] == {'a': 10, 'b': 20, 'c': 50}, "Test 1 variable state mismatch!"
    raw_target_code = generate_target_code(res["instructions"])
    assert any("MUL" in line for line in raw_target_code.splitlines()), "Target code must include MUL on arithmetic expressions"
    print("Raw Target Code (excerpt):")
    for l in raw_target_code.splitlines()[:10]: print(" ", l)
    print("[PASS] TEST 1")

def test_2():
    print("\n--- TEST 2: Parentheses Precedence ---")
    code = "a = 10;\nb = 20;\nc = (a + b) * 2;"
    res = run_pipeline(code)
    print("Execution Variables:", res["exec"]["final_variables"])
    assert res["exec"]["final_variables"] == {'a': 10, 'b': 20, 'c': 60}, "Test 2 variable state mismatch! Expected c=60"
    print("[PASS] TEST 2")

def test_3():
    print("\n--- TEST 3: If-Else Branches & CFG ---")
    code = """a = 10;
b = 20;
c = a + b;

if (c > 30) {
    d = c - 5;
} else {
    d = c + 5;
}"""
    res = run_pipeline(code)
    print("Basic Blocks Count:", len(res["blocks"]))
    for b in res["blocks"]:
        print(f"  {b['id']}: {b['instructions']} -> Successors: {b['successors']}")
    print("Execution Variables:", res["exec"]["final_variables"])
    assert res["exec"]["final_variables"] == {'a': 10, 'b': 20, 'c': 30, 'd': 35}, "Test 3 variable mismatch!"
    print("[PASS] TEST 3")

def test_4():
    print("\n--- TEST 4: While Loop & CFG ---")
    code = """a = 0;

while (a < 5) {
    a = a + 1;
}"""
    res = run_pipeline(code)
    print("Basic Blocks Count:", len(res["blocks"]))
    for b in res["blocks"]:
        print(f"  {b['id']}: {b['instructions']} -> Successors: {b['successors']}")
    print("Execution Variables:", res["exec"]["final_variables"])
    assert res["exec"]["final_variables"] == {'a': 5}, f"Test 4 variable mismatch! Expected a=5, got {res['exec']['final_variables']}"
    print("[PASS] TEST 4")

def test_5():
    print("\n--- TEST 5: Optimization Passes ---")
    code = """a = 10 + 20;
b = a * 1;
c = b + 0;"""
    res = run_pipeline(code)
    print("Optimized TAC:")
    for t in res["opt_tac"]: print(" ", t)
    print("Passes Applied:", res["passes_applied"])
    print("Execution Variables:", res["exec"]["final_variables"])
    assert res["exec"]["final_variables"] == {'a': 30, 'b': 30, 'c': 30}, "Test 5 variable mismatch!"
    assert "Constant Folding" in res["passes_applied"]
    assert "Algebraic Simplification" in res["passes_applied"]
    print("[PASS] TEST 5")

def test_6():
    print("\n--- TEST 6: Syntax Error Handling (a = ;) ---")
    code = "a = ;"
    try:
        tokens = tokenize(code)
        parser = Parser(tokens)
        parser.parse()
        assert False, "Test 6 should have raised SyntaxError!"
    except SyntaxError as e:
        print("Caught Expected Syntax Error:", e)
        assert "Line 1" in str(e) or "Column" in str(e)
    print("[PASS] TEST 6")

def test_7():
    print("\n--- TEST 7: Division by Zero Error Handling (a = 10 / 0;) ---")
    code = "a = 10 / 0;"
    try:
        tokens = tokenize(code)
        parser = Parser(tokens)
        parser.parse()
        assert False, "Test 7 should have raised ZeroDivisionError!"
    except ZeroDivisionError as e:
        print("Caught Expected ZeroDivisionError:", e)
        assert "Division by zero" in str(e)
    print("[PASS] TEST 7")

if __name__ == "__main__":
    test_1()
    test_2()
    test_3()
    test_4()
    test_5()
    test_6()
    test_7()
    print("\n==========================================")
    print(" [OK] ALL 7 CRITICAL TESTS PASSED SUCCESSFULLY!")
    print("==========================================\n")
