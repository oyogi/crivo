# Desempenho

Conferência do benchmark em Linux, Python 3.14.8, Intel Core i5-1335U,
`OPENBLAS_NUM_THREADS=1`. Foram 500 predições completas, incluindo a análise
dos termos, sobre 200 textos do teste, após dez chamadas de aquecimento.
Não inclui carga do modelo ou HTTP.

| Caminho | Modelo | Mediana | P95 |
|---|---|---:|---:|
| Inferência da 0.2 | 40 mil features | 11,617 ms | 12,258 ms |
| Atual | 100 mil features | 0,347 ms | 0,437 ms |

O caminho `legacy` reproduz as duas transformações e a reconstrução dos nomes
em cada chamada. O atual transforma uma vez e mantém os nomes em cache.
A comparação troca também o modelo, como no uso das duas versões.
[Resultados e ambiente](../reports/benchmark_recheck.json).

## Reproduzir

Depois de baixar o corpus com `uv run crivo download`:

```bash
gh release download v0.2.0 --repo oyogi/crivo --pattern model.pkl --output artifacts/baseline.pkl
OPENBLAS_NUM_THREADS=1 uv run python scripts/benchmark.py --engine legacy --model artifacts/baseline.pkl --output artifacts/benchmark-legacy.json
OPENBLAS_NUM_THREADS=1 uv run python scripts/benchmark.py --model artifacts/model.pkl --output artifacts/benchmark-current.json
```

Os tempos variam entre máquinas e execuções. A medição original da versão 0.3
continua em [performance.json](../reports/performance.json).
