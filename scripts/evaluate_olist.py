"""avalia um modelo pronto na olist, sem ajustar treino ou limiar."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np

from crivo.data import SOURCE_SHA256 as B2W_SHA256
from crivo.data import normalize, sha256
from crivo.model import policy_metrics, score_texts
from crivo.train import classification_metrics, load_bundle, write_json

SOURCE_PAGE = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
SOURCE_URL = "https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce?datasetVersionNumber=2"
SOURCE_SHA256 = "012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7"
CSV_NAME = "olist_order_reviews_dataset.csv"


def download(path: Path) -> Path:
    if path.exists():
        if sha256(path) != SOURCE_SHA256:
            raise ValueError("o csv olist existente não confere com a versão usada")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    archive = path.with_suffix(".download.zip")
    temporary = path.with_suffix(".part")
    try:
        with urlopen(SOURCE_URL, timeout=120) as response, archive.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        with ZipFile(archive) as zipped:
            with zipped.open(CSV_NAME) as source, temporary.open("wb") as destination:
                while chunk := source.read(1024 * 1024):
                    destination.write(chunk)
        if sha256(temporary) != SOURCE_SHA256:
            raise ValueError("o csv olist baixado não confere com a versão usada")
        temporary.replace(path)
    finally:
        archive.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
    return path


def load_external(csv_path: Path, b2w_path: Path) -> tuple[list[str], np.ndarray, dict]:
    with b2w_path.open(encoding="utf-8-sig", newline="") as handle:
        source = csv.DictReader(handle)
        if "review_text" not in (source.fieldnames or []):
            raise ValueError("csv b2w sem review_text")
        b2w_texts = {normalize(row["review_text"]) for row in source}
    unique = {}
    conflicts = set()
    counts = Counter()
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        source = csv.DictReader(handle)
        if not {"review_comment_message", "review_score"}.issubset(
            source.fieldnames or []
        ):
            raise ValueError("csv olist sem as colunas esperadas")
        for row in source:
            counts["raw_rows"] += 1
            text = (row["review_comment_message"] or "").strip()
            key = normalize(text)
            if not key:
                counts["empty_text"] += 1
                continue
            if key in b2w_texts:
                counts["b2w_overlap_rows_removed"] += 1
                continue
            try:
                rating = int(row["review_score"])
            except (ValueError, TypeError):
                counts["invalid_rating"] += 1
                continue
            if rating not in range(1, 6):
                counts["invalid_rating"] += 1
                continue
            label = 2 if rating == 3 else int(rating >= 4)
            if key in unique:
                counts["duplicate_rows"] += 1
                if unique[key][1] != label:
                    conflicts.add(key)
            else:
                unique[key] = (text, label)
    clean = [value for key, value in unique.items() if key not in conflicts]
    counts["conflicting_text_groups_removed"] = len(conflicts)
    counts["three_star_rows_removed"] = sum(label == 2 for _, label in clean)
    binary = [(text, label) for text, label in clean if label != 2]
    counts["evaluated_rows"] = len(binary)
    counts["negative_rows"] = sum(label == 0 for _, label in binary)
    counts["positive_rows"] = sum(label == 1 for _, label in binary)
    return (
        [text for text, _ in binary],
        np.array([label for _, label in binary]),
        dict(counts),
    )


def evaluate(model_path: Path, texts: list[str], labels: np.ndarray) -> dict:
    bundle = load_bundle(model_path)
    probabilities, known = score_texts(bundle["model"], texts)
    return {
        "model_sha256": sha256(model_path),
        "threshold": bundle["threshold"],
        "forced": classification_metrics(labels, probabilities >= 0.5),
        "policy": policy_metrics(labels, probabilities, known, bundle["threshold"]),
    }


def run(
    csv_path: Path, b2w_path: Path, model_path: Path, baseline_path: Path | None = None
) -> dict:
    if sha256(csv_path) != SOURCE_SHA256:
        raise ValueError("o csv olist não corresponde à versão documentada")
    if sha256(b2w_path) != B2W_SHA256:
        raise ValueError("o csv b2w não corresponde à revisão documentada")
    texts, labels, cleaning = load_external(csv_path, b2w_path)
    if not texts or len(np.unique(labels)) != 2:
        raise ValueError("a avaliação externa precisa das duas classes")
    models = {"current": evaluate(model_path, texts, labels)}
    if baseline_path is not None:
        models["baseline"] = evaluate(baseline_path, texts, labels)
    return {
        "dataset": "Olist Brazilian E-Commerce Public Dataset",
        "source": SOURCE_PAGE,
        "download_url": SOURCE_URL,
        "source_version": 2,
        "source_sha256": SOURCE_SHA256,
        "license": "CC BY-NC-SA 4.0",
        "cleaning": cleaning,
        "evaluation_text_sha256": hashlib.sha256(
            "\n".join(normalize(t) for t in texts).encode()
        ).hexdigest(),
        "protocol": "avaliação externa; nenhum treino ou ajuste de limiar na olist; textos presentes em todo o b2w bruto excluídos",
        "models": models,
    }


def main():
    parser = argparse.ArgumentParser(
        description="avaliação externa com comentários da olist"
    )
    parser.add_argument("--csv", type=Path, default=Path("data") / CSV_NAME)
    parser.add_argument("--b2w", type=Path, default=Path("data/B2W-Reviews01.csv"))
    parser.add_argument("--model", type=Path, default=Path("artifacts/model.pkl"))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/external_olist.json")
    )
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    try:
        if args.download:
            download(args.csv)
        report = run(args.csv, args.b2w, args.model, args.baseline)
        write_json(args.output, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except (OSError, ValueError) as error:
        parser.exit(1, f"erro: {error}\n")


if __name__ == "__main__":
    main()
