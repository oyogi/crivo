"""requisições em memória para testar a demo sem abrir porta nem baixar dados."""

import io
import json

import pytest

from crivo.model import build_model
from crivo.web import MAX_BODY_BYTES, make_handler


class FakeSocket:
    def __init__(self, request):
        self.request = io.BytesIO(request)
        self.response = bytearray()

    def makefile(self, *args, **kwargs):
        return self.request

    def sendall(self, data):
        self.response.extend(data)

    def settimeout(self, timeout):
        pass


@pytest.fixture(scope="module")
def handler():
    model = build_model().fit(["produto ótimo"] * 3 + ["produto péssimo"] * 3,
                              [1] * 3 + [0] * 3)
    return make_handler({"model": model, "threshold": 0.8})


def request(handler, method, path, body=b"", headers=None):
    if headers is None:
        headers = [("Content-Length", str(len(body)))]
    raw = f"{method} {path} HTTP/1.0\r\n".encode()
    raw += b"".join(f"{name}: {value}\r\n".encode() for name, value in headers)
    connection = FakeSocket(raw + b"\r\n" + body)
    handler(connection, ("127.0.0.1", 12345), None)
    head, response = bytes(connection.response).split(b"\r\n\r\n", 1)
    status = int(head.split(b" ")[1])
    return status, head, response


def test_page_and_prediction(handler, capsys):
    status, head, body = request(handler, "GET", "/")
    assert status == 200
    assert b"text/html; charset=utf-8" in head
    assert "Crivo" in body.decode()
    assert b"Cache-Control: no-store" in head
    status, _, body = request(handler, "POST", "/predict", json.dumps({"text": "produto ótimo"}).encode())
    assert status == 200
    result = json.loads(body)
    assert result["decisao"] in ("positiva", "revisar")
    assert result["termos"]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("body", [b"{", b"[]", b"null", b"{}", b'{"text":12}', b'{"text":null}', b'\xff'])
def test_invalid_json_or_text_returns_400(handler, body):
    status, _, response = request(handler, "POST", "/predict", body)
    assert status == 400
    assert json.loads(response)["erro"]


@pytest.mark.parametrize("length", ["-1", "2.5", "abc", "+2", "1e5", ""])
def test_malformed_length_is_rejected(handler, length):
    status, _, _ = request(handler, "POST", "/predict", b"{}", [("Content-Length", length)])
    assert status == 400


def test_missing_duplicated_length_and_chunked_are_rejected(handler):
    for headers in [[], [("Content-Length", "2"), ("Content-Length", "2")],
                    [("Content-Length", "2"), ("Transfer-Encoding", "chunked")]]:
        status, _, _ = request(handler, "POST", "/predict", b"{}", headers)
        assert status == 400


def test_oversized_body_and_huge_numeric_header_are_rejected(handler):
    for length in [str(MAX_BODY_BYTES + 1), "9" * 5000]:
        status, _, _ = request(handler, "POST", "/predict", b"", [("Content-Length", length)])
        assert status == 413


def test_short_body_and_text_above_model_limit_are_rejected(handler):
    status, _, _ = request(handler, "POST", "/predict", b"{}", [("Content-Length", "20")])
    assert status == 400
    status, _, body = request(handler, "POST", "/predict", json.dumps({"text": "a" * 10001}).encode())
    assert status == 400
    assert "10 mil" in json.loads(body)["erro"]


@pytest.mark.parametrize("method,path", [("GET", "/predict"), ("POST", "/"), ("GET", "/favicon.ico")])
def test_unknown_routes_return_404(handler, method, path):
    status, _, _ = request(handler, method, path)
    assert status == 404


def test_html_treats_model_terms_as_text(handler):
    _, _, html = request(handler, "GET", "/")
    assert b"innerHTML" not in html
    assert b"name.textContent=term.termo" in html


def test_body_limit_is_inclusive_and_length_allows_leading_zeroes(handler):
    body = b'{"text":"produto"}'
    padded = body + b" " * (MAX_BODY_BYTES - len(body))
    status, _, _ = request(handler, "POST", "/predict", padded)
    assert status == 200
    status, _, _ = request(handler, "POST", "/predict", body,
                           [("Content-Length", "000" + str(len(body)))])
    assert status == 200


def test_examples_are_on_their_own_page(handler):
    _, _, response = request(handler, "GET", "/")
    html = response.decode()
    assert 'href="/exemplos"' in html
    assert "16.988" not in html
    assert "89,93%" not in html
    assert "1,90%" not in html
    assert "Jogo de panelas" not in html
    status, _, response = request(handler, "GET", "/exemplos")
    assert status == 200
    examples = response.decode()
    assert "Linha 14" in examples
    assert "Linha 79" in examples
    assert "Linha 345" in examples
    assert "Produto 29302228" in examples
    assert "4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv" in examples
    assert "CC BY-NC-SA 4.0" in examples


def test_shared_stylesheet_is_served(handler):
    status, headers, response = request(handler, "GET", "/style.css")
    assert status == 200
    assert b"text/css; charset=utf-8" in headers
    assert b"style-src 'self'" in headers
    assert b".shell" in response
