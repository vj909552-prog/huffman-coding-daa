"""Local web interface for the Huffman compressor."""

import base64
import binascii
import json
import mimetypes
import os
import struct
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import huffman as hf

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
MAX_DATA_BYTES = 25 * 1024 * 1024
MAX_REQUEST_BYTES = 34 * 1024 * 1024


def _read_bytes(value):
    if not isinstance(value, str):
        raise ValueError("Expected base64-encoded data.")
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("The uploaded data is not valid base64.") from exc
    if len(data) > MAX_DATA_BYTES:
        raise ValueError("Files must be 25 MiB or smaller.")
    return data


def compress_for_web(data):
    started = time.perf_counter()
    blob = hf.compress(data)
    compress_ms = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    restored = hf.decompress(blob)
    decompress_ms = (time.perf_counter() - started) * 1000

    frequencies = hf.build_frequency_table(data)
    codes = hf.generate_codes(hf.build_tree(frequencies))
    rows = [
        {
            "byte": symbol,
            "label": (
                "SPACE"
                if symbol == 32
                else chr(symbol) if 33 <= symbol < 127 else f"0x{symbol:02x}"
            ),
            "frequency": frequency,
            "code": codes[symbol],
        }
        for symbol, frequency in sorted(
            frequencies.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    return {
        "compressed": base64.b64encode(blob).decode("ascii"),
        "stats": hf.compression_stats(len(data), len(blob)),
        "compress_ms": compress_ms,
        "decompress_ms": decompress_ms,
        "verified": restored == data,
        "codes": rows,
    }


def decompress_for_web(blob):
    started = time.perf_counter()
    data = hf.decompress(blob)
    return {
        "data": base64.b64encode(data).decode("ascii"),
        "bytes": len(data),
        "decompress_ms": (time.perf_counter() - started) * 1000,
    }


class HuffmanRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {
            "/": "index.html",
            "/index.html": "index.html",
            "/styles.css": "styles.css",
            "/app.js": "app.js",
            "/benchmark.png": None,
            "/sample.txt": "sample.txt",
        }
        path = self.path.split("?", 1)[0]
        if path not in routes:
            self.send_error(404, "Not found")
            return

        filename = routes[path] or "benchmark.png"
        asset_root = os.path.dirname(__file__) if path in ("/benchmark.png", "/sample.txt") else WEB_DIR
        full_path = os.path.join(asset_root, filename)
        try:
            with open(full_path, "rb") as file:
                body = file.read()
        except OSError:
            self.send_error(404, "App asset not found")
            return

        content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        route = self.path.split("?", 1)[0]
        if route not in ("/api/compress", "/api/decompress"):
            self._send_json({"error": "Not found."}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"error": "Invalid request length."}, 400)
            return
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._send_json({"error": "Files must be 25 MiB or smaller."}, 413)
            return

        try:
            request = json.loads(self.rfile.read(length))
            if route == "/api/compress":
                data = _read_bytes(request.get("data") if isinstance(request, dict) else None)
                result = compress_for_web(data)
            else:
                blob = _read_bytes(request.get("data") if isinstance(request, dict) else None)
                result = decompress_for_web(blob)
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            struct.error,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as exc:
            self._send_json({"error": str(exc) or "Invalid Huffman data."}, 400)
            return

        self._send_json(result)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        print(f"[web] {self.address_string()} - {format_string % args}")


def serve(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), HuffmanRequestHandler)
    print(f"Huffman web app running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Huffman web app.")
    finally:
        server.server_close()
