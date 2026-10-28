"""obtém o modelo publicado quando a demo ainda não tem artefato local."""

import shutil
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from .data import sha256

MODEL_URL = "https://github.com/oyogi/crivo/releases/download/v0.3.0/model.pkl"
MODEL_SHA256 = "261583a46fabe6d1718cbfcf6f4b0f50a24f076323b675edbb37d0d40f78afc8"


def ensure_model(path: Path) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".download")
    try:
        try:
            with (
                urlopen(MODEL_URL, timeout=60) as response,
                temporary.open("wb") as output,
            ):
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        except HTTPError as error:
            if error.code not in (403, 404) or not shutil.which("gh"):
                raise ValueError(
                    "modelo indisponível; confira o acesso ao repositório"
                ) from error
            temporary.unlink(missing_ok=True)
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "release",
                        "download",
                        "v0.3.0",
                        "--repo",
                        "oyogi/crivo",
                        "--pattern",
                        "model.pkl",
                        "--output",
                        str(temporary),
                    ],
                    capture_output=True,
                    timeout=120,
                )
            except subprocess.TimeoutExpired as timeout:
                raise ValueError(
                    "o download do modelo excedeu o tempo limite"
                ) from timeout
            if result.returncode:
                raise ValueError(
                    "modelo indisponível; confira a autenticação do GitHub CLI"
                )
        if sha256(temporary) != MODEL_SHA256:
            raise ValueError("o modelo baixado não corresponde à release")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path
