"""checagens da política e do modelo com exemplos sintéticos pequenos."""

import numpy as np
import pytest

from crivo.model import (
    batch_signals, build_model, explain, policy_metrics, predict,
    score_texts, select_threshold, wilson_upper,
)


@pytest.fixture
def fitted_model():
    texts = ["ótimo produto gostei bastante"] * 4 + ["péssimo produto defeito horrível"] * 4
    return build_model().fit(texts, [1] * 4 + [0] * 4)


def test_vectorizer_does_not_learn_test_tokens(fitted_model):
    vocabulary = dict(fitted_model["tfidf"].vocabulary_)
    _, known = score_texts(fitted_model, ["xilofonecosmico", "ótimo produto"])
    assert "xilofonecosmico" not in vocabulary
    assert fitted_model["tfidf"].vocabulary_ == vocabulary
    assert known.tolist() == [False, True]


def test_threshold_maximizes_coverage_under_validation_error_bound():
    labels = np.array([1] * 200 + [0] * 20)
    probabilities = np.array([0.9] * 200 + [0.6] * 20)
    selected, curve = select_threshold(
        labels, probabilities, np.ones(220, dtype=bool), target_error=0.05,
    )
    assert selected["threshold"] == 0.61
    assert selected["accepted"] == 200
    assert selected["errors"] == 0
    assert selected["wilson_upper_95"] <= 0.05
    feasible = [row for row in curve if row["accepted"] >= 100
                and row["wilson_upper_95"] <= 0.05]
    assert selected["coverage"] == max(row["coverage"] for row in feasible)
    assert curve[0]["error_rate"] == pytest.approx(20 / 220)


def test_impossible_target_or_insufficient_sample_falls_back_to_review():
    for labels, probabilities, target in [
        ([1] * 200, [0.99] * 200, 0.0),
        ([1] * 99, [0.99] * 99, 0.1),
    ]:
        selected, _ = select_threshold(labels, probabilities, [True] * len(labels), target)
        assert selected["threshold"] > 1
        assert selected["accepted"] == 0
        assert selected["coverage"] == 0
        assert selected["error_rate"] is None


def test_unknown_text_is_reviewed_even_with_extreme_intercept(fitted_model):
    fitted_model["classifier"].intercept_[:] = 50
    result = predict({"model": fitted_model, "threshold": 0.9}, "xilofonecosmico")
    assert result["score"] == 1.0
    assert result["decisao"] == "revisar"
    assert result["motivo"] == "sem_vocabulario"
    assert result["termos"] == []


def test_explanation_uses_actual_tfidf_times_linear_coefficients(fitted_model):
    text = "ótimo produto defeito horrível"
    contributions = explain(fitted_model, text, limit=100)
    features = fitted_model["tfidf"].transform([text])
    names = fitted_model["tfidf"].get_feature_names_out()
    classifier = fitted_model["classifier"]
    expected = {names[index]: float(value * classifier.coef_[0, index])
                for index, value in zip(features.indices, features.data)}
    assert set(row["termo"] for row in contributions) == set(expected)
    for row in contributions:
        assert row["peso"] == pytest.approx(expected[row["termo"]], abs=0.000051)
        assert row["direcao"] == ("positiva" if expected[row["termo"]] > 0 else "negativa")
    assert sum(row["peso"] for row in contributions) == pytest.approx(
        fitted_model.decision_function([text])[0] - classifier.intercept_[0], abs=0.001,
    )
    assert [abs(row["peso"]) for row in contributions] == sorted(
        [abs(row["peso"]) for row in contributions], reverse=True,
    )


def test_metrics_exclude_unknowns_and_handle_total_abstention():
    row = policy_metrics([1, 0, 1], [0.9, 0.9, 0.9], [True, False, True], 0.8)
    assert row["accepted"] == 2
    assert row["errors"] == 0
    assert row["coverage"] == pytest.approx(2 / 3)
    row = policy_metrics([1], [0.9], [False], 0.8)
    assert row["error_rate"] is None
    assert row["wilson_upper_95"] is None
    assert wilson_upper(0, 0) == 1.0
    assert wilson_upper(0, 100) > 0


def test_batch_rejects_empty_input_and_reports_unknown_text(fitted_model):
    with pytest.raises(ValueError, match="pelo menos um"):
        batch_signals(fitted_model, [], 0.8)
    signals = batch_signals(fitted_model, ["xilofonecosmico", "astronautazul"], 0.8)
    assert signals == {
        "rows": 2, "review_rate": 1.0, "no_vocabulary_rate": 1.0, "short_text_rate": 1.0,
    }


@pytest.mark.parametrize("text", [None, 123, "a" * 10001])
def test_predict_rejects_invalid_input(fitted_model, text):
    with pytest.raises(ValueError, match="até 10 mil"):
        predict({"model": fitted_model, "threshold": 0.8}, text)
