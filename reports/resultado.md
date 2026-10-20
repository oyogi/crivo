# Resultado do experimento

Gerado por `uv run crivo train`. Fonte e versões estão em [metrics.json](metrics.json).
O teste contém 16,988 textos de produtos fora do treino.

| avaliação no teste | resultado |
| --- | ---: |
| macro-F1 do baseline de classe majoritária | 0.4144 |
| macro-F1 do modelo, classificando tudo | 0.9409 |
| acurácia do modelo, classificando tudo | 95.12% |
| recall de negativas, classificando tudo | 91.22% |
| limiar escolhido na validação | 0.81 |
| cobertura automática | 89.93% |
| erro entre decisões automáticas | 1.90% |
| textos enviados para revisão | 10.07% |

O erro seletivo só considera os 15,278 textos aceitos.
Não deve ser comparado ao erro total sem mostrar a cobertura ao lado.
A meta de validação usa o limite superior de Wilson de 95% para erro ≤2%,
com pelo menos 100 aceites. Isso é um critério de seleção, não uma garantia
de acurácia futura. Selecionar modelo e limiar na mesma validação também
introduz otimismo; o teste separado é a checagem que falta nessa seleção.

Foram testados C=0.5, 2 e 8; venceu C=8 pelo macro-F1
na validação. O vocabulário tem 40,000 features.
Tempo da execução: 14.6s, sem incluir download.

No diagnóstico de três estrelas, 28.64%
dos textos foram para revisão. O modelo não foi treinado para reconhecer essa
nota, e rejeitar poucos textos desse grupo expõe uma limitação da política.

[Curva de cobertura e erro](risk_coverage.csv) · [Erros de score alto](errors.json)

Os erros apontam a linha do CSV original, sem copiar avaliações para o Git.
O relatório também traz métricas separadas por textos de até cinco palavras
e textos mais longos. Esses recortes são diagnósticos, sem retreino por recorte.
