import http.server
import socketserver
import subprocess
import io
import contextlib
import sys
import os

PORT = 7444

class CodeExecutorHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        client_ip = self.client_address[0]
        print(f"Received message from {client_ip}")

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        code = post_data.decode('utf-8')

        output = io.StringIO()
        error = io.StringIO()

        sys.path.append(os.getcwd())

        try:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                exec(code, globals())

            self.send_response(200)
            self.end_headers()
            response = output.getvalue()
            self.wfile.write(f"Code executed successfully.\n\nOutput:\n{response}".encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            error_info = error.getvalue() + f"\nError: {e}"
            self.wfile.write(f"Code execution failed.\n\n{error_info}".encode('utf-8'))

with socketserver.TCPServer(("", PORT), CodeExecutorHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
