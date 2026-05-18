import http.server
import json
import os
import threading

PORT = 3000
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state.json')
lock = threading.Lock()


def read_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        initial = [
            {"id": 1, "title": "INERTIA", "occupied": False},
            {"id": 2, "title": "ORIGINAL", "occupied": False},
            {"id": 3, "title": "93 tpm", "occupied": False},
            {"id": 4, "title": "TOO MANY AND ONE", "occupied": False},
        ]
        write_state(initial)
        return initial


def write_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public'), **kwargs)

    def do_GET(self):
        if self.path == '/api/state':
            with lock:
                state = read_state()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(state).encode())
        else:
            super().do_GET()

    def do_PUT(self):
        if self.path.startswith('/api/state/'):
            try:
                item_id = int(self.path.split('/')[-1])
            except ValueError:
                self.send_response(400)
                self.end_headers()
                return

            with lock:
                state = read_state()
                item = next((i for i in state if i['id'] == item_id), None)
                if not item:
                    self.send_response(404)
                    self.end_headers()
                    return
                item['occupied'] = not item['occupied']
                write_state(state)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(state).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    with http.server.ThreadingHTTPServer(('', PORT), Handler) as httpd:
        print(f'Server running on http://localhost:{PORT}')
        httpd.serve_forever()
