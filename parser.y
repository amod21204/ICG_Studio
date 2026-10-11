%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define strdup _strdup
#endif

extern int yylex(void);
extern int yylineno;
extern FILE *yyin;
void yyerror(const char *s);

/* Temporary and Label counters */
int temp_count = 1;
int label_count = 1;

char* new_temp() {
    char* buf = (char*)malloc(16);
    sprintf(buf, "t%d", temp_count++);
    return buf;
}

char* new_label() {
    char* buf = (char*)malloc(16);
    sprintf(buf, "L%d", label_count++);
    return buf;
}

/* AST Node Structure */
typedef enum {
    NODE_NUM,
    NODE_ID,
    NODE_BINOP,
    NODE_ASSIGN,
    NODE_IF,
    NODE_STMT_LIST
} NodeType;

typedef struct ASTNode {
    NodeType type;
    char* val;
    char* op;
    struct ASTNode* left;
    struct ASTNode* right;
    struct ASTNode* else_branch;
} ASTNode;

ASTNode* create_num_node(char* val) {
    ASTNode* n = (ASTNode*)calloc(1, sizeof(ASTNode));
    n->type = NODE_NUM;
    n->val = val;
    return n;
}

ASTNode* create_id_node(char* val) {
    ASTNode* n = (ASTNode*)calloc(1, sizeof(ASTNode));
    n->type = NODE_ID;
    n->val = val;
    return n;
}

ASTNode* create_binop_node(char* op, ASTNode* left, ASTNode* right) {
    ASTNode* n = (ASTNode*)calloc(1, sizeof(ASTNode));
    n->type = NODE_BINOP;
    n->op = op;
    n->left = left;
    n->right = right;
    return n;
}

ASTNode* create_assign_node(char* var, ASTNode* expr) {
    ASTNode* n = (ASTNode*)calloc(1, sizeof(ASTNode));
    n->type = NODE_ASSIGN;
    n->val = var;
    n->right = expr;
    return n;
}

ASTNode* create_if_node(ASTNode* cond, ASTNode* then_part, ASTNode* else_part) {
    ASTNode* n = (ASTNode*)calloc(1, sizeof(ASTNode));
    n->type = NODE_IF;
    n->left = cond;
    n->right = then_part;
    n->else_branch = else_part;
    return n;
}

ASTNode* create_stmt_list_node(ASTNode* list, ASTNode* stmt) {
    ASTNode* n = (ASTNode*)calloc(1, sizeof(ASTNode));
    n->type = NODE_STMT_LIST;
    n->left = list;
    n->right = stmt;
    return n;
}

void print_ast(ASTNode* node, int indent) {
    if (!node) return;
    for (int i = 0; i < indent; i++) printf("  ");
    switch (node->type) {
        case NODE_NUM:
            printf("NUMBER: %s\n", node->val);
            break;
        case NODE_ID:
            printf("ID: %s\n", node->val);
            break;
        case NODE_BINOP:
            printf("BINOP (%s)\n", node->op);
            print_ast(node->left, indent + 1);
            print_ast(node->right, indent + 1);
            break;
        case NODE_ASSIGN:
            printf("ASSIGN (%s =)\n", node->val);
            print_ast(node->right, indent + 1);
            break;
        case NODE_IF:
            printf("IF STATEMENT\n");
            for (int i = 0; i <= indent; i++) printf("  ");
            printf("[Condition]\n");
            print_ast(node->left, indent + 2);
            for (int i = 0; i <= indent; i++) printf("  ");
            printf("[Then Branch]\n");
            print_ast(node->right, indent + 2);
            if (node->else_branch) {
                for (int i = 0; i <= indent; i++) printf("  ");
                printf("[Else Branch]\n");
                print_ast(node->else_branch, indent + 2);
            }
            break;
        case NODE_STMT_LIST:
            print_ast(node->left, indent);
            print_ast(node->right, indent);
            break;
    }
}

