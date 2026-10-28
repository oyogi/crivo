"""comandos para reproduzir o experimento e testar o artefato local."""

import argparse
import json
from pathlib import Path

from .artifacts import ensure_model
from .data import download
from .model import batch_signals, predict
from .train import load_bundle, run


def main():
    parser = argparse.ArgumentParser(
        description="classifica avaliações ou pede revisão"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    get = commands.add_parser("download", help="baixa e confere o corpus original")
    get.add_argument("--csv", type=Path, default=Path("data/B2W-Reviews01.csv"))
    train = commands.add_parser("train", help="treina, escolhe limiar e avalia")
    train.add_argument("--csv", type=Path, default=Path("data/B2W-Reviews01.csv"))
    train.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    train.add_argument("--reports", type=Path, default=Path("reports"))
    train.add_argument(
        "--target-error",
        type=float,
        default=0.02,
        help="meta de erro na validação; padrão: 0.02",
    )
    infer = commands.add_parser("predict", help="classifica um texto")
    infer.add_argument("text")
    monitor = commands.add_parser("monitor", help="compara sinais de um lote jsonl")
    monitor.add_argument("input", type=Path)
    serve = commands.add_parser("serve", help="abre uma demo local no navegador")
    serve.add_argument("--port", type=int, default=8000)
    demo = commands.add_parser("demo", help="abre a demo com o modelo publicado")
    demo.add_argument("--port", type=int, default=8000)
    for cmd in (infer, monitor, serve, demo):
        cmd.add_argument("--model", type=Path, default=Path("artifacts/model.pkl"))
    args = parser.parse_args()
    try:
        if args.command == "download":
            print(download(args.csv))
        elif args.command == "train":
            result = run(args.csv, args.artifacts, args.reports, args.target_error)
            print(json.dumps(result["test"], indent=2, ensure_ascii=False))
        else:
            if args.command == "demo":
                ensure_model(args.model)
            bundle = load_bundle(args.model)
            if args.command == "predict":
                print(
                    json.dumps(predict(bundle, args.text), indent=2, ensure_ascii=False)
                )
            elif args.command in ("serve", "demo"):
                from .web import serve

                serve(bundle, args.port)
            else:
                with args.input.open(encoding="utf-8") as handle:
                    rows = [json.loads(line) for line in handle if line.strip()]
                if any(not isinstance(row, dict) or "text" not in row for row in rows):
                    raise ValueError(
                        "cada linha do lote deve ser um objeto json com o campo text"
                    )
                texts = [row["text"] for row in rows]
                if any(
                    not isinstance(text, str) or len(text) > 10000 for text in texts
                ):
                    raise ValueError(
                        "cada texto deve ser uma string com até 10 mil caracteres"
                    )
                signals = batch_signals(bundle["model"], texts, bundle["threshold"])
                delta = {
                    key: round(signals[key] - bundle["reference"][key], 4)
                    for key in signals
                    if key != "rows"
                }
                print(
                    json.dumps(
                        {
                            "signals": signals,
                            "delta_vs_test_reference": delta,
                            "note": "variação de sinais não prova queda de acurácia",
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"erro: {error}\n")


if __name__ == "__main__":
    main()
