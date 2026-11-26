"""假的通知管道：把 Alertmanager 送來的告警印出來（代替 Email / Slack / Discord）。"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        for a in body.get("alerts", []):
            print(
                f"[{a['status'].upper()}] {a['labels'].get('alertname')}: "
                f"{a['annotations'].get('summary', '')}",
                flush=True,
            )
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


HTTPServer(("", 5001), Handler).serve_forever()
