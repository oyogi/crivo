"""fixtures pequenas para checar limpeza externa sem acesso à rede."""

import csv
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "evaluate_olist", Path(__file__).parents[1] / "scripts/evaluate_olist.py"
)
external = importlib.util.module_from_spec(spec)
spec.loader.exec_module(external)


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    return path


def test_external_removes_raw_b2w_overlap_duplicates_conflicts_and_three_stars(
    tmp_path,
):
    b2w = write_csv(
        tmp_path / "b2w.csv",
        ["review_text"],
        [["Já aparece no treino!"], ["texto de qualquer outra partição"]],
    )
    olist = write_csv(
        tmp_path / "olist.csv",
        ["review_comment_message", "review_score"],
        [
            ["JÁ aparece no treino...", 5],
            ["Texto de qualquer outra partição", 1],
            ["Boa experiência de compra", 5],
            ["BOA experiência de compra!", 4],
            ["conflito positivo e negativo", 1],
            ["conflito positivo e negativo", 5],
            ["conflito com três estrelas", 3],
            ["conflito com três estrelas", 1],
            ["avaliação mediana isolada", 3],
            ["produto não foi entregue", 1],
            ["", 5],
            ["...", 1],
            ["nota inválida", 6],
            ["outra nota inválida", "ruim"],
        ],
    )
    texts, labels, counts = external.load_external(olist, b2w)
    assert texts == ["Boa experiência de compra", "produto não foi entregue"]
    assert labels.tolist() == [1, 0]
    assert counts["raw_rows"] == 14
    assert counts["b2w_overlap_rows_removed"] == 2
    assert counts["duplicate_rows"] == 3
    assert counts["conflicting_text_groups_removed"] == 2
    assert counts["three_star_rows_removed"] == 1
    assert counts["empty_text"] == 2
    assert counts["invalid_rating"] == 2
    assert counts["evaluated_rows"] == 2


def test_wrong_csv_schema_has_a_clear_error(tmp_path):
    bad = write_csv(tmp_path / "bad.csv", ["title"], [["teste"]])
    b2w = write_csv(tmp_path / "b2w.csv", ["review_text"], [["avaliação"]])
    with pytest.raises(ValueError, match="olist sem as colunas"):
        external.load_external(bad, b2w)
    with pytest.raises(ValueError, match="b2w sem review_text"):
        external.load_external(bad, bad)
