class ASTNode:
    def to_dict(self):
        raise NotImplementedError

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def to_dict(self):
        return {
            "name": "Program",
            "type": "Program",
            "children": [s.to_dict() for s in self.statements]
        }

class AssignNode(ASTNode):
    def __init__(self, var_name, expr, line, column=1):
        self.var_name = var_name
        self.expr = expr
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "name": f"ASSIGN: {self.var_name} =",
            "type": "Assignment",
            "var": self.var_name,
            "line": self.line,
            "children": [
                {
                    "name": f"ID: {self.var_name}",
                    "type": "Identifier",
                    "value": self.var_name,
                    "line": self.line
                },
                self.expr.to_dict()
            ]
        }

class IfNode(ASTNode):
    def __init__(self, condition, then_branch, else_branch, line, column=1):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = line
        self.column = column

    def to_dict(self):
        node = {
            "name": "IF Statement",
            "type": "If",
            "line": self.line,
            "children": [
                {
                    "name": "Condition",
                    "type": "Branch",
                    "children": [self.condition.to_dict()]
                },
                {
                    "name": "Then",
                    "type": "Branch",
                    "children": [self.then_branch.to_dict()]
                }
            ]
        }
        if self.else_branch:
            node["children"].append({
                "name": "Else",
                "type": "Branch",
                "children": [self.else_branch.to_dict()]
            })
        return node

class WhileNode(ASTNode):
    def __init__(self, condition, body, line, column=1):
        self.condition = condition
        self.body = body
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "name": "WHILE Loop",
            "type": "While",
            "line": self.line,
            "children": [
                {
                    "name": "Condition",
                    "type": "Branch",
                    "children": [self.condition.to_dict()]
                },
                {
                    "name": "Body",
                    "type": "Branch",
                    "children": [self.body.to_dict()]
                }
            ]
        }

class BlockNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def to_dict(self):
        return {
            "name": "Block { }",
            "type": "Block",
            "children": [s.to_dict() for s in self.statements]
        }

class BinOpNode(ASTNode):
    def __init__(self, op, left, right, line, column=1):
        self.op = op
        self.left = left
        self.right = right
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "name": f"Op: {self.op}",
            "type": "BinOp",
            "op": self.op,
            "line": self.line,
            "children": [self.left.to_dict(), self.right.to_dict()]
        }

class UnaryOpNode(ASTNode):
    def __init__(self, op, operand, line, column=1):
        self.op = op
        self.operand = operand
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "name": f"Unary: {self.op}",
            "type": "UnaryOp",
            "op": self.op,
            "line": self.line,
            "children": [self.operand.to_dict()]
        }

class VarNode(ASTNode):
    def __init__(self, name, line, column=1):
        self.name = name
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "name": f"ID: {self.name}",
            "type": "Identifier",
            "value": self.name,
            "line": self.line
        }

class NumNode(ASTNode):
    def __init__(self, value, line, column=1):
        self.value = value
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "name": f"Num: {self.value}",
            "type": "Number",
            "value": self.value,
            "line": self.line
        }

