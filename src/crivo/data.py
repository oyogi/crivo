"""download verificável e preparação sem usar dados pessoais como features."""

import csv
import hashlib
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

SOURCE_REVISION = "4639429ec698d7821fc99a0bc665fa213d9fcd5a"
SOURCE_URL = (
    "https://raw.githubusercontent.com/americanas-tech/b2w-reviews01/"
    f"{SOURCE_REVISION}/B2W-Reviews01.csv"
)
SOURCE_SHA256 = "821fb0bf9f7230b0fba4e4f9fadd75a66d1a9ff0b1657810791d33007eb2ab38"


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def download(path: Path) -> Path:
    if path.exists():
        if sha256(path) != SOURCE_SHA256:
            raise ValueError("o csv existente não confere com o checksum da fonte")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".part")
    try:
        with urlopen(SOURCE_URL, timeout=120) as response, temporary.open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        if sha256(temporary) != SOURCE_SHA256:
            raise ValueError("download incompleto ou fonte diferente do esperado")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def normalize(text: str) -> str:
    return re.sub(r"\W+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def split_for(product: str) -> str:
    bucket = int(hashlib.sha256(f"na-duvida-v1:{product}".encode()).hexdigest(), 16) % 100
    return "train" if bucket < 70 else "validation" if bucket < 85 else "test"


@dataclass(frozen=True)
class Review:
    row: int
    product: str
    text: str
    rating: int

    @property
    def label(self) -> int:
        if self.rating == 3:
            raise ValueError("três estrelas não entra na tarefa binária")
        return int(self.rating >= 4)


def prepare(path: Path) -> tuple[list[Review], dict]:
    unique: dict[str, Review] = {}
    conflicts: set[str] = set()
    counts = Counter()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"product_id", "review_text", "overall_rating"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("csv sem as colunas esperadas; o delimitador é vírgula")
        for number, row in enumerate(reader, 2):
            counts["raw_rows"] += 1
            text = row["review_text"].strip()
            key = normalize(text)
            if not key:
                counts["empty_text"] += 1
                continue
            try:
                rating = int(row["overall_rating"])
            except (ValueError, TypeError):
                counts["invalid_rating"] += 1
                continue
            product = row["product_id"].strip()
            if rating not in range(1, 6) or not product:
                counts["invalid_rating_or_product"] += 1
                continue
            item = Review(number, product, text, rating)
            if key in unique:
                counts["duplicate_rows"] += 1
                old = unique[key]
                # notas diferentes dentro da mesma classe ainda representam o mesmo alvo
                old_class = 2 if old.rating == 3 else old.label
                new_class = 2 if rating == 3 else item.label
                if old_class != new_class:
                    conflicts.add(key)
            else:
                unique[key] = item
    clean = [item for key, item in unique.items() if key not in conflicts]
    counts["conflicting_text_groups_removed"] = len(conflicts)
    counts["clean_rows"] = len(clean)
    return clean, dict(counts)


def partition(reviews: list[Review]) -> dict[str, list[Review]]:
    parts = {name: [] for name in ("train", "validation", "test", "three_star_test")}
    for item in reviews:
        split = split_for(item.product)
        if item.rating == 3:
            if split == "test":
                parts["three_star_test"].append(item)
        else:
            parts[split].append(item)
    return parts
