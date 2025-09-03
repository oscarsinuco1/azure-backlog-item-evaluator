from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import json

# === Servidor para el Dashboard ===
class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Sirve archivos desde el directorio 'public'
        super().__init__(*args, directory='public', **kwargs)

    def do_GET(self):
        if self.path == '/data':
            # Este endpoint especial sirve el archivo res.json desde el directorio raíz del proyecto
            try:
                with open('res.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, 'res.json no encontrado')
        else:
            # Para todas las demás peticiones, usa el comportamiento por defecto
            # que sirve archivos desde el directorio 'public'
            super().do_GET()

    def log_message(self, format, *args):
        """Silencia los logs del servidor para mantener la salida limpia."""
        return

def start_server(port=8000):
    httpd = HTTPServer(("", port), DashboardRequestHandler)
    print(f"🌐 Servidor corriendo en http://localhost:{port}")
    httpd.serve_forever()