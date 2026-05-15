import http.server
import socketserver
import json
import threading
import os
import functools
import time
from pathlib import Path

# Próba importu tfd_state, jeśli nie ma (np. start jako samodzielny skrypt), tworzymy atrapę
import sys
try:
    from editor.TFD.tfd_state import tfd_state
except ImportError:
    from tfd_state import tfd_state

PORT = 8765
OVERLAY_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = Path(__file__).resolve().parents[2]

class TFDHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Wyciszamy logowanie dla bardzo częstych zapytań o dane (telemetria i stream)
        if self.path.startswith('/tfd_data') or self.path.startswith('/tfd_stream'):
            return
        super().log_message(format, *args)

    def do_GET(self):
        if self.path.startswith('/tfd_stream'):
            if not tfd_state:
                self.send_error(503, "TFD State not initialized")
                return
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            last_id = -1
            try:
                while True:
                    full_data = tfd_state.to_dict()
                    curr_id = full_data.get("packet_id", 0)
                    
                    if curr_id != last_id:
                        # Przesyłamy pełny JSON, aby zasilić wszystkie pola overlay (tytuły, osie, czujniki)
                        self.wfile.write(f"data: {json.dumps(full_data)}\n\n".encode('utf-8'))
                        self.wfile.flush()
                        last_id = curr_id
                    time.sleep(0.01)  # Sprawdzanie co 10ms (100Hz)
            except (ConnectionResetError, BrokenPipeError):
                pass # Klient się rozłączył
            return

        if self.path.startswith('/tfd_data'):
            if not tfd_state:
                self.send_error(503, "TFD State not initialized")
                return
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            # Wyłączenie cache dla OBS
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            data = tfd_state.to_dict()
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return
        elif self.path in ['/tfd', '/tfd/']:
            # Alias dla głównego pliku nakładki
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_path = os.path.join(OVERLAY_DIR, 'tarzan_tfd_overlay.html')
            with open(html_path, 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
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

def run_server(ready_event=None):
    class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True
    handler_factory = functools.partial(TFDHandler, directory=OVERLAY_DIR)
    
    with ThreadingTCPServer(("0.0.0.0", PORT), handler_factory) as httpd:
        print(f"TFD Server started at http://localhost:{PORT}/tarzan_tfd_overlay.html")
        if ready_event:
            ready_event.set()
        httpd.serve_forever()

def start_tfd_server():
    ready_event = threading.Event()
    thread = threading.Thread(target=run_server, args=(ready_event,), daemon=True)
    thread.start()
    
    # Czekamy chwilę na start bindowania w wątku, aby ew. błędy były widoczne
    # Błędy bindowania w run_server rzucą wyjątek w wątku i będą widoczne w konsoli
    return thread

if __name__ == "__main__":
    run_server()
