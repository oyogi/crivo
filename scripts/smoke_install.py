"""confere o wheel instalado fora do ambiente editável do projeto."""

import json
import pickle
import subprocess
import sys
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

import sklearn

from crivo.model import build_model

for asset in ("demo.html", "examples.html", "style.css"):
    assert files("crivo").joinpath(asset).read_bytes()

with TemporaryDirectory() as directory:
    path = Path(directory) / "model.pkl"
    model = build_model().fit(
        ["ótimo produto recomendo"] * 3 + ["péssimo produto quebrado"] * 3,
        [1] * 3 + [0] * 3,
    )
    with path.open("wb") as handle:
        pickle.dump(
            {"model": model, "threshold": 0.5, "sklearn_version": sklearn.__version__},
            handle,
        )
    output = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "crivo",
            "predict",
            "ótimo recomendo",
            "--model",
            str(path),
        ],
        cwd=directory,
        text=True,
    )
    assert json.loads(output)["decisao"] == "positiva"
print("wheel instalado: inferência e arquivos da interface conferidos")
