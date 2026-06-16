from http.server import BaseHTTPRequestHandler
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'placement_analytics_task', 'placement.db')

# Tables that are read-only allowed for the public SQL sandbox
BLOCKED_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'ATTACH', 'DETACH']


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            payload = json.loads(body.decode('utf-8'))
            query = payload.get('query', '').strip()

            # Safety check — block writes
            q_upper = query.upper()
            for kw in BLOCKED_KEYWORDS:
                if kw in q_upper:
                    result = json.dumps({
                        "error": f"'{kw}' statements are not permitted in the public sandbox. This is a read-only interface."
                    }).encode('utf-8')
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(result)
                    return

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()

            result = json.dumps({
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows)
            }).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result)

        except Exception as e:
            error = json.dumps({"error": str(e)}).encode('utf-8')
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(error)

    def log_message(self, format, *args):
        pass
