#!/usr/bin/env python3
"""Browser-collab side-channel HTTP server.

Serves SERVE_ROOT over HTTP. The browser GETs static files (the page itself and
the polled `out.json`) and POSTs `{path, content}` to `/write` to update files
inside WRITE_ROOT.

Env vars:
    SERVE_ROOT  required — directory to serve and (by default) write into
    WRITE_ROOT  optional — defaults to SERVE_ROOT; must be inside SERVE_ROOT
    PORT        optional — defaults to 0 (OS-assigned ephemeral)

On startup prints two lines to stdout:
    serving <SERVE_ROOT> at http://127.0.0.1:<port>
    write root: <WRITE_ROOT>

Caller reads the first line to learn the assigned port.
"""
import json
import os
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _env_path(name: str, default: str | None = None) -> Path:
    raw = os.environ.get(name, default)
    if raw is None:
        sys.exit(f"missing required env var: {name}")
    return Path(raw).resolve()


SERVE_ROOT = _env_path("SERVE_ROOT")
WRITE_ROOT = _env_path("WRITE_ROOT", str(SERVE_ROOT))
PORT = int(os.environ.get("PORT", "0"))

LIVERELOAD_SNIPPET = b"""<script>
(() => {
  const keyOf = (s) => s.src || s.textContent;
  const executed = new Set();
  for (const s of document.querySelectorAll('script')) executed.add(keyOf(s));

  async function softSwap() {
    let html;
    try {
      const r = await fetch(location.pathname, { cache: 'no-store' });
      if (!r.ok) throw 0;
      html = await r.text();
    } catch {
      location.reload();
      return;
    }
    const doc = new DOMParser().parseFromString(html, 'text/html');

    const preserved = new Map();
    for (const n of document.querySelectorAll('[data-preserve]')) {
      if (n.id) preserved.set(n.id, n);
    }

    const scrollY = window.scrollY;
    const activeId = document.activeElement && document.activeElement.id;

    document.head.replaceChildren(...doc.head.childNodes);
    document.body.replaceChildren(...doc.body.childNodes);

    for (const [id, node] of preserved) {
      const placeholder = document.getElementById(id);
      if (placeholder && placeholder !== node) placeholder.replaceWith(node);
    }

    for (const s of document.querySelectorAll('script')) {
      const key = keyOf(s);
      if (executed.has(key)) continue;
      executed.add(key);
      const clone = document.createElement('script');
      if (s.src) clone.src = s.src;
      else clone.textContent = s.textContent;
      s.replaceWith(clone);
    }

    window.scrollTo(0, scrollY);
    if (activeId) {
      const el = document.getElementById(activeId);
      if (el && typeof el.focus === 'function') el.focus();
    }
  }

  new EventSource('/livereload').addEventListener('reload', softSwap);
})();
</script>"""


def _inject_livereload(html: bytes) -> bytes:
    lower = html.lower()
    idx = lower.rfind(b"</body>")
    if idx == -1:
        idx = lower.rfind(b"</html>")
    if idx == -1:
        return html + LIVERELOAD_SNIPPET
    return html[:idx] + LIVERELOAD_SNIPPET + html[idx:]


def _max_watched_mtime() -> float:
    latest = 0.0
    for path in SERVE_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() == ".json":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > latest:
            latest = mtime
    return latest


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SERVE_ROOT), **kwargs)

    def _common_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def end_headers(self):
        self._common_headers()
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404, "directory listings disabled")
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/livereload":
            self._stream_livereload()
            return

        fs_path = Path(self.translate_path(self.path))
        if fs_path.is_dir():
            fs_path = fs_path / "index.html"
        if fs_path.is_file() and fs_path.suffix.lower() in (".html", ".htm"):
            self._serve_html_with_livereload(fs_path)
            return

        super().do_GET()

    def _serve_html_with_livereload(self, fs_path: Path):
        try:
            raw = fs_path.read_bytes()
        except OSError:
            self.send_error(500, "could not read html")
            return
        body = _inject_livereload(raw)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _stream_livereload(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        last = _max_watched_mtime()
        try:
            while True:
                time.sleep(0.5)
                current = _max_watched_mtime()
                if current > last:
                    last = current
                    self.wfile.write(b"event: reload\ndata: 1\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return

    def do_POST(self):
        if self.path.rstrip("/") != "/write":
            self.send_error(404, "only POST /write is supported")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError as exc:
            self._reply(400, {"ok": False, "error": f"invalid json body: {exc}"})
            return

        rel_path = payload.get("path")
        content = payload.get("content")
        if not isinstance(rel_path, str) or content is None:
            self._reply(400, {"ok": False, "error": "body needs {path: string, content: any}"})
            return

        target = (WRITE_ROOT / rel_path).resolve()
        try:
            target.relative_to(WRITE_ROOT)
        except ValueError:
            self._reply(400, {"ok": False, "error": f"path must stay under {WRITE_ROOT}"})
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(content, indent=2) + "\n")
        self._reply(200, {"ok": True, "path": str(target)})

    def _reply(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main():
    if not SERVE_ROOT.is_dir():
        sys.exit(f"SERVE_ROOT does not exist: {SERVE_ROOT}")
    try:
        WRITE_ROOT.relative_to(SERVE_ROOT)
    except ValueError:
        sys.exit(f"WRITE_ROOT ({WRITE_ROOT}) must be inside SERVE_ROOT ({SERVE_ROOT})")

    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    print(f"serving {SERVE_ROOT} at http://127.0.0.1:{port}", flush=True)
    print(f"write root: {WRITE_ROOT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
