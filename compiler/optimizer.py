import copy
from compiler.icg import Instruction

def is_number(val):
    if val is None:
        return False
    try:
        float(val)
        return True
    except ValueError:
        return False

def parse_num(val):
    f = float(val)
    return int(f) if f.is_integer() else f

def eval_binop(op, a, b):
    a = parse_num(a)
    b = parse_num(b)
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '/':
        if b == 0:
            raise ZeroDivisionError(f"Semantic Error: Division by zero encountered ({a} / 0)")
        return a // b if (isinstance(a, int) and isinstance(b, int) and a % b == 0) else a / b
    if op == '%':
        if b == 0:
            raise ZeroDivisionError(f"Semantic Error: Modulo by zero encountered ({a} % 0)")
        return a % b
    if op == '==': return 1 if a == b else 0
    if op == '!=': return 1 if a != b else 0
    if op == '<':  return 1 if a < b else 0
    if op == '>':  return 1 if a > b else 0
    if op == '<=': return 1 if a <= b else 0
    if op == '>=': return 1 if a >= b else 0
    return None

class Optimizer:
    def __init__(self, instructions):
        self.instructions = [copy.deepcopy(instr) for instr in instructions]
        self.logs = []
        self.passes_applied = set()

    def log(self, pass_name, detail):
        self.logs.append({
            "pass": pass_name,
            "detail": detail
        })
        self.passes_applied.add(pass_name)

    def run_all(self, passes=None):
        """
        Runs configured optimization passes iteratively until fixed point or max iterations.
        """
        if passes is None:
            passes = ['constant_propagation', 'constant_folding', 'algebraic_simplification', 'common_subexpression', 'dead_code_elimination']

        iteration = 0
        max_iterations = 6

        while iteration < max_iterations:
            initial_state = [repr(i) for i in self.instructions]

            if 'constant_propagation' in passes:
                self.constant_propagation()

            if 'constant_folding' in passes:
                self.constant_folding()

            if 'algebraic_simplification' in passes:
                self.algebraic_simplification()

            if 'common_subexpression' in passes:
                self.common_subexpression_elimination()

            if 'dead_code_elimination' in passes:
                self.dead_code_elimination()

            final_state = [repr(i) for i in self.instructions]
            if initial_state == final_state:
                break
            iteration += 1

        return self.instructions, self.logs, sorted(list(self.passes_applied))

    def constant_propagation(self):
        """
        Replaces variables whose values are known constants with the constant literal.
        Works across straight-line code between labels / branches.
        """
        known_constants = {}

        for instr in self.instructions:
            # Labels or jumps clear or invalidate straight-line assumptions
            if instr.op in ('label', 'goto', 'if_false', 'if_true'):
                known_constants.clear()
                continue

            # Check if arg1 can be propagated
            if instr.arg1 and not is_number(instr.arg1) and instr.arg1 in known_constants:
                old = instr.arg1
                instr.arg1 = str(known_constants[old])
                self.log("Constant Propagation", f"Replaced '{old}' with constant '{instr.arg1}' in '{instr.to_tac()}'")

            # Check if arg2 can be propagated
            if instr.arg2 and not is_number(instr.arg2) and instr.arg2 in known_constants:
                old = instr.arg2
                instr.arg2 = str(known_constants[old])
                self.log("Constant Propagation", f"Replaced '{old}' with constant '{instr.arg2}' in '{instr.to_tac()}'")

            # Track new constants: x = 10
            if instr.op == '=' and is_number(instr.arg1) and instr.result:
                known_constants[instr.result] = parse_num(instr.arg1)
            elif instr.result and instr.result in known_constants:
                del known_constants[instr.result]

    def constant_folding(self):
        """
        Evaluates constant expressions at compile-time:
        t1 = 20 * 2  -->  t1 = 40
        """
        for instr in self.instructions:
            if instr.op in ('+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='):
                if is_number(instr.arg1) and is_number(instr.arg2):
                    folded = eval_binop(instr.op, instr.arg1, instr.arg2)
                    if folded is not None:
                        orig = instr.to_tac()
                        instr.op = '='
                        instr.arg1 = str(folded)
                        instr.arg2 = None
                        self.log("Constant Folding", f"Folded expression: '{orig}' -> '{instr.to_tac()}'")
            elif instr.op == 'uminus' and is_number(instr.arg1):
                orig = instr.to_tac()
                folded = -parse_num(instr.arg1)
                instr.op = '='
                instr.arg1 = str(folded)
                self.log("Constant Folding", f"Folded unary negation: '{orig}' -> '{instr.to_tac()}'")

    def algebraic_simplification(self):
        """
        Simplifies algebraic identities:
        x + 0 -> x
        x - 0 -> x
        x * 1 -> x
        x / 1 -> x
        x * 0 -> 0
        """
        for instr in self.instructions:
            if instr.op == '+':
                if instr.arg2 == '0':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = {instr.arg1}'")
                    instr.op = '='
                    instr.arg2 = None
                elif instr.arg1 == '0':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = {instr.arg2}'")
                    instr.op = '='
                    instr.arg1 = instr.arg2
                    instr.arg2 = None
            elif instr.op == '-':
                if instr.arg2 == '0':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = {instr.arg1}'")
                    instr.op = '='
                    instr.arg2 = None
            elif instr.op == '*':
                if instr.arg2 == '1':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = {instr.arg1}'")
                    instr.op = '='
                    instr.arg2 = None
                elif instr.arg1 == '1':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = {instr.arg2}'")
                    instr.op = '='
                    instr.arg1 = instr.arg2
                    instr.arg2 = None
                elif instr.arg2 == '0' or instr.arg1 == '0':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = 0'")
                    instr.op = '='
                    instr.arg1 = '0'
                    instr.arg2 = None
            elif instr.op == '/':
                if instr.arg2 == '1':
                    self.log("Algebraic Simplification", f"Identity: '{instr.to_tac()}' -> '{instr.result} = {instr.arg1}'")
                    instr.op = '='
                    instr.arg2 = None

    def common_subexpression_elimination(self):
        """
        Eliminates duplicate computations within straight-line blocks:
        t1 = a + b
        ... (a, b unmodified)
        t2 = a + b  -->  t2 = t1
        """
        expr_map = {}  # (op, arg1, arg2) -> result_var

        for instr in self.instructions:
            if instr.op in ('label', 'goto', 'if_false', 'if_true'):
                expr_map.clear()
                continue

            # Check if this instruction computes an already known expression
            if instr.op in ('+', '-', '*', '/', '%'):
                key = (instr.op, instr.arg1, instr.arg2)
                # Commutative operations (+, *) sort operands
                if instr.op in ('+', '*'):
                    sorted_args = sorted([str(instr.arg1), str(instr.arg2)])
                    key = (instr.op, sorted_args[0], sorted_args[1])

                if key in expr_map:
                    prev_res = expr_map[key]
                    orig = instr.to_tac()
                    instr.op = '='
                    instr.arg1 = prev_res
                    instr.arg2 = None
                    self.log("Common Subexpression Elimination", f"Reused subexpression '{orig}' -> '{instr.to_tac()}'")
                else:
                    expr_map[key] = instr.result

            # Invalidate expressions containing variable if reassigned
            if instr.result:
                res_var = instr.result
                keys_to_del = [k for k in expr_map if k[1] == res_var or k[2] == res_var]
                for k in keys_to_del:
                    del expr_map[k]

    def dead_code_elimination(self):
        """
        Removes temporary assignments (t1 = ...) that are never read subsequently.
        Guarantees that user variables (a, b, x, etc.) are NOT eliminated.
        """
        used_variables = set()
        for instr in self.instructions:
            if instr.arg1 and not is_number(instr.arg1):
                used_variables.add(instr.arg1)
            if instr.arg2 and not is_number(instr.arg2):
                used_variables.add(instr.arg2)

        new_instructions = []
        for instr in self.instructions:
            if instr.op == '=' and instr.result and instr.result.startswith('t'):
                if instr.result not in used_variables:
                    self.log("Dead Code Elimination", f"Removed dead temporary assignment: '{instr.to_tac()}'")
                    continue
            new_instructions.append(instr)

        self.instructions = new_instructions
