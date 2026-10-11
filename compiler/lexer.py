import re

TOKEN_SPECIFICATIONS = [
    ('KEYWORD',     r'\b(if|else|while)\b'),
    ('NUMBER',      r'\d+(\.\d+)?'),
    ('ID',          r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('RELOP',       r'(==|!=|<=|>=|<|>)'),
    ('ASSIGN',      r'='),
    ('ARITHOP',     r'[\+\-\*/%]'),
    ('SEMI',        r';'),
    ('LBRACE',      r'\{'),
    ('RBRACE',      r'\}'),
    ('LPAREN',      r'\('),
    ('RPAREN',      r'\)'),
    ('COMMENT',     r'//.*'),
    ('WHITESPACE',  r'[ \t]+'),
    ('NEWLINE',     r'\r?\n'),
    ('MISMATCH',    r'.'),
]

MASTER_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATIONS)

class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.lexeme = value
        self.line = line
        self.column = column

    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "lexeme": self.lexeme,
            "line": self.line,
            "column": self.column
        }

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.column})"

def tokenize(source_code):
    tokens = []
    line_num = 1
    line_start = 0

    for mo in re.finditer(MASTER_REGEX, source_code):
        kind = mo.lastgroup
        value = mo.group()
        col = mo.start() - line_start + 1

        if kind == 'NEWLINE':
            line_num += 1
            line_start = mo.end()
            continue
        elif kind == 'WHITESPACE' or kind == 'COMMENT':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Lexical Error: Unexpected character '{value}' at Line {line_num}, Column {col}")

        sub_type = kind
        if kind == 'KEYWORD':
            sub_type = value.upper()
        elif kind == 'RELOP':
            sub_type = 'RELOP'
        elif kind == 'ARITHOP':
            sub_type = 'ARITHOP'

        tokens.append(Token(sub_type, value, line_num, col))

    tokens.append(Token('EOF', '', line_num, len(source_code) - line_start + 1))
    return tokens
