"""treino e relatório; o teste só é consultado depois da seleção."""

import csv
import hashlib
import json
import pickle
import platform
import time
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score

from .data import SOURCE_REVISION, SOURCE_SHA256, partition, prepare, sha256
from .model import (
    MODEL_CANDIDATES,
    batch_signals,
    build_model,
    policy_metrics,
    score_texts,
    select_threshold,
    word_count,
)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def classification_metrics(labels, predictions) -> dict:
    if not len(labels):
        return {
            "accuracy": None,
            "macro_f1": None,
            "negative_recall": None,
            "confusion_matrix_negative_positive": [[0, 0], [0, 0]],
        }
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(
            f1_score(
                labels, predictions, average="macro", labels=[0, 1], zero_division=0
            )
        ),
        "negative_recall": float(
            recall_score(labels, predictions, pos_label=0, zero_division=0)
        ),
        "confusion_matrix_negative_positive": confusion_matrix(
            labels, predictions, labels=[0, 1]
        ).tolist(),
    }


def run(
    csv_path: Path, artifacts: Path, reports: Path, target_error: float = 0.02
) -> dict:
    if not 0 < target_error < 0.5:
        raise ValueError(
            "a meta de erro precisa ficar entre 0 e 0.5, sem incluir os extremos"
        )
    started = time.perf_counter()
    if sha256(csv_path) != SOURCE_SHA256:
        raise ValueError("o csv não corresponde à revisão documentada; rode download")
    reviews, cleaning = prepare(csv_path)
    parts = partition(reviews)
    texts = {key: [item.text for item in rows] for key, rows in parts.items()}
    labels = {
        key: np.array([item.label for item in parts[key]])
        for key in ("train", "validation", "test")
    }
    if any(len(np.unique(target)) != 2 for target in labels.values()):
        raise ValueError("cada conjunto binário precisa conter as duas classes")
    best_model, best_rank, selected_config = None, (-1.0, -1.0), None
    experiments = []
    for config in MODEL_CANDIDATES:
        model = build_model(
            **{key: value for key, value in config.items() if key != "name"}
        )
        model.fit(texts["train"], labels["train"])
        val_proba, known = score_texts(model, texts["validation"])
        score = float(f1_score(labels["validation"], val_proba >= 0.5, average="macro"))
        policy, _ = select_threshold(
            labels["validation"], val_proba, known, target_error=target_error
        )
        rank = (score, policy["coverage"])
        experiments.append(
            {
                "config": config,
                "validation_macro_f1": score,
                "validation_policy": policy,
            }
        )
        if rank > best_rank:
            best_model, best_rank, selected_config = model, rank, config
    model = best_model
    val_proba, val_known = score_texts(model, texts["validation"])
    selected, _ = select_threshold(
        labels["validation"], val_proba, val_known, target_error=target_error
    )
    threshold = selected["threshold"]
    test_proba, test_known = score_texts(model, texts["test"])
    predictions = test_proba >= 0.5
    dummy = DummyClassifier(strategy="most_frequent").fit(
        np.zeros((len(labels["train"]), 1)), labels["train"]
    )
    baseline = dummy.predict(np.zeros((len(labels["test"]), 1)))
    test_policy = policy_metrics(labels["test"], test_proba, test_known, threshold)
    reference = batch_signals(model, texts["test"], threshold)
    split_summary = {
        key: {
            "rows": len(rows),
            "products": len({item.product for item in rows}),
            "stars": dict(sorted(Counter(str(item.rating) for item in rows).items())),
        }
        for key, rows in parts.items()
    }
    # a curva no teste é diagnóstico; não volta para a seleção do limiar
    thresholds = sorted(
        set([float(t) for t in np.round(np.arange(0.5, 1, 0.01), 2)] + [threshold])
    )
    curve = [
        policy_metrics(labels["test"], test_proba, test_known, t) for t in thresholds
    ]
    slices = {}
    short = np.array([word_count(item.text) <= 5 for item in parts["test"]])
    for name, mask in (("up_to_5_words", short), ("over_5_words", ~short)):
        slices[name] = {
            "rows": int(mask.sum()),
            "forced": classification_metrics(labels["test"][mask], predictions[mask]),
            "policy": policy_metrics(
                labels["test"][mask], test_proba[mask], test_known[mask], threshold
            ),
        }
    summary = {
        "source_revision": SOURCE_REVISION,
        "source_sha256": SOURCE_SHA256,
        "cleaning": cleaning,
        "splits": split_summary,
        "split_row_sha256": {
            key: hashlib.sha256(
                "\n".join(str(r.row) for r in rows).encode()
            ).hexdigest()
            for key, rows in parts.items()
        },
        "experiments": experiments,
        "selected_C": model["classifier"].C,
        "target_error": target_error,
        "selected_config": selected_config,
        "validation_policy": selected,
        "test": {
            "baseline": classification_metrics(labels["test"], baseline),
            "forced": classification_metrics(labels["test"], predictions),
            "policy": test_policy,
            "slices": slices,
        },
        "three_star_diagnostic": batch_signals(
            model, texts["three_star_test"], threshold
        )
        if texts["three_star_test"]
        else None,
        "monitor_reference": reference,
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "vocabulary_size": len(model["classifier"].coef_[0]),
        "training_seconds": round(time.perf_counter() - started, 3),
    }
    artifacts.mkdir(parents=True, exist_ok=True)
    model_path = artifacts / "model.pkl"
    bundle = {
        "model": model,
        "threshold": threshold,
        "reference": reference,
        "sklearn_version": sklearn.__version__,
    }
    with model_path.open("wb") as handle:
        pickle.dump(bundle, handle, protocol=5)
    summary["model_sha256"] = sha256(model_path)
    write_json(artifacts / "metadata.json", summary)
    write_json(reports / "metrics.json", summary)
    reports.mkdir(parents=True, exist_ok=True)
    with (reports / "risk_coverage.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(curve[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(curve)
    confidence = np.maximum(test_proba, 1 - test_proba)
    mistakes = np.flatnonzero(predictions != labels["test"])
    worst = sorted(mistakes, key=lambda i: -confidence[i])[:15]
    write_json(
        reports / "errors.json",
        [
            {
                "source_csv_record": parts["test"][i].row,
                "stars": parts["test"][i].rating,
                "predicted": "positiva" if predictions[i] else "negativa",
                "score": round(float(confidence[i]), 4),
                "accepted": bool(test_known[i] and confidence[i] >= threshold),
            }
            for i in worst
        ],
    )
    write_report(reports / "resultado.md", summary)
    return summary


def write_report(path: Path, result: dict) -> None:
    test = result["test"]
    policy = test["policy"]
    risk = (
        "sem decisões automáticas"
        if policy["error_rate"] is None
        else f"{policy['error_rate']:.2%}"
    )
    diagnostic = result["three_star_diagnostic"]
    diagnostic_text = (
        f"No diagnóstico de três estrelas, {diagnostic['review_rate']:.2%} dos textos foram para revisão."
        if diagnostic
        else "Não há avaliações de três estrelas neste teste."
    )
    text = f"""# Resultado do experimento

Gerado por `uv run crivo train`. Fonte e versões estão em [metrics.json](metrics.json).
O teste contém {result["splits"]["test"]["rows"]:,} textos de produtos fora do treino.

| avaliação no teste | resultado |
| --- | ---: |
| macro-F1 do baseline de classe majoritária | {test["baseline"]["macro_f1"]:.4f} |
| macro-F1 do modelo, classificando tudo | {test["forced"]["macro_f1"]:.4f} |
| acurácia do modelo, classificando tudo | {test["forced"]["accuracy"]:.2%} |
| recall de negativas, classificando tudo | {test["forced"]["negative_recall"]:.2%} |
| limiar escolhido na validação | {policy["threshold"]:.2f} |
| cobertura automática | {policy["coverage"]:.2%} |
| erro entre decisões automáticas | {risk} |
| textos enviados para revisão | {1 - policy["coverage"]:.2%} |

O erro seletivo só considera os {policy["accepted"]:,} textos aceitos.
Não deve ser comparado ao erro total sem mostrar a cobertura ao lado.
A meta de validação usa o limite superior de Wilson de 95% para erro ≤{result["target_error"]:.0%},
com pelo menos 100 aceites. Isso é um critério de seleção, não uma garantia
de acurácia futura. Selecionar modelo e limiar na mesma validação também
introduz otimismo; o teste separado é a checagem que falta nessa seleção.

Foram comparadas {len(result["experiments"])} configurações; venceu {result["selected_config"]["name"]} pelo macro-F1
na validação, com cobertura como desempate. O vocabulário tem {result["vocabulary_size"]:,} features.
Tempo da execução: {result["training_seconds"]:.1f}s, sem incluir download.

{diagnostic_text}

[Curva de cobertura e erro](risk_coverage.csv) · [Erros de score alto](errors.json)

Os erros apontam o registro do CSV original, contando o cabeçalho, sem copiar avaliações para o Git.
O relatório também traz métricas separadas por textos de até cinco palavras
e textos mais longos. Esses recortes são diagnósticos, sem retreino por recorte.
"""
    path.write_text(text, encoding="utf-8")


def load_bundle(path: Path) -> dict:
    # pickle só deve ser aberto quando o arquivo foi produzido por você
    with path.open("rb") as handle:
        bundle = pickle.load(handle)
    if bundle["sklearn_version"] != sklearn.__version__:
        raise ValueError(
            "versão de scikit-learn diferente da usada no treino; retreine o modelo"
        )
    return bundle
