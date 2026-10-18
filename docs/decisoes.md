# Algumas escolhas e o que ficou de fora

## Por que um modelo linear?

Para esse tamanho de projeto, uma boa pergunta é: um modelo barato já resolve
parte do problema? TF-IDF com regressão logística deixa o treino curto, roda
em CPU e permite inspecionar os pesos. Uma comparação com BERTimbau seria
interessante depois, medindo ganho, memória e latência sob o mesmo split.
Não houve essa comparação aqui, então não há conclusão sobre qual modelo vence.

Não removo stopwords: “não” pode inverter a opinião. Mantenho unigramas e
bigramas para capturar expressões como “não recomendo”. Isso ajuda em alguns
casos, mas não dá compreensão geral de negação, ironia ou contexto.

## Por que comparar com a classe majoritária?

O teste tem mais avaliações positivas. Um sistema que só diz “positiva” já
acerta 70,77%, mas tem recall zero para negativas. Macro-F1 dá o mesmo peso
às duas classes e deixa esse defeito mais claro. A matriz de confusão e o
recall de negativas também estão no JSON.

## O que a revisão está otimizando?

Não é “reconhecer texto difícil”. É reduzir o erro nas decisões automáticas,
aceitando encaminhar parte dos textos para uma pessoa. Para cada limiar de
0,50 a 0,99, em passos de 0,01, conto cobertura e erro na validação.
Uso o limite superior do intervalo de Wilson de 95%, não só a estimativa
pontual; um limiar que aceitou dois textos não ganha por sorte.

Uma primeira execução usou orçamento de 10% de erro. Na validação,
o modelo já errava cerca de 4,5%, então o limiar 0,50 aceitava quase tudo.
A meta foi apertada para 2% para estudar a troca entre erro e cobertura.
Os resultados do piloto, inclusive do teste, já tinham sido vistos durante
o desenvolvimento. Por isso os resultados finais são **exploratórios**,
e não um benchmark confirmatório com teste jamais consultado.
O código final escolhe C e limiar só na validação, mas uma avaliação rigorosa
posterior deve usar novos dados ainda não vistos pelo desenvolvimento.

A mesma validação escolhe C e limiar. O intervalo usado na seleção não corrige
o efeito de buscar vários candidatos. Também não considera dependência entre
avaliações do mesmo produto. “Limite de 2%” é orçamento para selecionar uma
política, não SLA, garantia estatística futura ou probabilidade individual.
No teste publicado o erro pontual ficou em 1,90%, enquanto o limite superior
de Wilson ultrapassa 2%. Isso permanece no relatório, sem retocar o limiar.

## Por que não retreinar com treino + validação?

O limiar foi escolhido para os scores daquele modelo, treinado só no treino.
Retreinar muda os scores e invalidaria essa escolha. O artefato salvo é o
mesmo modelo avaliado, sem esse retreino.

## O que vale investigar em seguida

- Coletar um lote rotulado no domínio de destino e congelar um teste externo.
- Calibrar scores em uma partição própria e verificar com reliability diagram.
- Medir incerteza por produto, com bootstrap agrupado, em vez de tratar linhas
  correlacionadas como observações independentes.
- Auditar rótulos discordantes e os erros de score alto antes de trocar de modelo.
- Comparar com um encoder em português mantendo o mesmo protocolo.

Referências técnicas: [extração de texto](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction),
[regressão logística](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression),
[métricas](https://scikit-learn.org/stable/modules/model_evaluation.html),
[persistência de modelos](https://scikit-learn.org/stable/model_persistence.html).
