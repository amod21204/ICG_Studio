from compiler.optimizer import is_number, parse_num, eval_binop

class Interpreter:
    def __init__(self, instructions):
        self.instructions = instructions
        self.env = {}
        self.trace = []

    def run(self, max_steps=500):
        self.env = {}
        self.trace = []

        # Map labels to instruction indices
        label_map = {}
        for idx, instr in enumerate(self.instructions):
            if instr.op == 'label':
                label_map[instr.result] = idx

        pc = 0
        steps = 0
        runtime_error = None

        while pc < len(self.instructions) and steps < max_steps:
            instr = self.instructions[pc]
            steps += 1

            step_info = {
                "step": steps,
                "pc": pc,
                "tac": instr.to_tac(),
                "variables": dict(self.env)
            }

            try:
                if instr.op == 'label':
                    pc += 1
                elif instr.op == '=':
                    val = self._resolve(instr.arg1)
                    self.env[instr.result] = val
                    step_info["action"] = f"Assigned {instr.result} = {val}"
                    pc += 1
                elif instr.op in ('+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='):
                    v1 = self._resolve(instr.arg1)
                    v2 = self._resolve(instr.arg2)
                    res = eval_binop(instr.op, v1, v2)
                    self.env[instr.result] = res
                    step_info["action"] = f"Computed {instr.result} = {res}"
                    pc += 1
                elif instr.op == 'uminus':
                    v1 = self._resolve(instr.arg1)
                    res = -v1
                    self.env[instr.result] = res
                    step_info["action"] = f"Computed {instr.result} = {res}"
                    pc += 1
                elif instr.op == 'goto':
                    step_info["action"] = f"Jumped to {instr.result}"
                    pc = label_map.get(instr.result, len(self.instructions))
                elif instr.op == 'if_false':
                    cond_val = self._resolve(instr.arg1)
                    if cond_val == 0 or cond_val is False:
                        step_info["action"] = f"Condition '{instr.arg1}' is FALSE (0) -> jumped to {instr.result}"
                        pc = label_map.get(instr.result, len(self.instructions))
                    else:
                        step_info["action"] = f"Condition '{instr.arg1}' is TRUE ({cond_val}) -> fallthrough"
                        pc += 1
                elif instr.op == 'if_true':
                    cond_val = self._resolve(instr.arg1)
                    if cond_val != 0 and cond_val is not False:
                        step_info["action"] = f"Condition '{instr.arg1}' is TRUE ({cond_val}) -> jumped to {instr.result}"
                        pc = label_map.get(instr.result, len(self.instructions))
                    else:
                        step_info["action"] = f"Condition '{instr.arg1}' is FALSE (0) -> fallthrough"
                        pc += 1
                else:
                    pc += 1
            except ZeroDivisionError as err:
                step_info["action"] = f"Execution Error: {str(err)}"
                runtime_error = str(err)
                self.trace.append(step_info)
                break

            user_vars = {k: v for k, v in self.env.items() if not k.startswith('t')}
            step_info["variables"] = user_vars
            self.trace.append(step_info)

        user_vars = {k: v for k, v in self.env.items() if not k.startswith('t')}
        return {
            "final_variables": user_vars,
            "all_variables": self.env,
            "steps_count": len(self.trace),
            "trace": self.trace[:60],
            "runtime_error": runtime_error
        }

    def _resolve(self, val):
        if is_number(val):
            return parse_num(val)
        return self.env.get(val, 0)
