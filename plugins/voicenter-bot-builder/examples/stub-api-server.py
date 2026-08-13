#!/usr/bin/env python3
"""Local stub API for the F1 baseline fixture's RT=2 intent.

Skill 2 hard-blocks an RT=2 intent from reaching [detailed] until a live curl
returns 2xx with every dotted path declared in spec section 4.5.4 present in
the body. The F1 fixture describes a fictional clinic, so there is no real
endpoint to verify against — this stub stands in for it.

It is committed alongside the fixture so the section 7.6 verification entry
stays reproducible: anyone re-running the F1 verification (or CI) starts this
server first and curls the same URL.

The response is fully deterministic — no timestamps, no randomness — so
repeated verification runs are byte-identical.

Usage:
    python stub-api-server.py [--port 8787]

Endpoint:
    POST /available-slots
        request : {"requested_date": <str>, "preferred_clinician": <str>}
        response: 200 with the payload below

Dotted paths declared in spec 4.5.4 and guaranteed present:
    available_slots.0.display
    available_slots.0.slot_id
    clinician.name
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Deterministic payload. Slot displays are fixed strings, not computed from the
# current date, so the fixture's verification never drifts.
RESPONSE = {
    "status": "ok",
    "clinician": {
        "name": "Dr. Maya Ellison",
        "room": "3B",
    },
    "available_slots": [
        {"slot_id": "S-1041", "display": "Tuesday 14 April, 09:30"},
        {"slot_id": "S-1042", "display": "Tuesday 14 April, 11:00"},
        {"slot_id": "S-1043", "display": "Wednesday 15 April, 16:15"},
    ],
}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/available-slots":
            self._send(404, {"status": "error", "message": "unknown endpoint"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"status": "error", "message": "malformed json body"})
            return

        self._send(200, RESPONSE)

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # keep verification output clean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"stub API listening on http://127.0.0.1:{args.port}/available-slots")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
