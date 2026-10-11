"""
Lex & Yacc Equivalent Simulation in Python
This script mirrors lexer.l and parser.y using recursive descent parsing.
It builds the AST and generates Three-Address Code (TAC) for input.txt.
"""

import sys
import re

# ----------------- LEXER -----------------
TOKEN_SPEC = [
    ('IF',      r'\bif\b'),
    ('ELSE',    r'\belse\b'),
    ('NUMBER',  r'\d+'),
    ('ID',      r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('EQ',      r'=='),
    ('NE',      r'!='),
    ('LE',      r'<='),
    ('GE',      r'>='),
    ('GT',      r'>'),
    ('LT',      r'<'),
    ('PLUS',    r'\+'),
    ('MINUS',   r'-'),
    ('MUL',     r'\*'),
    ('DIV',     r'/'),
    ('ASSIGN',  r'='),
    ('SEMI',    r';'),
    ('LBRACE',  r'\{'),
    ('RBRACE',  r'\}'),
    ('LPAREN',  r'\('),
    ('RPAREN',  r'\)'),
    ('COMMENT', r'//.*'),
    ('SKIP',    r'[ \t\r\n]+'),
    ('MISMATCH',r'.'),
]

tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)

class Token:
    def __init__(self, type_, val, line):
        self.type = type_
        self.val = val
        self.line = line
    def __repr__(self):
        return f"Token({self.type}, {self.val})"

def tokenize(code):
    tokens = []
    line_num = 1
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP' or kind == 'COMMENT':
            line_num += value.count('\n')
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected character {value!r} on line {line_num}")
        tokens.append(Token(kind, value, line_num))
    tokens.append(Token('EOF', '', line_num))
    return tokens

# ----------------- AST NODES -----------------
class ASTNode:
    pass

class NumNode(ASTNode):
    def __init__(self, val):
        self.val = val

class IdNode(ASTNode):
    def __init__(self, val):
        self.val = val

