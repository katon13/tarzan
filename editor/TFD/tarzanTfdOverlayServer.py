import http.server
import socketserver
import json
import threading
import os
from pathlib import Path

# Próba importu tfd_state, jeśli nie ma (np. start jako samodzielny skrypt), tworzymy atrapę
try:
    from editor.TFD.tfd_state import tfd_state
except ImportError:
    from tfd_state import tfd_state

PORT = 8765
ROOT_DIR = Path(__file__).resolve().parents[2]

class TFDHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/tfd_data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = tfd_state.to_dict()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif self.path.startswith('/img/'):
            # Serwowanie obrazów z X:/tarzan/img/
            img_path = ROOT_DIR / self.path.lstrip('/')
            if img_path.exists():
                self.send_response(200)
                if img_path.suffix == '.png': self.send_header('Content-type', 'image/png')
                elif img_path.suffix == '.jpg': self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                with open(img_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        else:
            # Domyślnie serwujemy pliki z katalogu overlay
            super().do_GET()

def run_server():
    # Ustawiamy katalog roboczy na katalog serwera (dla plików statycznych html/css/js)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = TFDHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"TFD Server started at port {PORT}")
        httpd.serve_forever()

def start_tfd_server():
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    run_server()
