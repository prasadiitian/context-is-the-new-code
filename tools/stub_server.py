"""stub_server.py -- a stand-in model endpoint for testing."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

REPLY = "Stub reply. Point MODEL_URL at a real model to get answers."


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(size))
        text = " ".join(m["content"] for m in body["messages"])
        reply = {
            "choices": [{"message": {"role": "assistant",
                                     "content": REPLY}}],
            "usage": {"prompt_tokens": len(text) // 4,
                      "completion_tokens": len(REPLY) // 4}}
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("stub model on http://127.0.0.1:8808/v1/chat/completions")
    HTTPServer(("127.0.0.1", 8808), Handler).serve_forever()
