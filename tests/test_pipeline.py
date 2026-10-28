"""treino completo em uma fixture pequena, sem rede ou corpus externo."""

import csv
import json

from crivo import train
from crivo.data import sha256
from crivo.model import predict


def test_train_save_load_predict_pipeline(tmp_path, monkeypatch):
    source = tmp_path / "reviews.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["product_id", "review_text", "overall_rating"])
        for product in range(800):
            writer.writerow(
                [
                    f"p{product}",
                    f"excelente gostei recomendo produto qualidade amostra {product}",
                    5,
                ]
            )
            writer.writerow(
                [
                    f"p{product}",
                    f"péssimo quebrado defeito devolução ruim amostra {product}",
                    1,
                ]
            )
    monkeypatch.setattr(train, "SOURCE_SHA256", sha256(source))
    monkeypatch.setattr(train, "MODEL_CANDIDATES", [{"name": "fixture", "c": 8.0}])
    artifacts, reports = tmp_path / "artifacts", tmp_path / "reports"
    result = train.run(source, artifacts, reports)
    bundle = train.load_bundle(artifacts / "model.pkl")
    assert result["model_sha256"] == sha256(artifacts / "model.pkl")
    assert result["test"]["forced"]["macro_f1"] > 0.95
    assert json.loads((reports / "metrics.json").read_text()) == result
    assert (reports / "risk_coverage.csv").exists()
    assert result["test"]["slices"]["up_to_5_words"]["forced"]["accuracy"] is None
    assert result["three_star_diagnostic"] is None
    assert predict(bundle, "excelente gostei recomendo")["decisao"] == "positiva"
    assert predict(bundle, "péssimo quebrado defeito")["decisao"] == "negativa"
    assert predict(bundle, "xilofonecosmico")["decisao"] == "revisar"
