"""modelo linear, política de revisão e sinais simples para acompanhar lotes."""

import math
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

LABELS = ("negativa", "positiva")


MODEL_CANDIDATES = [
    {
        "name": "word40-c8",
        "c": 8.0,
        "max_features": 40000,
        "min_df": 3,
        "ngram_range": (1, 2),
    },
    {
        "name": "word100-c4",
        "c": 4.0,
        "max_features": 100000,
        "min_df": 2,
        "ngram_range": (1, 2),
    },
    {
        "name": "word100-c8",
        "c": 8.0,
        "max_features": 100000,
        "min_df": 2,
        "ngram_range": (1, 2),
    },
    {
        "name": "word150-c8",
        "c": 8.0,
        "max_features": 150000,
        "min_df": 2,
        "ngram_range": (1, 2),
    },
    {
        "name": "trigram100-c8",
        "c": 8.0,
        "max_features": 100000,
        "min_df": 2,
        "ngram_range": (1, 3),
    },
    {
        "name": "word-char-c4",
        "c": 4.0,
        "max_features": 60000,
        "min_df": 3,
        "ngram_range": (1, 2),
        "char": True,
    },
]


def build_model(
    c: float = 2.0, max_features=40000, min_df=3, ngram_range=(1, 2), char=False
) -> Pipeline:
    features = TfidfVectorizer(
        strip_accents="unicode",
        ngram_range=ngram_range,
        min_df=min_df,
        max_features=max_features,
        sublinear_tf=True,
    )
    if char:
        characters = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            strip_accents="unicode",
            min_df=3,
            max_features=50000,
            sublinear_tf=True,
        )
        features = FeatureUnion(
            [("word", features), ("char", characters)],
            transformer_weights={"word": 1.0, "char": 0.65},
        )
    return Pipeline(
        [
            ("tfidf", features),
            (
                "classifier",
                LogisticRegression(
                    C=c, solver="liblinear", max_iter=500, random_state=42
                ),
            ),
        ]
    )


def score_texts(model: Pipeline, texts: list[str]) -> tuple[np.ndarray, np.ndarray]:
    features = model["tfidf"].transform(texts)
    probabilities = model["classifier"].predict_proba(features)[:, 1]
    known = np.asarray(features.getnnz(axis=1) > 0).ravel()
    return probabilities, known


def wilson_upper(errors: int, total: int) -> float:
    if total == 0:
        return 1.0
    z = 1.96
    rate = errors / total
    return (
        rate
        + z * z / (2 * total)
        + z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total))
    ) / (1 + z * z / total)


def policy_metrics(labels, probabilities, known, threshold: float) -> dict:
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities)
    accepted = np.asarray(known) & (
        np.maximum(probabilities, 1 - probabilities) >= threshold
    )
    count = int(accepted.sum())
    errors = int(((probabilities >= 0.5) != labels)[accepted].sum())
    class_coverage = {
        name: float(accepted[labels == value].mean())
        if np.any(labels == value)
        else None
        for value, name in ((0, "negative_coverage"), (1, "positive_coverage"))
    }
    return {
        "threshold": float(threshold),
        "accepted": count,
        "errors": errors,
        "coverage": count / len(labels) if len(labels) else 0.0,
        "error_rate": errors / count if count else None,
        "wilson_upper_95": wilson_upper(errors, count) if count else None,
        **class_coverage,
    }


def select_threshold(labels, probabilities, known, target_error=0.10, min_accepted=100):
    curve = [
        policy_metrics(labels, probabilities, known, float(t))
        for t in np.round(np.arange(0.50, 1.00, 0.01), 2)
    ]
    feasible = [
        row
        for row in curve
        if row["accepted"] >= min_accepted and row["wilson_upper_95"] <= target_error
    ]
    # sem evidência suficiente, a política manda tudo para revisão
    selected = (
        max(feasible, key=lambda row: row["coverage"])
        if feasible
        else {
            "threshold": 1.01,
            "accepted": 0,
            "coverage": 0.0,
            "error_rate": None,
            "wilson_upper_95": None,
            "errors": 0,
        }
    )
    return selected, curve


def _contributions(model, vector, names, limit):
    contributions = vector.data * model["classifier"].coef_[0, vector.indices]
    order = np.argsort(-np.abs(contributions))[:limit]
    return [
        {
            "termo": str(names[vector.indices[i]]),
            "peso": round(float(contributions[i]), 4),
            "direcao": "positiva" if contributions[i] > 0 else "negativa",
        }
        for i in order
    ]


def explain(model: Pipeline, text: str, limit: int = 5) -> list[dict]:
    vector = model["tfidf"].transform([text]).tocsr()
    return _contributions(model, vector, model["tfidf"].get_feature_names_out(), limit)


def predict(bundle: dict, text: str) -> dict:
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError("envie um texto com até 10 mil caracteres")
    model = bundle["model"]
    vector = model["tfidf"].transform([text]).tocsr()
    probability = float(model["classifier"].predict_proba(vector)[0, 1])
    known = vector.nnz > 0
    if "feature_names" not in bundle:
        bundle["feature_names"] = model["tfidf"].get_feature_names_out()
    score = max(probability, 1 - probability)
    accepted = bool(known and score >= bundle["threshold"])
    reason = (
        "score_suficiente"
        if accepted
        else "score_baixo"
        if known
        else "sem_vocabulario"
    )
    return {
        "decisao": LABELS[int(probability >= 0.5)] if accepted else "revisar",
        "score": round(score, 4),
        "motivo": reason,
        "limiar": bundle["threshold"],
        "termos": _contributions(model, vector, bundle["feature_names"], 5),
    }


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))


def batch_signals(model, texts: list[str], threshold: float) -> dict:
    if not texts:
        raise ValueError("o lote precisa ter pelo menos um texto")
    probabilities, known = score_texts(model, texts)
    review = ~known | (np.maximum(probabilities, 1 - probabilities) < threshold)
    return {
        "rows": len(texts),
        "review_rate": float(review.mean()),
        "no_vocabulary_rate": float((~known).mean()),
        "short_text_rate": float(np.mean([word_count(t) <= 5 for t in texts])),
    }
