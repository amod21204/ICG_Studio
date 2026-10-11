def generate_target_code(instructions):
    """
    Translates Intermediate TAC instructions into educational register-based pseudo-assembly.
    Supports: MOV, ADD, SUB, MUL, DIV, MOD, CMP, JMP, JE, JNE, JL, JG, JLE, JGE.
    """
    assembly = []
    reg_counter = 1
    rel_counter = 1

    for idx, instr in enumerate(instructions):
        op = instr.op
        arg1 = str(instr.arg1) if instr.arg1 is not None else ""
        arg2 = str(instr.arg2) if instr.arg2 is not None else ""
        res = str(instr.result) if instr.result is not None else ""

        assembly.append(f"; TAC: {instr.to_tac()}")

        if op == 'label':
            assembly.append(f"{res}:")

        elif op == 'goto':
            assembly.append(f"    JMP {res}")

        elif op == 'if_false':
            # Check condition against 0 (false)
            assembly.append(f"    CMP {arg1}, 0")
            assembly.append(f"    JE {res}")

        elif op == 'if_true':
            # Check condition against 0 (false)
            assembly.append(f"    CMP {arg1}, 0")
            assembly.append(f"    JNE {res}")

        elif op == '=':
            assembly.append(f"    MOV {res}, {arg1}")

        elif op in ('+', '-', '*', '/', '%'):
            r = f"R{reg_counter}"
            reg_counter = (reg_counter % 4) + 1  # Cycle R1 to R4

            assembly.append(f"    MOV {r}, {arg1}")
            if op == '+':
                assembly.append(f"    ADD {r}, {arg2}")
            elif op == '-':
                assembly.append(f"    SUB {r}, {arg2}")
            elif op == '*':
                assembly.append(f"    MUL {r}, {arg2}")
            elif op == '/':
                assembly.append(f"    DIV {r}, {arg2}")
            elif op == '%':
                assembly.append(f"    MOD {r}, {arg2}")

            assembly.append(f"    MOV {res}, {r}")

        elif op in ('==', '!=', '<', '>', '<=', '>='):
            r = f"R{reg_counter}"
            reg_counter = (reg_counter % 4) + 1
            lbl_true = f".L_rel_true_{rel_counter}"
            lbl_end = f".L_rel_end_{rel_counter}"
            rel_counter += 1

            assembly.append(f"    MOV {r}, 0")
            assembly.append(f"    CMP {arg1}, {arg2}")

            if op == '==':
                assembly.append(f"    JE {lbl_true}")
            elif op == '!=':
                assembly.append(f"    JNE {lbl_true}")
            elif op == '<':
                assembly.append(f"    JL {lbl_true}")
            elif op == '>':
                assembly.append(f"    JG {lbl_true}")
            elif op == '<=':
                assembly.append(f"    JLE {lbl_true}")
            elif op == '>=':
                assembly.append(f"    JGE {lbl_true}")

            assembly.append(f"    JMP {lbl_end}")
            assembly.append(f"{lbl_true}:")
            assembly.append(f"    MOV {r}, 1")
            assembly.append(f"{lbl_end}:")
            assembly.append(f"    MOV {res}, {r}")

        elif op == 'uminus':
            r = f"R{reg_counter}"
            reg_counter = (reg_counter % 4) + 1
            assembly.append(f"    MOV {r}, 0")
            assembly.append(f"    SUB {r}, {arg1}")
            assembly.append(f"    MOV {res}, {r}")

        assembly.append("")  # Empty line separator

    return "\n".join(assembly).strip()