class BinOpNode(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class AssignNode(ASTNode):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

class IfNode(ASTNode):
    def __init__(self, cond, then_part, else_part=None):
        self.cond = cond
        self.then_part = then_part
        self.else_part = else_part

class BlockNode(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts

# ----------------- PARSER -----------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def match(self, expected_type):
        tok = self.current()
        if tok.type == expected_type:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected {expected_type}, got {tok.type} ('{tok.val}') at line {tok.line}")

    def parse_program(self):
        stmts = []
        while self.current().type != 'EOF':
            stmts.append(self.parse_statement())
        return BlockNode(stmts)

    def parse_statement(self):
        tok = self.current()
        if tok.type == 'ID':
            var_name = self.match('ID').val
            self.match('ASSIGN')
            expr = self.parse_expr()
            self.match('SEMI')
            return AssignNode(var_name, expr)
        elif tok.type == 'IF':
            self.match('IF')
            self.match('LPAREN')
            cond = self.parse_expr()
            self.match('RPAREN')
            then_part = self.parse_statement()
            else_part = None
            if self.current().type == 'ELSE':
                self.match('ELSE')
                else_part = self.parse_statement()
            return IfNode(cond, then_part, else_part)
        elif tok.type == 'LBRACE':
            self.match('LBRACE')
            stmts = []
            while self.current().type != 'RBRACE' and self.current().type != 'EOF':
                stmts.append(self.parse_statement())
            self.match('RBRACE')
            return BlockNode(stmts)
        else:
            raise SyntaxError(f"Unexpected token {tok.type} at line {tok.line}")

    def parse_expr(self):
        return self.parse_relational()

    def parse_relational(self):
        left = self.parse_arithmetic()
        while self.current().type in ('EQ', 'NE', 'LT', 'GT', 'LE', 'GE'):
            op_tok = self.match(self.current().type)
            right = self.parse_arithmetic()
            left = BinOpNode(op_tok.val, left, right)
        return left

    def parse_arithmetic(self):
        left = self.parse_term()
        while self.current().type in ('PLUS', 'MINUS'):
            op_tok = self.match(self.current().type)
            right = self.parse_term()
            left = BinOpNode(op_tok.val, left, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.current().type in ('MUL', 'DIV'):
            op_tok = self.match(self.current().type)
            right = self.parse_factor()
            left = BinOpNode(op_tok.val, left, right)
        return left

    def parse_factor(self):
        tok = self.current()
        if tok.type == 'NUMBER':
            return NumNode(self.match('NUMBER').val)
        elif tok.type == 'ID':
            return IdNode(self.match('ID').val)
        elif tok.type == 'LPAREN':
            self.match('LPAREN')
            expr = self.parse_expr()
            self.match('RPAREN')
            return expr
        else:
            raise SyntaxError(f"Unexpected expression token {tok.type} at line {tok.line}")

# ----------------- TAC GENERATOR -----------------
class TACGenerator:
    def __init__(self):
        self.temp_count = 1
        self.label_count = 1
        self.code = []

    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self):
        l = f"L{self.label_count}"
        self.label_count += 1
        return l

    def emit(self, instruction):
        self.code.append(instruction)

    def generate(self, node):
        if isinstance(node, NumNode):
            return node.val
        elif isinstance(node, IdNode):
            return node.val
        elif isinstance(node, BinOpNode):
            left = self.generate(node.left)
            right = self.generate(node.right)
            t = self.new_temp()
            self.emit(f"{t} = {left} {node.op} {right}")
            return t
        elif isinstance(node, AssignNode):
            rhs = self.generate(node.expr)
            self.emit(f"{node.var} = {rhs}")
            return None
        elif isinstance(node, IfNode):
            cond = self.generate(node.cond)
            l_else = self.new_label()
            l_end = self.new_label()
            if node.else_part:
                self.emit(f"if_false {cond} goto {l_else}")
                self.generate(node.then_part)
                self.emit(f"goto {l_end}")
                self.emit(f"{l_else}:")
                self.generate(node.else_part)
                self.emit(f"{l_end}:")
            else:
                self.emit(f"if_false {cond} goto {l_end}")
                self.generate(node.then_part)
                self.emit(f"{l_end}:")
            return None
        elif isinstance(node, BlockNode):
            for stmt in node.stmts:
                self.generate(stmt)
            return None

def print_ast(node, indent=0):
    pref = "  " * indent
    if isinstance(node, NumNode):
        print(f"{pref}NUMBER: {node.val}")
    elif isinstance(node, IdNode):
        print(f"{pref}ID: {node.val}")
    elif isinstance(node, BinOpNode):
        print(f"{pref}BINOP ({node.op})")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, AssignNode):
        print(f"{pref}ASSIGN ({node.var} =)")
        print_ast(node.expr, indent + 1)
    elif isinstance(node, IfNode):
        print(f"{pref}IF STATEMENT")
        print(f"{pref}  [Condition]")
        print_ast(node.cond, indent + 2)
        print(f"{pref}  [Then Branch]")
        print_ast(node.then_part, indent + 2)
        if node.else_part:
            print(f"{pref}  [Else Branch]")
            print_ast(node.else_part, indent + 2)
    elif isinstance(node, BlockNode):
        for stmt in node.stmts:
            print_ast(stmt, indent)

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'input.txt'
    with open(filepath, 'r') as f:
        src = f.read()

    print("========================================")
    print("   COMPILER DESIGN: LEX & YACC PARSER   ")
    print("========================================\n")
    print(f"Reading input from: {filepath}\n")

    tokens = tokenize(src)
    parser = Parser(tokens)
    ast = parser.parse_program()

    print("[STATUS] Parsing finished successfully!\n")
    print("----------------------------------------")
    print("1. ABSTRACT SYNTAX TREE (AST)")
    print("----------------------------------------")
    print_ast(ast)

    print("\n----------------------------------------")
    print("2. THREE-ADDRESS CODE (TAC)")
    print("----------------------------------------")
    tac_gen = TACGenerator()
    tac_gen.generate(ast)
    for line in tac_gen.code:
        print(line)
    print("\n========================================")

if __name__ == '__main__':
    main()
