%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser.tab.h"

#ifdef _WIN32
#define strdup _strdup
#endif
%}

%option noyywrap
%option yylineno

%%

"if"                    { return IF; }
"else"                  { return ELSE; }

[0-9]+                  { yylval.str = strdup(yytext); return NUMBER; }
[a-zA-Z_][a-zA-Z0-9_]*  { yylval.str = strdup(yytext); return ID; }

"=="                    { yylval.str = strdup(yytext); return EQ; }
"!="                    { yylval.str = strdup(yytext); return NE; }
"<="                    { yylval.str = strdup(yytext); return LE; }
">="                    { yylval.str = strdup(yytext); return GE; }
">"                     { yylval.str = strdup(yytext); return GT; }
"<"                     { yylval.str = strdup(yytext); return LT; }

"+"                     { return PLUS; }
"-"                     { return MINUS; }
"*"                     { return MUL; }
"/"                     { return DIV; }
"="                     { return ASSIGN; }

";"                     { return SEMI; }
"{"                     { return LBRACE; }
"}"                     { return RBRACE; }
"("                     { return LPAREN; }
")"                     { return RPAREN; }

"//".*                  { /* Ignore single-line comments */ }
[ \t\r\n]+              { /* Ignore whitespace */ }

.                       { printf("Lexical Error at line %d: Unexpected character '%s'\n", yylineno, yytext); }

%%
