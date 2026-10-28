"""mede a predição completa, incluindo os pesos exibidos pela interface."""

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

from crivo.data import partition, prepare
from crivo.model import predict
from crivo.train import load_bundle


def measure(bundle, texts, repetitions=500):
    for text in texts[:10]:
        predict(bundle, text)
    elapsed = []
    for i in range(repetitions):
        start = time.perf_counter_ns()
        predict(bundle, texts[i % len(texts)])
        elapsed.append((time.perf_counter_ns() - start) / 1e6)
    return {
        'repetitions': repetitions,
        'texts': len(texts),
        'median_ms': round(float(np.median(elapsed)), 4),
        'p95_ms': round(float(np.percentile(elapsed, 95)), 4),
        'mean_ms': round(float(np.mean(elapsed)), 4),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=Path('artifacts/model.pkl'))
    parser.add_argument('--csv', type=Path, default=Path('data/B2W-Reviews01.csv'))
    parser.add_argument('--output', type=Path, default=Path('reports/benchmark.json'))
    args = parser.parse_args()
    reviews, _ = prepare(args.csv)
    texts = [r.text for r in partition(reviews)['test'][:200]]
    result = measure(load_bundle(args.model), texts)
    result.update({'python': platform.python_version(), 'model_bytes': args.model.stat().st_size,
                   'scope': 'cpu local, sem http, depois de aquecer; mesma amostra de 200 textos'})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
