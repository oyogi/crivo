"""demo local sem dependências extras, persistência ou logs dos textos."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files

from .model import predict

MAX_BODY_BYTES = 32 * 1024


def make_handler(bundle: dict):

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # o texto enviado e o caminho da requisição não vão para logs
            pass

        def respond(self, status: int, body: bytes, content_type: str):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; "
                "script-src 'unsafe-inline'; style-src 'self'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def json_response(self, status: int, value: dict):
            body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode(
                "utf-8"
            )
            self.respond(status, body, "application/json; charset=utf-8")

        def do_GET(self):
            routes = {
                "/": ("demo.html", "text/html; charset=utf-8"),
                "/exemplos": ("examples.html", "text/html; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
            }
            if self.path not in routes:
                self.json_response(404, {"erro": "rota não encontrada"})
                return
            filename, content_type = routes[self.path]
            self.respond(
                200, files("crivo").joinpath(filename).read_bytes(), content_type
            )

        def do_POST(self):
            if self.path != "/predict":
                self.json_response(404, {"erro": "rota não encontrada"})
                return
            lengths = self.headers.get_all("Content-Length", [])
            if (
                self.headers.get("Transfer-Encoding")
                or len(lengths) != 1
                or not lengths[0].isascii()
                or not lengths[0].isdigit()
            ):
                self.json_response(400, {"erro": "content-length ausente ou inválido"})
                return
            # comparar pelo tamanho evita converter inteiros gigantes enviados no cabeçalho
            significant = lengths[0].lstrip("0") or "0"
            if len(significant) > 5 or int(significant) > MAX_BODY_BYTES:
                self.json_response(413, {"erro": "o corpo deve ter até 32 kib"})
                return
            length = int(significant)
            try:
                self.connection.settimeout(3)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("corpo incompleto")
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict) or not isinstance(
                    payload.get("text"), str
                ):
                    raise ValueError(
                        "envie um objeto json com o campo text em formato de texto"
                    )
                result = predict(bundle, payload["text"])
            except (TimeoutError, ValueError, UnicodeError) as error:
                self.json_response(400, {"erro": str(error)})
                return
            self.json_response(200, result)

    return Handler


def serve(bundle: dict, port: int = 8000):
    with ThreadingHTTPServer(("127.0.0.1", port), make_handler(bundle)) as server:
        print(f"demo em http://127.0.0.1:{server.server_port}; ctrl+c para sair")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\ndemo encerrada")
