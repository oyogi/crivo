"""compara dois modelos no mesmo teste, reamostrando produtos em pares."""

import argparse
from pathlib import Path

import numpy as np

from crivo.data import SOURCE_SHA256, partition, prepare, sha256
from crivo.model import score_texts
from crivo.train import load_bundle, write_json


def compare(csv_path, baseline_path, model_path, repetitions=2000):
    if sha256(csv_path) != SOURCE_SHA256:
        raise ValueError("csv diferente da revisão do experimento")
    reviews = partition(prepare(csv_path)[0])["test"]
    labels = np.array([r.label for r in reviews])
    texts = [r.text for r in reviews]
    products, groups = np.unique([r.product for r in reviews], return_inverse=True)
    predictions, totals = [], []
    for path in (baseline_path, model_path):
        probabilities, _ = score_texts(load_bundle(path)["model"], texts)
        predicted = probabilities >= 0.5
        predictions.append(predicted)
        cells = labels * 2 + predicted
        totals.append(
            np.stack(
                [
                    np.bincount(groups, weights=cells == cell, minlength=len(products))
                    for cell in range(4)
                ],
                axis=1,
            )
        )

    def summarize(cells):
        tn, fp, fn, tp = cells
        return np.array(
            [
                (tn + tp) / sum(cells),
                (2 * tn / (2 * tn + fp + fn) + 2 * tp / (2 * tp + fp + fn)) / 2,
            ]
        )

    random = np.random.default_rng(42)
    differences = []
    for _ in range(repetitions):
        sample = random.integers(0, len(products), size=len(products))
        differences.append(
            summarize(totals[1][sample].sum(axis=0))
            - summarize(totals[0][sample].sum(axis=0))
        )
    intervals = np.quantile(differences, [0.025, 0.975], axis=0)
    previous, current = predictions
    return {
        "resampling_unit": "product_id",
        "replicates": repetitions,
        "seed": 42,
        "products": len(products),
        "baseline_wrong_winner_right": int(
            ((previous != labels) & (current == labels)).sum()
        ),
        "baseline_right_winner_wrong": int(
            ((previous == labels) & (current != labels)).sum()
        ),
        "paired_accuracy_delta_95_percentile": intervals[:, 0].tolist(),
        "paired_macro_f1_delta_95_percentile": intervals[:, 1].tolist(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("data/B2W-Reviews01.csv"))
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.pkl"))
    parser.add_argument(
        "--output", type=Path, default=Path("reports/paired_comparison.json")
    )
    args = parser.parse_args()
    write_json(args.output, compare(args.csv, args.baseline, args.model))
