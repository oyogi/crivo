"""a demo só publica downloads íntegros e preserva modelos locais."""

import hashlib
import io

import pytest

from crivo import artifacts


def test_demo_download_is_verified_and_atomic(tmp_path, monkeypatch):
    content = b"fixture de download, nunca carregada como pickle"
    path = tmp_path / "artifacts/model.pkl"
    monkeypatch.setattr(artifacts, "MODEL_SHA256", hashlib.sha256(content).hexdigest())
    monkeypatch.setattr(
        artifacts, "urlopen", lambda *args, **kwargs: io.BytesIO(content)
    )
    assert artifacts.ensure_model(path) == path
    assert path.read_bytes() == content
    assert not path.with_suffix(".download").exists()
    monkeypatch.setattr(
        artifacts, "urlopen", lambda *args, **kwargs: pytest.fail("download duplicado")
    )
    assert artifacts.ensure_model(path) == path


def test_corrupted_download_never_becomes_a_model(tmp_path, monkeypatch):
    path = tmp_path / "model.pkl"
    monkeypatch.setattr(
        artifacts, "urlopen", lambda *args, **kwargs: io.BytesIO(b"incompleto")
    )
    with pytest.raises(ValueError, match="não corresponde"):
        artifacts.ensure_model(path)
    assert not path.exists()
    assert not path.with_suffix(".download").exists()


def test_private_release_uses_authenticated_download(tmp_path, monkeypatch):
    import subprocess
    from urllib.error import HTTPError

    content = b"fixture de release privada"
    path = tmp_path / "model.pkl"
    monkeypatch.setattr(artifacts, "MODEL_SHA256", hashlib.sha256(content).hexdigest())
    monkeypatch.setattr(artifacts.shutil, "which", lambda name: "/test/gh")

    def private(*args, **kwargs):
        raise HTTPError(artifacts.MODEL_URL, 404, "private", {}, None)

    def authenticated(command, **kwargs):
        assert command[:4] == ["gh", "release", "download", "v0.3.0"]
        assert "oyogi/crivo" in command
        assert kwargs["timeout"] == 120
        path.with_suffix(".download").write_bytes(content)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(artifacts, "urlopen", private)
    monkeypatch.setattr(artifacts.subprocess, "run", authenticated)
    assert artifacts.ensure_model(path).read_bytes() == content
