# Ficha do modelo

**Nome:** Crivo v0.2.0. **Tipo:** TF-IDF + regressão logística binária.
**Entrada:** uma avaliação em português. **Saída:** positiva, negativa ou revisar,
com score e contribuições de termos. Treino e inferência locais, em CPU.

## Uso previsto

Experimento de classificação seletiva e apoio à triagem humana de avaliações
de produtos. Não valida intenção do cliente, gravidade da reclamação, fraude,
qualidade do estabelecimento nem necessidade de compensação.

## Treino e avaliação

Corpus B2W-Reviews01, avaliações de 2018. Somente o corpo do texto é entrada;
as estrelas são supervisão fraca. Divisão por produto após deduplicação;
detalhes em [dados.md](dados.md). C é selecionado na validação, assim como
o limiar de score. A política manda todo texto sem features conhecidas para
revisão, mesmo quando o intercepto gera score alto.

Os [resultados](../reports/resultado.md) se referem a um único split. O
[JSON](../reports/metrics.json) inclui contagens, versões, parâmetros, matriz
de confusão, recortes por comprimento, cobertura por classe e referência de
monitoramento. Os recortes curtos têm amostra pequena. O desenvolvimento
incluiu um piloto, explicado em [decisões.md](decisoes.md).

## Limitações

Score não calibrado; ironia e opiniões mistas podem passar com score alto.
A abstenção depende do score, não de uma compreensão de ambiguidade.
Três estrelas é um diagnóstico separado: não é classe aprendida nem base
para calcular acurácia binária. O split não isola autores e não é temporal.
Não foram feitas auditorias demográficas, ensaios de carga, avaliação em
delivery, comparação com LLM ou validação comercial.

As contribuições de termos são pesos locais do modelo linear, somados no
espaço de log-odds com um intercepto. Elas não explicam causas do sentimento
nem justificam decisões sobre pessoas. Nenhuma explicação é gerada por LLM.

## Operação e manutenção

`monitor` reporta sinais agregados e diferenças contra o lote de teste. A
referência é histórica, não uma janela móvel. Não há retreino automático nem
alarme baseado em rótulos que não existem. Novos dados rotulados devem
passar por avaliação antes de substituir o modelo e a referência juntos.
O projeto não persiste textos de inferência, mas o CSV de origem tem dados de
perfil e merece cuidado ao ser armazenado fora deste experimento.

`model.pkl` é produzido pelo treino local e não é versionado no Git. Pickle
pode executar código ao carregar: só abra artefatos que você mesmo treinou
ou cuja origem confia. A versão de scikit-learn é verificada **depois** da
leitura; essa verificação não torna um pickle externo seguro. O hash gerado
serve para identificar a execução, não é uma assinatura de confiança.

## Licença e origem

Código MIT. Corpus B2W Digital e derivados sob CC BY-NC-SA 4.0, com atribuição
de Real, Oshiro e Mafra (2019). O modelo não foi treinado com dados do iFood.
