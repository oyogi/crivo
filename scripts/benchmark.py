"""mede a predição completa, incluindo os pesos exibidos pela interface."""

import argparse
import json
import os
import platform
import time
from pathlib import Path

import numpy as np

from crivo.data import partition, prepare
from crivo.model import LABELS, explain, predict, score_texts
from crivo.train import load_bundle


def legacy_predict(bundle, text):
    model = bundle["model"]
    probabilities, known = score_texts(model, [text])
    probability = float(probabilities[0])
    score = max(probability, 1 - probability)
    accepted = bool(known[0] and score >= bundle["threshold"])
    return {
        "decisao": LABELS[int(probability >= 0.5)] if accepted else "revisar",
        "score": round(score, 4),
        "motivo": "score_suficiente"
        if accepted
        else "score_baixo"
        if known[0]
        else "sem_vocabulario",
        "limiar": bundle["threshold"],
        "termos": explain(model, text),
    }


def cpu_name():
    info = Path("/proc/cpuinfo")
    if info.exists():
        for line in info.read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or platform.machine()


def measure(bundle, texts, repetitions=500, predictor=predict):
    for text in texts[:10]:
        predictor(bundle, text)
    elapsed = []
    for i in range(repetitions):
        start = time.perf_counter_ns()
        predictor(bundle, texts[i % len(texts)])
        elapsed.append((time.perf_counter_ns() - start) / 1e6)
    return {
        "repetitions": repetitions,
        "texts": len(texts),
        "median_ms": round(float(np.median(elapsed)), 4),
        "p95_ms": round(float(np.percentile(elapsed, 95)), 4),
        "mean_ms": round(float(np.mean(elapsed)), 4),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.pkl"))
    parser.add_argument("--csv", type=Path, default=Path("data/B2W-Reviews01.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/benchmark.json"))
    parser.add_argument("--engine", choices=["current", "legacy"], default="current")
    args = parser.parse_args()
    reviews, _ = prepare(args.csv)
    texts = [r.text for r in partition(reviews)["test"][:200]]
    result = measure(
        load_bundle(args.model),
        texts,
        predictor=legacy_predict if args.engine == "legacy" else predict,
    )
    result.update(
        {
            "python": platform.python_version(),
            "engine": args.engine,
            "cpu": cpu_name(),
            "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS", "default"),
            "platform": platform.system(),
            "model_bytes": args.model.stat().st_size,
            "scope": "cpu local, sem http, depois de aquecer; mesma amostra de 200 textos",
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
