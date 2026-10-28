# O que os erros mostram

Três casos aceitos pelo modelo com score alto, mas discordantes da nota:

| Registro | Nota | Predição | Trecho |
|---|---:|---|---|
| 9045 | 1 | positiva | “Produto excelente, recomendo,e chegou antes do prazo!” |
| 8539 | 1 | positiva | “Ótimo produto ...recomendo ..chegou antes do prazo” |
| 127456 | 4 | negativa | “na segunda vez recebi um produto falsificado e veio pela metade.” |

Os dois primeiros textos elogiam a compra, apesar da nota baixa. O terceiro
reclama do produto, apesar da nota alta. Nesses casos, a divergência pode
estar na nota usada como rótulo. O score alto não resolve esse problema.

Os rótulos foram mantidos. Esses casos continuam contando como erros nas
métricas publicadas. Três exemplos não permitem atribuir todos os erros
à qualidade dos rótulos.

O registro conta as entradas do CSV incluindo o cabeçalho, não as linhas
físicas, pois uma avaliação pode conter quebras de linha.
[Todos os erros destacados](../reports/errors.json).

Fonte: [B2W-Reviews01](https://github.com/americanas-tech/b2w-reviews01/blob/4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv),
Real, Oshiro e Mafra / B2W Digital, CC BY-NC-SA 4.0.
