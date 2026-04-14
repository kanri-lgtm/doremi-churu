#!/usr/bin/env python3
"""ドレミのチュール管理アプリ - サーバー"""

import json
import os
from datetime import datetime, date
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
DAILY_LIMIT = 4


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"records": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_today_records(data):
    today = date.today().isoformat()
    return [r for r in data["records"] if r["date"] == today]


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/records":
            data = load_data()
            today_records = get_today_records(data)
            today_count = len(today_records)
            response = {
                "today_records": today_records,
                "today_count": today_count,
                "limit": DAILY_LIMIT,
                "over_limit": today_count >= DAILY_LIMIT,
            }
            self._json_response(response)

        elif parsed.path == "/api/history":
            data = load_data()
            response = {"records": data["records"]}
            self._json_response(response)

        elif parsed.path == "/":
            self._serve_file("index.html", "text/html")

        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/feed":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            data = load_data()
            today_records = get_today_records(data)

            if len(today_records) >= DAILY_LIMIT:
                self._json_response({"ok": False, "message": "もうあげないで！"}, 400)
                return

            record = {
                "id": len(data["records"]) + 1,
                "date": date.today().isoformat(),
                "time": datetime.now().strftime("%H:%M"),
                "person": body["person"],
                "flavor": body["flavor"],
            }
            data["records"].append(record)
            save_data(data)

            today_count = len(today_records) + 1
            self._json_response({
                "ok": True,
                "record": record,
                "today_count": today_count,
                "over_limit": today_count >= DAILY_LIMIT,
            })

        elif parsed.path == "/api/delete":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            record_id = body.get("id")

            data = load_data()
            data["records"] = [r for r in data["records"] if r["id"] != record_id]
            save_data(data)

            today_records = get_today_records(data)
            self._json_response({
                "ok": True,
                "today_count": len(today_records),
                "over_limit": len(today_records) >= DAILY_LIMIT,
            })

        else:
            self._json_response({"error": "Not found"}, 404)

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass  # suppress logs


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🐱 ドレミのチュール管理アプリ起動中: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