char* gen_tac(ASTNode* node) {
    if (!node) return NULL;
    switch (node->type) {
        case NODE_NUM:
            return strdup(node->val);
        case NODE_ID:
            return strdup(node->val);
        case NODE_BINOP: {
            char* left = gen_tac(node->left);
            char* right = gen_tac(node->right);
            char* t = new_temp();
            printf("%s = %s %s %s\n", t, left, node->op, right);
            free(left);
            free(right);
            return t;
        }
        case NODE_ASSIGN: {
            char* rhs = gen_tac(node->right);
            printf("%s = %s\n", node->val, rhs);
            free(rhs);
            return NULL;
        }
        case NODE_IF: {
            char* cond = gen_tac(node->left);
            char* l_else = new_label();
            char* l_end = new_label();
            if (node->else_branch) {
                printf("if_false %s goto %s\n", cond, l_else);
                gen_tac(node->right);
                printf("goto %s\n", l_end);
                printf("%s:\n", l_else);
                gen_tac(node->else_branch);
                printf("%s:\n", l_end);
            } else {
                printf("if_false %s goto %s\n", cond, l_end);
                gen_tac(node->right);
                printf("%s:\n", l_end);
            }
            free(cond);
            free(l_else);
            free(l_end);
            return NULL;
        }
        case NODE_STMT_LIST: {
            gen_tac(node->left);
            gen_tac(node->right);
            return NULL;
        }
    }
    return NULL;
}

ASTNode* root = NULL;
%}

%union {
    char* str;
    struct ASTNode* node;
}

%token <str> NUMBER ID
%token <str> EQ NE LE GE GT LT
%token PLUS MINUS MUL DIV ASSIGN
%token SEMI LBRACE RBRACE LPAREN RPAREN
%token IF ELSE

%type <node> program stmt_list stmt expr

%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%left EQ NE LT GT LE GE
%left PLUS MINUS
%left MUL DIV

%%

program:
    stmt_list {
        root = $1;
    }
    ;

stmt_list:
    stmt_list stmt {
        $$ = create_stmt_list_node($1, $2);
    }
  | /* empty */ {
        $$ = NULL;
    }
  ;

stmt:
    ID ASSIGN expr SEMI {
        $$ = create_assign_node($1, $3);
    }
  | IF LPAREN expr RPAREN stmt %prec LOWER_THAN_ELSE {
        $$ = create_if_node($3, $5, NULL);
    }
  | IF LPAREN expr RPAREN stmt ELSE stmt {
        $$ = create_if_node($3, $5, $7);
    }
  | LBRACE stmt_list RBRACE {
        $$ = $2;
    }
  ;

expr:
    expr PLUS expr      { $$ = create_binop_node("+", $1, $3); }
  | expr MINUS expr     { $$ = create_binop_node("-", $1, $3); }
  | expr MUL expr       { $$ = create_binop_node("*", $1, $3); }
  | expr DIV expr       { $$ = create_binop_node("/", $1, $3); }
  | expr EQ expr        { $$ = create_binop_node("==", $1, $3); }
  | expr NE expr        { $$ = create_binop_node("!=", $1, $3); }
  | expr LT expr        { $$ = create_binop_node("<", $1, $3); }
  | expr GT expr        { $$ = create_binop_node(">", $1, $3); }
  | expr LE expr        { $$ = create_binop_node("<=", $1, $3); }
  | expr GE expr        { $$ = create_binop_node(">=", $1, $3); }
  | LPAREN expr RPAREN  { $$ = $2; }
  | ID                  { $$ = create_id_node($1); }
  | NUMBER              { $$ = create_num_node($1); }
  ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Syntax Error at line %d: %s\n", yylineno, s);
}

int main(int argc, char** argv) {
    if (argc > 1) {
        FILE* fp = fopen(argv[1], "r");
        if (!fp) {
            perror(argv[1]);
            return 1;
        }
        yyin = fp;
    }

    printf("========================================\n");
    printf("   COMPILER DESIGN: LEX & YACC PARSER   \n");
    printf("========================================\n\n");

    if (yyparse() == 0) {
        printf("[STATUS] Parsing finished successfully!\n\n");
        printf("----------------------------------------\n");
        printf("1. ABSTRACT SYNTAX TREE (AST)\n");
        printf("----------------------------------------\n");
        print_ast(root, 0);

        printf("\n----------------------------------------\n");
        printf("2. THREE-ADDRESS CODE (TAC)\n");
        printf("----------------------------------------\n");
        gen_tac(root);
        printf("\n========================================\n");
    } else {
        printf("\n[STATUS] Parsing failed.\n");
    }

    return 0;
}
