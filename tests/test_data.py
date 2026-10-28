"""dados inventados só para testar limpeza e isolamento, sem download."""

import csv

import pytest

from crivo.data import Review, normalize, partition, prepare, split_for


def write_reviews(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["product_id", "review_text", "overall_rating"])
        writer.writerows(rows)
    return path


def test_duplicates_and_conflicting_labels_are_removed(tmp_path):
    path = write_reviews(
        tmp_path / "reviews.csv",
        [
            ("a", "Muito bom!", 4),
            ("b", "  MUITO bom...  ", 5),
            ("c", "opinião conflitante", 1),
            ("d", "opinião conflitante", 4),
            ("e", "neutro ou positivo", 3),
            ("f", "neutro ou positivo", 5),
            ("g", "negativo ou neutro", 2),
            ("h", "negativo ou neutro", 3),
            ("i", "texto único", 1),
        ],
    )
    reviews, counts = prepare(path)
    assert [(review.product, review.rating) for review in reviews] == [
        ("a", 4),
        ("i", 1),
    ]
    assert counts["duplicate_rows"] == 4
    assert counts["conflicting_text_groups_removed"] == 3
    assert counts["clean_rows"] == 2


def test_empty_invalid_rows_and_invalid_schema(tmp_path):
    path = write_reviews(
        tmp_path / "reviews.csv",
        [
            ("a", "...", 1),
            ("b", "texto de teste", "sem nota"),
            ("c", "outro texto", 6),
            ("", "produto ausente", 5),
            ("d", "avaliação válida", 3),
        ],
    )
    reviews, counts = prepare(path)
    assert len(reviews) == 1
    assert counts["empty_text"] == 1
    assert counts["invalid_rating"] == 1
    assert counts["invalid_rating_or_product"] == 2
    with pytest.raises(ValueError, match="três estrelas"):
        _ = reviews[0].label
    path.write_text("product_id;review_text;overall_rating\na;b;1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="delimitador"):
        prepare(path)


def test_products_and_normalized_texts_never_cross_partitions(tmp_path):
    products = {}
    for number in range(1000):
        product = f"produto-{number}"
        products.setdefault(split_for(product), product)
        if len(products) == 3:
            break
    rows = []
    for name, product in products.items():
        rows.extend(
            [
                (product, f"avaliação boa {name}", 5),
                (product, f"avaliação ruim {name}", 1),
                (product, f"avaliação média {name}", 3),
            ]
        )
    rows.append((products["test"], "AVALIAÇÃO BOA train!", 4))
    reviews, _ = prepare(write_reviews(tmp_path / "reviews.csv", rows))
    parts = partition(reviews)
    names = ("train", "validation", "test")
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            assert {r.product for r in parts[left]}.isdisjoint(
                r.product for r in parts[right]
            )
            assert {normalize(r.text) for r in parts[left]}.isdisjoint(
                normalize(r.text) for r in parts[right]
            )
    assert all(r.rating != 3 for name in names for r in parts[name])
    assert len(parts["three_star_test"]) == 1
    assert parts["three_star_test"][0].product == products["test"]
    assert {r.product for r in parts["three_star_test"]}.isdisjoint(
        r.product for name in ("train", "validation") for r in parts[name]
    )
    assert len(reviews) == 9
    assert len({normalize(r.text) for r in reviews}) == len(reviews)
    assert {normalize(r.text) for r in parts["three_star_test"]}.isdisjoint(
        normalize(r.text) for name in names for r in parts[name]
    )


def test_partition_is_independent_of_input_order():
    rows = [Review(i, f"produto-{i}", f"texto {i}", 5) for i in range(40)]
    first = partition(rows)
    second = partition(list(reversed(rows)))
    assert {name: set(values) for name, values in first.items()} == {
        name: set(values) for name, values in second.items()
    }
