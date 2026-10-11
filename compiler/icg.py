from compiler.parser import (
    ProgramNode, AssignNode, IfNode, WhileNode,
    BlockNode, BinOpNode, UnaryOpNode, VarNode, NumNode
)

class Instruction:
    def __init__(self, op, arg1=None, arg2=None, result=None, label=None):
        self.op = op          # e.g., '+', '=', 'if_false', 'goto', 'label'
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result  # Target variable or label
        self.label = label    # Optional label marking this instruction

    def to_tac(self):
        if self.op == 'label':
            return f"{self.result}:"
        elif self.op == '=':
            return f"{self.result} = {self.arg1}"
        elif self.op in ('+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.op == 'uminus':
            return f"{self.result} = -{self.arg1}"
        elif self.op == 'if_false':
            return f"if_false {self.arg1} goto {self.result}"
        elif self.op == 'if_true':
            return f"if {self.arg1} goto {self.result}"
        elif self.op == 'goto':
            return f"goto {self.result}"
        return f"{self.op} {self.arg1} {self.arg2} -> {self.result}"

    def to_quadruple(self):
        return {
            "op": self.op,
            "arg1": str(self.arg1) if self.arg1 is not None else "-",
            "arg2": str(self.arg2) if self.arg2 is not None else "-",
            "result": str(self.result) if self.result is not None else "-"
        }

    def get_why(self):
        if self.op == 'label':
            return f"Defines jump destination label '{self.result}' for branch targets and loop boundaries."
        elif self.op == 'goto':
            return f"Unconditional jump transferring program execution directly to label '{self.result}'."
        elif self.op == 'if_false':
            return f"Conditional jump: checks condition '{self.arg1}'. If false (0), jumps to label '{self.result}'."
        elif self.op == 'if_true':
            return f"Conditional jump: checks condition '{self.arg1}'. If true (non-zero), jumps to label '{self.result}'."
        elif self.op == '=':
            if self.result and self.result.startswith('t'):
                return f"Stores immediate value '{self.arg1}' into temporary '{self.result}' for following computations."
            return f"Assigns evaluated expression value '{self.arg1}' into program variable '{self.result}'."
        elif self.op == '+':
            return f"Calculates sum of '{self.arg1}' and '{self.arg2}', storing result in temporary '{self.result}'."
        elif self.op == '-':
            return f"Subtracts '{self.arg2}' from '{self.arg1}', storing difference in temporary '{self.result}'."
        elif self.op == '*':
            return f"Multiplies '{self.arg1}' by '{self.arg2}', saving product in temporary '{self.result}' respecting precedence."
        elif self.op == '/':
            return f"Divides '{self.arg1}' by '{self.arg2}', saving quotient in temporary '{self.result}'."
        elif self.op == '%':
            return f"Computes modulo of '{self.arg1}' by '{self.arg2}', storing remainder in temporary '{self.result}'."
        elif self.op in ('==', '!=', '<', '>', '<=', '>='):
            return f"Evaluates relational test ({self.arg1} {self.op} {self.arg2}), setting flag (1 for true, 0 for false) in '{self.result}'."
        elif self.op == 'uminus':
            return f"Applies unary negation to '{self.arg1}', saving signed value in temporary '{self.result}'."
        return f"Executes operation '{self.op}' with arguments '{self.arg1}' and '{self.arg2}' into '{self.result}'."

    def __repr__(self):
        return self.to_tac()


class ICG:
    def __init__(self):
        self.temp_id = 1
        self.label_id = 1
        self.instructions = []

    def new_temp(self):
        t = f"t{self.temp_id}"
        self.temp_id += 1
        return t

    def new_label(self):
        l = f"L{self.label_id}"
        self.label_id += 1
        return l

    def emit(self, op, arg1=None, arg2=None, result=None):
        instr = Instruction(op, arg1, arg2, result)
        self.instructions.append(instr)
        return instr

    def emit_label(self, label_name):
        instr = Instruction('label', result=label_name)
        self.instructions.append(instr)
        return instr

    def generate(self, ast_root):
        self.instructions = []
        self.temp_id = 1
        self.label_id = 1
        self._gen_node(ast_root)
        return self.instructions

    def _gen_node(self, node):
        if isinstance(node, ProgramNode):
            for stmt in node.statements:
                self._gen_node(stmt)

        elif isinstance(node, AssignNode):
            rhs = self._gen_expr(node.expr)
            self.emit('=', rhs, None, node.var_name)

        elif isinstance(node, IfNode):
            cond = self._gen_expr(node.condition)
            l_else = self.new_label()
            l_end = self.new_label()

            if node.else_branch:
                self.emit('if_false', cond, None, l_else)
                self._gen_node(node.then_branch)
                self.emit('goto', None, None, l_end)
                self.emit_label(l_else)
                self._gen_node(node.else_branch)
                self.emit_label(l_end)
            else:
                self.emit('if_false', cond, None, l_end)
                self._gen_node(node.then_branch)
                self.emit_label(l_end)

        elif isinstance(node, WhileNode):
            l_start = self.new_label()
            l_end = self.new_label()

            self.emit_label(l_start)
            cond = self._gen_expr(node.condition)
            self.emit('if_false', cond, None, l_end)
            self._gen_node(node.body)
            self.emit('goto', None, None, l_start)
            self.emit_label(l_end)

        elif isinstance(node, BlockNode):
            for stmt in node.statements:
                self._gen_node(stmt)

    def _gen_expr(self, node):
        if isinstance(node, NumNode):
            return str(node.value)
        elif isinstance(node, VarNode):
            return node.name
        elif isinstance(node, BinOpNode):
            left = self._gen_expr(node.left)
            right = self._gen_expr(node.right)
            t = self.new_temp()
            self.emit(node.op, left, right, t)
            return t
        elif isinstance(node, UnaryOpNode):
            val = self._gen_expr(node.operand)
            t = self.new_temp()
            self.emit('uminus', val, None, t)
            return t
        return ""


def build_triples(instructions):
    triples = []
    temp_map = {}  # maps temp var (e.g. 't1') to triple index (e.g. '(0)')

    for idx, instr in enumerate(instructions):
        arg1_val = str(instr.arg1) if instr.arg1 is not None else "-"
        arg2_val = str(instr.arg2) if instr.arg2 is not None else "-"

        # Replace temp with triple reference
        if arg1_val in temp_map:
            arg1_val = temp_map[arg1_val]
        if arg2_val in temp_map:
            arg2_val = temp_map[arg2_val]

        if instr.op == '=':
            triples.append({
                "index": f"({idx})",
                "op": "=",
                "arg1": str(instr.result),
                "arg2": arg1_val
            })
        elif instr.op == 'label':
            triples.append({
                "index": f"({idx})",
                "op": "label",
                "arg1": str(instr.result),
                "arg2": "-"
            })
        elif instr.op in ('goto', 'if_false'):
            triples.append({
                "index": f"({idx})",
                "op": instr.op,
                "arg1": arg1_val if instr.op == 'if_false' else str(instr.result),
                "arg2": str(instr.result) if instr.op == 'if_false' else "-"
            })
        else:
            triples.append({
                "index": f"({idx})",
                "op": instr.op,
                "arg1": arg1_val,
                "arg2": arg2_val
            })
            if instr.result and instr.result.startswith('t'):
                temp_map[instr.result] = f"({idx})"

    return triples


def build_basic_blocks(instructions):
    """
    Partitions 3-Address Code into Basic Blocks using textbook Dragon Book rules:
    1. First instruction is a leader.
    2. Target of a jump is a leader.
    3. Instruction following a jump is a leader.
    """
    if not instructions:
        return []

    leaders = {0}
    label_to_index = {}

    for idx, instr in enumerate(instructions):
        if instr.op == 'label':
            label_to_index[instr.result] = idx
            leaders.add(idx)

    for idx, instr in enumerate(instructions):
        if instr.op in ('goto', 'if_false', 'if_true'):
            target_label = instr.result
            if target_label in label_to_index:
                leaders.add(label_to_index[target_label])
            if idx + 1 < len(instructions):
                leaders.add(idx + 1)

    sorted_leaders = sorted(list(leaders))
    blocks = []

    for i in range(len(sorted_leaders)):
        start = sorted_leaders[i]
        end = sorted_leaders[i + 1] if i + 1 < len(sorted_leaders) else len(instructions)
        block_instrs = instructions[start:end]

        block_id = f"B{i + 1}"
        tac_lines = [instr.to_tac() for instr in block_instrs]

        # Determine jumps / control flow successors
        successors = []
        last_instr = block_instrs[-1] if block_instrs else None

        if last_instr:
            if last_instr.op == 'goto':
                target = last_instr.result
                for b_idx, s in enumerate(sorted_leaders):
                    if instructions[s].op == 'label' and instructions[s].result == target:
                        successors.append(f"B{b_idx + 1}")
                        break
            elif last_instr.op in ('if_false', 'if_true'):
                target = last_instr.result
                # Conditional branch target
                for b_idx, s in enumerate(sorted_leaders):
                    if instructions[s].op == 'label' and instructions[s].result == target:
                        successors.append(f"B{b_idx + 1}")
                        break
                # Fallthrough target
                if i + 1 < len(sorted_leaders):
                    successors.append(f"B{i + 2}")
            else:
                # Normal fallthrough to next block
                if i + 1 < len(sorted_leaders):
                    successors.append(f"B{i + 2}")

        blocks.append({
            "id": block_id,
            "instructions": tac_lines,
            "successors": successors
        })

    return blocks
