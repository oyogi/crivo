"""entradas de lote inválidas precisam produzir erro legível, sem traceback."""

import sys

import pytest

from crivo import __main__ as cli


@pytest.mark.parametrize("content", ['null', '[]', '"texto"', '{}', '{"text": 42}'])
def test_monitor_rejects_invalid_jsonl_schema(tmp_path, monkeypatch, capsys, content):
    path = tmp_path / "lote.jsonl"
    path.write_text(content + "\n", encoding="utf-8")
    monkeypatch.setattr(cli, "load_bundle", lambda path: {})
    monkeypatch.setattr(sys, "argv", ["na-duvida", "monitor", str(path)])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    assert "erro:" in capsys.readouterr().err
