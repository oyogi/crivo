# Decisões do experimento

## Modelo

TF-IDF e regressão logística permitem treinar em CPU e inspecionar os pesos.
O vocabulário usa sequências de uma a três palavras. Não removo stopwords
para preservar expressões como “não recomendo”. Seis configurações foram
comparadas pelo macro-F1 na validação: diferentes vocabulários, regularização,
trigramas e caracteres. Venceu trigram100-c8, com até 100 mil features,
min_df=2 e C=8. Os resultados de cada candidato estão em comparison.json.

O baseline sempre prevê a classe majoritária. Ele acerta 70,77% do teste,
mas não identifica nenhuma avaliação negativa. Por isso a comparação usa
macro-F1, além da matriz de confusão e do recall de negativas.

## Revisão

A validação escolhe o limiar de maior cobertura cujo limite superior de
Wilson de 95% para o erro fique em até 2%, com pelo menos 100 textos aceitos.
A busca percorre 0,50 a 0,99 em passos de 0,01. Sem candidato, tudo vai para
revisão. Textos sem termos conhecidos também vão para revisão.

No teste, o limiar 0,81 aceita 89,85% dos textos e erra 1,71% nessa parcela.
O limite superior de Wilson fica em 1,93%. A meta de validação não é uma
garantia sobre novos dados. Os scores não foram calibrados.

## Avaliação

O piloto usava uma meta de 10%, que aceitava quase tudo na validação.
A meta foi reduzida para 2% após o piloto, quando o primeiro resultado de
teste já havia sido visto. Os resultados publicados são exploratórios.

Modelo e limiar compartilham a validação. O intervalo não corrige a busca entre
candidatos nem a dependência entre avaliações do mesmo produto.
O artefato salvo foi treinado só no treino; refazê-lo com a validação mudaria
os scores usados para escolher o limiar.

A limpeza remove conflitos de rótulo no corpus inteiro. As métricas valem
para essa base filtrada. O split isola produtos, mas não autores ou datas.

[Parâmetros e métricas](../reports/metrics.json) · [Erros](../reports/errors.json)

## Comparação e dados externos

O teste B2W é o mesmo da versão 0.2, com os mesmos hashes de partição.
O novo modelo corrige 84 erros e introduz 52: saldo de 32 a menos.
O bootstrap pareado por produto, com 2.000 réplicas e semente 42, dá intervalo
percentil de 95% para o ganho de acurácia entre 0,051 e 0,330 ponto percentual.
Esse intervalo descreve o teste conhecido, sem transformar a exploração em
avaliação confirmatória. Reprodução: `uv run python scripts/compare.py --baseline modelo-antigo.pkl`.

A Olist foi reservada para avaliação externa depois da seleção no B2W.
Removi comentários vazios, duplicatas, conflitos, três estrelas e textos que
aparecem em qualquer partição do B2W bruto. Restaram 30.211 comentários.
Não houve treino ou ajuste de limiar na Olist. O erro seletivo externo é 3,88%,
com cobertura de 84,50%. O desempenho menor que no B2W expõe a mudança de fonte.

Reprodução: `uv run python scripts/evaluate_olist.py --download`.
A medição de tempo está em `scripts/benchmark.py`: 500 predições completas,
200 textos do teste, aquecimento de dez chamadas, sem incluir carga ou HTTP.
