#!/usr/bin/env python3
"""
Custom proxy: accepts Cursor agent connections, forwards OpenAI-format
requests to FreeLLM API gateway (freellm.aldof.duckdns.org/v1).
Does NOT implement Cursor's private auth RPC (/auth/exchange_user_api_key);
intended for SDK/openai clients, not full agent CLI.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, json, os, sys

FREELLM_BASE = os.getenv("OPENAI_BASE_URL", "https://freellm.aldof.duckdns.org/v1")
FREELLM_KEY  = os.getenv("OPENAI_API_KEY", "freellmapi-893cc5a20ad598f62880e287ac46914c7f8cd0611f1890fe")

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body)
            # Forward chat/completions to gateway
            url = FREELLM_BASE + "/chat/completions"
            req = urllib.request.Request(url, data=body,
                headers={"Authorization": f"Bearer {FREELLM_KEY}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                out = resp.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
    def log_message(self, fmt, *args): pass  # silent

if __name__ == "__main__":
    port = int(os.getenv("PROXY_PORT", 9888))
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Proxy listening on {port} -> {FREELLM_BASE}")
    server.serve_forever()
