# Decisões do experimento

## Modelo

TF-IDF e regressão logística permitem treinar em CPU e inspecionar os pesos.
O vocabulário usa palavras e pares de palavras. Não removo stopwords para
preservar expressões como “não recomendo”. C=0,5, 2 e 8 são comparados pelo
macro-F1 na validação; venceu C=8.

O baseline sempre prevê a classe majoritária. Ele acerta 70,77% do teste,
mas não identifica nenhuma avaliação negativa. Por isso a comparação usa
macro-F1, além da matriz de confusão e do recall de negativas.

## Revisão

A validação escolhe o limiar de maior cobertura cujo limite superior de
Wilson de 95% para o erro fique em até 2%, com pelo menos 100 textos aceitos.
A busca percorre 0,50 a 0,99 em passos de 0,01. Sem candidato, tudo vai para
revisão. Textos sem termos conhecidos também vão para revisão.

No teste, o limiar 0,81 aceita 89,93% dos textos e erra 1,90% nessa parcela.
O limite superior de Wilson fica em 2,13%. A meta de validação não é uma
garantia sobre novos dados. Os scores não foram calibrados.

## Avaliação

O piloto usava uma meta de 10%, que aceitava quase tudo na validação.
A meta foi reduzida para 2% após o piloto, quando o primeiro resultado de
teste já havia sido visto. Os resultados publicados são exploratórios.

C e limiar compartilham a validação. O intervalo não corrige a busca entre
candidatos nem a dependência entre avaliações do mesmo produto.
O artefato salvo foi treinado só no treino; refazê-lo com a validação mudaria
os scores usados para escolher o limiar.

A limpeza remove conflitos de rótulo no corpus inteiro. As métricas valem
para essa base filtrada. O split isola produtos, mas não autores ou datas.

[Parâmetros e métricas](../reports/metrics.json) · [Erros](../reports/errors.json)
