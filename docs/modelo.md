# Modelo

Crivo 0.3.0. TF-IDF com até 100 mil features e regressão logística.

| Entrada | Saída |
|---|---|
| Texto de uma avaliação | positiva, negativa ou revisar |

Treinado no B2W-Reviews01. Notas 1 e 2 definem a classe negativa; 4 e 5,
a positiva. Três estrelas fica fora do treino e aparece num diagnóstico
separado. Só o corpo da avaliação vira feature.

## Uso

`predict` analisa um texto; `serve` abre a interface local. Os pesos dos
termos ficam em “Ver análise”. O servidor não persiste os textos enviados.

`monitor` compara taxa de revisão, ausência de vocabulário e textos curtos
com a referência do teste. Esses sinais não medem acurácia sem novos rótulos.

## Limites

As notas podem discordar do texto. Ironia e opiniões mistas podem receber
score alto. O corpus é de 2018 e o modelo não foi avaliado em delivery.
O split não isola autores ou datas. O protocolo é exploratório;
[detalhes da avaliação](decisoes.md).

O pickle da [release](https://github.com/oyogi/crivo/releases/tag/v0.3.0)
corresponde ao modelo avaliado. Carregue apenas pickles de origem confiável.
As versões e o hash estão nos metadados da release.

Código MIT. Corpus, modelo e relatórios derivados: CC BY-NC-SA 4.0.
[Atribuição](dados.md).