def count_ast_nodes(node):
    if not node:
        return 0
    cnt = 1
    if isinstance(node, ProgramNode):
        for s in node.statements:
            cnt += count_ast_nodes(s)
    elif isinstance(node, AssignNode):
        cnt += count_ast_nodes(node.expr)
    elif isinstance(node, IfNode):
        cnt += count_ast_nodes(node.condition)
        cnt += count_ast_nodes(node.then_branch)
        if node.else_branch:
            cnt += count_ast_nodes(node.else_branch)
    elif isinstance(node, WhileNode):
        cnt += count_ast_nodes(node.condition)
        cnt += count_ast_nodes(node.body)
    elif isinstance(node, BlockNode):
        for s in node.statements:
            cnt += count_ast_nodes(s)
    elif isinstance(node, BinOpNode):
        cnt += count_ast_nodes(node.left)
        cnt += count_ast_nodes(node.right)
    elif isinstance(node, UnaryOpNode):
        cnt += count_ast_nodes(node.operand)
    return cnt


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def consume(self, expected_type=None, expected_val=None, custom_msg=None):
        current = self.peek()
        if expected_type and current.type != expected_type:
            if custom_msg:
                raise SyntaxError(custom_msg)
            raise SyntaxError(f"Syntax Error: Expected token type '{expected_type}', found '{current.type}' ('{current.value}') at Line {current.line}, Column {current.column}")
        if expected_val and current.value != expected_val:
            if custom_msg:
                raise SyntaxError(custom_msg)
            raise SyntaxError(f"Syntax Error: Expected '{expected_val}', found '{current.value}' at Line {current.line}, Column {current.column}")
        self.pos += 1
        return current

    def parse(self):
        statements = []
        while self.peek().type != 'EOF':
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_statement(self):
        tok = self.peek()

        if tok.type == 'ID':
            return self.parse_assignment()
        elif tok.type == 'IF':
            return self.parse_if()
        elif tok.type == 'WHILE':
            return self.parse_while()
        elif tok.type == 'LBRACE':
            return self.parse_block()
        elif tok.type == 'SEMI':
            self.consume('SEMI')
            return BlockNode([])
        else:
            raise SyntaxError(f"Syntax Error: Unexpected statement starting with '{tok.value}' at Line {tok.line}, Column {tok.column}")

    def parse_assignment(self):
        id_tok = self.consume('ID')
        self.consume('ASSIGN', custom_msg=f"Syntax Error: Expected '=' after identifier '{id_tok.value}' at Line {id_tok.line}, Column {id_tok.column}")

        # Check if right-hand side is missing before consuming expression
        if self.peek().type == 'SEMI':
            curr = self.peek()
            raise SyntaxError(f"Syntax Error: Missing expression after '=' for variable '{id_tok.value}' at Line {curr.line}, Column {curr.column}")

        expr = self.parse_expression()
        self.consume('SEMI', custom_msg=f"Syntax Error: Missing ';' at the end of statement at Line {id_tok.line}, Column {self.peek().column}")
        return AssignNode(id_tok.value, expr, id_tok.line, id_tok.column)

    def parse_if(self):
        if_tok = self.consume('IF')
        self.consume('LPAREN', custom_msg=f"Syntax Error: Expected '(' after 'if' at Line {if_tok.line}, Column {if_tok.column}")
        condition = self.parse_expression()
        self.consume('RPAREN', custom_msg=f"Syntax Error: Missing ')' closing if-condition at Line {self.peek().line}, Column {self.peek().column}")
        then_branch = self.parse_statement()
        else_branch = None
        if self.peek().type == 'ELSE':
            self.consume('ELSE')
            else_branch = self.parse_statement()
        return IfNode(condition, then_branch, else_branch, if_tok.line, if_tok.column)

    def parse_while(self):
        while_tok = self.consume('WHILE')
        self.consume('LPAREN', custom_msg=f"Syntax Error: Expected '(' after 'while' at Line {while_tok.line}, Column {while_tok.column}")
        condition = self.parse_expression()
        self.consume('RPAREN', custom_msg=f"Syntax Error: Missing ')' closing while-condition at Line {self.peek().line}, Column {self.peek().column}")
        body = self.parse_statement()
        return WhileNode(condition, body, while_tok.line, while_tok.column)

    def parse_block(self):
        lbrace = self.consume('LBRACE')
        stmts = []
        while self.peek().type != 'RBRACE' and self.peek().type != 'EOF':
            stmts.append(self.parse_statement())
        if self.peek().type == 'EOF':
            raise SyntaxError(f"Syntax Error: Missing closing brace '}}' for block opened at Line {lbrace.line}, Column {lbrace.column}")
        self.consume('RBRACE')
        return BlockNode(stmts)

    def parse_expression(self):
        return self.parse_relational()

    def parse_relational(self):
        left = self.parse_additive()
        while self.peek().type == 'RELOP':
            op_tok = self.consume('RELOP')
            right = self.parse_additive()
            left = BinOpNode(op_tok.value, left, right, op_tok.line, op_tok.column)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().type == 'ARITHOP' and self.peek().value in ('+', '-'):
            op_tok = self.consume('ARITHOP')
            right = self.parse_multiplicative()
            left = BinOpNode(op_tok.value, left, right, op_tok.line, op_tok.column)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek().type == 'ARITHOP' and self.peek().value in ('*', '/', '%'):
            op_tok = self.consume('ARITHOP')
            right = self.parse_unary()
            # Compile-time division by zero detection
            if op_tok.value in ('/', '%') and isinstance(right, NumNode) and right.value == 0:
                raise ZeroDivisionError(f"Semantic Error: Division by zero detected in '{op_tok.value} 0' at Line {op_tok.line}, Column {op_tok.column}")
            left = BinOpNode(op_tok.value, left, right, op_tok.line, op_tok.column)
        return left

    def parse_unary(self):
        if self.peek().type == 'ARITHOP' and self.peek().value == '-':
            op_tok = self.consume('ARITHOP')
            operand = self.parse_unary()
            return UnaryOpNode('-', operand, op_tok.line, op_tok.column)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()
        if tok.type == 'NUMBER':
            self.consume('NUMBER')
            num_val = float(tok.value) if '.' in tok.value else int(tok.value)
            return NumNode(num_val, tok.line, tok.column)
        elif tok.type == 'ID':
            self.consume('ID')
            return VarNode(tok.value, tok.line, tok.column)
        elif tok.type == 'LPAREN':
            self.consume('LPAREN')
            expr = self.parse_expression()
            if self.peek().type != 'RPAREN':
                raise SyntaxError(f"Syntax Error: Missing closing parenthesis ')' at Line {self.peek().line}, Column {self.peek().column}. Found '{self.peek().value}'")
            self.consume('RPAREN')
            return expr
        else:
            raise SyntaxError(f"Syntax Error: Unexpected token '{tok.value}' in expression at Line {tok.line}, Column {tok.column}. Expected identifier, number, or '('")
