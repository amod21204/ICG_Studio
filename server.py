import os
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler

from compiler.lexer import tokenize
from compiler.parser import Parser, count_ast_nodes
from compiler.icg import ICG, build_triples, build_basic_blocks
from compiler.optimizer import Optimizer
from compiler.target_code import generate_target_code
from compiler.interpreter import Interpreter

PORT = 8000
HOST = "127.0.0.1"
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

class CompilerServerHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Prevent caching for live development
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        # Normalize path
        req_path = self.path.split('?')[0]

        if req_path in ('/', '/index.html'):
            filepath = os.path.join(STATIC_DIR, "index.html")
            self._serve_file(filepath, "text/html; charset=utf-8")
        elif req_path.startswith('/static/'):
            filename = req_path[len('/static/'):]
            filepath = os.path.join(STATIC_DIR, filename)
            mime_type, _ = mimetypes.guess_type(filepath)
            self._serve_file(filepath, mime_type or "application/octet-stream")
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Resource not found"}).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/compile':
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len).decode('utf-8')
                payload = json.loads(post_body) if post_body else {}
                code = payload.get('code', '').strip()

                if not code:
                    self._send_json(400, {"error": "Source code cannot be empty. Please enter C-style code."})
                    return

                # Compile & Optimize Pipeline
                result = self._execute_compiler_pipeline(code, payload.get('passes'))
                self._send_json(200, result)

            except (SyntaxError, ValueError, ZeroDivisionError) as err:
                # Clean error reporting without raw Python stack traces
                self._send_json(400, {
                    "error": str(err),
                    "error_type": err.__class__.__name__
                })
            except Exception as err:
                self._send_json(500, {
                    "error": f"Internal Compiler Error: {str(err)}",
                    "error_type": "CompilerException"
                })
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def _execute_compiler_pipeline(self, code, requested_passes):
        # 1. Lexical Analysis
        tokens = tokenize(code)
        tokens_data = [t.to_dict() for t in tokens if t.type != 'EOF']

        # 2. Syntax Analysis & AST Construction
        parser = Parser(tokens)
        ast_root = parser.parse()
        ast_data = ast_root.to_dict()
        ast_nodes_count = count_ast_nodes(ast_root)

        # 3. Intermediate Code Generation (ICG)
        icg = ICG()
        unopt_instructions = icg.generate(ast_root)

        unopt_tac_list = []
        for idx, instr in enumerate(unopt_instructions):
            unopt_tac_list.append({
                "index": idx,
                "tac": instr.to_tac(),
                "op": instr.op,
                "why": instr.get_why()
            })

        unopt_quads = [instr.to_quadruple() for instr in unopt_instructions]
        unopt_triples = build_triples(unopt_instructions)
        unopt_blocks = build_basic_blocks(unopt_instructions)

        # 4. Code Optimization
        opt_passes = requested_passes if requested_passes is not None else [
            'constant_propagation',
            'constant_folding',
            'algebraic_simplification',
            'common_subexpression',
            'dead_code_elimination'
        ]

        optimizer = Optimizer(unopt_instructions)
        opt_instructions, opt_logs, passes_applied = optimizer.run_all(opt_passes)

        opt_tac_list = []
        for idx, instr in enumerate(opt_instructions):
            opt_tac_list.append({
                "index": idx,
                "tac": instr.to_tac(),
                "op": instr.op,
                "why": instr.get_why()
            })

        opt_quads = [instr.to_quadruple() for instr in opt_instructions]
        opt_triples = build_triples(opt_instructions)
        opt_blocks = build_basic_blocks(opt_instructions)

        # 5. Target-like Pseudo Assembly Code
        target_code = generate_target_code(opt_instructions)

        # 6. Runtime Simulation
        interpreter = Interpreter(opt_instructions)
        exec_results = interpreter.run()

        # 7. Comprehensive Compiler Statistics
        statistics = {
            "tokens_count": len(tokens_data),
            "ast_nodes_count": ast_nodes_count,
            "tac_instructions_count": len(unopt_instructions),
            "temporaries_count": max(0, icg.temp_id - 1),
            "quadruples_count": len(unopt_quads),
            "triples_count": len(unopt_triples),
            "basic_blocks_count": len(unopt_blocks),
            "opt_instructions_count": len(opt_instructions),
            "instructions_removed": max(0, len(unopt_instructions) - len(opt_instructions)),
            "passes_applied": passes_applied
        }

        return {
            "status": "success",
            "tokens": tokens_data,
            "ast": ast_data,
            "intermediate": {
                "unoptimized": {
                    "tac": [item["tac"] for item in unopt_tac_list],
                    "detailed_tac": unopt_tac_list,
                    "quadruples": unopt_quads,
                    "triples": unopt_triples,
                    "blocks": unopt_blocks
                },
                "optimized": {
                    "tac": [item["tac"] for item in opt_tac_list],
                    "detailed_tac": opt_tac_list,
                    "quadruples": opt_quads,
                    "triples": opt_triples,
                    "blocks": opt_blocks
                }
            },
            "target_code": target_code,
            "optimization_logs": opt_logs,
            "statistics": statistics,
            "execution": exec_results
        }

    def _serve_file(self, filepath, mime_type):
        if os.path.exists(filepath) and os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"File not found")

    def _send_json(self, status_code, data):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Quiet standard logging to keep console clean
        return


def run_server():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, CompilerServerHandler)
    print("\n" + "=" * 60)
    print(" [SERVER] COMPILER CONSTRUCTION STUDIO STARTED")
    print(" [TECH]   HTML5, CSS3, Vanilla JavaScript, Python 3")
    print(f" [URL]    http://{HOST}:{PORT}")
    print(" [DEPS]   100% Python Standard Library (Zero pip install)")
    print("=" * 60 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
