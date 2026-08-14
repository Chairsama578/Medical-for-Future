#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StrokeGuard dashboard server (runs on HOST, arduino user).
Serves the dashboard HTML + /api/state JSON written by the app container.

The container writes state to /app/.cache/state.json (via bind mount),
which appears on the host as:
    /home/arduino/ArduinoApps/strokeguard_ai/.cache/state.json

Usage:
    python3 dashboard_server.py [--port 8080]
"""
import json
import os
import sys
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_STATE = os.path.join(
    os.path.expanduser("~"),
    "ArduinoApps", "strokeguard_ai", ".cache", "state.json",
)
DEFAULT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

STATE_FILE = os.environ.get("STROKEGUARD_STATE", DEFAULT_STATE)
HTML_FILE = os.environ.get("STROKEGUARD_HTML", DEFAULT_HTML)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # quiet

    def _send(self, code, content, ctype):
        body = content if isinstance(content, bytes) else content.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html", "/dashboard"):
            try:
                with open(HTML_FILE, "rb") as f:
                    self._send(200, f.read(), "text/html")
            except OSError:
                self._send(404, "index.html not found", "text/plain")
            return

        if path == "/api/state":
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                self._send(200, json.dumps(data), "application/json")
            except FileNotFoundError:
                self._send(200, json.dumps({
                    "ts": 0, "count": 0, "signal": {"ok": False, "finger": False,
                                                    "valid_ratio": 0, "ir": 0},
                    "vitals": {"hr": None, "spo2": None, "motion_dev": 0, "roll": 0, "pitch": 0},
                    "status": {"level": "NO_SIGNAL", "score": 0, "reasons": [],
                               "since": 0},
                    "history": {}, "alerts": [],
                    "device": {"state_file": STATE_FILE},
                }), "application/json")
            except Exception as e:
                self._send(200, json.dumps({"error": str(e), "ts": 0}),
                           "application/json")
            return

        if path == "/api/health":
            ok = os.path.exists(STATE_FILE)
            age = None
            if ok:
                try:
                    m = os.path.getmtime(STATE_FILE)
                    age = round(time.time() - m, 1)
                except OSError:
                    pass
            self._send(200, json.dumps({"ok": ok, "age_s": age}), "application/json")
            return

        self._send(404, "Not found", "text/plain")


def main():
    import time  # noqa
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(f"StrokeGuard dashboard  ->  http://{args.host}:{args.port}")
    print(f"  state file : {STATE_FILE}")
    print(f"  html file  : {HTML_FILE}")
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()